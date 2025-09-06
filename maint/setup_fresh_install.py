#!/usr/bin/env python3
"""
Docsmait Fresh Installation Setup Script

This script sets up a fresh Docsmait installation by:
1. Initializing the database with all tables
2. Creating default admin user
3. Setting up basic configuration

Usage:
    python setup_fresh_install.py [options]

Options:
    --admin-username USERNAME    Default admin username (default: admin)
    --admin-email EMAIL         Default admin email (default: admin@docsmait.com) 
    --admin-password PASSWORD   Default admin password (default: admin123)
    --skip-confirmation         Skip interactive confirmations
    --help                      Show this help message

Environment Variables:
    You can also set these via environment variables:
    DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD
"""

import sys
import os
import argparse
from datetime import datetime

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.append(backend_path)

try:
    from app.init_db import init_database, check_database_connection, create_tables, create_default_admin_user
    from app.database_config import engine
    from app.db_models import User
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from app.database_config import get_db
    import bcrypt
except ImportError as e:
    print(f"❌ Error importing backend modules: {e}")
    print("Make sure you're running this script from the docsmait root directory")
    sys.exit(1)

def setup_fresh_installation(admin_username="admin", admin_email="admin@docsmait.com", admin_password="admin123", skip_confirmation=False):
    """Set up a fresh Docsmait installation"""
    
    print("🚀 Docsmait Fresh Installation Setup")
    print("=" * 50)
    print(f"Admin Username: {admin_username}")
    print(f"Admin Email: {admin_email}")
    print(f"Admin Password: {'*' * len(admin_password)}")
    print("=" * 50)
    
    if not skip_confirmation:
        response = input("\nProceed with fresh installation? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("❌ Installation cancelled")
            return False
    
    try:
        print("\n🔍 Step 1: Checking database connection...")
        if not check_database_connection():
            print("❌ Cannot connect to database. Check your database configuration.")
            return False
        
        print("\n🗄️ Step 2: Creating database tables...")
        if not create_tables():
            print("❌ Failed to create database tables")
            return False
        
        print("\n👤 Step 3: Creating default admin user...")
        
        # Set environment variables for the admin user creation
        os.environ["DEFAULT_ADMIN_USERNAME"] = admin_username
        os.environ["DEFAULT_ADMIN_EMAIL"] = admin_email 
        os.environ["DEFAULT_ADMIN_PASSWORD"] = admin_password
        
        if not create_default_admin_user():
            print("❌ Failed to create default admin user")
            return False
        
        print("\n✅ Fresh installation completed successfully!")
        print("\n" + "=" * 50)
        print("🎉 INSTALLATION SUMMARY")
        print("=" * 50)
        print(f"✅ Database tables created")
        print(f"✅ Admin user created")
        print(f"   Username: {admin_username}")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print("\n⚠️  IMPORTANT SECURITY NOTES:")
        print("   1. Change the default admin password after first login")
        print("   2. The admin user has full system privileges")
        print("   3. Access the application at http://localhost:8501")
        print("   4. Use EMAIL (not username) for login")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fresh installation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_installation():
    """Verify that the installation was successful"""
    try:
        print("\n🔍 Verifying installation...")
        
        # Check if tables exist
        with engine.connect() as conn:
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"))
            tables = result.fetchall()
            print(f"✅ Found {len(tables)} database tables")
        
        # Check if admin user exists
        db = next(get_db())
        try:
            admin_user = db.query(User).filter(User.is_admin == True).first()
            if admin_user:
                print(f"✅ Admin user exists: {admin_user.username} ({admin_user.email})")
            else:
                print("❌ No admin user found")
                return False
        finally:
            db.close()
        
        print("✅ Installation verification successful")
        return True
        
    except Exception as e:
        print(f"❌ Installation verification failed: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Docsmait Fresh Installation Setup Script',
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
    parser.add_argument('--verify-only', action='store_true',
                      help='Only verify existing installation')
    
    args = parser.parse_args()
    
    if args.verify_only:
        success = verify_installation()
        sys.exit(0 if success else 1)
    
    # Run fresh installation
    success = setup_fresh_installation(
        admin_username=args.admin_username,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        skip_confirmation=args.skip_confirmation
    )
    
    if success:
        verify_installation()
        print("\n🎉 Setup complete! You can now start using Docsmait.")
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()