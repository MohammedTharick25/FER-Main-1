from app import app, db, User
from werkzeug.security import generate_password_hash

def initialize_database():
    with app.app_context():
        try:
            # First create all tables
            db.create_all()
            print("Database tables created successfully!")
            
            # Then check for admin user
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
                print("Admin user created successfully!")
            else:
                print("Admin user already exists")
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    initialize_database()