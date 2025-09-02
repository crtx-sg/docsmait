#!/usr/bin/env python3
"""
Docsmait Docker Setup Script

This script sets up Docsmait when running in Docker containers.
It's designed to be run from within the backend container.

Usage (from within backend container):
    python setup_docker.py [options]

Usage (from docker-compose):
    docker exec docsmait_backend python setup_docker.py [options]

Options:
    --admin-username USERNAME    Default admin username (default: admin)
    --admin-email EMAIL         Default admin email (default: admin@docsmait.com) 
    --admin-password PASSWORD   Default admin password (default: admin123)
    --skip-confirmation         Skip interactive confirmations
    --force-recreate           Force recreate admin user even if exists
    --help                      Show this help message
"""

import sys
import os
import argparse
from datetime import datetime

# Add the app directory to the path
sys.path.append('/app')

try:
    from app.init_db import check_database_connection, create_tables, create_default_admin_user
    from app.database_config import engine, get_db
    from app.db_models import User
    from sqlalchemy import text
    import bcrypt
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

def setup_docker_installation(admin_username="admin", admin_email="admin@docsmait.com", 
                             admin_password="admin123", skip_confirmation=False, force_recreate=False):
    """Set up Docsmait in Docker environment"""
    
    print("🐳 Docsmait Docker Setup")
    print("=" * 50)
    print(f"Admin Username: {admin_username}")
    print(f"Admin Email: {admin_email}")
    print(f"Admin Password: {'*' * len(admin_password)}")
    print(f"Force Recreate: {force_recreate}")
    print("=" * 50)
    
    if not skip_confirmation:
        response = input("\nProceed with Docker setup? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("❌ Setup cancelled")
            return False
    
    try:
        print("\n🔍 Step 1: Checking database connection...")
        if not check_database_connection():
            print("❌ Cannot connect to database. Make sure PostgreSQL container is running.")
            return False
        
        print("\n🗄️ Step 2: Creating database tables...")
        if not create_tables():
            print("❌ Failed to create database tables")
            return False
        
        print("\n👤 Step 3: Setting up admin user...")
        
        if force_recreate:
            # Delete existing admin user if force_recreate is True
            try:
                db = next(get_db())
                existing_admin = db.query(User).filter(User.username == admin_username).first()
                if existing_admin:
                    db.delete(existing_admin)
                    db.commit()
                    print(f"🗑️  Deleted existing admin user: {admin_username}")
                db.close()
            except Exception as e:
                print(f"⚠️  Warning: Could not delete existing admin user: {e}")
        
        # Set environment variables for the admin user creation
        os.environ["DEFAULT_ADMIN_USERNAME"] = admin_username
        os.environ["DEFAULT_ADMIN_EMAIL"] = admin_email 
        os.environ["DEFAULT_ADMIN_PASSWORD"] = admin_password
        
        if not create_default_admin_user():
            print("❌ Failed to create default admin user")
            return False
        
        print("\n✅ Docker setup completed successfully!")
        print("\n" + "=" * 50)
        print("🎉 DOCKER SETUP SUMMARY")
        print("=" * 50)
        print(f"✅ Database tables created")
        print(f"✅ Admin user ready")
        print(f"   Username: {admin_username}")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print("\n🌐 Access Information:")
        print("   Frontend: http://localhost:8501")
        print("   Backend API: http://localhost:8000")
        print("   Login with: EMAIL (not username)")
        print("\n⚠️  Security Notes:")
        print("   1. Change default password after first login")
        print("   2. Admin user has full system privileges")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Docker setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_docker_setup():
    """Verify that the Docker setup was successful"""
    try:
        print("\n🔍 Verifying Docker setup...")
        
        # Check if tables exist
        with engine.connect() as conn:
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"))
            tables = result.fetchall()
            print(f"✅ Found {len(tables)} database tables")
            
            # List some key tables
            key_tables = ['users', 'projects', 'documents', 'templates']
            found_key_tables = [t[0] for t in tables if t[0] in key_tables]
            print(f"✅ Key tables present: {', '.join(found_key_tables)}")
        
        # Check if admin user exists
        db = next(get_db())
        try:
            admin_users = db.query(User).filter(User.is_admin == True).all()
            if admin_users:
                for admin in admin_users:
                    print(f"✅ Admin user: {admin.username} ({admin.email})")
            else:
                print("❌ No admin users found")
                return False
        finally:
            db.close()
        
        print("✅ Docker setup verification successful")
        return True
        
    except Exception as e:
        print(f"❌ Docker setup verification failed: {e}")
        return False

def quick_user_creation(username, email, password, is_admin=False):
    """Quick utility to create a user"""
    try:
        db = next(get_db())
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"⚠️  User {username} already exists")
            return False
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin,
            is_super_admin=is_admin,
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ User created: {username} ({email}) - Admin: {is_admin}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create user {username}: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Docsmait Docker Setup Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--admin-username', default='admin',
                      help='Default admin username (default: admin)')
    parser.add_argument('--admin-email', default='admin@docsmait.com',
                      help='Default admin email (default: admin@docsmait.com)')
    parser.add_argument('--admin-password', default='admin123',
                      help='Default admin password (default: admin123)')
    parser.add_argument('--skip-confirmation', action='store_true',
                      help='Skip interactive confirmations')
    parser.add_argument('--force-recreate', action='store_true',
                      help='Force recreate admin user even if exists')
    parser.add_argument('--verify-only', action='store_true',
                      help='Only verify existing setup')
    parser.add_argument('--create-user', nargs=3, metavar=('USERNAME', 'EMAIL', 'PASSWORD'),
                      help='Create a regular user: USERNAME EMAIL PASSWORD')
    parser.add_argument('--create-admin', nargs=3, metavar=('USERNAME', 'EMAIL', 'PASSWORD'),
                      help='Create an admin user: USERNAME EMAIL PASSWORD')
    
    args = parser.parse_args()
    
    if args.verify_only:
        success = verify_docker_setup()
        sys.exit(0 if success else 1)
    
    if args.create_user:
        username, email, password = args.create_user
        success = quick_user_creation(username, email, password, is_admin=False)
        sys.exit(0 if success else 1)
    
    if args.create_admin:
        username, email, password = args.create_admin
        success = quick_user_creation(username, email, password, is_admin=True)
        sys.exit(0 if success else 1)
    
    # Run Docker setup
    success = setup_docker_installation(
        admin_username=args.admin_username,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        skip_confirmation=args.skip_confirmation,
        force_recreate=args.force_recreate
    )
    
    if success:
        verify_docker_setup()
        print("\n🎉 Docker setup complete! Docsmait is ready to use.")
    else:
        print("\n❌ Docker setup failed. Please check the errors above and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()