#!/usr/bin/env python3
# backend/migrate_to_postgres.py
"""
Migration script to move data from SQLite to PostgreSQL
Run this script when upgrading from SQLite to PostgreSQL
"""

import os
import sqlite3
import sys
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database_config import DATABASE_URL
from app.db_models import User, Project, ProjectMember, Template, Document
from app.init_db import create_tables

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    
    # SQLite database path
    sqlite_path = os.getenv("SQLITE_DATABASE_PATH", "/app/users.db")
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found at {sqlite_path}")
        print("   If your SQLite database is elsewhere, set SQLITE_DATABASE_PATH environment variable")
        return False
    
    print(f"🔄 Starting migration from {sqlite_path} to PostgreSQL...")
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to PostgreSQL
        pg_engine = create_engine(DATABASE_URL)
        
        # Ensure PostgreSQL tables exist
        print("📋 Creating PostgreSQL tables...")
        if not create_tables():
            return False
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
        pg_session = SessionLocal()
        
        # Migrate Users
        print("👥 Migrating users...")
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        for user_row in users:
            existing_user = pg_session.query(User).filter(User.id == user_row['id']).first()
            if not existing_user:
                user = User(
                    id=user_row['id'],
                    username=user_row['username'],
                    email=user_row['email'],
                    password_hash=user_row['password_hash'],
                    is_admin=bool(user_row['is_admin']),
                    created_at=user_row['created_at']
                )
                pg_session.add(user)
        
        pg_session.commit()
        print(f"✅ Migrated {len(users)} users")
        
        # Migrate Projects (if table exists)
        try:
            sqlite_cursor.execute("SELECT * FROM projects")
            projects = sqlite_cursor.fetchall()
            
            print("📁 Migrating projects...")
            for project_row in projects:
                existing_project = pg_session.query(Project).filter(Project.id == project_row['id']).first()
                if not existing_project:
                    project = Project(
                        id=project_row['id'],
                        name=project_row['name'],
                        description=project_row['description'],
                        created_by=project_row['created_by'],
                        created_at=project_row['created_at'],
                        updated_at=project_row['updated_at']
                    )
                    pg_session.add(project)
            
            pg_session.commit()
            print(f"✅ Migrated {len(projects)} projects")
            
        except sqlite3.OperationalError:
            print("⚠️  No projects table found in SQLite database")
        
        # Add more migrations for templates, documents, etc. as needed
        
        pg_session.close()
        sqlite_conn.close()
        
        print("🎉 Migration completed successfully!")
        print("📝 Next steps:")
        print("   1. Update your .env file to use DATABASE_URL")
        print("   2. Restart your application")
        print("   3. Verify all data migrated correctly")
        print("   4. Backup your SQLite database before removing it")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Docsmait SQLite to PostgreSQL Migration")
    print("=" * 50)
    
    # Check if PostgreSQL is available
    try:
        pg_engine = create_engine(DATABASE_URL)
        with pg_engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ Cannot connect to PostgreSQL: {e}")
        print("   Make sure PostgreSQL container is running and DATABASE_URL is correct")
        sys.exit(1)
    
    if migrate_data():
        print("\n🎉 Migration successful! Your application is now using PostgreSQL.")
    else:
        print("\n❌ Migration failed. Please check the errors above and try again.")
        sys.exit(1)