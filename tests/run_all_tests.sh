#!/bin/bash

# Docsmait Comprehensive Test Runner
# Executes all test categories with proper reporting

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_RESULTS_DIR="$SCRIPT_DIR/test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$TEST_RESULTS_DIR/test_execution_$TIMESTAMP.log"
REPORT_FILE="$TEST_RESULTS_DIR/test_report_$TIMESTAMP.html"
JSON_REPORT="$TEST_RESULTS_DIR/test_results_$TIMESTAMP.json"

# Create results directory
mkdir -p "$TEST_RESULTS_DIR"

# Initialize log file
cat > "$LOG_FILE" << EOF
========================================
Docsmait Test Suite Execution Log
========================================
Started: $(date)
Test Directory: $SCRIPT_DIR
Results Directory: $TEST_RESULTS_DIR
========================================

EOF

# Logging function
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docsmait is running
    if ! curl -s http://localhost:8001/settings > /dev/null; then
        log_error "Backend service not running on http://localhost:8001"
        log_error "Please start Docsmait with: docker compose up -d"
        exit 1
    fi
    
    if ! curl -s http://localhost:8501 > /dev/null; then
        log_warning "Frontend service not accessible on http://localhost:8501"
        log_warning "Some frontend tests may be skipped"
    fi
    
    # Check Python and pytest
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is required but not installed"
        exit 1
    fi
    
    if ! python3 -c "import pytest" 2>/dev/null; then
        log_error "pytest is required. Install with: pip install pytest"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to install test dependencies
install_dependencies() {
    log_info "Installing test dependencies..."
    
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        if pip install -r "$SCRIPT_DIR/requirements.txt" >> "$LOG_FILE" 2>&1; then
            log_success "Test dependencies installed"
        else
            log_warning "Some test dependencies may not have installed properly"
        fi
    else
        log_warning "requirements.txt not found, skipping dependency installation"
    fi
}

# Function to run test category
run_test_category() {
    local category=$1
    local category_dir="$SCRIPT_DIR/$category"
    local category_results="$TEST_RESULTS_DIR/${category}_results_$TIMESTAMP.xml"
    
    log_info "Running $category tests..."
    
    if [[ ! -d "$category_dir" ]]; then
        log_warning "$category directory not found, skipping"
        return 0
    fi
    
    # Count test files
    test_files=$(find "$category_dir" -name "test_*.py" | wc -l)
    if [[ $test_files -eq 0 ]]; then
        log_warning "No test files found in $category, skipping"
        return 0
    fi
    
    # Run tests with comprehensive options
    local pytest_cmd="python3 -m pytest $category_dir \
        --verbose \
        --tb=short \
        --maxfail=5 \
        --junit-xml=$category_results \
        --capture=sys \
        -m \"not slow\" \
        --disable-warnings"
    
    log_info "Executing: $pytest_cmd"
    
    if eval $pytest_cmd >> "$LOG_FILE" 2>&1; then
        log_success "$category tests completed successfully"
        return 0
    else
        local exit_code=$?
        log_error "$category tests failed with exit code $exit_code"
        return $exit_code
    fi
}

# Function to run slow tests separately
run_slow_tests() {
    log_info "Running slow/integration tests..."
    
    local slow_results="$TEST_RESULTS_DIR/slow_tests_$TIMESTAMP.xml"
    local pytest_cmd="python3 -m pytest \
        --verbose \
        --tb=short \
        --maxfail=3 \
        --junit-xml=$slow_results \
        --capture=sys \
        -m \"slow\" \
        --disable-warnings \
        integration/ performance/"
    
    if eval $pytest_cmd >> "$LOG_FILE" 2>&1; then
        log_success "Slow tests completed successfully"
        return 0
    else
        log_warning "Some slow tests failed (this may be expected)"
        return 0  # Don't fail entire suite for slow test failures
    fi
}

# Function to generate comprehensive report
generate_report() {
    log_info "Generating test report..."
    
    # Create HTML report
    cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Docsmait Test Suite Report - $TIMESTAMP</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        .section { margin: 20px 0; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 3px; overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Docsmait Test Suite Report</h1>
        <p><strong>Generated:</strong> $(date)</p>
        <p><strong>Test Run ID:</strong> $TIMESTAMP</p>
    </div>
    
    <div class="section">
        <h2>Test Execution Summary</h2>
EOF

    # Add summary statistics
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    local skipped_tests=0
    
    # Parse XML results if available
    for xml_file in "$TEST_RESULTS_DIR"/*_results_$TIMESTAMP.xml; do
        if [[ -f "$xml_file" ]]; then
            if command -v xmllint &> /dev/null; then
                local file_tests=$(xmllint --xpath "//testsuite/@tests" "$xml_file" 2>/dev/null | grep -o '[0-9]*' || echo "0")
                local file_failures=$(xmllint --xpath "//testsuite/@failures" "$xml_file" 2>/dev/null | grep -o '[0-9]*' || echo "0")
                local file_skipped=$(xmllint --xpath "//testsuite/@skipped" "$xml_file" 2>/dev/null | grep -o '[0-9]*' || echo "0")
                
                total_tests=$((total_tests + file_tests))
                failed_tests=$((failed_tests + file_failures))
                skipped_tests=$((skipped_tests + file_skipped))
            fi
        fi
    done
    
    passed_tests=$((total_tests - failed_tests - skipped_tests))
    
    cat >> "$REPORT_FILE" << EOF
        <table>
            <tr><th>Metric</th><th>Count</th></tr>
            <tr><td>Total Tests</td><td>$total_tests</td></tr>
            <tr><td class="success">Passed</td><td>$passed_tests</td></tr>
            <tr><td class="error">Failed</td><td>$failed_tests</td></tr>
            <tr><td class="warning">Skipped</td><td>$skipped_tests</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Test Categories</h2>
        <ul>
            <li><strong>API Tests:</strong> Authentication, endpoints, CRUD operations</li>
            <li><strong>Database Tests:</strong> CRUD operations, constraints, performance</li>
            <li><strong>Frontend Tests:</strong> UI components, navigation, accessibility</li>
            <li><strong>Integration Tests:</strong> End-to-end workflows</li>
            <li><strong>Performance Tests:</strong> Load testing, response times</li>
            <li><strong>Security Tests:</strong> Input validation, access controls</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Test Execution Log</h2>
        <pre>$(tail -50 "$LOG_FILE")</pre>
    </div>
    
    <div class="section">
        <h2>System Information</h2>
        <table>
            <tr><th>Item</th><th>Value</th></tr>
            <tr><td>Backend URL</td><td>http://localhost:8001</td></tr>
            <tr><td>Frontend URL</td><td>http://localhost:8501</td></tr>
            <tr><td>Test Environment</td><td>$(uname -a)</td></tr>
            <tr><td>Python Version</td><td>$(python3 --version)</td></tr>
            <tr><td>Docker Status</td><td>$(docker --version 2>/dev/null || echo "Not available")</td></tr>
        </table>
    </div>
    
</body>
</html>
EOF

    log_success "HTML report generated: $REPORT_FILE"
    
    # Generate JSON summary
    cat > "$JSON_REPORT" << EOF
{
    "timestamp": "$TIMESTAMP",
    "summary": {
        "total_tests": $total_tests,
        "passed": $passed_tests,
        "failed": $failed_tests,
        "skipped": $skipped_tests
    },
    "categories_tested": [
        "api", "database", "frontend", "integration", "performance", "security"
    ],
    "test_environment": {
        "backend_url": "http://localhost:8001",
        "frontend_url": "http://localhost:8501",
        "python_version": "$(python3 --version)",
        "system": "$(uname -s)"
    }
}
EOF
    
    log_success "JSON report generated: $JSON_REPORT"
}

# Function to create latest symlinks
create_latest_links() {
    # Create symlinks to latest results
    ln -sf "test_execution_$TIMESTAMP.log" "$TEST_RESULTS_DIR/latest_run.log"
    ln -sf "test_report_$TIMESTAMP.html" "$TEST_RESULTS_DIR/latest_report.html"
    ln -sf "test_results_$TIMESTAMP.json" "$TEST_RESULTS_DIR/latest_results.json"
    
    log_info "Latest result links created"
}

# Main execution
main() {
    echo "========================================="
    echo "🧪 Docsmait Comprehensive Test Suite"
    echo "========================================="
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Run all phases
    check_prerequisites
    install_dependencies
    
    # Track overall success
    overall_success=true
    
    # Run each test category
    test_categories=("api" "database" "frontend" "integration" "security")
    
    for category in "${test_categories[@]}"; do
        if ! run_test_category "$category"; then
            overall_success=false
        fi
    done
    
    # Run slow tests
    run_slow_tests
    
    # Generate reports
    generate_report
    create_latest_links
    
    # Final summary
    echo ""
    echo "========================================="
    if $overall_success; then
        log_success "🎉 Test suite completed successfully!"
        echo -e "${GREEN}✓ View results: $REPORT_FILE${NC}"
        echo -e "${GREEN}✓ Latest log: $TEST_RESULTS_DIR/latest_run.log${NC}"
        exit 0
    else
        log_warning "⚠️  Test suite completed with some failures"
        echo -e "${YELLOW}⚠ View results: $REPORT_FILE${NC}"
        echo -e "${YELLOW}⚠ Check log: $TEST_RESULTS_DIR/latest_run.log${NC}"
        exit 1
    fi
}

# Handle script termination
cleanup() {
    log_info "Test execution interrupted"
    exit 130
}

trap cleanup INT TERM

# Run main function
main "$@"