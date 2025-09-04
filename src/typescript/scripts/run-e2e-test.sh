#!/bin/bash

# Main E2E Test Runner
# This script runs all end-to-end tests for the nacos-mcp-router project

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        exit 1
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        log_error "curl is not installed"
        exit 1
    fi
    
    log_info "✓ All dependencies are available"
}

# Install project dependencies
install_dependencies() {
    log_info "Installing project dependencies..."
    cd "$PROJECT_ROOT"
    
    if [ ! -d "node_modules" ]; then
        npm install || {
            log_error "Failed to install dependencies"
            exit 1
        }
    fi
    
    log_info "✓ Dependencies installed"
}

# Build project
build_project() {
    log_info "Building project..."
    cd "$PROJECT_ROOT"
    
    npm run build || {
        log_error "Failed to build project"
        exit 1
    }
    
    log_info "✓ Project built successfully"
}

# Run unit tests first
run_unit_tests() {
    log_header "Running Unit Tests"
    cd "$PROJECT_ROOT"
    
    npm test || {
        log_error "Unit tests failed"
        exit 1
    }
    
    log_info "✓ Unit tests passed"
}

# Run E2E tests
run_e2e_tests() {
    log_header "Running E2E Tests"
    
    # Run search functionality E2E test
    log_info "Running search functionality E2E test..."
    "$SCRIPT_DIR/e2e/run-search-e2e-test.sh" || {
        log_error "Search E2E test failed"
        exit 1
    }
    
    log_info "✓ All E2E tests passed"
}

# Main function
main() {
    log_header "Nacos MCP Router E2E Test Suite"
    log_info "Project root: $PROJECT_ROOT"
    
    # Check if we should skip unit tests
    SKIP_UNIT_TESTS=false
    if [ "$1" = "--skip-unit" ]; then
        SKIP_UNIT_TESTS=true
        log_warn "Skipping unit tests as requested"
    fi
    
    # Check if we should only run E2E tests
    E2E_ONLY=false
    if [ "$1" = "--e2e-only" ]; then
        E2E_ONLY=true
        log_info "Running E2E tests only"
    fi
    
    # Run checks and setup
    check_dependencies
    install_dependencies
    build_project
    
    # Run tests
    if [ "$E2E_ONLY" = "false" ] && [ "$SKIP_UNIT_TESTS" = "false" ]; then
        run_unit_tests
    fi
    
    run_e2e_tests
    
    log_header "Test Suite Complete"
    log_info "🎉 All tests passed successfully!"
    log_info ""
    log_info "Summary:"
    log_info "  ✓ Dependencies checked"
    log_info "  ✓ Project built"
    if [ "$E2E_ONLY" = "false" ] && [ "$SKIP_UNIT_TESTS" = "false" ]; then
        log_info "  ✓ Unit tests passed"
    fi
    log_info "  ✓ E2E tests passed"
    log_info ""
    log_info "The nacos-mcp-router project is working correctly!"
}

# Show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-unit    Skip unit tests and run only E2E tests"
    echo "  --e2e-only     Run only E2E tests (same as --skip-unit)"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 --skip-unit        # Run only E2E tests"
    echo "  $0 --e2e-only         # Run only E2E tests"
}

# Handle command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
    exit 0
fi

# Run main function
main "$@"