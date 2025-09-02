#!/usr/bin/env python3
"""
Docsmait System Reset Script

This script provides a nuclear reset option for the Docsmait system,
completely wiping all data and returning the system to initial state.

⚠️  DANGER: This will permanently delete ALL data in the system!

Usage:
    python reset_system.py [options]

Options:
    --keep-admin            Keep the admin user accounts
    --keep-settings         Keep system settings (SMTP, etc.)
    --confirm               Required flag to actually perform reset
    --help                  Show this help message
"""

import sys
import os
import argparse
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.app.database_config import get_db, engine
    from backend.app.config import config
    from backend.app.db_models import *
    import qdrant_client
    from sqlalchemy.orm import Session
    from sqlalchemy import text
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    sys.exit(1)

def reset_database(keep_admin: bool = False, keep_settings: bool = False):
    """Reset the database to initial state"""
    print("🗄️  Resetting database...")
    
    db = next(get_db())
    try:
        # Store admin users if keeping them
        admin_users = []
        if keep_admin:
            admin_users = db.query(User).filter(User.is_admin == True).all()
            admin_data = [{
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'is_admin': user.is_admin,
                'is_super_admin': user.is_super_admin
            } for user in admin_users]
        
        # Store settings if keeping them
        settings_data = []
        if keep_settings:
            settings = db.query(SystemSetting).all()
            settings_data = [{
                'key': setting.key,
                'value': setting.value,
                'category': setting.category,
                'description': setting.description
            } for setting in settings]
        
        # Delete all data in correct order (respecting foreign keys)
        tables_to_clear = [
            'code_comments',
            'code_reviews', 
            'pull_request_files',
            'pull_requests',
            'repositories',
            'corrective_actions',
            'findings',
            'audits',
            'review_requests',
            'training_records',
            'document_reviews',
            'document_reviewers',
            'document_revisions',
            'documents',
            'template_approvals',
            'templates',
            'project_resources',
            'project_members',
            'projects',
            'kb_document_tags',
            'kb_queries',
            'kb_documents',
            'kb_collections',
            'kb_config',
            'traceability_matrices',
            'compliance_standards'
        ]
        
        if not keep_settings:
            tables_to_clear.append('system_settings')
        if not keep_admin:
            tables_to_clear.append('users')
        
        for table in tables_to_clear:
            try:
                db.execute(text(f"DELETE FROM {table}"))
                print(f"  ✅ Cleared table: {table}")
            except Exception as e:
                print(f"  ⚠️  Warning clearing {table}: {e}")
        
        # Reset sequences
        sequences_to_reset = [
            'users_id_seq',
            'project_members_id_seq',
            'project_resources_id_seq',
            'template_approvals_id_seq',
            'document_reviewers_id_seq',
            'document_reviews_id_seq',
            'kb_queries_id_seq',
            'kb_document_tags_id_seq',
            'system_settings_id_seq'
        ]
        
        for seq in sequences_to_reset:
            try:
                db.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
            except Exception as e:
                print(f"  ⚠️  Warning resetting sequence {seq}: {e}")
        
        # Restore admin users
        if keep_admin and admin_data:
            for user_data in admin_data:
                user = User(**user_data)
                db.add(user)
            print(f"  ✅ Restored {len(admin_data)} admin users")
        
        # Restore settings
        if keep_settings and settings_data:
            for setting_data in settings_data:
                setting = SystemSetting(**setting_data)
                db.add(setting)
            print(f"  ✅ Restored {len(settings_data)} settings")
        
        db.commit()
        print("✅ Database reset complete")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Database reset failed: {e}")
        raise
    finally:
        db.close()

def reset_knowledge_base():
    """Reset the knowledge base"""
    print("🧠 Resetting knowledge base...")
    
    try:
        qdrant_client_instance = qdrant_client.QdrantClient(url=config.QDRANT_URL)
        
        # Get all collections
        collections = qdrant_client_instance.get_collections()
        
        # Delete all collections
        for collection in collections.collections:
            try:
                qdrant_client_instance.delete_collection(collection.name)
                print(f"  ✅ Deleted collection: {collection.name}")
            except Exception as e:
                print(f"  ⚠️  Warning deleting collection {collection.name}: {e}")
        
        print("✅ Knowledge base reset complete")
        
    except Exception as e:
        print(f"❌ Knowledge base reset failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description='Docsmait System Reset Script - DANGER: This will delete ALL data!',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--keep-admin', action='store_true',
                      help='Keep admin user accounts')
    parser.add_argument('--keep-settings', action='store_true', 
                      help='Keep system settings')
    parser.add_argument('--confirm', action='store_true', required=True,
                      help='Required flag to confirm you want to reset the system')
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("❌ The --confirm flag is required to perform a system reset")
        return
    
    print("🚨" * 20)
    print("DOCSMAIT SYSTEM RESET")
    print("🚨" * 20)
    print("⚠️  This will permanently delete ALL data in the system!")
    print(f"Keep admin users: {args.keep_admin}")
    print(f"Keep settings: {args.keep_settings}")
    print()
    
    # Final confirmation
    print("Type 'RESET EVERYTHING' to confirm:")
    confirmation = input().strip()
    
    if confirmation != 'RESET EVERYTHING':
        print("❌ Reset cancelled - confirmation phrase not matched")
        return
    
    print("\n🚀 Starting system reset...")
    start_time = datetime.now()
    
    try:
        # Reset database
        reset_database(keep_admin=args.keep_admin, keep_settings=args.keep_settings)
        
        # Reset knowledge base
        reset_knowledge_base()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "="*50)
        print("🎉 SYSTEM RESET COMPLETE")
        print("="*50)
        print(f"Duration: {duration}")
        print(f"Timestamp: {end_time}")
        
        if args.keep_admin:
            print("ℹ️  Admin users were preserved")
        else:
            print("⚠️  All users were deleted - you'll need to create a new admin user")
        
        if args.keep_settings:
            print("ℹ️  System settings were preserved")
        else:
            print("⚠️  All settings were reset - reconfigure SMTP and other settings")
        
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ System reset failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()