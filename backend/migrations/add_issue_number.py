#!/usr/bin/env python3
"""
Migration script to add issue_number column to issues table
Usage: python add_issue_number.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database_config import DATABASE_URL, engine
from app.db_models import Issue, Project
from app.database_config import get_db
import re

def generate_project_code(project_name: str) -> str:
    """Generate a project code from project name"""
    # Remove special characters and convert to uppercase
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', project_name)
    words = clean_name.split()
    
    if len(words) >= 2:
        # Use first letter of first two words
        code = (words[0][0] + words[1][0]).upper()
    elif len(words) == 1 and len(words[0]) >= 3:
        # Use first 3 letters of single word
        code = words[0][:3].upper()
    elif len(words) == 1:
        # Use the whole word if short
        code = words[0].upper()
    else:
        code = "PROJ"
    
    return code[:4]  # Limit to 4 characters

def migrate_add_issue_number():
    """Add issue_number column and populate existing issues"""
    print("Starting migration: add issue_number column...")
    
    # Use the existing engine from database_config
    
    try:
        # Step 1: Add the column (allowing NULL initially)
        print("Adding issue_number column...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE issues ADD COLUMN IF NOT EXISTS issue_number VARCHAR(20)"))
            conn.commit()
        
        # Step 2: Populate existing issues with issue_number
        print("Populating issue_number for existing issues...")
        db = next(get_db())
        
        try:
            # Get all projects
            projects = db.query(Project).all()
            
            for project in projects:
                print(f"Processing project: {project.name}")
                project_code = generate_project_code(project.name)
                
                # Get issues for this project ordered by creation date
                issues = db.query(Issue).filter(
                    Issue.project_id == project.id
                ).order_by(Issue.created_at).all()
                
                # Assign sequential numbers
                for idx, issue in enumerate(issues, 1):
                    if not issue.issue_number:  # Only update if not already set
                        issue_number = f"{project_code}-{idx:03d}"
                        issue.issue_number = issue_number
                        print(f"  Issue '{issue.title[:50]}...' -> {issue_number}")
            
            db.commit()
            print("Successfully populated issue numbers")
            
        except Exception as e:
            db.rollback()
            print(f"Error populating issue numbers: {e}")
            return False
        finally:
            db.close()
        
        # Step 3: Make the column NOT NULL and add unique constraint
        print("Making issue_number NOT NULL and adding unique constraint...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE issues ALTER COLUMN issue_number SET NOT NULL"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_issues_issue_number ON issues (issue_number)"))
            conn.commit()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_add_issue_number()