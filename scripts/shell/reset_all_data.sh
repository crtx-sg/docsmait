#!/bin/bash
# Docsmait Data Reset Script v1.2
# Resets all system data while preserving admin user and configuration

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

confirm_reset() {
    title "Data Reset Confirmation"
    
    echo ""
    warning "⚠️  DANGER: This will permanently delete all data except admin user!"
    echo ""
    echo -e "${RED}The following will be PERMANENTLY DELETED:${NC}"
    echo "  • All projects and their data"
    echo "  • All issues and comments"
    echo "  • All documents and templates (except system templates)"
    echo "  • All knowledge base collections and documents"
    echo "  • All training records and audit logs"
    echo "  • All design records, requirements, and test data"
    echo "  • All vector database embeddings"
    echo ""
    echo -e "${GREEN}The following will be PRESERVED:${NC}"
    echo "  • Admin user account and credentials"
    echo "  • System configuration"
    echo "  • Docker containers and images"
    echo "  • System templates"
    echo ""
    
    read -p "Type 'RESET ALL DATA' to confirm complete data reset: " confirmation
    
    if [ "$confirmation" != "RESET ALL DATA" ]; then
        log "Data reset cancelled"
        exit 0
    fi
    
    echo ""
    read -p "Are you absolutely sure? This cannot be undone! (y/N): " final_confirm
    
    if [ "$final_confirm" != "y" ] && [ "$final_confirm" != "Y" ]; then
        log "Data reset cancelled"
        exit 0
    fi
    
    success "Data reset confirmed by user"
}

check_services() {
    log "Checking service status..."
    
    local containers=("docsmait_postgres" "docsmait_qdrant" "docsmait_backend")
    local running_containers=()
    
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" --format "{{.Names}}" | grep -q "^$container$"; then
            running_containers+=("$container")
            success "$container is running"
        else
            error "$container is not running"
        fi
    done
    
    if [ ${#running_containers[@]} -ne ${#containers[@]} ]; then
        warning "Not all required containers are running"
        read -p "Start missing containers? (y/N): " start_containers
        
        if [ "$start_containers" = "y" ] || [ "$start_containers" = "Y" ]; then
            log "Starting services..."
            docker-compose -f "$SCRIPT_DIR/docker-compose.yml" up -d
            sleep 10
        else
            error "Cannot proceed without all containers running"
            exit 1
        fi
    fi
}

backup_admin_user() {
    title "Backing Up Admin User"
    
    local admin_backup="/tmp/docsmait_admin_backup_$(date '+%Y%m%d_%H%M%S').sql"
    
    log "Creating admin user backup..."
    
    # Export admin users to SQL file
    local cmd=(
        "docker" "exec" "docsmait_postgres"
        "pg_dump" "-U" "docsmait_user" "-d" "docsmait"
        "--table=users" "--data-only"
        "--column-inserts" "--no-owner" "--no-privileges"
    )
    
    if "${cmd[@]}" > "$admin_backup" 2>/dev/null; then
        success "Admin user backup created: $admin_backup"
        echo "$admin_backup"  # Return backup file path
    else
        error "Failed to backup admin user"
        exit 1
    fi
}

reset_postgresql_data() {
    title "Resetting PostgreSQL Data"
    
    log "Stopping backend to prevent database access..."
    docker stop docsmait_backend 2>/dev/null || true
    
    # List of tables to truncate (preserve users table)
    local tables_to_reset=(
        "activity_logs"
        "audits"
        "compliance_records"
        "compliance_standards"
        "corrective_actions"
        "customer_complaints"
        "design_artifacts"
        "document_comments"
        "document_reviewers"
        "document_reviews"
        "document_revisions"
        "documents"
        "findings"
        "fmea_analyses"
        "issue_comments"
        "issues"
        "kb_collections"
        "kb_config"
        "kb_document_tags"
        "kb_documents"
        "kb_queries"
        "lab_equipment_calibration"
        "non_conformances"
        "parts_inventory"
        "post_market_records"
        "project_members"
        "project_resources"
        "projects"
        "suppliers"
        "system_hazards"
        "system_requirements"
        "system_settings"
        "template_approvals"
        "templates"
        "test_artifacts"
        "traceability_matrix"
        "training_records"
    )
    
    log "Truncating database tables..."
    
    for table in "${tables_to_reset[@]}"; do
        local cmd=(
            "docker" "exec" "docsmait_postgres"
            "psql" "-U" "docsmait_user" "-d" "docsmait" "-c"
            "TRUNCATE TABLE $table CASCADE;"
        )
        
        if "${cmd[@]}" 2>/dev/null; then
            log "Truncated table: $table"
        else
            warning "Failed to truncate table: $table (may not exist)"
        fi
    done
    
    # Reset sequences
    log "Resetting database sequences..."
    
    local reset_sequences_cmd=(
        "docker" "exec" "docsmait_postgres"
        "psql" "-U" "docsmait_user" "-d" "docsmait" "-c"
        "SELECT setval(pg_get_serial_sequence(quote_ident(PGT.schemaname)||'.'||quote_ident(PGT.tablename), quote_ident(PGC.attname)), 1, false) FROM pg_class PGC, pg_attribute PGC, pg_tables PGT WHERE PGC.oid=PGC.attrelid AND PGC.attnum>0 AND PGT.tablename=PGC.relname AND PGC.attname LIKE '%_id' AND PGT.schemaname='public';"
    )
    
    "${reset_sequences_cmd[@]}" 2>/dev/null || warning "Some sequences may not have been reset"
    
    success "PostgreSQL data reset completed"
    
    log "Restarting backend..."
    docker start docsmait_backend
    sleep 5
}

restore_admin_user() {
    local admin_backup="$1"
    
    title "Restoring Admin User"
    
    if [ -f "$admin_backup" ]; then
        log "Restoring admin user from backup..."
        
        local cmd=(
            "docker" "exec" "-i" "docsmait_postgres"
            "psql" "-U" "docsmait_user" "-d" "docsmait"
        )
        
        if cat "$admin_backup" | "${cmd[@]}" 2>/dev/null; then
            success "Admin user restored successfully"
            rm -f "$admin_backup"
        else
            error "Failed to restore admin user"
            warning "Admin backup saved at: $admin_backup"
            return 1
        fi
    else
        error "Admin backup file not found: $admin_backup"
        return 1
    fi
}

reset_qdrant_data() {
    title "Resetting Qdrant Vector Database"
    
    log "Stopping Qdrant container..."
    docker stop docsmait_qdrant 2>/dev/null || true
    
    # Clear all collections from Qdrant
    log "Clearing Qdrant collections..."
    
    # Remove Qdrant data volume
    docker run --rm -v docsmait_qdrant_data:/data alpine sh -c "rm -rf /data/*" 2>/dev/null || true
    
    log "Restarting Qdrant container..."
    docker start docsmait_qdrant
    sleep 10
    
    # Wait for Qdrant to be ready
    local max_retries=30
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -s "http://localhost:6333/health" | grep -q "ok" 2>/dev/null; then
            success "Qdrant is ready"
            break
        fi
        
        log "Waiting for Qdrant to be ready... ($((retry_count + 1))/$max_retries)"
        sleep 2
        ((retry_count++))
    done
    
    if [ $retry_count -eq $max_retries ]; then
        warning "Qdrant may not be fully ready, but continuing..."
    fi
    
    success "Qdrant vector database reset completed"
}

reset_file_system_data() {
    title "Resetting File System Data"
    
    # Clear uploaded files from containers
    log "Clearing uploaded files..."
    
    local containers=("docsmait_backend" "docsmait_frontend")
    
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "^$container$"; then
            docker exec "$container" sh -c "rm -rf /app/uploads/* 2>/dev/null || true" 2>/dev/null || true
            log "Cleared uploads from $container"
        fi
    done
    
    # Clear temporary files
    log "Clearing temporary files..."
    rm -f /tmp/docsmait_*.log 2>/dev/null || true
    rm -f /tmp/docsmait_health_report_*.txt 2>/dev/null || true
    
    success "File system data reset completed"
}

verify_reset() {
    title "Verifying Reset"
    
    local issues=()
    
    # Check database
    log "Checking database state..."
    
    # Count records in key tables
    local project_count=$(docker exec docsmait_postgres psql -U docsmait_user -d docsmait -t -c "SELECT COUNT(*) FROM projects;" 2>/dev/null | xargs || echo "0")
    local issue_count=$(docker exec docsmait_postgres psql -U docsmait_user -d docsmait -t -c "SELECT COUNT(*) FROM issues;" 2>/dev/null | xargs || echo "0")
    local document_count=$(docker exec docsmait_postgres psql -U docsmait_user -d docsmait -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null | xargs || echo "0")
    local user_count=$(docker exec docsmait_postgres psql -U docsmait_user -d docsmait -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs || echo "0")
    
    echo "  Projects: $project_count"
    echo "  Issues: $issue_count"
    echo "  Documents: $document_count"
    echo "  Users: $user_count"
    
    if [ "$project_count" != "0" ] || [ "$issue_count" != "0" ] || [ "$document_count" != "0" ]; then
        issues+=("Database tables still contain data")
    fi
    
    if [ "$user_count" = "0" ]; then
        issues+=("No admin user found in database")
    fi
    
    # Check Qdrant
    log "Checking Qdrant state..."
    
    if curl -s "http://localhost:6333/collections" 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('result', {}).get('collections', [])))" 2>/dev/null | grep -q "0"; then
        echo "  Qdrant collections: 0 (clean)"
    else
        issues+=("Qdrant still contains collections")
    fi
    
    # Report results
    echo ""
    if [ ${#issues[@]} -eq 0 ]; then
        success "Reset verification passed - system is clean"
    else
        warning "Reset verification found issues:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
    fi
}

post_reset_instructions() {
    title "Post-Reset Instructions"
    
    echo ""
    success "Data reset completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. 🔍 Verify System:"
    echo "   • Open http://localhost:8501 in your browser"
    echo "   • Log in with your admin account"
    echo "   • Confirm the system is clean"
    echo ""
    echo "2. 🚀 Start Fresh:"
    echo "   • Create new projects as needed"
    echo "   • Import templates if required"
    echo "   • Configure system settings"
    echo ""
    echo "3. 👥 Add Users:"
    echo "   • Create user accounts for team members"
    echo "   • Set up project memberships"
    echo "   • Configure permissions"
    echo ""
    echo "4. 📊 Restore Data (if needed):"
    echo "   • Import specific data from backups"
    echo "   • Use selective restore if available"
    echo ""
    info "The admin user and system configuration have been preserved"
}

show_usage() {
    echo "Docsmait Data Reset Script"
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --confirm     Skip interactive confirmation (DANGEROUS)"
    echo "  --help, -h    Show this help message"
    echo ""
    echo "This script will:"
    echo "  • Reset all application data (projects, issues, documents, etc.)"
    echo "  • Clear the Qdrant vector database"
    echo "  • Remove uploaded files"
    echo "  • Preserve the admin user account"
    echo "  • Preserve system configuration"
    echo ""
    echo "⚠️  WARNING: This operation is irreversible!"
    echo "   Make sure you have backups of any important data."
}

# Main execution
main() {
    local skip_confirm=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --confirm)
                skip_confirm=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    title "Docsmait Data Reset"
    
    # Confirmation
    if [ "$skip_confirm" = false ]; then
        confirm_reset
    else
        warning "Skipping confirmation as requested - proceeding with reset!"
    fi
    
    # Pre-flight checks
    check_services
    
    # Backup admin user
    local admin_backup
    admin_backup=$(backup_admin_user)
    
    # Reset data
    reset_postgresql_data
    reset_qdrant_data
    reset_file_system_data
    
    # Restore admin user
    restore_admin_user "$admin_backup"
    
    # Verify reset
    verify_reset
    
    # Instructions
    post_reset_instructions
    
    success "=== Data Reset Process Completed ==="
}

# Execute main function
main "$@"