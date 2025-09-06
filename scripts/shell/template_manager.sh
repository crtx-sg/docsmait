#!/bin/bash
# Docsmait Template Management Script v1.2
# Bulk template operations, import/export, and management utilities

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/templates"
BACKEND_TEMPLATE_DIR="$SCRIPT_DIR/backend/templates"

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

check_dependencies() {
    # Check if required tools are available
    local tools=("docker" "python3" "find" "tar")
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Check if backend is accessible
    if ! docker ps --filter "name=docsmait_backend" --filter "status=running" --format "{{.Names}}" | grep -q "^docsmait_backend$"; then
        warning "Backend container is not running - some operations may not work"
    fi
}

list_templates() {
    title "Available Templates"
    
    echo ""
    info "File System Templates:"
    
    if [ -d "$TEMPLATE_DIR" ]; then
        find "$TEMPLATE_DIR" -name "*.md" -type f | while read -r template; do
            local rel_path=${template#$TEMPLATE_DIR/}
            local size=$(du -h "$template" | cut -f1)
            echo "  📄 $rel_path ($size)"
        done
    else
        warning "Template directory not found: $TEMPLATE_DIR"
    fi
    
    if [ -d "$BACKEND_TEMPLATE_DIR" ]; then
        echo ""
        info "Backend Templates:"
        find "$BACKEND_TEMPLATE_DIR" -name "*.md" -type f | while read -r template; do
            local rel_path=${template#$BACKEND_TEMPLATE_DIR/}
            local size=$(du -h "$template" | cut -f1)
            echo "  📄 $rel_path ($size)"
        done
    fi
    
    echo ""
    info "Database Templates:"
    
    # Try to get templates from database via API
    if curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
        # Backend is accessible, try to get templates
        # This would require implementing an API endpoint for template listing
        echo "  (Database template listing requires API implementation)"
    else
        echo "  (Backend not accessible)"
    fi
}

bulk_upload_templates() {
    local source_dir="$1"
    
    title "Bulk Template Upload"
    
    if [ ! -d "$source_dir" ]; then
        error "Source directory not found: $source_dir"
        return 1
    fi
    
    log "Uploading templates from: $source_dir"
    
    # Find all template files
    local template_count=0
    local success_count=0
    
    find "$source_dir" -name "*.md" -type f | while read -r template_file; do
        ((template_count++))
        
        local filename=$(basename "$template_file")
        local category=$(dirname "${template_file#$source_dir/}")
        
        if [ "$category" = "." ]; then
            category="general"
        fi
        
        log "Uploading: $filename (category: $category)"
        
        # Copy to backend template directory
        local target_dir="$BACKEND_TEMPLATE_DIR/$category"
        mkdir -p "$target_dir"
        
        if cp "$template_file" "$target_dir/"; then
            success "Uploaded: $filename"
            ((success_count++))
        else
            error "Failed to upload: $filename"
        fi
    done
    
    success "Bulk upload completed: $success_count/$template_count templates"
}

export_templates() {
    local output_dir="$1"
    local format="${2:-directory}"
    
    title "Template Export"
    
    if [ -z "$output_dir" ]; then
        output_dir="/tmp/docsmait_templates_$(date '+%Y%m%d_%H%M%S')"
    fi
    
    log "Exporting templates to: $output_dir"
    log "Export format: $format"
    
    mkdir -p "$output_dir"
    
    local exported_count=0
    
    # Export from file system
    if [ -d "$TEMPLATE_DIR" ]; then
        log "Exporting file system templates..."
        
        find "$TEMPLATE_DIR" -name "*.md" -type f | while read -r template; do
            local rel_path=${template#$TEMPLATE_DIR/}
            local target_path="$output_dir/filesystem/$rel_path"
            
            mkdir -p "$(dirname "$target_path")"
            cp "$template" "$target_path"
            ((exported_count++))
        done
    fi
    
    # Export from backend
    if [ -d "$BACKEND_TEMPLATE_DIR" ]; then
        log "Exporting backend templates..."
        
        find "$BACKEND_TEMPLATE_DIR" -name "*.md" -type f | while read -r template; do
            local rel_path=${template#$BACKEND_TEMPLATE_DIR/}
            local target_path="$output_dir/backend/$rel_path"
            
            mkdir -p "$(dirname "$target_path")"
            cp "$template" "$target_path"
            ((exported_count++))
        done
    fi
    
    # Create export manifest
    cat > "$output_dir/export_manifest.json" << EOF
{
  "export_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "export_format": "$format",
  "exported_templates": $exported_count,
  "source_directories": [
    "$TEMPLATE_DIR",
    "$BACKEND_TEMPLATE_DIR"
  ],
  "docsmait_version": "1.2"
}
EOF
    
    if [ "$format" = "archive" ]; then
        local archive_path="${output_dir}.tar.gz"
        log "Creating archive: $archive_path"
        
        tar -czf "$archive_path" -C "$(dirname "$output_dir")" "$(basename "$output_dir")"
        rm -rf "$output_dir"
        
        success "Templates exported to archive: $archive_path"
    else
        success "Templates exported to directory: $output_dir"
    fi
    
    success "Export completed: $exported_count templates"
}

import_templates() {
    local source_path="$1"
    
    title "Template Import"
    
    if [ ! -e "$source_path" ]; then
        error "Source path not found: $source_path"
        return 1
    fi
    
    local temp_dir="/tmp/template_import_$$"
    local import_count=0
    
    # Extract if archive
    if [[ "$source_path" == *.tar.gz ]] || [[ "$source_path" == *.tgz ]]; then
        log "Extracting archive: $source_path"
        mkdir -p "$temp_dir"
        
        if tar -xzf "$source_path" -C "$temp_dir"; then
            source_path=$(find "$temp_dir" -maxdepth 1 -type d | head -2 | tail -1)
            success "Archive extracted to: $source_path"
        else
            error "Failed to extract archive"
            rm -rf "$temp_dir"
            return 1
        fi
    fi
    
    log "Importing templates from: $source_path"
    
    # Import templates
    find "$source_path" -name "*.md" -type f | while read -r template; do
        local rel_path=${template#$source_path/}
        
        # Skip certain directories
        case "$rel_path" in
            export_manifest.json) continue ;;
        esac
        
        # Determine target directory
        local target_path
        if [[ "$rel_path" == filesystem/* ]]; then
            target_path="$TEMPLATE_DIR/${rel_path#filesystem/}"
        elif [[ "$rel_path" == backend/* ]]; then
            target_path="$BACKEND_TEMPLATE_DIR/${rel_path#backend/}"
        else
            target_path="$BACKEND_TEMPLATE_DIR/imported/$rel_path"
        fi
        
        mkdir -p "$(dirname "$target_path")"
        
        if cp "$template" "$target_path"; then
            log "Imported: $rel_path"
            ((import_count++))
        else
            error "Failed to import: $rel_path"
        fi
    done
    
    # Clean up temporary directory
    if [ -d "$temp_dir" ]; then
        rm -rf "$temp_dir"
    fi
    
    success "Import completed: $import_count templates"
}

validate_templates() {
    title "Template Validation"
    
    local total_count=0
    local valid_count=0
    local invalid_count=0
    
    # Validate file system templates
    if [ -d "$TEMPLATE_DIR" ]; then
        log "Validating file system templates..."
        
        find "$TEMPLATE_DIR" -name "*.md" -type f | while read -r template; do
            ((total_count++))
            
            local filename=$(basename "$template")
            local size=$(stat -c%s "$template")
            
            # Basic validation checks
            local issues=()
            
            # Check file size (should not be empty or too large)
            if [ "$size" -eq 0 ]; then
                issues+=("empty file")
            elif [ "$size" -gt 1048576 ]; then  # 1MB
                issues+=("file too large (>1MB)")
            fi
            
            # Check markdown format
            if ! head -n 1 "$template" | grep -q "^#"; then
                issues+=("no markdown header")
            fi
            
            # Check for basic content
            if [ "$(wc -l < "$template")" -lt 3 ]; then
                issues+=("too few lines")
            fi
            
            if [ ${#issues[@]} -eq 0 ]; then
                success "Valid: $filename"
                ((valid_count++))
            else
                error "Invalid: $filename ($(IFS=', '; echo "${issues[*]}"))"
                ((invalid_count++))
            fi
        done
    fi
    
    # Validate backend templates
    if [ -d "$BACKEND_TEMPLATE_DIR" ]; then
        log "Validating backend templates..."
        
        find "$BACKEND_TEMPLATE_DIR" -name "*.md" -type f | while read -r template; do
            # Similar validation logic as above
            local filename=$(basename "$template")
            local size=$(stat -c%s "$template")
            
            local issues=()
            
            if [ "$size" -eq 0 ]; then
                issues+=("empty file")
            elif [ "$size" -gt 1048576 ]; then
                issues+=("file too large (>1MB)")
            fi
            
            if ! head -n 1 "$template" | grep -q "^#"; then
                issues+=("no markdown header")
            fi
            
            if [ ${#issues[@]} -eq 0 ]; then
                success "Valid: backend/$filename"
            else
                error "Invalid: backend/$filename ($(IFS=', '; echo "${issues[*]}"))"
            fi
        done
    fi
    
    echo ""
    info "Validation Summary:"
    echo "  Total templates: $total_count"
    echo "  Valid: $valid_count"
    echo "  Invalid: $invalid_count"
    
    if [ "$invalid_count" -eq 0 ]; then
        success "All templates are valid!"
    else
        warning "$invalid_count templates have validation issues"
    fi
}

organize_templates() {
    title "Template Organization"
    
    log "Organizing templates by category..."
    
    local organized_count=0
    
    # Create category directories
    local categories=("medical-devices" "automotive" "industrial" "general" "regulatory")
    
    for category in "${categories[@]}"; do
        mkdir -p "$BACKEND_TEMPLATE_DIR/$category"
        mkdir -p "$TEMPLATE_DIR/$category"
    done
    
    # Move uncategorized templates
    find "$BACKEND_TEMPLATE_DIR" -maxdepth 1 -name "*.md" -type f | while read -r template; do
        local filename=$(basename "$template")
        local category="general"
        
        # Categorize based on filename or content
        case "$filename" in
            *iso13485*|*iso14971*|*iec62304*|*fda*|*medical*)
                category="medical-devices"
                ;;
            *iso26262*|*asil*|*automotive*)
                category="automotive"
                ;;
            *iec61508*|*sil*|*industrial*)
                category="industrial"
                ;;
            *regulation*|*compliance*|*audit*)
                category="regulatory"
                ;;
        esac
        
        local target="$BACKEND_TEMPLATE_DIR/$category/$filename"
        
        if mv "$template" "$target"; then
            log "Moved $filename to $category/"
            ((organized_count++))
        fi
    done
    
    success "Organization completed: $organized_count templates organized"
}

cleanup_templates() {
    title "Template Cleanup"
    
    warning "This will remove duplicate and invalid templates"
    read -p "Continue? (y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log "Cleanup cancelled"
        return 0
    fi
    
    local removed_count=0
    
    # Remove empty files
    find "$TEMPLATE_DIR" "$BACKEND_TEMPLATE_DIR" -name "*.md" -type f -empty -delete 2>/dev/null && {
        log "Removed empty template files"
        ((removed_count++))
    }
    
    # Remove duplicate files (based on content hash)
    declare -A seen_hashes
    
    find "$BACKEND_TEMPLATE_DIR" -name "*.md" -type f | while read -r template; do
        local hash=$(md5sum "$template" | cut -d' ' -f1)
        
        if [ -n "${seen_hashes[$hash]}" ]; then
            log "Removing duplicate: $template (same as ${seen_hashes[$hash]})"
            rm -f "$template"
            ((removed_count++))
        else
            seen_hashes[$hash]="$template"
        fi
    done
    
    # Remove templates that are too small (likely incomplete)
    find "$BACKEND_TEMPLATE_DIR" -name "*.md" -type f -size -100c -delete 2>/dev/null && {
        log "Removed templates smaller than 100 bytes"
        ((removed_count++))
    }
    
    # Clean up empty directories
    find "$TEMPLATE_DIR" "$BACKEND_TEMPLATE_DIR" -type d -empty -delete 2>/dev/null && {
        log "Removed empty directories"
    }
    
    success "Cleanup completed: $removed_count items removed"
}

show_usage() {
    echo "Docsmait Template Management Script"
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  list                          List all available templates"
    echo "  upload <source_directory>     Bulk upload templates from directory"
    echo "  export <output_dir> [format]  Export templates (format: directory|archive)"
    echo "  import <source_path>          Import templates from directory or archive"
    echo "  validate                      Validate all templates"
    echo "  organize                      Organize templates by category"
    echo "  cleanup                       Clean up duplicate and invalid templates"
    echo ""
    echo "Examples:"
    echo "  $0 list                           # List all templates"
    echo "  $0 upload /path/to/templates      # Upload templates from directory"
    echo "  $0 export /tmp/backup archive     # Export as archive"
    echo "  $0 import templates.tar.gz        # Import from archive"
    echo "  $0 validate                       # Validate templates"
    echo "  $0 organize                       # Organize by categories"
}

# Main execution
main() {
    if [ $# -eq 0 ]; then
        show_usage
        exit 0
    fi
    
    # Pre-flight checks
    check_dependencies
    
    case "$1" in
        list)
            list_templates
            ;;
        upload)
            if [ -z "$2" ]; then
                error "Upload requires source directory"
                exit 1
            fi
            bulk_upload_templates "$2"
            ;;
        export)
            export_templates "$2" "$3"
            ;;
        import)
            if [ -z "$2" ]; then
                error "Import requires source path"
                exit 1
            fi
            import_templates "$2"
            ;;
        validate)
            validate_templates
            ;;
        organize)
            organize_templates
            ;;
        cleanup)
            cleanup_templates
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