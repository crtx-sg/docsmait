#!/bin/bash
# Docsmait Comprehensive Backup Script v1.2
# Backs up PostgreSQL, Qdrant, configuration files, and filesystem data

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
DEFAULT_BACKUP_DIR="/tmp/docsmait_backup"
BACKUP_DIR="${1:-$DEFAULT_BACKUP_DIR}"
LOG_FILE="/tmp/docsmait_backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    success "Docker is available and running"
}

check_containers() {
    log "Checking required containers..."
    
    containers=("docsmait_postgres" "docsmait_qdrant" "docsmait_backend")
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "^$container$"; then
            success "Container $container is running"
        else
            warning "Container $container is not running"
        fi
    done
}

create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    success "Backup directory created: $BACKUP_DIR"
}

run_backup() {
    log "Starting Docsmait comprehensive backup..."
    log "Backup directory: $BACKUP_DIR"
    log "Log file: $LOG_FILE"
    
    # Run Python backup script
    if python3 "$SCRIPT_DIR/scripts/backup.py" "$BACKUP_DIR" 2>&1 | tee -a "$LOG_FILE"; then
        success "Backup completed successfully!"
        
        # Find the latest backup archive
        LATEST_BACKUP=$(find "$BACKUP_DIR" -name "docsmait_backup_*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [ -n "$LATEST_BACKUP" ]; then
            BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
            success "Archive created: $LATEST_BACKUP ($BACKUP_SIZE)"
            
            # Display backup info
            INFO_FILE=$(echo "$LATEST_BACKUP" | sed 's/\.tar\.gz/_info.json/')
            if [ -f "$INFO_FILE" ]; then
                log "Backup information:"
                cat "$INFO_FILE" | python3 -m json.tool 2>/dev/null || cat "$INFO_FILE"
            fi
            
            return 0
        else
            error "Backup archive not found"
            return 1
        fi
    else
        error "Backup failed"
        return 1
    fi
}

cleanup_old_backups() {
    log "Cleaning up old backups (keeping last 5)..."
    
    # Count backups
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "docsmait_backup_*.tar.gz" -type f | wc -l)
    
    if [ "$BACKUP_COUNT" -gt 5 ]; then
        # Remove old backups, keep 5 most recent
        find "$BACKUP_DIR" -name "docsmait_backup_*.tar.gz" -type f -printf '%T@ %p\n' | \
        sort -n | head -n -5 | cut -d' ' -f2- | \
        while read -r old_backup; do
            rm -f "$old_backup"
            # Also remove corresponding info file
            INFO_FILE=$(echo "$old_backup" | sed 's/\.tar\.gz/_info.json/')
            rm -f "$INFO_FILE"
            log "Removed old backup: $(basename "$old_backup")"
        done
        
        success "Cleaned up old backups"
    else
        log "No cleanup needed (${BACKUP_COUNT} backups found)"
    fi
}

show_usage() {
    echo "Docsmait Comprehensive Backup Script"
    echo "Usage: $0 [backup_directory]"
    echo ""
    echo "Arguments:"
    echo "  backup_directory  Directory to store backup files (default: $DEFAULT_BACKUP_DIR)"
    echo ""
    echo "Example:"
    echo "  $0"
    echo "  $0 /data/backups/docsmait"
    echo ""
    echo "This script will:"
    echo "  • Backup PostgreSQL database with all tables including Issues Management"
    echo "  • Backup Qdrant vector database"
    echo "  • Backup configuration files and environment settings"
    echo "  • Backup file system data (uploads, templates)"
    echo "  • Create compressed archive with timestamp"
    echo "  • Clean up old backups (keep 5 most recent)"
}

# Main execution
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    log "=== Docsmait Comprehensive Backup Starting ==="
    
    # Pre-flight checks
    check_docker
    check_containers
    create_backup_dir
    
    # Run backup
    if run_backup; then
        cleanup_old_backups
        
        success "=== Backup Process Completed Successfully ==="
        log "Log file: $LOG_FILE"
        
        # Show next steps
        echo ""
        echo "📋 Next Steps:"
        echo "  • Test the backup by running a restore to a test environment"
        echo "  • Consider copying backup to remote storage for disaster recovery"
        echo "  • Schedule regular backups via cron job"
        echo ""
        echo "📁 Cron Job Example (daily at 2 AM):"
        echo "  0 2 * * * $SCRIPT_DIR/$0 $BACKUP_DIR >> $LOG_FILE 2>&1"
        
        exit 0
    else
        error "=== Backup Process Failed ==="
        log "Check the log file for details: $LOG_FILE"
        exit 1
    fi
}

# Execute main function
main "$@"