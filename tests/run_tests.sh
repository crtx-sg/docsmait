#!/bin/bash

# Docsmait Selective Test Runner
# Run specific test categories or individual tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_RESULTS_DIR="$SCRIPT_DIR/test_results"

# Create results directory
mkdir -p "$TEST_RESULTS_DIR"

# Default options
CATEGORY=""
VERBOSE=false
COVERAGE=false
SLOW_TESTS=false
PARALLEL=false
MAX_WORKERS=4
FILTER=""

# Help function
show_help() {
    cat << EOF
Docsmait Selective Test Runner

Usage: $0 [OPTIONS]

Options:
    --category=NAME     Run tests for specific category (api, auth, database, frontend, integration, performance, security)
    --verbose, -v       Run tests in verbose mode
    --coverage, -c      Run tests with coverage reporting
    --slow, -s          Include slow tests
    --parallel, -p      Run tests in parallel
    --workers=N         Number of parallel workers (default: 4)
    --filter=PATTERN    Run tests matching pattern
    --help, -h          Show this help message

Categories:
    api                 API endpoint tests
    auth                Authentication tests
    database            Database operation tests  
    frontend            Frontend UI tests
    integration         End-to-end integration tests
    performance         Performance and load tests
    security            Security validation tests

Examples:
    $0 --category=api                    # Run all API tests
    $0 --category=api --verbose          # Run API tests with verbose output
    $0 --category=frontend --coverage    # Run frontend tests with coverage
    $0 --filter="test_login"             # Run tests matching "test_login"
    $0 --category=integration --slow     # Run integration tests including slow ones
    $0 --parallel --workers=8            # Run all tests with 8 parallel workers

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --category=*)
            CATEGORY="${1#*=}"
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --slow|-s)
            SLOW_TESTS=true
            shift
            ;;
        --parallel|-p)
            PARALLEL=true
            shift
            ;;
        --workers=*)
            MAX_WORKERS="${1#*=}"
            shift
            ;;
        --filter=*)
            FILTER="${1#*=}"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_services() {
    log_info "Checking service availability..."
    
    if ! curl -s http://localhost:8001/settings > /dev/null; then
        log_error "Backend service not running on http://localhost:8001"
        log_error "Start Docsmait with: docker compose up -d"
        exit 1
    fi
    
    log_success "Backend service is accessible"
}

# Build pytest command
build_pytest_command() {
    local cmd="python3 -m pytest"
    
    # Add test path
    if [[ -n "$CATEGORY" ]]; then
        case $CATEGORY in
            api)
                cmd+=" api/"
                ;;
            auth)
                cmd+=" api/test_authentication.py"
                ;;
            database)
                cmd+=" database/"
                ;;
            frontend)
                cmd+=" frontend/"
                ;;
            integration)
                cmd+=" integration/"
                ;;
            performance)
                cmd+=" performance/ -m \"performance or slow\""
                ;;
            security)
                cmd+=" security/"
                ;;
            *)
                log_error "Unknown category: $CATEGORY"
                log_error "Available categories: api, auth, database, frontend, integration, performance, security"
                exit 1
                ;;
        esac
    else
        cmd+=" ."
    fi
    
    # Add verbosity
    if $VERBOSE; then
        cmd+=" --verbose"
    else
        cmd+=" -q"
    fi
    
    # Add coverage
    if $COVERAGE; then
        cmd+=" --cov=app --cov-report=html:$TEST_RESULTS_DIR/coverage_html --cov-report=term"
    fi
    
    # Add parallel execution
    if $PARALLEL; then
        cmd+=" -n $MAX_WORKERS"
    fi
    
    # Add slow tests or exclude them
    if $SLOW_TESTS; then
        cmd+=" -m \"not skip\""
    else
        cmd+=" -m \"not slow\""
    fi
    
    # Add filter
    if [[ -n "$FILTER" ]]; then
        cmd+=" -k \"$FILTER\""
    fi
    
    # Add common options
    cmd+=" --tb=short --maxfail=10 --disable-warnings"
    
    # Add result reporting
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local category_name="${CATEGORY:-all}"
    cmd+=" --junit-xml=$TEST_RESULTS_DIR/${category_name}_results_$timestamp.xml"
    
    echo "$cmd"
}

# Run tests
run_tests() {
    local pytest_cmd
    pytest_cmd=$(build_pytest_command)
    
    log_info "Running tests with command:"
    echo "  $pytest_cmd"
    echo ""
    
    # Change to test directory
    cd "$SCRIPT_DIR"
    
    # Execute tests
    if eval $pytest_cmd; then
        local exit_code=$?
        log_success "Tests completed successfully"
        
        # Show coverage report location if generated
        if $COVERAGE && [[ -d "$TEST_RESULTS_DIR/coverage_html" ]]; then
            log_info "Coverage report: $TEST_RESULTS_DIR/coverage_html/index.html"
        fi
        
        return $exit_code
    else
        local exit_code=$?
        log_error "Tests failed with exit code $exit_code"
        return $exit_code
    fi
}

# Show test summary
show_summary() {
    local category_display="${CATEGORY:-all tests}"
    
    echo ""
    echo "========================================="
    echo "🧪 Test Summary for $category_display"
    echo "========================================="
    
    # Find latest result file
    local latest_xml=$(ls -t "$TEST_RESULTS_DIR"/*.xml 2>/dev/null | head -1)
    
    if [[ -f "$latest_xml" ]] && command -v xmllint &> /dev/null; then
        local total=$(xmllint --xpath "//testsuite/@tests" "$latest_xml" 2>/dev/null | grep -o '[0-9]*' || echo "0")
        local failures=$(xmllint --xpath "//testsuite/@failures" "$latest_xml" 2>/dev/null | grep -o '[0-9]*' || echo "0")
        local skipped=$(xmllint --xpath "//testsuite/@skipped" "$latest_xml" 2>/dev/null | grep -o '[0-9]*' || echo "0")
        local passed=$((total - failures - skipped))
        
        echo "Total tests: $total"
        echo -e "Passed: ${GREEN}$passed${NC}"
        echo -e "Failed: ${RED}$failures${NC}"
        echo -e "Skipped: ${YELLOW}$skipped${NC}"
    fi
    
    echo ""
    echo "Results saved to: $TEST_RESULTS_DIR/"
    
    if $COVERAGE; then
        echo "Coverage report: $TEST_RESULTS_DIR/coverage_html/index.html"
    fi
}

# Quick test function for individual test discovery
list_tests() {
    log_info "Discovering available tests..."
    
    cd "$SCRIPT_DIR"
    
    echo ""
    echo "Available test categories:"
    echo "  api         - $(find api/ -name "test_*.py" 2>/dev/null | wc -l) test files"
    echo "  database    - $(find database/ -name "test_*.py" 2>/dev/null | wc -l) test files"
    echo "  frontend    - $(find frontend/ -name "test_*.py" 2>/dev/null | wc -l) test files"
    echo "  integration - $(find integration/ -name "test_*.py" 2>/dev/null | wc -l) test files"
    echo "  security    - $(find security/ -name "test_*.py" 2>/dev/null | wc -l) test files"
    echo ""
    
    if [[ -n "$CATEGORY" ]]; then
        echo "Tests in $CATEGORY category:"
        python3 -m pytest --collect-only -q "$CATEGORY/" 2>/dev/null | grep "test_" | head -20
        echo ""
    fi
}

# Main execution
main() {
    echo "🧪 Docsmait Selective Test Runner"
    echo "=================================="
    
    # Show test discovery if no specific action
    if [[ -z "$CATEGORY" && -z "$FILTER" ]]; then
        list_tests
        echo "Use --help for usage information"
        echo "Example: $0 --category=api --verbose"
        exit 0
    fi
    
    # Check services
    check_services
    
    # Run tests
    if run_tests; then
        show_summary
        exit 0
    else
        show_summary
        exit 1
    fi
}

# Handle interruption
cleanup() {
    log_info "Test execution interrupted"
    exit 130
}

trap cleanup INT TERM

# Execute main function
main "$@"