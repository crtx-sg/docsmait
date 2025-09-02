#!/usr/bin/env python3
"""
Template Bulk Import Script for Docsmait

This script imports Markdown templates from the /app/templates/ directory
into the Docsmait database with the following behavior:

Directory Structure:
- /app/templates/Reports/quarterly.md → name="quarterly", tags=["Reports"]
- /app/templates/Reports/Financial/budget.md → name="budget", tags=["Reports,Financial"]

Features:
- Processes all .md files recursively
- Extracts metadata from YAML frontmatter or content
- Auto-increments version for existing templates (1.0 → 1.1 → 1.2)
- Creates templates with document_type='Process Documents'
- Handles duplicate names by updating existing templates

Usage:
    python import_templates.py [--dry-run] [--verbose]
"""

import os
import sys
import re
import yaml
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Add the app directory to Python path
sys.path.append('/app')

from app.config import Config
from app.db_models import Base, Template, User
from app.database_config import SessionLocal, engine

# Configure logging
handlers = [logging.StreamHandler(sys.stdout)]

# Add file handler if logs directory exists
if os.path.exists('/app/logs'):
    handlers.append(logging.FileHandler('/app/logs/template_import.log', mode='a'))
elif os.path.exists('/app'):
    # Create logs directory
    os.makedirs('/app/logs', exist_ok=True)
    handlers.append(logging.FileHandler('/app/logs/template_import.log', mode='a'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

class TemplateImporter:
    """Handles bulk import of markdown templates from filesystem to database"""
    
    def __init__(self, templates_dir: str = "/app/templates", dry_run: bool = False):
        self.templates_dir = Path(templates_dir)
        self.dry_run = dry_run
        self.session = SessionLocal()
        
        # Get system user for created_by field (prefer admin user, fallback to any admin)
        self.system_user = self.session.query(User).filter(User.username == "admin").first()
        if not self.system_user:
            # Fallback to any admin user
            self.system_user = self.session.query(User).filter(User.is_admin == True).first()
        
        if not self.system_user:
            logger.error("No admin user found. Templates need a creator.")
            raise ValueError("Admin user required for template import")
            
        logger.info(f"Using user '{self.system_user.username}' as template creator")
    
    def extract_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter from markdown content"""
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1)) or {}
                content_body = match.group(2)
                return frontmatter, content_body
            except yaml.YAMLError as e:
                logger.warning(f"Invalid YAML frontmatter: {e}")
                return {}, content
        
        return {}, content
    
    def extract_description(self, content: str, frontmatter: Dict, filename: str) -> str:
        """Extract description from frontmatter, content, or filename"""
        # Priority: frontmatter > first heading > filename
        if 'description' in frontmatter:
            return frontmatter['description']
        
        # Look for first heading or comment
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            if line.startswith('<!-- ') and line.endswith(' -->'):
                return line[5:-4].strip()
        
        # Fallback to filename (without extension)
        return filename.replace('_', ' ').replace('-', ' ').title()
    
    def generate_tags_from_path(self, file_path: Path) -> List[str]:
        """Generate hierarchical tags from file path relative to templates directory"""
        relative_path = file_path.relative_to(self.templates_dir)
        path_parts = relative_path.parts[:-1]  # Exclude filename
        
        if not path_parts:
            return ["General"]  # Default tag for root level files
        
        # Create hierarchical tag: "Reports,Financial,Quarterly"
        hierarchical_tag = ",".join(path_parts)
        return [hierarchical_tag]
    
    def increment_version(self, current_version: str) -> str:
        """Increment version number: 1.0 → 1.1, 1.9 → 1.10, 2.5 → 2.6"""
        try:
            parts = current_version.split('.')
            if len(parts) >= 2:
                major = int(parts[0])
                minor = int(parts[1])
                return f"{major}.{minor + 1}"
            else:
                return "1.1"
        except (ValueError, IndexError):
            return "1.1"
    
    def get_next_version(self, template_name: str) -> str:
        """Get the next version number for a template"""
        existing_template = self.session.query(Template).filter(
            Template.name == template_name
        ).first()
        
        if existing_template:
            return self.increment_version(existing_template.version)
        else:
            return "1.0"
    
    def process_markdown_file(self, file_path: Path) -> Optional[Dict]:
        """Process a single markdown file and return template data"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            if not raw_content.strip():
                logger.warning(f"Empty file skipped: {file_path}")
                return None
            
            # Extract frontmatter and content
            frontmatter, content_body = self.extract_frontmatter(raw_content)
            
            # Generate template data
            filename_without_ext = file_path.stem
            template_data = {
                'name': frontmatter.get('name', filename_without_ext),
                'description': self.extract_description(content_body, frontmatter, filename_without_ext),
                'document_type': frontmatter.get('document_type', 'Process Documents'),
                'content': raw_content,  # Store full content including frontmatter
                'tags': frontmatter.get('tags', self.generate_tags_from_path(file_path)),
                'version': frontmatter.get('version', self.get_next_version(frontmatter.get('name', filename_without_ext))),
                'status': frontmatter.get('status', 'active'),
                'created_by': self.system_user.id,
                'file_path': str(file_path)  # For logging
            }
            
            return template_data
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None
    
    def save_template(self, template_data: Dict) -> bool:
        """Save or update template in database"""
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would import: {template_data['name']} v{template_data['version']}")
                return True
            
            # Check if template exists
            existing_template = self.session.query(Template).filter(
                Template.name == template_data['name']
            ).first()
            
            if existing_template:
                # Update existing template
                for key, value in template_data.items():
                    if key not in ['file_path', 'created_by']:  # Don't update these fields
                        setattr(existing_template, key, value)
                
                logger.info(f"Updated template: {template_data['name']} → v{template_data['version']}")
                action = "updated"
            else:
                # Create new template with UUID
                template_dict = {k: v for k, v in template_data.items() if k != 'file_path'}
                template_dict['id'] = str(uuid.uuid4())
                new_template = Template(**template_dict)
                self.session.add(new_template)
                logger.info(f"Created template: {template_data['name']} v{template_data['version']}")
                action = "created"
            
            self.session.commit()
            return True
            
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Database integrity error for {template_data['name']}: {e}")
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving template {template_data['name']}: {e}")
            return False
    
    def import_templates(self) -> Dict[str, int]:
        """Import all templates from the templates directory"""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        
        if not self.templates_dir.exists():
            logger.error(f"Templates directory not found: {self.templates_dir}")
            return stats
        
        logger.info(f"Starting template import from: {self.templates_dir}")
        logger.info(f"Dry run mode: {self.dry_run}")
        
        # Find all markdown files recursively
        markdown_files = list(self.templates_dir.glob("**/*.md"))
        logger.info(f"Found {len(markdown_files)} markdown files")
        
        for file_path in markdown_files:
            stats['processed'] += 1
            logger.debug(f"Processing: {file_path}")
            
            # Process the file
            template_data = self.process_markdown_file(file_path)
            
            if template_data is None:
                stats['skipped'] += 1
                continue
            
            # Save to database
            if self.save_template(template_data):
                # Determine if it was created or updated
                existing = self.session.query(Template).filter(
                    Template.name == template_data['name']
                ).first()
                
                if not self.dry_run and existing and existing.version != "1.0":
                    stats['updated'] += 1
                else:
                    stats['created'] += 1
            else:
                stats['errors'] += 1
        
        return stats
    
    def close(self):
        """Clean up database connection"""
        if hasattr(self, 'session'):
            self.session.close()

def main():
    """Main entry point for the script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import markdown templates into Docsmait database")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--templates-dir', default='/app/templates', help='Templates directory path')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    importer = None
    try:
        # Create importer and run import
        importer = TemplateImporter(templates_dir=args.templates_dir, dry_run=args.dry_run)
        stats = importer.import_templates()
        
        # Print summary
        logger.info("=== Import Summary ===")
        logger.info(f"Files processed: {stats['processed']}")
        logger.info(f"Templates created: {stats['created']}")
        logger.info(f"Templates updated: {stats['updated']}")
        logger.info(f"Files skipped: {stats['skipped']}")
        logger.info(f"Errors: {stats['errors']}")
        
        if args.dry_run:
            logger.info("This was a dry run - no changes were made to the database")
        
        # Return appropriate exit code
        sys.exit(0 if stats['errors'] == 0 else 1)
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
    
    finally:
        if importer:
            importer.close()

if __name__ == "__main__":
    main()