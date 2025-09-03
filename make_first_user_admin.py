#!/usr/bin/env python3
"""
Database migration to ensure the first user has admin privileges
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def make_first_user_admin():
    """Make the first user (by ID) admin and super admin"""
    
    # Try different database URLs
    database_urls = [
        os.getenv("DATABASE_URL"),
        "postgresql://docsmait_user:docsmait_password@localhost:5432/docsmait",
        "postgresql://postgres:postgres@localhost:5432/docsmait",
        "sqlite:///./docsmait.db"
    ]
    
    for db_url in database_urls:
        if not db_url:
            continue
            
        print(f"🔍 Trying database: {db_url.split('@')[0] if '@' in db_url else db_url}")
        
        try:
            engine = create_engine(db_url)
            
            with engine.connect() as conn:
                # Check if users table exists
                result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'"))
                if result.scalar() == 0:
                    print("❌ Users table not found")
                    continue
                
                # Get first user (lowest ID)
                result = conn.execute(text("SELECT id, username, is_admin, is_super_admin FROM users ORDER BY id LIMIT 1"))
                first_user = result.fetchone()
                
                if not first_user:
                    print("❌ No users found in database")
                    continue
                
                user_id, username, is_admin, is_super_admin = first_user
                print(f"🎯 First user: {username} (ID: {user_id})")
                print(f"   Current admin status: {is_admin}")
                print(f"   Current super admin status: {is_super_admin}")
                
                if not is_admin or not is_super_admin:
                    print("🔧 Updating admin status...")
                    conn.execute(text(
                        "UPDATE users SET is_admin = true, is_super_admin = true WHERE id = :user_id"
                    ), {"user_id": user_id})
                    conn.commit()
                    print(f"✅ {username} now has admin privileges!")
                else:
                    print(f"✅ {username} already has admin privileges!")
                
                return True
                
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            continue
    
    print("❌ Could not connect to any database")
    print("\n🛠️  Manual fix options:")
    print("1. If using Docker: docker exec -it <container> psql -U <user> -d <db>")
    print("2. Then run: UPDATE users SET is_admin=true, is_super_admin=true WHERE id=(SELECT MIN(id) FROM users);")
    return False

if __name__ == "__main__":
    make_first_user_admin()