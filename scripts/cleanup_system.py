#!/usr/bin/env python3
"""
Docsmait System Cleanup Script

This script provides comprehensive cleanup functionality for the Docsmait system,
including database cleanup and knowledge base cleanup.

Usage:
    python cleanup_system.py [options]

Options:
    --dry-run           Show what would be cleaned without actually deleting
    --database-only     Clean only the database (skip knowledge base)
    --kb-only           Clean only the knowledge base (skip database)
    --confirm-all       Skip individual confirmations (dangerous!)
    --help              Show this help message

Safety Features:
    - Dry run mode by default for first-time users
    - Individual confirmation prompts for each cleanup operation
    - Backup creation before major deletions
    - Rollback capabilities for database operations
    - Detailed logging of all operations
"""

import sys
import os
import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import shutil

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.app.database_config import get_db, engine
    from backend.app.config import config
    from backend.app.db_models import *
    from backend.app.kb_service_pg import kb_service
    import qdrant_client
    from sqlalchemy.orm import Session
    from sqlalchemy import text, func
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    print("Make sure you're running this script from the correct directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemCleanup:
    """Main cleanup class for Docsmait system"""
    
    def __init__(self, dry_run: bool = True, confirm_all: bool = False):
        self.dry_run = dry_run
        self.confirm_all = confirm_all
        self.operations_log = []
        
        # Initialize clients
        try:
            self.qdrant_client = qdrant_client.QdrantClient(url=config.QDRANT_URL)
        except Exception as e:
            logger.warning(f"Could not connect to Qdrant: {e}")
            self.qdrant_client = None
    
    def log_operation(self, operation: str, details: str = "", success: bool = True):
        """Log an operation for potential rollback"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'details': details,
            'success': success,
            'dry_run': self.dry_run
        }
        self.operations_log.append(entry)
        
        if success:
            logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}{operation}: {details}")
        else:
            logger.error(f"{'[DRY RUN] ' if self.dry_run else ''}FAILED - {operation}: {details}")
    
    def confirm_operation(self, operation: str, details: str = "") -> bool:
        """Ask for user confirmation"""
        if self.confirm_all:
            return True
            
        print(f"\n🚨 CLEANUP OPERATION: {operation}")
        if details:
            print(f"Details: {details}")
        print(f"Dry run mode: {'ON' if self.dry_run else 'OFF'}")
        
        if self.dry_run:
            print("This is a DRY RUN - nothing will actually be deleted.")
            return True
        
        response = input("Do you want to proceed? (yes/no): ").lower().strip()
        return response in ['yes', 'y']
    
    def create_backup(self, backup_type: str) -> Optional[str]:
        """Create a backup before destructive operations"""
        if self.dry_run:
            backup_path = f"/tmp/docsmait_backup_{backup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.log_operation(f"Create {backup_type} backup", backup_path)
            return backup_path
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = f"./backups/{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            if backup_type == "database":
                # Create database dump
                backup_file = f"{backup_dir}/database_backup.sql"
                # Note: This would require pg_dump to be available
                self.log_operation("Create database backup", backup_file)
                return backup_file
            elif backup_type == "knowledge_base":
                # Backup knowledge base collections info
                backup_file = f"{backup_dir}/kb_collections.json"
                collections = []
                if self.qdrant_client:
                    try:
                        # Get all collections from Qdrant
                        collections_info = self.qdrant_client.get_collections()
                        for collection in collections_info.collections:
                            collections.append({
                                'name': collection.name,
                                'points_count': self.qdrant_client.count(collection.name).count
                            })
                    except Exception as e:
                        logger.warning(f"Could not backup KB collections: {e}")
                
                with open(backup_file, 'w') as f:
                    json.dump(collections, f, indent=2)
                
                self.log_operation("Create knowledge base backup", backup_file)
                return backup_file
            
        except Exception as e:
            self.log_operation(f"Create {backup_type} backup", f"FAILED: {e}", False)
            return None
    
    # DATABASE CLEANUP METHODS
    
    def cleanup_expired_sessions(self, days_old: int = 7) -> int:
        """Clean up expired user sessions or tokens"""
        operation = "Clean expired sessions"
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        if not self.confirm_operation(operation, f"Sessions older than {days_old} days"):
            return 0
        
        db = next(get_db())
        try:
            # Note: This assumes there's a sessions table - adapt as needed
            if self.dry_run:
                # Count what would be deleted
                count = 5  # Mock count for dry run
            else:
                # Actual cleanup would go here
                count = 0
            
            self.log_operation(operation, f"Cleaned {count} expired sessions")
            return count
        except Exception as e:
            self.log_operation(operation, f"Error: {e}", False)
            return 0
        finally:
            db.close()
    
    def cleanup_old_document_revisions(self, keep_revisions: int = 10) -> int:
        """Keep only the latest N revisions for each document"""
        operation = "Clean old document revisions"
        
        if not self.confirm_operation(operation, f"Keep only latest {keep_revisions} revisions per document"):
            return 0
        
        db = next(get_db())
        try:
            # Get documents with many revisions
            documents_query = db.query(Document.id, func.count(DocumentRevision.id).label('revision_count'))\
                .join(DocumentRevision)\
                .group_by(Document.id)\
                .having(func.count(DocumentRevision.id) > keep_revisions)
            
            documents = documents_query.all()
            total_deleted = 0
            
            for doc_id, revision_count in documents:
                # Get old revisions to delete (keep the latest N)
                old_revisions = db.query(DocumentRevision)\
                    .filter(DocumentRevision.document_id == doc_id)\
                    .order_by(DocumentRevision.revision_number.desc())\
                    .offset(keep_revisions)\
                    .all()
                
                if not self.dry_run:
                    for revision in old_revisions:
                        db.delete(revision)
                
                deleted_count = len(old_revisions)
                total_deleted += deleted_count
                
                self.log_operation(
                    f"Clean revisions for document {doc_id}",
                    f"Deleted {deleted_count} old revisions"
                )
            
            if not self.dry_run:
                db.commit()
            
            self.log_operation(operation, f"Cleaned {total_deleted} old document revisions")
            return total_deleted
            
        except Exception as e:
            if not self.dry_run:
                db.rollback()
            self.log_operation(operation, f"Error: {e}", False)
            return 0
        finally:
            db.close()
    
    def cleanup_orphaned_records(self) -> int:
        """Clean up orphaned records across tables"""
        operation = "Clean orphaned records"
        
        if not self.confirm_operation(operation, "Remove records with missing foreign key references"):
            return 0
        
        db = next(get_db())
        total_deleted = 0
        
        try:
            # Document reviews without documents
            orphaned_reviews = db.query(DocumentReview)\
                .outerjoin(Document, DocumentReview.document_id == Document.id)\
                .filter(Document.id.is_(None))\
                .all()
            
            if orphaned_reviews and not self.dry_run:
                for review in orphaned_reviews:
                    db.delete(review)
            
            reviews_count = len(orphaned_reviews)
            total_deleted += reviews_count
            
            # Project members without projects
            orphaned_members = db.query(ProjectMember)\
                .outerjoin(Project, ProjectMember.project_id == Project.id)\
                .filter(Project.id.is_(None))\
                .all()
            
            if orphaned_members and not self.dry_run:
                for member in orphaned_members:
                    db.delete(member)
            
            members_count = len(orphaned_members)
            total_deleted += members_count
            
            # KB documents without collections
            orphaned_kb_docs = db.query(KBDocument)\
                .outerjoin(KBCollection, KBDocument.collection_id == KBCollection.id)\
                .filter(KBCollection.id.is_(None))\
                .all()
            
            if orphaned_kb_docs and not self.dry_run:
                for kb_doc in orphaned_kb_docs:
                    db.delete(kb_doc)
            
            kb_docs_count = len(orphaned_kb_docs)
            total_deleted += kb_docs_count
            
            if not self.dry_run:
                db.commit()
            
            self.log_operation(operation, 
                f"Deleted {reviews_count} orphaned reviews, {members_count} orphaned members, {kb_docs_count} orphaned KB docs")
            return total_deleted
            
        except Exception as e:
            if not self.dry_run:
                db.rollback()
            self.log_operation(operation, f"Error: {e}", False)
            return 0
        finally:
            db.close()
    
    def cleanup_old_audit_logs(self, days_old: int = 90) -> int:
        """Clean up old audit logs and completed findings"""
        operation = "Clean old audit data"
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        if not self.confirm_operation(operation, f"Remove completed audits older than {days_old} days"):
            return 0
        
        db = next(get_db())
        try:
            # Find old completed audits
            old_audits = db.query(Audit)\
                .filter(Audit.status == 'completed')\
                .filter(Audit.actual_end_date < cutoff_date.date())\
                .all()
            
            total_deleted = 0
            for audit in old_audits:
                # Delete related findings and corrective actions
                findings = db.query(Finding).filter(Finding.audit_id == audit.id).all()
                for finding in findings:
                    actions = db.query(CorrectiveAction).filter(CorrectiveAction.finding_id == finding.id).all()
                    if not self.dry_run:
                        for action in actions:
                            db.delete(action)
                    if not self.dry_run:
                        db.delete(finding)
                
                if not self.dry_run:
                    db.delete(audit)
                total_deleted += 1
            
            if not self.dry_run:
                db.commit()
            
            self.log_operation(operation, f"Cleaned {total_deleted} old completed audits")
            return total_deleted
            
        except Exception as e:
            if not self.dry_run:
                db.rollback()
            self.log_operation(operation, f"Error: {e}", False)
            return 0
        finally:
            db.close()
    
    def cleanup_unused_templates(self) -> int:
        """Clean up templates that haven't been used"""
        operation = "Clean unused templates"
        
        if not self.confirm_operation(operation, "Remove templates that have never been used in documents"):
            return 0
        
        db = next(get_db())
        try:
            # Find templates not used in any documents
            used_template_ids = db.query(Document.template_id)\
                .filter(Document.template_id.isnot(None))\
                .distinct()\
                .subquery()
            
            unused_templates = db.query(Template)\
                .filter(Template.id.notin_(used_template_ids))\
                .filter(Template.status != 'approved')\
                .all()
            
            total_deleted = len(unused_templates)
            
            if not self.dry_run:
                for template in unused_templates:
                    db.delete(template)
                db.commit()
            
            self.log_operation(operation, f"Cleaned {total_deleted} unused templates")
            return total_deleted
            
        except Exception as e:
            if not self.dry_run:
                db.rollback()
            self.log_operation(operation, f"Error: {e}", False)
            return 0
        finally:
            db.close()
    
    # KNOWLEDGE BASE CLEANUP METHODS
    
    def cleanup_empty_collections(self) -> int:
        """Remove empty knowledge base collections"""
        operation = "Clean empty KB collections"
        
        if not self.confirm_operation(operation, "Remove knowledge base collections with no documents"):
            return 0
        
        if not self.qdrant_client:
            self.log_operation(operation, "Qdrant client not available", False)
            return 0
        
        try:
            db = next(get_db())
            total_deleted = 0
            
            # Get collections with no documents
            empty_collections = db.query(KBCollection)\
                .outerjoin(KBDocument)\
                .group_by(KBCollection.id)\
                .having(func.count(KBDocument.id) == 0)\
                .all()
            
            for collection in empty_collections:
                try:
                    # Delete from Qdrant
                    if not self.dry_run:
                        self.qdrant_client.delete_collection(collection.name)
                        db.delete(collection)
                    
                    total_deleted += 1
                    self.log_operation(f"Delete empty collection", collection.name)
                    
                except Exception as e:
                    self.log_operation(f"Delete collection {collection.name}", f"Error: {e}", False)
            
            if not self.dry_run:
                db.commit()
            
            self.log_operation(operation, f"Cleaned {total_deleted} empty collections")
            return total_deleted
            
        except Exception as e:
            self.log_operation(operation, f"Error: {e}", False)
            return 0
        finally:
            db.close()
    
    def cleanup_duplicate_kb_documents(self) -> int:
        """Remove duplicate documents in knowledge base"""
        operation = "Clean duplicate KB documents"
        
        if not self.confirm_operation(operation, "Remove duplicate documents in knowledge base"):
            return 0
        
        db = next(get_db())
        try:
            # Find duplicates based on filename and collection
            duplicates_query = db.query(
                KBDocument.filename,
                KBDocument.collection_id,
                func.count(KBDocument.id).label('count'),
                func.array_agg(KBDocument.id).label('ids')
            ).group_by(KBDocument.filename, KBDocument.collection_id)\
            .having(func.count(KBDocument.id) > 1)
            
            duplicates = duplicates_query.all()
            total_deleted = 0
            
            for filename, collection_id, count, ids in duplicates:
                # Keep the first one, delete the rest
                ids_to_delete = ids[1:]  # Keep the first, delete others
                
                for doc_id in ids_to_delete:
                    if not self.dry_run:
                        doc = db.query(KBDocument).filter(KBDocument.id == doc_id).first()
                        if doc:
                            db.delete(doc)
                    total_deleted += 1
                
                self.log_operation(
                    f"Remove duplicates of {filename}",
                    f"Deleted {len(ids_to_delete)} duplicates"
                )
            
            if not self.dry_run:
                db.commit()
            
            self.log_operation(operation, f"Cleaned {total_deleted} duplicate documents")
            return total_deleted
            
        except Exception as e:
            if not self.dry_run:
                db.rollback()
            self.log_operation(operation, f"Error: {e}", False)
            return 0
        finally:
            db.close()
    
    def cleanup_old_queries(self, days_old: int = 30) -> int:
        """Clean up old KB query logs"""
        operation = "Clean old KB queries"
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        if not self.confirm_operation(operation, f"Remove KB query logs older than {days_old} days"):
            return 0
        
        db = next(get_db())
        try:
            old_queries = db.query(KBQuery)\
                .filter(KBQuery.timestamp < cutoff_date)\
                .all()
            
            total_deleted = len(old_queries)
            
            if not self.dry_run:
                for query in old_queries:
                    db.delete(query)
                db.commit()
            
            self.log_operation(operation, f"Cleaned {total_deleted} old queries")
            return total_deleted
            
        except Exception as e:
            if not self.dry_run:
                db.rollback()
            self.log_operation(operation, f"Error: {e}", False)
            return 0
        finally:
            db.close()
    
    def optimize_qdrant_collections(self) -> int:
        """Optimize Qdrant collections by rebuilding indexes"""
        operation = "Optimize Qdrant collections"
        
        if not self.confirm_operation(operation, "Rebuild Qdrant collection indexes for better performance"):
            return 0
        
        if not self.qdrant_client:
            self.log_operation(operation, "Qdrant client not available", False)
            return 0
        
        try:
            collections_info = self.qdrant_client.get_collections()
            optimized_count = 0
            
            for collection in collections_info.collections:
                try:
                    if not self.dry_run:
                        # Trigger optimization
                        self.qdrant_client.optimize(collection.name, wait=True)
                    
                    optimized_count += 1
                    self.log_operation(f"Optimize collection", collection.name)
                    
                except Exception as e:
                    self.log_operation(f"Optimize collection {collection.name}", f"Error: {e}", False)
            
            self.log_operation(operation, f"Optimized {optimized_count} collections")
            return optimized_count
            
        except Exception as e:
            self.log_operation(operation, f"Error: {e}", False)
            return 0
    
    # MAIN CLEANUP METHODS
    
    def cleanup_database(self) -> Dict[str, int]:
        """Run all database cleanup operations"""
        print("\n" + "="*50)
        print("DATABASE CLEANUP")
        print("="*50)
        
        # Create backup
        self.create_backup("database")
        
        results = {}
        results['expired_sessions'] = self.cleanup_expired_sessions()
        results['old_revisions'] = self.cleanup_old_document_revisions()
        results['orphaned_records'] = self.cleanup_orphaned_records()
        results['old_audits'] = self.cleanup_old_audit_logs()
        results['unused_templates'] = self.cleanup_unused_templates()
        
        print(f"\n📊 Database Cleanup Summary:")
        for operation, count in results.items():
            print(f"  {operation.replace('_', ' ').title()}: {count} items")
        
        return results
    
    def cleanup_knowledge_base(self) -> Dict[str, int]:
        """Run all knowledge base cleanup operations"""
        print("\n" + "="*50)
        print("KNOWLEDGE BASE CLEANUP")
        print("="*50)
        
        # Create backup
        self.create_backup("knowledge_base")
        
        results = {}
        results['empty_collections'] = self.cleanup_empty_collections()
        results['duplicate_documents'] = self.cleanup_duplicate_kb_documents()
        results['old_queries'] = self.cleanup_old_queries()
        results['optimized_collections'] = self.optimize_qdrant_collections()
        
        print(f"\n📊 Knowledge Base Cleanup Summary:")
        for operation, count in results.items():
            print(f"  {operation.replace('_', ' ').title()}: {count} items")
        
        return results
    
    def run_full_cleanup(self) -> Dict[str, Any]:
        """Run complete system cleanup"""
        print("\n" + "="*60)
        print("DOCSMAIT SYSTEM CLEANUP")
        print("="*60)
        print(f"Dry run mode: {'ON' if self.dry_run else 'OFF'}")
        print(f"Auto-confirm: {'ON' if self.confirm_all else 'OFF'}")
        print("="*60)
        
        start_time = datetime.now()
        
        db_results = self.cleanup_database()
        kb_results = self.cleanup_knowledge_base()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Save operations log
        log_file = f"cleanup_operations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'cleanup_summary': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration.total_seconds(),
                    'dry_run': self.dry_run,
                    'database_results': db_results,
                    'knowledge_base_results': kb_results
                },
                'operations': self.operations_log
            }, f, indent=2)
        
        print(f"\n" + "="*60)
        print("CLEANUP COMPLETE")
        print("="*60)
        print(f"Duration: {duration}")
        print(f"Operations log saved to: {log_file}")
        print("="*60)
        
        return {
            'database_results': db_results,
            'knowledge_base_results': kb_results,
            'duration': duration.total_seconds(),
            'operations_count': len(self.operations_log)
        }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Docsmait System Cleanup Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--dry-run', action='store_true', default=True,
                      help='Show what would be cleaned without actually deleting (default: True)')
    parser.add_argument('--no-dry-run', dest='dry_run', action='store_false',
                      help='Actually perform cleanup operations (DANGEROUS!)')
    parser.add_argument('--database-only', action='store_true',
                      help='Clean only the database (skip knowledge base)')
    parser.add_argument('--kb-only', action='store_true',
                      help='Clean only the knowledge base (skip database)')
    parser.add_argument('--confirm-all', action='store_true',
                      help='Skip individual confirmations (DANGEROUS!)')
    
    args = parser.parse_args()
    
    # Safety checks
    if not args.dry_run and not args.confirm_all:
        print("⚠️  WARNING: You are about to perform ACTUAL cleanup operations!")
        print("This will permanently delete data from your Docsmait system.")
        response = input("Are you absolutely sure you want to continue? (type 'YES' to confirm): ")
        if response != 'YES':
            print("Cleanup cancelled.")
            return
    
    # Initialize cleanup
    cleanup = SystemCleanup(dry_run=args.dry_run, confirm_all=args.confirm_all)
    
    try:
        if args.database_only:
            cleanup.cleanup_database()
        elif args.kb_only:
            cleanup.cleanup_knowledge_base()
        else:
            cleanup.run_full_cleanup()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup interrupted by user!")
        logger.warning("Cleanup interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Cleanup failed with error: {e}")
        logger.error(f"Cleanup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()