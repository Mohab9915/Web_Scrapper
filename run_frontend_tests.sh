#!/bin/bash

# Comprehensive Frontend Integration Test Runner
# This script runs complete frontend-backend integration tests

set -e  # Exit on any error

echo "🚀 ScrapeMaster AI - Frontend Integration Test Suite"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    print_success "Python found: $PYTHON_CMD"
}

# Check if Node.js and npm are available
check_nodejs() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Node.js and npm found"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Check if requests is available
    if ! $PYTHON_CMD -c "import requests" &> /dev/null; then
        print_status "Installing requests..."
        pip install requests
    fi
    
    # Check if psutil is available
    if ! $PYTHON_CMD -c "import psutil" &> /dev/null; then
        print_status "Installing psutil..."
        pip install psutil
    fi
    
    print_success "Python dependencies ready"
}

# Check if backend dependencies are installed
check_backend_deps() {
    print_status "Checking backend dependencies..."
    
    if [ -d "backend/venv" ]; then
        print_success "Backend virtual environment found"
    elif [ -f "backend/requirements.txt" ]; then
        print_warning "Backend requirements.txt found but venv not detected"
        print_status "You may need to install backend dependencies manually"
    else
        print_warning "Backend directory structure not as expected"
    fi
}

# Check if frontend dependencies are installed
check_frontend_deps() {
    print_status "Checking frontend dependencies..."
    
    if [ -d "new-front/node_modules" ]; then
        print_success "Frontend dependencies already installed"
    elif [ -f "new-front/package.json" ]; then
        print_status "Installing frontend dependencies..."
        cd new-front
        npm install
        cd ..
        print_success "Frontend dependencies installed"
    else
        print_error "Frontend package.json not found"
        exit 1
    fi
}

# Run the comprehensive tests
run_tests() {
    print_status "Starting comprehensive frontend integration tests..."
    
    # Make sure test files are executable
    chmod +x comprehensive_frontend_integration_test.py
    chmod +x frontend_ui_integration_test.py
    chmod +x run_comprehensive_frontend_tests.py
    
    # Run the comprehensive test suite
    $PYTHON_CMD run_comprehensive_frontend_tests.py
}

# Main execution
main() {
    echo ""
    print_status "Performing pre-flight checks..."
    
    # Check prerequisites
    check_python
    check_nodejs
    install_python_deps
    check_backend_deps
    check_frontend_deps
    
    echo ""
    print_status "All prerequisites checked. Ready to run tests."
    echo ""
    
    # Ask for confirmation
    read -p "Do you want to proceed with the comprehensive frontend integration tests? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    else
        print_status "Tests cancelled by user"
        exit 0
    fi
}

# Handle script interruption
trap 'print_warning "Script interrupted by user"; exit 1' INT

# Run main function
main "$@"
