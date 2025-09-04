#!/usr/bin/env python3
"""
Docsmait Backup Script
Backs up PostgreSQL database, Qdrant vector database, and configuration files
"""

import os
import sys
import json
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocsmaitBackup:
    def __init__(self, backup_dir="/tmp/docsmait_backup"):
        self.backup_dir = Path(backup_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_name = f"docsmait_backup_{self.timestamp}"
        self.backup_path = self.backup_dir / self.backup_name
        
        # Docker container names
        self.postgres_container = "docsmait_postgres"
        self.qdrant_container = "docsmait_qdrant"
        
        # Database credentials from environment or defaults
        self.db_name = os.getenv("DB_NAME", "docsmait")
        self.db_user = os.getenv("DB_USER", "docsmait_user")
        self.db_password = os.getenv("DB_PASSWORD", "docsmait_password")
        
    def create_backup_directory(self):
        """Create backup directory structure"""
        try:
            self.backup_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created backup directory: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")
            return False
    
    def validate_database_tables(self):
        """Validate that all expected tables exist in the database"""
        try:
            logger.info("Validating database tables...")
            
            # Expected tables from the system
            expected_tables = [
                'users', 'projects', 'project_members', 'project_resources',
                'templates', 'template_approvals', 'documents', 'document_revisions',
                'document_reviewers', 'document_reviews', 'document_comments',
                'kb_collections', 'kb_documents', 'kb_queries', 'kb_config', 'kb_document_tags',
                'audits', 'findings', 'corrective_actions', 'repositories', 'pull_requests',
                'pull_request_files', 'code_reviews', 'code_comments', 'review_requests',
                'training_records', 'traceability_matrix', 'compliance_standards',
                'system_settings', 'activity_logs', 'suppliers', 'parts_inventory',
                'lab_equipment_calibration', 'customer_complaints', 'non_conformances',
                'system_requirements', 'system_hazards', 'fmea_analyses', 'design_artifacts',
                'test_artifacts', 'compliance_records', 'post_market_records'
            ]
            
            # Check tables exist
            cmd = [
                "docker", "exec", self.postgres_container,
                "psql", "-U", self.db_user, "-d", self.db_name, "-t", "-c",
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  env={**os.environ, "PGPASSWORD": self.db_password})
            
            if result.returncode == 0:
                existing_tables = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                missing_tables = [table for table in expected_tables if table not in existing_tables]
                
                if missing_tables:
                    logger.warning(f"Missing tables detected: {missing_tables}")
                else:
                    logger.info("All expected tables found in database")
                
                return True
            else:
                logger.error(f"Failed to validate tables: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Table validation error: {e}")
            return False

    def backup_postgres(self):
        """Backup PostgreSQL database"""
        try:
            logger.info("Starting PostgreSQL backup...")
            postgres_backup_file = self.backup_path / "postgres_backup.sql"
            
            # Use docker exec to run pg_dump with comprehensive options
            cmd = [
                "docker", "exec", self.postgres_container,
                "pg_dump", "-U", self.db_user, "-d", self.db_name,
                "--no-password",
                "--verbose",
                "--clean",
                "--create",
                "--if-exists",
                "--disable-triggers",
                "--single-transaction"
            ]
            
            with open(postgres_backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, 
                                      text=True, env={**os.environ, "PGPASSWORD": self.db_password})
            
            if result.returncode == 0:
                logger.info(f"PostgreSQL backup completed: {postgres_backup_file}")
                # Validate backup includes all tables
                self.validate_backup_contents(postgres_backup_file)
                return True
            else:
                logger.error(f"PostgreSQL backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"PostgreSQL backup error: {e}")
            return False
    
    def validate_backup_contents(self, backup_file):
        """Validate that backup file contains all expected tables"""
        try:
            logger.info("Validating backup file contents...")
            
            expected_tables = [
                'users', 'projects', 'project_members', 'project_resources',
                'templates', 'template_approvals', 'documents', 'document_revisions',
                'document_reviewers', 'document_reviews', 'document_comments',
                'kb_collections', 'kb_documents', 'kb_queries', 'kb_config', 'kb_document_tags',
                'audits', 'findings', 'corrective_actions', 'repositories', 'pull_requests',
                'pull_request_files', 'code_reviews', 'code_comments', 'review_requests',
                'training_records', 'traceability_matrix', 'compliance_standards',
                'system_settings', 'activity_logs', 'suppliers', 'parts_inventory',
                'lab_equipment_calibration', 'customer_complaints', 'non_conformances',
                'system_requirements', 'system_hazards', 'fmea_analyses', 'design_artifacts',
                'test_artifacts', 'compliance_records', 'post_market_records'
            ]
            
            with open(backup_file, 'r') as f:
                backup_content = f.read()
            
            missing_tables = []
            for table in expected_tables:
                if f"CREATE TABLE public.{table}" not in backup_content and f"CREATE TABLE {table}" not in backup_content:
                    missing_tables.append(table)
            
            if missing_tables:
                logger.warning(f"Tables not found in backup: {missing_tables}")
            else:
                logger.info("All expected tables found in backup file")
            
            return len(missing_tables) == 0
            
        except Exception as e:
            logger.error(f"Backup validation error: {e}")
            return False
    
    def backup_qdrant(self):
        """Backup Qdrant vector database"""
        try:
            logger.info("Starting Qdrant backup...")
            qdrant_backup_dir = self.backup_path / "qdrant_data"
            
            # Copy Qdrant data from container
            cmd = [
                "docker", "cp",
                f"{self.qdrant_container}:/qdrant/storage",
                str(qdrant_backup_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Qdrant backup completed: {qdrant_backup_dir}")
                return True
            else:
                logger.error(f"Qdrant backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Qdrant backup error: {e}")
            return False
    
    def backup_configuration_files(self):
        """Backup configuration files and environment settings"""
        try:
            logger.info("Starting configuration backup...")
            config_backup_dir = self.backup_path / "configuration"
            config_backup_dir.mkdir(exist_ok=True)
            
            # Files to backup
            config_files = [
                ("docker-compose.yml", "docker-compose.yml"),
                ("backend/.env", "backend_env"),
                ("frontend/.env", "frontend_env") if Path("frontend/.env").exists() else None,
                (".env", "docker_env") if Path(".env").exists() else None,
                ("backend/app/config.py", "backend_config.py"),
                ("backend/requirements.txt", "backend_requirements.txt"),
                ("frontend/requirements.txt", "frontend_requirements.txt")
            ]
            
            backed_up_files = []
            
            for file_info in config_files:
                if file_info is None:
                    continue
                    
                source_file, backup_name = file_info
                source_path = Path(source_file)
                
                if source_path.exists():
                    destination = config_backup_dir / backup_name
                    shutil.copy2(source_path, destination)
                    backed_up_files.append(source_file)
                    logger.info(f"Backed up: {source_file}")
                else:
                    logger.warning(f"Config file not found: {source_file}")
            
            # Create backup manifest
            manifest = {
                "timestamp": self.timestamp,
                "backed_up_files": backed_up_files,
                "backup_type": "configuration"
            }
            
            with open(config_backup_dir / "backup_manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Configuration backup completed: {config_backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration backup error: {e}")
            return False
    
    def create_backup_archive(self):
        """Create compressed archive of backup"""
        try:
            logger.info("Creating backup archive...")
            archive_path = self.backup_dir / f"{self.backup_name}.tar.gz"
            
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(self.backup_path, arcname=self.backup_name)
            
            # Remove uncompressed backup directory
            shutil.rmtree(self.backup_path)
            
            logger.info(f"Backup archive created: {archive_path}")
            return archive_path
            
        except Exception as e:
            logger.error(f"Archive creation error: {e}")
            return None
    
    def create_backup_info(self, archive_path):
        """Create backup information file"""
        try:
            info_file = self.backup_dir / f"{self.backup_name}_info.json"
            
            backup_info = {
                "backup_name": self.backup_name,
                "timestamp": self.timestamp,
                "archive_path": str(archive_path),
                "components": ["postgres", "qdrant", "configuration"],
                "db_name": self.db_name,
                "created_by": "Docsmait Backup Script v1.0"
            }
            
            with open(info_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            logger.info(f"Backup info created: {info_file}")
            return True
            
        except Exception as e:
            logger.error(f"Backup info creation error: {e}")
            return False
    
    def run_backup(self):
        """Run complete backup process"""
        logger.info(f"Starting Docsmait backup: {self.backup_name}")
        
        # Check if Docker containers are running
        if not self.check_containers():
            return False
        
        if not self.create_backup_directory():
            return False
        
        # Validate database tables before backup
        if not self.validate_database_tables():
            logger.warning("Database validation completed with warnings")
        
        success = True
        
        # Backup PostgreSQL
        if not self.backup_postgres():
            success = False
        
        # Backup Qdrant
        if not self.backup_qdrant():
            success = False
        
        # Backup configuration files
        if not self.backup_configuration_files():
            success = False
        
        if success:
            # Create archive
            archive_path = self.create_backup_archive()
            if archive_path:
                self.create_backup_info(archive_path)
                logger.info(f"✅ Backup completed successfully: {archive_path}")
                return archive_path
            else:
                logger.error("❌ Failed to create backup archive")
                return False
        else:
            logger.error("❌ Backup completed with errors")
            return False
    
    def check_containers(self):
        """Check if required Docker containers are running"""
        try:
            containers = [self.postgres_container, self.qdrant_container]
            
            for container in containers:
                result = subprocess.run(
                    ["docker", "inspect", "-f", "{{.State.Running}}", container],
                    capture_output=True, text=True
                )
                
                if result.returncode != 0 or result.stdout.strip() != "true":
                    logger.error(f"Container {container} is not running")
                    return False
            
            logger.info("All required containers are running")
            return True
            
        except Exception as e:
            logger.error(f"Container check error: {e}")
            return False

def main():
    if len(sys.argv) > 1:
        backup_dir = sys.argv[1]
    else:
        backup_dir = "/tmp/docsmait_backup"
    
    backup = DocsmaitBackup(backup_dir)
    result = backup.run_backup()
    
    if result:
        print(f"\n✅ Backup completed successfully!")
        print(f"Archive location: {result}")
        sys.exit(0)
    else:
        print(f"\n❌ Backup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()