# backend/app/init_db.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database_config import engine, Base, get_db
from .db_models import *
import bcrypt
from datetime import datetime
import os

def create_tables():
    """Create all database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def check_database_connection():
    """Check if database connection is working"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_default_admin_user():
    """Create default admin user if none exists"""
    try:
        db = next(get_db())
        
        # Check if any admin user exists
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        if existing_admin:
            print(f"ℹ️  Admin user already exists: {existing_admin.username}")
            return True
        
        # Get admin credentials from environment or use defaults
        admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@docsmait.com")
        admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
        
        # Hash password
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create admin user
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=password_hash,
            is_admin=True,
            is_super_admin=True,
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Default admin user created successfully")
        print(f"   Username: {admin_username}")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print("   ⚠️  Please change the default password after first login!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating default admin user: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

def init_database():
    """Initialize database with tables and default data"""
    print("🚀 Initializing Docsmait database...")
    
    if not check_database_connection():
        return False
    
    if not create_tables():
        return False
    
    if not create_default_admin_user():
        return False
    
    print("✅ Database initialization completed successfully!")
    return True

if __name__ == "__main__":
    init_database()