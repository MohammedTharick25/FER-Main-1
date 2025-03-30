from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import cv2
import numpy as np
import tensorflow as tf
import base64
from io import BytesIO
from PIL import Image
import os
import re

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key_here'  # Change this in production

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Configure paths
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(APP_ROOT, 'templates')
STATIC_FOLDER = os.path.join(APP_ROOT, 'static')

app.template_folder = TEMPLATE_FOLDER
app.static_folder = STATIC_FOLDER

# Password requirements
MIN_PASSWORD_LENGTH = 8

# Load the trained model
try:
    model = tf.keras.models.load_model(os.path.join(APP_ROOT, 'model_file_30epochs.h5'))
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Load OpenCV face detector
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
except:
    try:
        face_cascade = cv2.CascadeClassifier(os.path.join(APP_ROOT, 'haarcascade_frontalface_default.xml'))
    except Exception as e:
        print(f"Error loading face cascade: {e}")
        face_cascade = None

# Emotion labels
labels_dict = {0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Neutral', 5: 'Sad', 6: 'Surprise'}

def detect_emotion(image):
    """Detects faces in the image and predicts emotion for each detected face."""
    if face_cascade is None or model is None:
        return {"error": "Model or face detector not loaded"}, 500
    
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return {"emotions": ["No Face Detected"]}

        emotions = []
        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            resized_face = cv2.resize(face, (48, 48)) / 255.0
            reshaped_face = np.reshape(resized_face, (1, 48, 48, 1))

            result = model.predict(reshaped_face)
            label = np.argmax(result, axis=1)[0]
            emotions.append(labels_dict[label])

        return {"emotions": emotions}
    except Exception as e:
        return {"error": str(e)}, 500

def is_valid_email(email):
    """Check if the email is valid."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_admin_user():
    """Create admin user if it doesn't exist"""
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                name='Admin User',
                email='admin@example.com',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")

# Context processor to make 'logged_in' available to all templates
@app.context_processor
def inject_user():
    return dict(logged_in='username' in session)

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/recognition')
def recognition():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('recognition.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = username
            if remember:
                session.permanent = True
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        name = request.form['name']
        email = request.form['email']

        # Validation checks
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
        elif len(password) < MIN_PASSWORD_LENGTH:
            flash(f'Password must be at least {MIN_PASSWORD_LENGTH} characters long', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match', 'danger')
        elif not is_valid_email(email):
            flash('Please enter a valid email address', 'danger')
        else:
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                name=name,
                email=email
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html', min_password_length=MIN_PASSWORD_LENGTH)

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/users')
def user_list():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('users.html', users=User.query.all(), current_user=session.get('username'))

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        file = request.files['file']
        image = Image.open(file).convert('RGB')
        image = np.array(image)
        return jsonify(detect_emotion(image))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400

    try:
        if ',' in data['image']:
            image_data = data['image'].split(",")[1]
        else:
            image_data = data['image']
            
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        image = np.array(image)
        return jsonify(detect_emotion(image))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    app.run(host='127.0.0.1', port=5500, debug=True)