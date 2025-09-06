#!/usr/bin/env python3
"""
Docsmait Restore Script
Restores PostgreSQL database, Qdrant vector database, and configuration files from backup
"""

import os
import sys
import json
import shutil
import subprocess
import tarfile
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocsmaitRestore:
    def __init__(self, backup_archive_path):
        self.backup_archive_path = Path(backup_archive_path)
        self.temp_dir = Path("/tmp/docsmait_restore")
        self.backup_dir = None
        
        # Import centralized configuration
        try:
            parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sys.path.append(parent_dir)
            from config.environments import config as env_config
            # Container names from config
            self.postgres_container = env_config.POSTGRES_SERVICE_NAME
            self.qdrant_container = env_config.QDRANT_SERVICE_NAME
            # Database credentials from config
            self.db_name = env_config.DB_NAME
            self.db_user = env_config.DB_USER
            self.db_password = env_config.DB_PASSWORD
        except ImportError:
            # Fallback for when centralized config is not available
            self.postgres_container = os.getenv("POSTGRES_SERVICE_NAME", "docsmait_postgres")
            self.qdrant_container = os.getenv("QDRANT_SERVICE_NAME", "docsmait_qdrant")
            self.db_name = os.getenv("DB_NAME", "docsmait")
            self.db_user = os.getenv("DB_USER", "docsmait_user")
            self.db_password = os.getenv("DB_PASSWORD", "docsmait_password")
        
    def extract_backup_archive(self):
        """Extract backup archive to temporary directory"""
        try:
            logger.info(f"Extracting backup archive: {self.backup_archive_path}")
            
            if not self.backup_archive_path.exists():
                logger.error(f"Backup archive not found: {self.backup_archive_path}")
                return False
            
            # Clean and create temp directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract archive
            with tarfile.open(self.backup_archive_path, "r:gz") as tar:
                tar.extractall(self.temp_dir)
            
            # Find extracted backup directory
            extracted_dirs = [d for d in self.temp_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                logger.error("No backup directory found in archive")
                return False
            
            self.backup_dir = extracted_dirs[0]
            logger.info(f"Backup extracted to: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Archive extraction error: {e}")
            return False
    
    def validate_backup(self):
        """Validate backup contents"""
        try:
            logger.info("Validating backup contents...")
            
            required_components = [
                ("postgres_backup.sql", "PostgreSQL backup"),
                ("qdrant_data", "Qdrant data"),
                ("configuration", "Configuration files"),
                ("filesystem", "File system data")
            ]
            
            for component, description in required_components:
                component_path = self.backup_dir / component
                if not component_path.exists():
                    logger.warning(f"Missing backup component: {description}")
                else:
                    logger.info(f"Found: {description}")
            
            # Validate PostgreSQL backup contains expected tables
            postgres_backup_file = self.backup_dir / "postgres_backup.sql"
            if postgres_backup_file.exists():
                self.validate_postgres_backup_contents(postgres_backup_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Backup validation error: {e}")
            return False
    
    def validate_postgres_backup_contents(self, backup_file):
        """Validate that backup file contains all expected tables"""
        try:
            logger.info("Validating PostgreSQL backup file contents...")
            
            expected_tables = [
                'users', 'projects', 'project_members', 'project_resources',
                'templates', 'template_approvals', 'documents', 'document_revisions',
                'document_reviewers', 'document_reviews', 'document_comments',
                'issues', 'issue_comments',  # Issues Management tables
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
                logger.warning(f"Tables not found in backup file: {missing_tables}")
                logger.warning("Restore may be incomplete for some system features")
            else:
                logger.info("All expected tables found in backup file")
            
            return len(missing_tables) == 0
            
        except Exception as e:
            logger.error(f"Backup content validation error: {e}")
            return False
    
    def restore_postgres(self):
        """Restore PostgreSQL database"""
        try:
            logger.info("Starting PostgreSQL restore...")
            postgres_backup_file = self.backup_dir / "postgres_backup.sql"
            
            if not postgres_backup_file.exists():
                logger.error("PostgreSQL backup file not found")
                return False
            
            # Drop existing database and recreate (be careful!)
            logger.warning("This will drop the existing database and recreate it!")
            response = input("Continue? (y/N): ").strip().lower()
            if response != 'y':
                logger.info("PostgreSQL restore cancelled by user")
                return False
            
            # Drop and recreate database
            drop_cmd = [
                "docker", "exec", self.postgres_container,
                "dropdb", "-U", self.db_user, "--if-exists", self.db_name
            ]
            
            create_cmd = [
                "docker", "exec", self.postgres_container,
                "createdb", "-U", self.db_user, self.db_name
            ]
            
            # Execute drop
            subprocess.run(drop_cmd, env={**os.environ, "PGPASSWORD": self.db_password})
            
            # Execute create
            result = subprocess.run(create_cmd, capture_output=True, text=True,
                                  env={**os.environ, "PGPASSWORD": self.db_password})
            
            if result.returncode != 0:
                logger.error(f"Failed to create database: {result.stderr}")
                return False
            
            # Restore from backup with enhanced options
            with open(postgres_backup_file, 'r') as f:
                restore_cmd = [
                    "docker", "exec", "-i", self.postgres_container,
                    "psql", "-U", self.db_user, "-d", self.db_name,
                    "--single-transaction",
                    "--set", "ON_ERROR_STOP=on"
                ]
                
                result = subprocess.run(restore_cmd, stdin=f, capture_output=True, text=True,
                                      env={**os.environ, "PGPASSWORD": self.db_password})
            
            if result.returncode == 0:
                logger.info("PostgreSQL restore completed successfully")
                # Validate restored database
                self.validate_restored_database()
                return True
            else:
                logger.error(f"PostgreSQL restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"PostgreSQL restore error: {e}")
            return False
    
    def validate_restored_database(self):
        """Validate that all expected tables were restored"""
        try:
            logger.info("Validating restored database...")
            
            expected_tables = [
                'users', 'projects', 'project_members', 'project_resources',
                'templates', 'template_approvals', 'documents', 'document_revisions',
                'document_reviewers', 'document_reviews', 'document_comments',
                'issues', 'issue_comments',  # Issues Management tables
                'kb_collections', 'kb_documents', 'kb_queries', 'kb_config', 'kb_document_tags',
                'audits', 'findings', 'corrective_actions', 'repositories', 'pull_requests',
                'pull_request_files', 'code_reviews', 'code_comments', 'review_requests',
                'training_records', 'traceability_matrix', 'compliance_standards',
                'system_settings', 'activity_logs', 'suppliers', 'parts_inventory',
                'lab_equipment_calibration', 'customer_complaints', 'non_conformances',
                'system_requirements', 'system_hazards', 'fmea_analyses', 'design_artifacts',
                'test_artifacts', 'compliance_records', 'post_market_records'
            ]
            
            # Check tables exist in restored database
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
                    logger.warning(f"Missing tables in restored database: {missing_tables}")
                else:
                    logger.info("✅ All expected tables found in restored database")
                
                return len(missing_tables) == 0
            else:
                logger.error(f"Failed to validate restored database: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Database validation error: {e}")
            return False
    
    def restore_qdrant(self):
        """Restore Qdrant vector database"""
        try:
            logger.info("Starting Qdrant restore...")
            qdrant_backup_dir = self.backup_dir / "qdrant_data"
            
            if not qdrant_backup_dir.exists():
                logger.error("Qdrant backup directory not found")
                return False
            
            # Stop Qdrant container to safely restore data
            logger.info("Stopping Qdrant container...")
            subprocess.run(["docker", "stop", self.qdrant_container], 
                         capture_output=True)
            
            # Remove existing Qdrant data
            remove_cmd = [
                "docker", "run", "--rm", "-v", "docsmait_qdrant_data:/data",
                "alpine", "sh", "-c", "rm -rf /data/*"
            ]
            subprocess.run(remove_cmd, capture_output=True)
            
            # Copy backup data to container volume
            # First, create a temporary container to copy data
            copy_cmd = [
                "docker", "run", "--rm", "-v", "docsmait_qdrant_data:/data",
                "-v", f"{qdrant_backup_dir}:/backup",
                "alpine", "sh", "-c", "cp -r /backup/* /data/"
            ]
            
            result = subprocess.run(copy_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Restart Qdrant container
                logger.info("Restarting Qdrant container...")
                subprocess.run(["docker", "start", self.qdrant_container])
                logger.info("Qdrant restore completed successfully")
                return True
            else:
                logger.error(f"Qdrant restore failed: {result.stderr}")
                # Try to restart container anyway
                subprocess.run(["docker", "start", self.qdrant_container])
                return False
                
        except Exception as e:
            logger.error(f"Qdrant restore error: {e}")
            # Try to restart container
            subprocess.run(["docker", "start", self.qdrant_container], 
                         capture_output=True)
            return False
    
    def restore_file_system_data(self):
        """Restore file system data including uploaded documents and templates"""
        try:
            logger.info("Starting file system data restore...")
            fs_backup_dir = self.backup_dir / "filesystem"
            
            if not fs_backup_dir.exists():
                logger.warning("No file system backup found, skipping...")
                return True
            
            # Read filesystem manifest if it exists
            manifest_file = fs_backup_dir / "filesystem_manifest.json"
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    backed_up_dirs = manifest.get("backed_up_directories", [])
                    logger.info(f"Restoring {len(backed_up_dirs)} backed up directories")
            
            # Restore targets
            restore_targets = [
                ("backend_uploads", "docsmait_backend", "/app/uploads"),
                ("backend_templates", "docsmait_backend", "/app/templates"),
                ("frontend_uploads", "docsmait_frontend", "/app/uploads")
            ]
            
            restored_directories = []
            
            for backup_name, container, container_path in restore_targets:
                backup_source = fs_backup_dir / backup_name
                
                if backup_source.exists():
                    # Create directory in container if it doesn't exist
                    mkdir_cmd = ["docker", "exec", container, "mkdir", "-p", container_path]
                    subprocess.run(mkdir_cmd, capture_output=True)
                    
                    # Copy data to container
                    # Use docker cp to copy contents
                    copy_cmd = ["docker", "cp", str(backup_source / "."), f"{container}:{container_path}"]
                    result = subprocess.run(copy_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        restored_directories.append(f"{container}:{container_path}")
                        logger.info(f"Restored: {container}:{container_path}")
                    else:
                        logger.warning(f"Could not restore to {container}:{container_path}: {result.stderr}")
                else:
                    logger.warning(f"Backup source not found: {backup_name}")
            
            logger.info(f"File system restore completed: {len(restored_directories)} directories restored")
            return True
            
        except Exception as e:
            logger.error(f"File system restore error: {e}")
            return False

    def restore_configuration_files(self):
        """Restore configuration files"""
        try:
            logger.info("Starting configuration restore...")
            config_backup_dir = self.backup_dir / "configuration"
            
            if not config_backup_dir.exists():
                logger.error("Configuration backup directory not found")
                return False
            
            # Read backup manifest
            manifest_file = config_backup_dir / "backup_manifest.json"
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                logger.info(f"Restoring configuration from backup: {manifest['timestamp']}")
            
            # Configuration file mappings
            config_mappings = [
                ("docker-compose.yml", "docker-compose.yml"),
                ("backend_env", "backend/.env"),
                ("frontend_env", "frontend/.env"),
                ("docker_env", ".env"),
                ("backend_config.py", "backend/app/config.py"),
                ("backend_requirements.txt", "backend/requirements.txt"),
                ("frontend_requirements.txt", "frontend/requirements.txt")
            ]
            
            restored_files = []
            
            for backup_name, target_path in config_mappings:
                backup_file = config_backup_dir / backup_name
                target_file = Path(target_path)
                
                if backup_file.exists():
                    # Create target directory if needed
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Backup existing file if it exists
                    if target_file.exists():
                        backup_existing = target_file.with_suffix(target_file.suffix + '.backup')
                        shutil.copy2(target_file, backup_existing)
                        logger.info(f"Backed up existing file: {target_path} -> {backup_existing}")
                    
                    # Restore file
                    shutil.copy2(backup_file, target_file)
                    restored_files.append(target_path)
                    logger.info(f"Restored: {target_path}")
                else:
                    logger.warning(f"Backup file not found: {backup_name}")
            
            logger.info(f"Configuration restore completed. Restored {len(restored_files)} files.")
            return True
            
        except Exception as e:
            logger.error(f"Configuration restore error: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    def run_restore(self):
        """Run complete restore process"""
        logger.info(f"Starting Docsmait restore from: {self.backup_archive_path}")
        
        try:
            if not self.extract_backup_archive():
                return False
            
            if not self.validate_backup():
                return False
            
            success = True
            
            # Restore PostgreSQL
            if not self.restore_postgres():
                success = False
            
            # Restore Qdrant
            if not self.restore_qdrant():
                success = False
            
            # Restore configuration files
            if not self.restore_configuration_files():
                success = False
            
            # Restore file system data
            if not self.restore_file_system_data():
                success = False
            
            if success:
                logger.info("✅ Restore completed successfully!")
                print("\n⚠️  IMPORTANT: After restore, you may need to:")
                print("   1. Restart Docker containers: docker-compose restart")
                print("   2. Check configuration files and update if needed")
                print("   3. Test the application functionality")
                return True
            else:
                logger.error("❌ Restore completed with errors")
                return False
                
        finally:
            self.cleanup()

def main():
    if len(sys.argv) < 2:
        print("Usage: python restore.py <backup_archive_path>")
        print("Example: python restore.py /tmp/docsmait_backup/docsmait_backup_20231201_120000.tar.gz")
        sys.exit(1)
    
    backup_archive_path = sys.argv[1]
    
    restore = DocsmaitRestore(backup_archive_path)
    result = restore.run_restore()
    
    if result:
        print(f"\n✅ Restore completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Restore failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()