#!/usr/bin/env python3
"""
Script to check and fix admin status for the first user (sganesh)
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append('backend')
sys.path.append('backend/app')

from backend.app.database_config import get_db
from backend.app.db_models import User

def check_and_fix_admin_status():
    """Check sganesh admin status and fix if needed"""
    
    db = next(get_db())
    
    try:
        # Find sganesh user
        sganesh_user = db.query(User).filter(User.username == "sganesh").first()
        
        if not sganesh_user:
            print("❌ User 'sganesh' not found!")
            return
            
        print(f"👤 Found user: {sganesh_user.username}")
        print(f"📧 Email: {sganesh_user.email}")
        print(f"🆔 ID: {sganesh_user.id}")
        print(f"👑 Is Admin: {sganesh_user.is_admin}")
        print(f"⭐ Is Super Admin: {sganesh_user.is_super_admin}")
        
        # Check if this should be the first user
        all_users = db.query(User).order_by(User.id).all()
        print(f"📊 Total users in database: {len(all_users)}")
        
        if all_users:
            first_user = all_users[0]
            print(f"🥇 First user in database: {first_user.username} (ID: {first_user.id})")
            
            # If sganesh is the first user but not admin, fix it
            if first_user.username == "sganesh" and not sganesh_user.is_admin:
                print("\n🔧 Fixing admin status...")
                sganesh_user.is_admin = True
                sganesh_user.is_super_admin = True
                db.commit()
                print("✅ Fixed! sganesh now has admin privileges.")
                
            elif first_user.username == "sganesh" and sganesh_user.is_admin:
                print("✅ Admin status is correct!")
                
            else:
                print(f"⚠️  Note: {first_user.username} is the first user, not sganesh")
        
        # Show final status
        db.refresh(sganesh_user)
        print(f"\n📋 Final status for {sganesh_user.username}:")
        print(f"   👑 Is Admin: {sganesh_user.is_admin}")
        print(f"   ⭐ Is Super Admin: {sganesh_user.is_super_admin}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_admin_status()