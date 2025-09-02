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
        
        # Docker container names
        self.postgres_container = "docsmait_postgres"
        self.qdrant_container = "docsmait_qdrant"
        
        # Database credentials from environment or defaults
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
                ("configuration", "Configuration files")
            ]
            
            for component, description in required_components:
                component_path = self.backup_dir / component
                if not component_path.exists():
                    logger.warning(f"Missing backup component: {description}")
                else:
                    logger.info(f"Found: {description}")
            
            return True
            
        except Exception as e:
            logger.error(f"Backup validation error: {e}")
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
            
            # Restore from backup
            with open(postgres_backup_file, 'r') as f:
                restore_cmd = [
                    "docker", "exec", "-i", self.postgres_container,
                    "psql", "-U", self.db_user, "-d", self.db_name
                ]
                
                result = subprocess.run(restore_cmd, stdin=f, capture_output=True, text=True,
                                      env={**os.environ, "PGPASSWORD": self.db_password})
            
            if result.returncode == 0:
                logger.info("PostgreSQL restore completed successfully")
                return True
            else:
                logger.error(f"PostgreSQL restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"PostgreSQL restore error: {e}")
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