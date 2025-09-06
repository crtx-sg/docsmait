#!/usr/bin/env python3
"""
Migration: Add updated_at column to project_resources table
Date: 2025-09-04
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Add the backend app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from config import config

def run_migration():
    """Add updated_at column to project_resources table"""
    engine = create_engine(config.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'project_resources' 
            AND column_name = 'updated_at'
            """
            
            result = conn.execute(text(check_column_sql))
            column_exists = result.fetchone() is not None
            
            if column_exists:
                print("✅ Column 'updated_at' already exists in project_resources table")
                return True
            
            # Add the updated_at column
            add_column_sql = """
            ALTER TABLE project_resources 
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            """
            
            conn.execute(text(add_column_sql))
            
            # Update existing records to set updated_at = uploaded_at
            update_existing_sql = """
            UPDATE project_resources 
            SET updated_at = uploaded_at 
            WHERE updated_at IS NULL
            """
            
            conn.execute(text(update_existing_sql))
            conn.commit()
            
            print("✅ Successfully added 'updated_at' column to project_resources table")
            print("✅ Updated existing records with uploaded_at values")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def rollback_migration():
    """Remove updated_at column from project_resources table"""
    engine = create_engine(config.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column exists
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'project_resources' 
            AND column_name = 'updated_at'
            """
            
            result = conn.execute(text(check_column_sql))
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                print("✅ Column 'updated_at' does not exist in project_resources table")
                return True
            
            # Remove the updated_at column
            drop_column_sql = """
            ALTER TABLE project_resources 
            DROP COLUMN updated_at
            """
            
            conn.execute(text(drop_column_sql))
            conn.commit()
            
            print("✅ Successfully removed 'updated_at' column from project_resources table")
            return True
            
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = rollback_migration()
    else:
        success = run_migration()
    
    sys.exit(0 if success else 1)