#!/bin/bash
# Docsmait Comprehensive Restore Script v1.2
# Restores PostgreSQL, Qdrant, configuration files, and filesystem data

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
LOG_FILE="/tmp/docsmait_restore.log"

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
            warning "Container $container is not running - will attempt to start during restore"
        fi
    done
}

validate_backup_archive() {
    BACKUP_ARCHIVE="$1"
    
    if [ ! -f "$BACKUP_ARCHIVE" ]; then
        error "Backup archive not found: $BACKUP_ARCHIVE"
        exit 1
    fi
    
    if [ ! -r "$BACKUP_ARCHIVE" ]; then
        error "Backup archive is not readable: $BACKUP_ARCHIVE"
        exit 1
    fi
    
    # Check if it's a valid tar.gz file
    if ! tar -tzf "$BACKUP_ARCHIVE" >/dev/null 2>&1; then
        error "Invalid backup archive format: $BACKUP_ARCHIVE"
        exit 1
    fi
    
    success "Backup archive validation passed: $BACKUP_ARCHIVE"
}

show_backup_info() {
    BACKUP_ARCHIVE="$1"
    INFO_FILE=$(echo "$BACKUP_ARCHIVE" | sed 's/\.tar\.gz/_info.json/')
    
    if [ -f "$INFO_FILE" ]; then
        log "Backup Information:"
        cat "$INFO_FILE" | python3 -m json.tool 2>/dev/null || cat "$INFO_FILE"
        echo ""
    fi
}

confirm_restore() {
    echo ""
    warning "⚠️  DANGER: This will completely replace your current data!"
    warning "   • PostgreSQL database will be dropped and recreated"
    warning "   • Qdrant vector database will be cleared"
    warning "   • Configuration files will be overwritten"
    warning "   • File system data will be replaced"
    echo ""
    
    read -p "Are you sure you want to continue? Type 'YES' to confirm: " confirmation
    
    if [ "$confirmation" != "YES" ]; then
        log "Restore cancelled by user"
        exit 0
    fi
    
    log "User confirmed restore operation"
}

run_restore() {
    BACKUP_ARCHIVE="$1"
    
    log "Starting Docsmait comprehensive restore..."
    log "Backup archive: $BACKUP_ARCHIVE"
    log "Log file: $LOG_FILE"
    
    # Run Python restore script
    if python3 "$SCRIPT_DIR/scripts/restore.py" "$BACKUP_ARCHIVE" 2>&1 | tee -a "$LOG_FILE"; then
        success "Restore completed successfully!"
        return 0
    else
        error "Restore failed"
        return 1
    fi
}

restart_services() {
    log "Restarting Docker services..."
    
    if docker-compose -f "$SCRIPT_DIR/docker-compose.yml" restart 2>&1 | tee -a "$LOG_FILE"; then
        success "Docker services restarted"
    else
        warning "Failed to restart services automatically - you may need to restart manually"
    fi
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_service_health
}

check_service_health() {
    log "Checking service health..."
    
    # Check if containers are running
    containers=("docsmait_postgres" "docsmait_qdrant" "docsmait_backend" "docsmait_frontend")
    healthy_count=0
    
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" --format "{{.Names}}" | grep -q "^$container$"; then
            success "Container $container is healthy"
            ((healthy_count++))
        else
            warning "Container $container is not running"
        fi
    done
    
    if [ $healthy_count -eq ${#containers[@]} ]; then
        success "All containers are healthy"
    else
        warning "$healthy_count/${#containers[@]} containers are healthy"
    fi
}

post_restore_instructions() {
    echo ""
    success "=== Restore Process Completed ==="
    echo ""
    echo "📋 Post-Restore Instructions:"
    echo ""
    echo "1. 🔍 Verify Application:"
    echo "   • Open http://localhost:8501 in your browser"
    echo "   • Test login with your admin account"
    echo "   • Check that data appears correctly"
    echo ""
    echo "2. 🛠️ Configuration Check:"
    echo "   • Review .env files for any updates needed"
    echo "   • Check SMTP settings if email notifications are used"
    echo "   • Verify API keys and external service configurations"
    echo ""
    echo "3. 🧪 Test Key Features:"
    echo "   • Issues Management: Create and update test issues"
    echo "   • Knowledge Base: Perform test queries"
    echo "   • Document Management: Upload and review test documents"
    echo "   • Email Notifications: Test issue assignments"
    echo ""
    echo "4. 📊 Monitor Performance:"
    echo "   • Check Docker container logs: docker-compose logs"
    echo "   • Monitor system resources with: docker stats"
    echo "   • Test vector search functionality"
    echo ""
    echo "5. 🔄 If Issues Occur:"
    echo "   • Restart specific services: docker-compose restart [service]"
    echo "   • Check log files in $LOG_FILE"
    echo "   • Verify database connectivity and AI model availability"
    echo ""
}

show_usage() {
    echo "Docsmait Comprehensive Restore Script"
    echo "Usage: $0 <backup_archive_path>"
    echo ""
    echo "Arguments:"
    echo "  backup_archive_path  Path to the backup archive (.tar.gz file)"
    echo ""
    echo "Example:"
    echo "  $0 /tmp/docsmait_backup/docsmait_backup_20231201_120000.tar.gz"
    echo ""
    echo "This script will:"
    echo "  • Validate the backup archive"
    echo "  • Restore PostgreSQL database with all tables including Issues Management"
    echo "  • Restore Qdrant vector database"
    echo "  • Restore configuration files"
    echo "  • Restore file system data (uploads, templates)"
    echo "  • Restart Docker services"
    echo "  • Provide post-restore verification steps"
    echo ""
    echo "⚠️  WARNING: This will completely replace your current data!"
}

# Main execution
main() {
    if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    BACKUP_ARCHIVE="$1"
    
    log "=== Docsmait Comprehensive Restore Starting ==="
    
    # Pre-flight checks
    check_docker
    check_containers
    validate_backup_archive "$BACKUP_ARCHIVE"
    show_backup_info "$BACKUP_ARCHIVE"
    confirm_restore
    
    # Run restore
    if run_restore "$BACKUP_ARCHIVE"; then
        restart_services
        post_restore_instructions
        
        success "=== Restore Process Completed Successfully ==="
        log "Log file: $LOG_FILE"
        
        exit 0
    else
        error "=== Restore Process Failed ==="
        log "Check the log file for details: $LOG_FILE"
        echo ""
        echo "🔧 Troubleshooting:"
        echo "  • Check that Docker containers are running"
        echo "  • Verify backup archive integrity"
        echo "  • Review log file: $LOG_FILE"
        echo "  • Try restarting Docker services: docker-compose restart"
        exit 1
    fi
}

# Execute main function
main "$@"