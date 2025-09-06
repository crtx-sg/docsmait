#!/bin/bash
# Docsmait System Management Script v1.2
# Unified script for common system management tasks

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

title() {
    echo -e "${PURPLE}=== $1 ===${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

start_services() {
    title "Starting Docsmait Services"
    
    if docker-compose -f "$SCRIPT_DIR/docker-compose.yml" up -d; then
        success "Services started successfully"
        
        # Wait for services to be ready
        log "Waiting for services to initialize..."
        sleep 15
        
        # Check service health
        "$SCRIPT_DIR/system_health.sh" --quiet
    else
        error "Failed to start services"
        return 1
    fi
}

stop_services() {
    title "Stopping Docsmait Services"
    
    if docker-compose -f "$SCRIPT_DIR/docker-compose.yml" down; then
        success "Services stopped successfully"
    else
        error "Failed to stop services"
        return 1
    fi
}

restart_services() {
    title "Restarting Docsmait Services"
    
    if docker-compose -f "$SCRIPT_DIR/docker-compose.yml" restart; then
        success "Services restarted successfully"
        
        # Wait for services to be ready
        log "Waiting for services to initialize..."
        sleep 15
        
        # Check service health
        "$SCRIPT_DIR/system_health.sh" --quiet
    else
        error "Failed to restart services"
        return 1
    fi
}

view_status() {
    title "Docsmait System Status"
    
    echo ""
    info "Container Status:"
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" ps
    
    echo ""
    info "Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | head -6
    
    echo ""
    info "Service Health:"
    "$SCRIPT_DIR/system_health.sh" --quiet
}

view_logs() {
    local service="$1"
    local follow="${2:-false}"
    
    title "Viewing Logs"
    
    if [ -z "$service" ]; then
        echo "Available services:"
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" config --services
        echo ""
        read -p "Enter service name (or 'all' for all services): " service
    fi
    
    if [ "$service" = "all" ]; then
        if [ "$follow" = "true" ]; then
            docker-compose -f "$SCRIPT_DIR/docker-compose.yml" logs -f
        else
            docker-compose -f "$SCRIPT_DIR/docker-compose.yml" logs --tail=50
        fi
    else
        if [ "$follow" = "true" ]; then
            docker-compose -f "$SCRIPT_DIR/docker-compose.yml" logs -f "$service"
        else
            docker-compose -f "$SCRIPT_DIR/docker-compose.yml" logs --tail=50 "$service"
        fi
    fi
}

run_backup() {
    title "Running System Backup"
    
    local backup_dir="${1:-/tmp/docsmait_backup}"
    
    if [ -f "$SCRIPT_DIR/comprehensive_backup.sh" ]; then
        "$SCRIPT_DIR/comprehensive_backup.sh" "$backup_dir"
    else
        error "Backup script not found: $SCRIPT_DIR/comprehensive_backup.sh"
        return 1
    fi
}

run_restore() {
    local backup_file="$1"
    
    title "Running System Restore"
    
    if [ -z "$backup_file" ]; then
        echo "Available backup files:"
        find /tmp -name "docsmait_backup_*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -5 | cut -d' ' -f2- | while read file; do
            echo "  $(basename "$file")"
        done
        echo ""
        read -p "Enter backup file path: " backup_file
    fi
    
    if [ -f "$backup_file" ]; then
        if [ -f "$SCRIPT_DIR/restore.sh" ]; then
            "$SCRIPT_DIR/restore.sh" "$backup_file"
        else
            error "Restore script not found: $SCRIPT_DIR/restore.sh"
            return 1
        fi
    else
        error "Backup file not found: $backup_file"
        return 1
    fi
}

cleanup_system() {
    title "System Cleanup"
    
    warning "This will clean up Docker resources and temporary files"
    read -p "Continue? (y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log "Cleanup cancelled"
        return 0
    fi
    
    log "Cleaning up Docker resources..."
    
    # Remove stopped containers
    if docker container prune -f; then
        success "Removed stopped containers"
    fi
    
    # Remove unused images
    if docker image prune -f; then
        success "Removed unused images"
    fi
    
    # Remove unused volumes (be careful!)
    echo ""
    warning "Volume cleanup can remove persistent data!"
    read -p "Clean up unused volumes? (y/N): " volume_confirm
    
    if [ "$volume_confirm" = "y" ] || [ "$volume_confirm" = "Y" ]; then
        if docker volume prune -f; then
            success "Removed unused volumes"
        fi
    fi
    
    # Clean up log files
    log "Cleaning up log files..."
    find /tmp -name "docsmait_*.log" -type f -mtime +7 -delete 2>/dev/null || true
    find /tmp -name "docsmait_health_report_*.txt" -type f -mtime +7 -delete 2>/dev/null || true
    success "Cleaned up old log files"
    
    # Clean up old backups (keep 10 most recent)
    log "Cleaning up old backups..."
    backup_count=$(find /tmp -name "docsmait_backup_*.tar.gz" -type f 2>/dev/null | wc -l)
    if [ "$backup_count" -gt 10 ]; then
        find /tmp -name "docsmait_backup_*.tar.gz" -type f -printf '%T@ %p\n' | \
        sort -n | head -n -10 | cut -d' ' -f2- | \
        while read -r old_backup; do
            rm -f "$old_backup"
            info_file=$(echo "$old_backup" | sed 's/\.tar\.gz/_info.json/')
            rm -f "$info_file"
        done
        success "Cleaned up old backups"
    fi
    
    success "System cleanup completed"
}

update_system() {
    title "System Update"
    
    log "Pulling latest Docker images..."
    if docker-compose -f "$SCRIPT_DIR/docker-compose.yml" pull; then
        success "Images updated successfully"
        
        warning "Services need to be restarted to use updated images"
        read -p "Restart services now? (y/N): " restart_confirm
        
        if [ "$restart_confirm" = "y" ] || [ "$restart_confirm" = "Y" ]; then
            restart_services
        fi
    else
        error "Failed to update images"
        return 1
    fi
}

show_interactive_menu() {
    while true; do
        clear
        echo -e "${PURPLE}╔══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${PURPLE}║                 Docsmait System Manager                  ║${NC}"
        echo -e "${PURPLE}╚══════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN}System Management:${NC}"
        echo "  1) Start Services"
        echo "  2) Stop Services" 
        echo "  3) Restart Services"
        echo "  4) View Status"
        echo "  5) View Logs"
        echo ""
        echo -e "${CYAN}Maintenance:${NC}"
        echo "  6) Run Backup"
        echo "  7) Run Restore"
        echo "  8) System Health Check"
        echo "  9) System Cleanup"
        echo " 10) Update System"
        echo ""
        echo " 99) Exit"
        echo ""
        read -p "Select an option: " choice
        
        case $choice in
            1) start_services ;;
            2) stop_services ;;
            3) restart_services ;;
            4) view_status ;;
            5) 
                read -p "Service name (or 'all'): " service
                read -p "Follow logs? (y/N): " follow
                view_logs "$service" "$([[ $follow == [yY] ]] && echo true || echo false)"
                ;;
            6) 
                read -p "Backup directory [/tmp/docsmait_backup]: " backup_dir
                run_backup "${backup_dir:-/tmp/docsmait_backup}"
                ;;
            7) 
                read -p "Backup file path: " backup_file
                run_restore "$backup_file"
                ;;
            8) "$SCRIPT_DIR/system_health.sh" ;;
            9) cleanup_system ;;
            10) update_system ;;
            99) break ;;
            *) 
                error "Invalid option"
                sleep 2
                ;;
        esac
        
        if [ "$choice" != "99" ] && [ "$choice" != "5" ]; then
            echo ""
            read -p "Press Enter to continue..."
        fi
    done
}

show_usage() {
    echo "Docsmait System Management Script"
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start             Start all services"
    echo "  stop              Stop all services"
    echo "  restart           Restart all services"
    echo "  status            Show system status"
    echo "  logs [service]    View logs (optionally for specific service)"
    echo "  logs-follow [service]  Follow logs in real-time"
    echo "  backup [dir]      Run system backup"
    echo "  restore <file>    Restore from backup"
    echo "  health            Run health check"
    echo "  cleanup           Clean up system resources"
    echo "  update            Update Docker images"
    echo "  menu              Show interactive menu"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start all services"
    echo "  $0 logs backend            # View backend logs"
    echo "  $0 backup /data/backups    # Backup to custom directory"
    echo "  $0 restore backup.tar.gz   # Restore from backup"
    echo "  $0 menu                    # Show interactive menu"
}

# Main execution
main() {
    if [ $# -eq 0 ]; then
        show_interactive_menu
        exit 0
    fi
    
    case "$1" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            view_status
            ;;
        logs)
            view_logs "$2" false
            ;;
        logs-follow)
            view_logs "$2" true
            ;;
        backup)
            run_backup "$2"
            ;;
        restore)
            if [ -z "$2" ]; then
                error "Restore requires backup file path"
                exit 1
            fi
            run_restore "$2"
            ;;
        health)
            "$SCRIPT_DIR/system_health.sh"
            ;;
        cleanup)
            cleanup_system
            ;;
        update)
            update_system
            ;;
        menu)
            show_interactive_menu
            ;;
        --help|-h|help)
            show_usage
            ;;
        *)
            error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"