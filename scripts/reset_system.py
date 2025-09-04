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
    from backend.app.db_models import *
    import qdrant_client
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy import text, create_engine
    import os
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    sys.exit(1)

# Create database connection for host system
def get_host_db_connection():
    """Create database connection that works from host system"""
    # Use localhost with external port for host access
    host_db_url = os.getenv(
        "HOST_DATABASE_URL",
        "postgresql://docsmait_user:docsmait_password@localhost:5433/docsmait"
    )
    
    try:
        engine = create_engine(host_db_url, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal(), engine
    except Exception as e:
        # Fallback: try to connect via Docker network (if script runs inside container)
        docker_db_url = "postgresql://docsmait_user:docsmait_password@docsmait_postgres:5432/docsmait"
        try:
            engine = create_engine(docker_db_url, echo=False)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            return SessionLocal(), engine
        except Exception:
            raise e

def reset_database(keep_admin: bool = False, keep_settings: bool = False):
    """Reset the database to initial state"""
    print("🗄️  Resetting database...")
    
    try:
        db, engine = get_host_db_connection()
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False
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
            # Activity logs (no dependencies)
            'activity_logs',
            
            # Code review related tables (maintain dependency order)
            'code_comments',
            'code_reviews', 
            'pull_request_files',
            'pull_requests',
            'repositories',
            
            # Audit management tables
            'corrective_actions',
            'findings',
            'audits',
            
            # Review and training tables
            'review_requests',
            'training_records',
            
            # Document management tables (maintain dependency order)
            'document_comments',
            'document_reviews',
            'document_reviewers',
            'document_revisions',
            'documents',
            
            # Template management
            'template_approvals',
            'templates',
            
            # Project management
            'project_resources',
            'project_members',
            'projects',
            
            # Knowledge base tables
            'kb_document_tags',
            'kb_queries',
            'kb_documents',
            'kb_collections',
            'kb_config',
            
            # Traceability and compliance
            'traceability_matrix',
            'compliance_standards',
            
            # Records management tables
            'customer_complaints',
            'non_conformances',
            'parts_inventory',
            'suppliers',
            'lab_equipment_calibration',
            
            # System engineering tables
            'post_market_records',
            'compliance_records',
            'test_artifacts',
            'design_artifacts',
            'fmea_analyses',
            'system_hazards',
            'system_requirements'
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
        
        # Reset sequences - only reset sequences that actually exist
        sequences_to_reset = [
            'users_id_seq',
            'project_members_id_seq',
            'template_approvals_id_seq',
            'document_reviewers_id_seq',
            'kb_queries_id_seq',
            'kb_document_tags_id_seq',
            'system_settings_id_seq',
            'activity_logs_id_seq',
            'training_records_id_seq',
            'suppliers_supplier_id_seq',
            'parts_inventory_part_id_seq',
            'lab_equipment_calibration_equipment_id_seq',
            'customer_complaints_complaint_id_seq',
            'non_conformances_nc_id_seq'
        ]
        
        # Get list of existing sequences
        try:
            existing_sequences_result = db.execute(text("""
                SELECT sequence_name FROM information_schema.sequences 
                WHERE sequence_schema = 'public'
            """))
            existing_sequences = [row[0] for row in existing_sequences_result]
            
            for seq in sequences_to_reset:
                if seq in existing_sequences:
                    try:
                        db.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
                        print(f"  ✅ Reset sequence: {seq}")
                    except Exception as e:
                        print(f"  ⚠️  Warning resetting sequence {seq}: {e}")
                        # Rollback this transaction and continue with a new one
                        db.rollback()
                        db.commit()  # Start fresh transaction
                else:
                    print(f"  ⚠️  Sequence {seq} does not exist, skipping")
        except Exception as e:
            print(f"  ⚠️  Error checking sequences: {e}")
            db.rollback()
            db.commit()  # Start fresh transaction
        
        # Restore admin users
        if keep_admin and admin_data:
            try:
                for user_data in admin_data:
                    # Remove the 'id' field if present to let the database auto-assign
                    user_data_clean = {k: v for k, v in user_data.items() if k != 'id'}
                    user = User(**user_data_clean)
                    db.add(user)
                db.commit()  # Commit after each major section
                print(f"  ✅ Restored {len(admin_data)} admin users")
            except Exception as e:
                print(f"  ⚠️  Error restoring admin users: {e}")
                db.rollback()
        
        # Restore settings
        if keep_settings and settings_data:
            try:
                for setting_data in settings_data:
                    setting = SystemSetting(**setting_data)
                    db.add(setting)
                db.commit()  # Commit after each major section
                print(f"  ✅ Restored {len(settings_data)} settings")
            except Exception as e:
                print(f"  ⚠️  Error restoring settings: {e}")
                db.rollback()
        
        # Final commit for any remaining transactions
        try:
            db.commit()
            print("✅ Database reset complete")
            return True
        except Exception as e:
            print(f"⚠️  Warning on final commit: {e}")
            db.rollback()
            return False
        
    except Exception as e:
        try:
            db.rollback()
        except:
            pass  # Ignore rollback errors if connection is already closed
        print(f"❌ Database reset failed: {e}")
        return False
    finally:
        try:
            db.close()
        except:
            pass  # Ignore close errors

def reset_knowledge_base():
    """Reset the knowledge base"""
    print("🧠 Resetting knowledge base...")
    
    try:
        # Use host-accessible Qdrant URL (port 6335 as seen in docker ps)
        qdrant_url = os.getenv("HOST_QDRANT_URL", "http://localhost:6335")
        
        # Suppress warnings temporarily for version compatibility
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            qdrant_client_instance = qdrant_client.QdrantClient(url=qdrant_url)
        
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