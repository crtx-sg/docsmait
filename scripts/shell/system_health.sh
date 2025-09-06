#!/bin/bash
# Docsmait System Health Check Script v1.2
# Monitors system health, containers, and services

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

check_docker() {
    log "Checking Docker..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        return 1
    fi
    
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
    success "Docker is running (version: $DOCKER_VERSION)"
    return 0
}

check_docker_compose() {
    log "Checking Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose version --short 2>/dev/null || echo "unknown")
        success "Docker Compose is available (version: $COMPOSE_VERSION)"
        return 0
    elif docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || echo "unknown")
        success "Docker Compose (plugin) is available (version: $COMPOSE_VERSION)"
        return 0
    else
        error "Docker Compose is not available"
        return 1
    fi
}

check_containers() {
    log "Checking containers..."
    
    local containers=(
        "docsmait_postgres:PostgreSQL Database"
        "docsmait_qdrant:Qdrant Vector DB"
        "docsmait_backend:FastAPI Backend"
        "docsmait_frontend:Streamlit Frontend"
        "docsmait_ollama:Ollama AI Service"
    )
    
    local healthy_count=0
    local total_count=${#containers[@]}
    
    for container_info in "${containers[@]}"; do
        IFS=':' read -r container_name description <<< "$container_info"
        
        if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "^$container_name"; then
            local status=$(docker ps --filter "name=$container_name" --format "{{.Status}}")
            local ports=$(docker ps --filter "name=$container_name" --format "{{.Ports}}")
            success "$description ($container_name): $status"
            if [ -n "$ports" ]; then
                echo "    Ports: $ports"
            fi
            ((healthy_count++))
        else
            error "$description ($container_name): Not running"
        fi
    done
    
    echo ""
    if [ $healthy_count -eq $total_count ]; then
        success "All containers are healthy ($healthy_count/$total_count)"
    else
        warning "$healthy_count/$total_count containers are healthy"
    fi
    
    return 0
}

check_service_endpoints() {
    log "Checking service endpoints..."
    
    local endpoints=(
        "http://localhost:8501:Frontend (Streamlit)"
        "http://localhost:8000:Backend (FastAPI)"
        "http://localhost:6333:Qdrant Vector DB"
        "http://localhost:11434:Ollama AI Service"
    )
    
    local healthy_endpoints=0
    
    for endpoint_info in "${endpoints[@]}"; do
        IFS=':' read -r url description <<< "$endpoint_info"
        
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            success "$description: $url"
            ((healthy_endpoints++))
        else
            error "$description: $url (unreachable)"
        fi
    done
    
    echo ""
    success "$healthy_endpoints/${#endpoints[@]} endpoints are accessible"
}

check_database_health() {
    log "Checking database health..."
    
    # Check PostgreSQL
    if docker exec docsmait_postgres pg_isready -U docsmait_user -d docsmait 2>/dev/null; then
        success "PostgreSQL database is ready"
        
        # Get database size and connection info
        DB_SIZE=$(docker exec docsmait_postgres psql -U docsmait_user -d docsmait -t -c "SELECT pg_size_pretty(pg_database_size('docsmait'));" 2>/dev/null | xargs)
        CONN_COUNT=$(docker exec docsmait_postgres psql -U docsmait_user -d docsmait -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='docsmait';" 2>/dev/null | xargs)
        
        echo "    Database size: $DB_SIZE"
        echo "    Active connections: $CONN_COUNT"
        
        # Check for Issues Management tables
        ISSUES_COUNT=$(docker exec docsmait_postgres psql -U docsmait_user -d docsmait -t -c "SELECT COUNT(*) FROM issues;" 2>/dev/null | xargs || echo "N/A")
        echo "    Issues count: $ISSUES_COUNT"
    else
        error "PostgreSQL database is not ready"
    fi
    
    # Check Qdrant
    if curl -s "http://localhost:6333/health" | grep -q "ok" 2>/dev/null; then
        success "Qdrant vector database is healthy"
        
        # Get collections info
        COLLECTIONS=$(curl -s "http://localhost:6333/collections" 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('result', {}).get('collections', [])))" 2>/dev/null || echo "N/A")
        echo "    Collections count: $COLLECTIONS"
    else
        error "Qdrant vector database is not healthy"
    fi
}

check_system_resources() {
    log "Checking system resources..."
    
    # Memory usage
    MEMORY_INFO=$(free -h | awk 'NR==2{printf "Used: %s/%s (%.1f%%)", $3, $2, $3*100/$2}')
    echo "Memory: $MEMORY_INFO"
    
    # Disk usage
    DISK_INFO=$(df -h . | awk 'NR==2{printf "Used: %s/%s (%.1f%%)", $3, $2, ($3/$2)*100}')
    echo "Disk: $DISK_INFO"
    
    # Docker resources
    if docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | tail -n +2 | head -5 > /dev/null 2>&1; then
        echo ""
        echo "Docker Container Resources:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -6
    fi
}

check_log_files() {
    log "Checking log files..."
    
    local log_locations=(
        "/tmp/docsmait_backup.log:Backup logs"
        "/tmp/docsmait_restore.log:Restore logs"
        "/tmp/docsmait_maintenance.log:Maintenance logs"
    )
    
    for log_info in "${log_locations[@]}"; do
        IFS=':' read -r log_file description <<< "$log_info"
        
        if [ -f "$log_file" ]; then
            local size=$(du -h "$log_file" | cut -f1)
            local last_modified=$(stat -c %y "$log_file" | cut -d. -f1)
            success "$description: $log_file ($size, modified: $last_modified)"
        else
            echo "    $description: Not found ($log_file)"
        fi
    done
}

check_configuration() {
    log "Checking configuration files..."
    
    local config_files=(
        "docker-compose.yml:Docker Compose configuration"
        ".env:Environment variables"
        "backend/app/config.py:Backend configuration"
        "frontend/config.py:Frontend configuration"
    )
    
    for config_info in "${config_files[@]}"; do
        IFS=':' read -r config_file description <<< "$config_info"
        
        if [ -f "$SCRIPT_DIR/$config_file" ]; then
            success "$description: ✓"
        else
            warning "$description: Missing ($config_file)"
        fi
    done
}

generate_health_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="/tmp/docsmait_health_report_$(date '+%Y%m%d_%H%M%S').txt"
    
    {
        echo "Docsmait System Health Report"
        echo "Generated: $timestamp"
        echo "========================================"
        echo ""
        
        # Re-run all checks but capture output
        check_docker
        check_docker_compose
        check_containers
        check_service_endpoints
        check_database_health
        check_system_resources
        check_log_files
        check_configuration
        
    } > "$report_file" 2>&1
    
    echo ""
    success "Health report generated: $report_file"
}

show_usage() {
    echo "Docsmait System Health Check Script"
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --report, -r     Generate detailed health report file"
    echo "  --quiet, -q      Show only errors and warnings"
    echo "  --help, -h       Show this help message"
    echo ""
    echo "This script checks:"
    echo "  • Docker and Docker Compose installation"
    echo "  • Container status and health"
    echo "  • Service endpoint accessibility"
    echo "  • Database connectivity and health"
    echo "  • System resource usage"
    echo "  • Log file status"
    echo "  • Configuration file presence"
}

# Main execution
main() {
    local generate_report=false
    local quiet_mode=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --report|-r)
                generate_report=true
                shift
                ;;
            --quiet|-q)
                quiet_mode=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    log "=== Docsmait System Health Check ==="
    echo ""
    
    local exit_code=0
    
    # Run all checks
    if ! check_docker; then exit_code=1; fi
    if ! check_docker_compose; then exit_code=1; fi
    echo ""
    
    check_containers
    echo ""
    
    check_service_endpoints
    echo ""
    
    check_database_health
    echo ""
    
    check_system_resources
    echo ""
    
    check_log_files
    echo ""
    
    check_configuration
    echo ""
    
    if [ "$generate_report" = true ]; then
        generate_health_report
    fi
    
    if [ $exit_code -eq 0 ]; then
        success "=== System Health Check Completed - All Critical Systems Healthy ==="
    else
        warning "=== System Health Check Completed - Some Issues Found ==="
        echo ""
        echo "🔧 Troubleshooting Steps:"
        echo "  • Check Docker installation and daemon status"
        echo "  • Verify all containers are running: docker-compose ps"
        echo "  • Review container logs: docker-compose logs [service]"
        echo "  • Restart services if needed: docker-compose restart"
    fi
    
    exit $exit_code
}

# Execute main function
main "$@"