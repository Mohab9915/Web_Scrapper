#!/bin/bash

# Azure Setup Script for Interactive Agentic Web Scraper & RAG System
# This script helps you set up the prerequisites for Azure deployment

set -e

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Azure CLI
install_azure_cli() {
    print_status "Installing Azure CLI..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install azure-cli
        else
            print_error "Homebrew not found. Please install Homebrew first or install Azure CLI manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        print_warning "Please install Azure CLI manually from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows"
        exit 1
    else
        print_error "Unsupported operating system. Please install Azure CLI manually."
        exit 1
    fi
    
    print_success "Azure CLI installed successfully"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check Azure CLI
    if ! command_exists az; then
        print_warning "Azure CLI not found"
        read -p "Would you like to install Azure CLI? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_azure_cli
        else
            missing_tools+=("azure-cli")
        fi
    else
        print_success "Azure CLI is installed"
    fi
    
    # Check Docker
    if ! command_exists docker; then
        print_warning "Docker not found"
        missing_tools+=("docker")
    else
        print_success "Docker is installed"
    fi
    
    # Check Git
    if ! command_exists git; then
        print_warning "Git not found"
        missing_tools+=("git")
    else
        print_success "Git is installed"
    fi
    
    # Check Node.js
    if ! command_exists node; then
        print_warning "Node.js not found"
        missing_tools+=("nodejs")
    else
        NODE_VERSION=$(node --version)
        print_success "Node.js is installed ($NODE_VERSION)"
    fi
    
    # Check Python
    if ! command_exists python3; then
        print_warning "Python 3 not found"
        missing_tools+=("python3")
    else
        PYTHON_VERSION=$(python3 --version)
        print_success "Python 3 is installed ($PYTHON_VERSION)"
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo
        echo "Please install the missing tools and run this script again."
        echo
        echo "Installation guides:"
        echo "- Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        echo "- Docker: https://docs.docker.com/get-docker/"
        echo "- Git: https://git-scm.com/downloads"
        echo "- Node.js: https://nodejs.org/en/download/"
        echo "- Python 3: https://www.python.org/downloads/"
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Function to login to Azure
azure_login() {
    print_status "Checking Azure login status..."
    
    if ! az account show &> /dev/null; then
        print_status "Not logged into Azure. Starting login process..."
        az login
    else
        print_success "Already logged into Azure"
        
        # Show current account
        CURRENT_ACCOUNT=$(az account show --query "name" --output tsv)
        print_status "Current account: $CURRENT_ACCOUNT"
        
        read -p "Would you like to use a different account? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            az login
        fi
    fi
    
    # List available subscriptions
    print_status "Available subscriptions:"
    az account list --output table
    
    echo
    read -p "Enter the subscription ID you want to use (or press Enter to use current): " SUBSCRIPTION_ID
    
    if [ ! -z "$SUBSCRIPTION_ID" ]; then
        az account set --subscription "$SUBSCRIPTION_ID"
        print_success "Subscription set to: $SUBSCRIPTION_ID"
    fi
}

# Function to verify environment configuration
verify_environment() {
    print_status "Verifying environment configuration..."
    
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        echo
        echo "Please create a .env file with your configuration:"
        echo "cp .env.production .env"
        echo "# Then edit .env with your actual values"
        exit 1
    fi
    
    # Check required environment variables
    source .env
    
    local missing_vars=()
    
    if [ -z "$SUPABASE_URL" ] || [[ "$SUPABASE_URL" == *"your_"* ]]; then
        missing_vars+=("SUPABASE_URL")
    fi
    
    if [ -z "$SUPABASE_KEY" ] || [[ "$SUPABASE_KEY" == *"your_"* ]]; then
        missing_vars+=("SUPABASE_KEY")
    fi
    
    if [ -z "$AZURE_OPENAI_API_KEY" ] || [[ "$AZURE_OPENAI_API_KEY" == *"your_"* ]]; then
        missing_vars+=("AZURE_OPENAI_API_KEY")
    fi
    
    if [ -z "$AZURE_OPENAI_ENDPOINT" ] || [[ "$AZURE_OPENAI_ENDPOINT" == *"your_"* ]]; then
        missing_vars+=("AZURE_OPENAI_ENDPOINT")
    fi
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing or incomplete environment variables: ${missing_vars[*]}"
        echo
        echo "Please update your .env file with the correct values."
        exit 1
    fi
    
    print_success "Environment configuration is valid"
}

# Function to test Azure services
test_azure_services() {
    print_status "Testing Azure services connectivity..."
    
    # Test Azure OpenAI
    print_status "Testing Azure OpenAI connectivity..."
    source .env
    
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "api-key: $AZURE_OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=2024-12-01-preview")
    
    if [ "$RESPONSE" = "200" ]; then
        print_success "Azure OpenAI connectivity test passed"
    else
        print_warning "Azure OpenAI connectivity test failed (HTTP $RESPONSE)"
        print_warning "This might be normal if the endpoint requires specific deployment names"
    fi
    
    # Test Supabase
    print_status "Testing Supabase connectivity..."
    
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "apikey: $SUPABASE_KEY" \
        "$SUPABASE_URL/rest/v1/")
    
    if [ "$RESPONSE" = "200" ]; then
        print_success "Supabase connectivity test passed"
    else
        print_error "Supabase connectivity test failed (HTTP $RESPONSE)"
        echo "Please check your Supabase URL and API key"
    fi
}

# Function to create GitHub secrets (optional)
setup_github_secrets() {
    print_status "Setting up GitHub secrets for CI/CD..."
    
    if ! command_exists gh; then
        print_warning "GitHub CLI not found. Skipping GitHub secrets setup."
        echo "To set up CI/CD later, install GitHub CLI and run:"
        echo "gh auth login"
        echo "gh secret set AZURE_CREDENTIALS --body '{...}'"
        return
    fi
    
    read -p "Would you like to set up GitHub secrets for CI/CD? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    print_status "Creating Azure service principal for GitHub Actions..."
    
    SUBSCRIPTION_ID=$(az account show --query "id" --output tsv)
    
    # Create service principal
    SP_OUTPUT=$(az ad sp create-for-rbac \
        --name "scrapemaster-github-actions" \
        --role contributor \
        --scopes "/subscriptions/$SUBSCRIPTION_ID" \
        --sdk-auth)
    
    # Set GitHub secrets
    echo "$SP_OUTPUT" | gh secret set AZURE_CREDENTIALS
    
    source .env
    echo "$SUPABASE_URL" | gh secret set SUPABASE_URL
    echo "$SUPABASE_KEY" | gh secret set SUPABASE_KEY
    echo "$AZURE_OPENAI_API_KEY" | gh secret set AZURE_OPENAI_API_KEY
    echo "$AZURE_OPENAI_ENDPOINT" | gh secret set AZURE_OPENAI_ENDPOINT
    echo "$SUBSCRIPTION_ID" | gh secret set AZURE_SUBSCRIPTION_ID
    
    print_success "GitHub secrets configured successfully"
}

# Main setup function
main() {
    echo "🚀 Azure Setup for Interactive Agentic Web Scraper & RAG System"
    echo "=============================================================="
    echo
    
    check_prerequisites
    azure_login
    verify_environment
    test_azure_services
    setup_github_secrets
    
    echo
    print_success "🎉 Azure setup completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Run './deploy-azure.sh' to deploy your application"
    echo "2. Or use GitHub Actions for automated deployment"
    echo "3. Monitor your deployment in the Azure Portal"
    echo
    echo "Useful commands:"
    echo "- Check deployment status: ./deploy-azure.sh status"
    echo "- View logs: ./deploy-azure.sh logs"
    echo "- Clean up resources: ./deploy-azure.sh clean"
}

# Run main function
main
