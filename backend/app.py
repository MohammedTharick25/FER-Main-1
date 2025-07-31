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
app.secret_key = 'your_secret_key_here'  # Replace with a secure key in production

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

# Password strength requirement
MIN_PASSWORD_LENGTH = 8

# Load model
try:
    model = tf.keras.models.load_model(os.path.join(APP_ROOT, 'model_file_30epochs.h5'))
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Load Haar Cascade face detector
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
except:
    face_cascade = None
    print("Error loading face cascade.")

# Emotion labels
labels_dict = {
    0: 'Angry',
    1: 'Disgust',
    2: 'Fear',
    3: 'Happy',
    4: 'Neutral',
    5: 'Sad',
    6: 'Surprise'
}

# Emotion detection function
def detect_emotion(image):
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
            resized = cv2.resize(face, (48, 48)) / 255.0
            reshaped = np.reshape(resized, (1, 48, 48, 1))
            prediction = model.predict(reshaped)
            emotion_label = labels_dict[np.argmax(prediction)]
            emotions.append(emotion_label)

        return {"emotions": emotions}
    except Exception as e:
        return {"error": str(e)}, 500

# Email format validation
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Create default admin user
def create_admin_user():
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                name='Admin',
                email='admin@example.com',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

# Global template context
@app.context_processor
def inject_user():
    return dict(logged_in='username' in session)

# Routes
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
            session.permanent = remember
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        name = request.form['name']
        email = request.form['email']

        if User.query.filter_by(username=username).first():
            flash('Username exists', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already used', 'danger')
        elif len(password) < MIN_PASSWORD_LENGTH:
            flash(f'Password must be at least {MIN_PASSWORD_LENGTH} characters', 'danger')
        elif password != confirm:
            flash('Passwords do not match', 'danger')
        elif not is_valid_email(email):
            flash('Invalid email format', 'danger')
        else:
            user = User(
                username=username,
                password=generate_password_hash(password),
                name=name,
                email=email
            )
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', min_password_length=MIN_PASSWORD_LENGTH)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
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
        return jsonify({"error": "Unauthorized"}), 401
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    try:
        file = request.files['file']
        image = Image.open(file).convert('RGB')
        np_image = np.array(image)
        return jsonify(detect_emotion(np_image))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400
    try:
        image_data = data['image'].split(",")[1] if "," in data['image'] else data['image']
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        image_np = np.array(image)
        result = detect_emotion(image_np)
        if isinstance(result, tuple):  # error response
            return jsonify(result[0]), result[1]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    app.run(host='0.0.0.0', port=5500, debug=True)
