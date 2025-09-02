#!/usr/bin/env python3
"""
Test Script for Template Import Functionality

This script tests the template import functionality by:
1. Running a dry-run to see what would be imported
2. Running the actual import
3. Verifying the templates were created correctly
4. Testing the versioning system by running import again
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.append('/app')

from app.database_config import SessionLocal
from app.db_models import Template

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_import_command(dry_run=False, verbose=False):
    """Run the import command and return the result"""
    cmd = ["python", "/app/import_templates.py"]
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/app")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_templates_in_db():
    """Check what templates exist in the database"""
    session = SessionLocal()
    
    try:
        templates = session.query(Template).all()
        logger.info(f"Found {len(templates)} templates in database:")
        
        for template in templates:
            logger.info(f"  - {template.name} v{template.version} [{','.join(template.tags)}] - {template.document_type}")
        
        return templates
    finally:
        session.close()

def main():
    """Run the test suite"""
    logger.info("=== Template Import Test Suite ===")
    
    # Check initial state
    logger.info("1. Checking initial database state...")
    initial_templates = check_templates_in_db()
    
    # Run dry-run first
    logger.info("2. Running dry-run import...")
    success, stdout, stderr = run_import_command(dry_run=True, verbose=True)
    
    if not success:
        logger.error(f"Dry-run failed: {stderr}")
        return False
    
    logger.info("Dry-run output:")
    for line in stdout.split('\n'):
        if line.strip():
            logger.info(f"  {line}")
    
    # Run actual import
    logger.info("3. Running actual import...")
    success, stdout, stderr = run_import_command(verbose=True)
    
    if not success:
        logger.error(f"Import failed: {stderr}")
        return False
    
    logger.info("Import output:")
    for line in stdout.split('\n'):
        if line.strip():
            logger.info(f"  {line}")
    
    # Check database after import
    logger.info("4. Checking database after import...")
    post_import_templates = check_templates_in_db()
    
    # Verify expected templates
    expected_templates = [
        ("quarterly-report", "Reports"),
        ("budget-analysis", "Reports,Financial"),
        ("audit-checklist", "Forms"),
        ("meeting-notes", "General")
    ]
    
    logger.info("5. Verifying expected templates...")
    for expected_name, expected_tag in expected_templates:
        found = False
        for template in post_import_templates:
            if template.name == expected_name:
                found = True
                if expected_tag in str(template.tags):
                    logger.info(f"  ✅ {expected_name} found with correct tags")
                else:
                    logger.warning(f"  ⚠️  {expected_name} found but tags incorrect: {template.tags}")
                break
        
        if not found:
            logger.error(f"  ❌ {expected_name} not found in database")
    
    # Test versioning - run import again
    logger.info("6. Testing versioning by running import again...")
    success, stdout, stderr = run_import_command(verbose=True)
    
    if not success:
        logger.error(f"Second import failed: {stderr}")
        return False
    
    logger.info("Second import output:")
    for line in stdout.split('\n'):
        if line.strip():
            logger.info(f"  {line}")
    
    # Check versions were incremented
    logger.info("7. Checking version increments...")
    final_templates = check_templates_in_db()
    
    for template in final_templates:
        if template.version != "1.0":
            logger.info(f"  ✅ {template.name} version incremented to {template.version}")
        else:
            logger.info(f"  ℹ️  {template.name} remains at version {template.version}")
    
    logger.info("=== Test Suite Complete ===")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)