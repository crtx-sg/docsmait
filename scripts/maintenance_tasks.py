#!/usr/bin/env python3
"""
Docsmait Maintenance Tasks Script

This script provides routine maintenance tasks that should be run periodically
to keep the Docsmait system healthy and performant.

Usage:
    python maintenance_tasks.py [options]

Available Tasks:
    --optimize-db           Optimize database performance (VACUUM, ANALYZE)
    --rebuild-kb-index      Rebuild knowledge base search indexes
    --update-stats          Update system statistics and metrics
    --clean-temp-files      Clean temporary files and caches
    --check-integrity       Run integrity checks on data
    --all                   Run all maintenance tasks
    --schedule              Show recommended maintenance schedule

Options:
    --dry-run               Show what would be done without executing
    --verbose               Show detailed output
    --help                  Show this help message
"""

import sys
import os
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.app.database_config import get_db, engine
    from backend.app.config import config
    from backend.app.db_models import *
    import qdrant_client
    from sqlalchemy.orm import Session
    from sqlalchemy import text, func
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    sys.exit(1)

class MaintenanceTasks:
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.results = {}
    
    def log(self, message: str, force: bool = False):
        """Log a message if verbose mode is on"""
        if self.verbose or force:
            prefix = "[DRY RUN] " if self.dry_run else ""
            print(f"{prefix}{message}")
    
    def optimize_database(self) -> dict:
        """Optimize database performance"""
        print("🗄️  Optimizing database...")
        results = {
            'tables_vacuumed': 0,
            'tables_analyzed': 0,
            'indexes_rebuilt': 0
        }
        
        db = next(get_db())
        try:
            # Get all table names
            tables_query = text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            
            tables = db.execute(tables_query).fetchall()
            
            for table in tables:
                table_name = table[0]
                
                try:
                    # VACUUM ANALYZE each table
                    if not self.dry_run:
                        # Note: VACUUM can't be run in a transaction
                        db.commit()  # End current transaction
                        db.execute(text(f"VACUUM ANALYZE {table_name}"))
                    
                    results['tables_vacuumed'] += 1
                    results['tables_analyzed'] += 1
                    self.log(f"  ✅ Optimized table: {table_name}")
                    
                except Exception as e:
                    self.log(f"  ⚠️  Warning optimizing {table_name}: {e}")
            
            # Rebuild critical indexes
            critical_indexes = [
                'idx_users_email',
                'idx_users_username', 
                'idx_projects_name',
                'idx_documents_project_id',
                'idx_kb_documents_collection_id'
            ]
            
            for index_name in critical_indexes:
                try:
                    if not self.dry_run:
                        db.execute(text(f"REINDEX INDEX {index_name}"))
                    
                    results['indexes_rebuilt'] += 1
                    self.log(f"  ✅ Rebuilt index: {index_name}")
                    
                except Exception as e:
                    self.log(f"  ⚠️  Warning rebuilding index {index_name}: {e}")
            
            print(f"✅ Database optimization complete - {results['tables_vacuumed']} tables optimized")
            
        except Exception as e:
            print(f"❌ Database optimization failed: {e}")
            results['error'] = str(e)
        finally:
            db.close()
        
        return results
    
    def rebuild_kb_index(self) -> dict:
        """Rebuild knowledge base search indexes"""
        print("🧠 Rebuilding knowledge base indexes...")
        results = {
            'collections_optimized': 0,
            'total_points': 0
        }
        
        try:
            qdrant_client_instance = qdrant_client.QdrantClient(url=config.QDRANT_URL)
            
            # Get all collections
            collections = qdrant_client_instance.get_collections()
            
            for collection in collections.collections:
                try:
                    collection_name = collection.name
                    
                    # Get collection info
                    info = qdrant_client_instance.get_collection(collection_name)
                    points_count = info.points_count
                    
                    if not self.dry_run:
                        # Optimize collection
                        qdrant_client_instance.optimize(collection_name, wait=True)
                    
                    results['collections_optimized'] += 1
                    results['total_points'] += points_count
                    self.log(f"  ✅ Optimized collection {collection_name} ({points_count} points)")
                    
                except Exception as e:
                    self.log(f"  ⚠️  Warning optimizing collection {collection.name}: {e}")
            
            print(f"✅ KB index rebuild complete - {results['collections_optimized']} collections optimized")
            
        except Exception as e:
            print(f"❌ KB index rebuild failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def update_stats(self) -> dict:
        """Update system statistics and metrics"""
        print("📊 Updating system statistics...")
        results = {}
        
        db = next(get_db())
        try:
            # Collect various statistics
            stats = {}
            
            # User statistics
            stats['total_users'] = db.query(User).count()
            stats['admin_users'] = db.query(User).filter(User.is_admin == True).count()
            
            # Project statistics
            stats['total_projects'] = db.query(Project).count()
            stats['total_project_members'] = db.query(ProjectMember).count()
            
            # Document statistics
            stats['total_documents'] = db.query(Document).count()
            stats['documents_by_status'] = dict(
                db.query(Document.status, func.count(Document.id))
                .group_by(Document.status).all()
            )
            
            # Template statistics
            stats['total_templates'] = db.query(Template).count()
            stats['approved_templates'] = db.query(Template).filter(Template.status == 'approved').count()
            
            # KB statistics
            stats['total_kb_collections'] = db.query(KBCollection).count()
            stats['total_kb_documents'] = db.query(KBDocument).count()
            
            # Audit statistics
            stats['total_audits'] = db.query(Audit).count()
            stats['active_audits'] = db.query(Audit).filter(Audit.status.in_(['planned', 'in_progress'])).count()
            stats['total_findings'] = db.query(Finding).count()
            stats['open_findings'] = db.query(Finding).filter(Finding.status == 'open').count()
            
            # Code review statistics
            stats['total_repositories'] = db.query(Repository).count()
            stats['total_pull_requests'] = db.query(PullRequest).count()
            stats['open_pull_requests'] = db.query(PullRequest).filter(PullRequest.status == 'open').count()
            
            # System health metrics
            stats['last_updated'] = datetime.now().isoformat()
            
            # Store stats in system settings if not dry run
            if not self.dry_run:
                from backend.app.settings_service import settings_service
                settings_service.set_setting(
                    'system_stats',
                    stats,
                    category='system',
                    description='System statistics and metrics'
                )
            
            results.update(stats)
            self.log(f"  ✅ Collected statistics for {len(stats)} metrics")
            
            print(f"✅ Statistics update complete")
            
        except Exception as e:
            print(f"❌ Statistics update failed: {e}")
            results['error'] = str(e)
        finally:
            db.close()
        
        return results
    
    def clean_temp_files(self) -> dict:
        """Clean temporary files and caches"""
        print("🧹 Cleaning temporary files...")
        results = {
            'files_deleted': 0,
            'bytes_freed': 0,
            'directories_cleaned': []
        }
        
        # Directories to clean
        temp_dirs = [
            '/tmp',
            tempfile.gettempdir(),
            './temp',
            './cache',
            './logs',
            './uploads/temp'
        ]
        
        # File patterns to clean
        patterns_to_clean = [
            '*.tmp',
            '*.temp',
            '*.cache',
            'docsmait_*.log',
            'cleanup_*.log',
            'upload_*',
            '*.bak'
        ]
        
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            
            try:
                dir_path = Path(temp_dir)
                files_in_dir = 0
                bytes_in_dir = 0
                
                for pattern in patterns_to_clean:
                    for file_path in dir_path.glob(pattern):
                        try:
                            if file_path.is_file():
                                file_size = file_path.stat().st_size
                                
                                # Only delete files older than 1 day
                                if datetime.now().timestamp() - file_path.stat().st_mtime > 86400:
                                    if not self.dry_run:
                                        file_path.unlink()
                                    
                                    files_in_dir += 1
                                    bytes_in_dir += file_size
                                    self.log(f"  🗑️  Deleted: {file_path}")
                        
                        except Exception as e:
                            self.log(f"  ⚠️  Warning deleting {file_path}: {e}")
                
                if files_in_dir > 0:
                    results['files_deleted'] += files_in_dir
                    results['bytes_freed'] += bytes_in_dir
                    results['directories_cleaned'].append({
                        'directory': str(dir_path),
                        'files_deleted': files_in_dir,
                        'bytes_freed': bytes_in_dir
                    })
                    self.log(f"  ✅ Cleaned {temp_dir}: {files_in_dir} files, {bytes_in_dir:,} bytes")
            
            except Exception as e:
                self.log(f"  ⚠️  Warning cleaning {temp_dir}: {e}")
        
        # Clean old log files
        log_patterns = ['*.log', '*.log.*']
        for pattern in log_patterns:
            for log_file in Path('.').glob(pattern):
                try:
                    # Keep logs from last 7 days
                    if datetime.now().timestamp() - log_file.stat().st_mtime > 7 * 86400:
                        file_size = log_file.stat().st_size
                        
                        if not self.dry_run:
                            log_file.unlink()
                        
                        results['files_deleted'] += 1
                        results['bytes_freed'] += file_size
                        self.log(f"  🗑️  Deleted old log: {log_file}")
                
                except Exception as e:
                    self.log(f"  ⚠️  Warning deleting log {log_file}: {e}")
        
        print(f"✅ Temp file cleanup complete - {results['files_deleted']} files, {results['bytes_freed']:,} bytes freed")
        
        return results
    
    def check_integrity(self) -> dict:
        """Run integrity checks on data"""
        print("🔍 Running data integrity checks...")
        results = {
            'checks_performed': 0,
            'issues_found': 0,
            'issues': []
        }
        
        db = next(get_db())
        try:
            # Check for orphaned records
            checks = [
                {
                    'name': 'Orphaned Project Members',
                    'query': db.query(ProjectMember).outerjoin(Project, ProjectMember.project_id == Project.id).filter(Project.id.is_(None))
                },
                {
                    'name': 'Orphaned Document Reviews', 
                    'query': db.query(DocumentReview).outerjoin(Document, DocumentReview.document_id == Document.id).filter(Document.id.is_(None))
                },
                {
                    'name': 'Orphaned KB Documents',
                    'query': db.query(KBDocument).outerjoin(KBCollection, KBDocument.collection_id == KBCollection.id).filter(KBCollection.id.is_(None))
                },
                {
                    'name': 'Users without valid email',
                    'query': db.query(User).filter(~User.email.contains('@'))
                },
                {
                    'name': 'Documents without projects',
                    'query': db.query(Document).outerjoin(Project, Document.project_id == Project.id).filter(Project.id.is_(None))
                },
                {
                    'name': 'Findings without audits',
                    'query': db.query(Finding).outerjoin(Audit, Finding.audit_id == Audit.id).filter(Audit.id.is_(None))
                }
            ]
            
            for check in checks:
                try:
                    count = check['query'].count()
                    results['checks_performed'] += 1
                    
                    if count > 0:
                        results['issues_found'] += count
                        issue = {
                            'check': check['name'],
                            'count': count,
                            'severity': 'warning' if count < 10 else 'error'
                        }
                        results['issues'].append(issue)
                        self.log(f"  ⚠️  {check['name']}: {count} issues found")
                    else:
                        self.log(f"  ✅ {check['name']}: OK")
                
                except Exception as e:
                    self.log(f"  ❌ Failed check {check['name']}: {e}")
            
            # Check database constraints
            constraint_checks = [
                "SELECT COUNT(*) FROM users WHERE email IS NULL OR email = ''",
                "SELECT COUNT(*) FROM projects WHERE name IS NULL OR name = ''",
                "SELECT COUNT(*) FROM documents WHERE created_by NOT IN (SELECT id FROM users)"
            ]
            
            for sql in constraint_checks:
                try:
                    result = db.execute(text(sql)).scalar()
                    results['checks_performed'] += 1
                    
                    if result > 0:
                        results['issues_found'] += result
                        self.log(f"  ⚠️  Constraint violation: {result} records")
                
                except Exception as e:
                    self.log(f"  ❌ Failed constraint check: {e}")
            
            print(f"✅ Integrity checks complete - {results['checks_performed']} checks, {results['issues_found']} issues found")
            
        except Exception as e:
            print(f"❌ Integrity checks failed: {e}")
            results['error'] = str(e)
        finally:
            db.close()
        
        return results
    
    def show_schedule(self):
        """Show recommended maintenance schedule"""
        schedule = {
            'Daily': [
                'Clean temp files (automatic)',
                'Update basic statistics'
            ],
            'Weekly': [
                'Run integrity checks',
                'Clean old log files',
                'Update detailed statistics'
            ],
            'Monthly': [
                'Optimize database (VACUUM ANALYZE)',
                'Rebuild knowledge base indexes',
                'Clean old audit data (>90 days)',
                'Clean unused templates'
            ],
            'Quarterly': [
                'Full system backup',
                'Performance analysis',
                'Security audit',
                'Cleanup old document revisions'
            ]
        }
        
        print("📅 RECOMMENDED MAINTENANCE SCHEDULE")
        print("=" * 50)
        
        for frequency, tasks in schedule.items():
            print(f"\n{frequency}:")
            for task in tasks:
                print(f"  • {task}")
        
        print("\n" + "=" * 50)
        print("💡 Tips:")
        print("  • Run maintenance during low-usage periods")
        print("  • Always backup before major operations")
        print("  • Monitor system performance after maintenance")
        print("  • Use --dry-run first to preview changes")
    
    def run_all_tasks(self) -> dict:
        """Run all maintenance tasks"""
        print("🔧 Running all maintenance tasks...")
        start_time = datetime.now()
        
        all_results = {}
        all_results['optimize_db'] = self.optimize_database()
        all_results['rebuild_kb_index'] = self.rebuild_kb_index()
        all_results['update_stats'] = self.update_stats()
        all_results['clean_temp_files'] = self.clean_temp_files()
        all_results['check_integrity'] = self.check_integrity()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Save maintenance log
        log_data = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'dry_run': self.dry_run,
            'results': all_results
        }
        
        log_file = f"maintenance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if not self.dry_run:
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            print(f"📋 Maintenance log saved to: {log_file}")
        
        print(f"\n🎉 All maintenance tasks complete - Duration: {duration}")
        
        return all_results

def main():
    parser = argparse.ArgumentParser(
        description='Docsmait Maintenance Tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Task options
    parser.add_argument('--optimize-db', action='store_true',
                      help='Optimize database performance')
    parser.add_argument('--rebuild-kb-index', action='store_true',
                      help='Rebuild knowledge base search indexes')  
    parser.add_argument('--update-stats', action='store_true',
                      help='Update system statistics')
    parser.add_argument('--clean-temp-files', action='store_true',
                      help='Clean temporary files and caches')
    parser.add_argument('--check-integrity', action='store_true',
                      help='Run integrity checks on data')
    parser.add_argument('--all', action='store_true',
                      help='Run all maintenance tasks')
    parser.add_argument('--schedule', action='store_true',
                      help='Show recommended maintenance schedule')
    
    # Control options
    parser.add_argument('--dry-run', action='store_true',
                      help='Show what would be done without executing')
    parser.add_argument('--verbose', action='store_true',
                      help='Show detailed output')
    
    args = parser.parse_args()
    
    # Show schedule if requested
    if args.schedule:
        tasks = MaintenanceTasks()
        tasks.show_schedule()
        return
    
    # Check if at least one task is specified
    if not any([args.optimize_db, args.rebuild_kb_index, args.update_stats, 
               args.clean_temp_files, args.check_integrity, args.all]):
        parser.print_help()
        return
    
    # Initialize maintenance tasks
    tasks = MaintenanceTasks(dry_run=args.dry_run, verbose=args.verbose)
    
    print("🔧 DOCSMAIT MAINTENANCE TASKS")
    print("=" * 40)
    print(f"Dry run mode: {'ON' if args.dry_run else 'OFF'}")
    print(f"Verbose mode: {'ON' if args.verbose else 'OFF'}")
    print("=" * 40)
    
    try:
        if args.all:
            tasks.run_all_tasks()
        else:
            if args.optimize_db:
                tasks.optimize_database()
            if args.rebuild_kb_index:
                tasks.rebuild_kb_index()
            if args.update_stats:
                tasks.update_stats()
            if args.clean_temp_files:
                tasks.clean_temp_files()
            if args.check_integrity:
                tasks.check_integrity()
    
    except KeyboardInterrupt:
        print("\n⚠️  Maintenance interrupted by user!")
    except Exception as e:
        print(f"\n❌ Maintenance failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()