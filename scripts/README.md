# Docsmait System Scripts

This directory contains utility scripts for managing and maintaining the Docsmait system.

## Available Scripts

### 1. `cleanup_system.py` - Comprehensive System Cleanup
Provides comprehensive cleanup functionality for both database and knowledge base.

```bash
# Dry run (safe preview)
python cleanup_system.py --dry-run

# Clean only database
python cleanup_system.py --database-only --no-dry-run --confirm-all

# Clean only knowledge base  
python cleanup_system.py --kb-only --no-dry-run

# Full cleanup with confirmations
python cleanup_system.py --no-dry-run
```

**Features:**
- ✅ Database cleanup (old revisions, orphaned records, expired sessions)
- ✅ Knowledge base cleanup (empty collections, duplicates, old queries) 
- ✅ Safety measures (dry-run mode, confirmations, backups)
- ✅ Detailed logging and operation tracking
- ✅ Rollback capabilities

### 2. `reset_system.py` - Nuclear Reset
Completely wipes all data and returns the system to initial state.

```bash
# Reset everything (DANGEROUS!)
python reset_system.py --confirm

# Keep admin users
python reset_system.py --keep-admin --confirm

# Keep system settings
python reset_system.py --keep-settings --confirm

# Keep both admin users and settings
python reset_system.py --keep-admin --keep-settings --confirm
```

**⚠️ WARNING:** This permanently deletes ALL data!

### 3. `maintenance_tasks.py` - Routine Maintenance
Provides routine maintenance tasks for optimal system performance.

```bash
# Show recommended maintenance schedule
python maintenance_tasks.py --schedule

# Run all maintenance tasks (dry run)
python maintenance_tasks.py --all --dry-run --verbose

# Optimize database only
python maintenance_tasks.py --optimize-db

# Clean temp files
python maintenance_tasks.py --clean-temp-files

# Run integrity checks
python maintenance_tasks.py --check-integrity --verbose
```

**Tasks Available:**
- 🗄️ Database optimization (VACUUM, ANALYZE)
- 🧠 Knowledge base index rebuilding
- 📊 System statistics updates
- 🧹 Temporary file cleanup
- 🔍 Data integrity checks

## Usage Examples

### Daily Maintenance
```bash
# Quick cleanup of temp files and stats update
python maintenance_tasks.py --clean-temp-files --update-stats
```

### Weekly Maintenance  
```bash
# Comprehensive maintenance
python maintenance_tasks.py --all --verbose
```

### Monthly Cleanup
```bash
# Safe cleanup preview
python cleanup_system.py --dry-run

# Actual cleanup after review
python cleanup_system.py --no-dry-run
```

### Emergency Reset
```bash
# When everything is broken beyond repair
python reset_system.py --keep-admin --keep-settings --confirm
```

## Safety Features

### All Scripts Include:
- **Dry-run mode** - Preview changes without executing
- **Confirmation prompts** - Individual confirmations for dangerous operations  
- **Backup creation** - Automatic backups before destructive operations
- **Detailed logging** - Complete operation logs with timestamps
- **Error handling** - Graceful failure handling with rollback capabilities

### Best Practices:
1. **Always run dry-run first** to preview changes
2. **Create backups** before major operations
3. **Run during low-usage periods** to minimize impact
4. **Monitor system** after maintenance operations
5. **Keep operation logs** for troubleshooting

## Scheduled Maintenance Recommendations

### Daily (Automated)
- Clean temporary files
- Update basic system statistics

### Weekly
- Run integrity checks
- Clean old log files  
- Update detailed statistics

### Monthly
- Database optimization (VACUUM ANALYZE)
- Rebuild knowledge base indexes
- Clean old audit data (>90 days)
- Remove unused templates

### Quarterly  
- Full system cleanup
- Performance analysis
- Security audit
- Clean old document revisions

## Requirements

### Python Dependencies
- `sqlalchemy`
- `qdrant-client`
- `psycopg2` (for PostgreSQL)
- All backend app dependencies

### System Requirements
- Python 3.8+
- PostgreSQL database access
- Qdrant vector database access
- Sufficient disk space for backups

## Configuration

Scripts automatically use configuration from:
- `backend/app/config.py` - Database and service URLs
- `backend/app/database_config.py` - Database connection settings

### Environment Variables
Scripts respect the same environment variables as the main application:
- `DATABASE_URL` - PostgreSQL connection string
- `QDRANT_URL` - Qdrant vector database URL
- `OLLAMA_BASE_URL` - Ollama API URL

## Troubleshooting

### Common Issues

**Permission Errors:**
```bash
# Ensure proper file permissions
chmod +x scripts/*.py
```

**Database Connection Errors:**
- Verify PostgreSQL is running
- Check database connection settings
- Ensure user has required permissions

**Qdrant Connection Errors:**  
- Verify Qdrant service is running
- Check Qdrant URL configuration
- Ensure network connectivity

**Import Errors:**
- Run from project root directory
- Install all required dependencies
- Check Python path configuration

### Getting Help
```bash
# Show detailed help for any script
python [script_name].py --help

# Show maintenance schedule
python maintenance_tasks.py --schedule
```

## Logs and Output

### Log Files Created:
- `cleanup_[timestamp].log` - Cleanup operation logs
- `maintenance_[timestamp].json` - Maintenance task results  
- `cleanup_operations_[timestamp].json` - Detailed operation tracking

### Log Locations:
- Current directory (where script is run)
- `./backups/[timestamp]/` - Backup files
- `/tmp/` - Temporary operation files

## Security Considerations

- Scripts require appropriate database permissions
- Admin operations need super-admin user access
- Backup files may contain sensitive data
- Clean up log files containing operational details
- Use secure file permissions on script files

---

**⚠️ IMPORTANT:** Always test scripts in a development environment before running in production!