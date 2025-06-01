#!/bin/bash

# GitHub Actions Setup Script for Azure Deployment
# Interactive Agentic Web Scraper & RAG System

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check Azure CLI
    if ! command_exists az; then
        missing_tools+=("azure-cli")
    else
        print_success "Azure CLI is installed"
    fi
    
    # Check Git
    if ! command_exists git; then
        missing_tools+=("git")
    else
        print_success "Git is installed"
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a Git repository. Please run this script from your project root."
        exit 1
    else
        print_success "In a Git repository"
    fi
    
    # Check GitHub CLI (optional)
    if ! command_exists gh; then
        print_warning "GitHub CLI not found. You'll need to set up secrets manually."
        GITHUB_CLI_AVAILABLE=false
    else
        print_success "GitHub CLI is installed"
        GITHUB_CLI_AVAILABLE=true
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo
        echo "Please install the missing tools:"
        echo "- Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        echo "- Git: https://git-scm.com/downloads"
        echo "- GitHub CLI (optional): https://cli.github.com/"
        exit 1
    fi
}

# Function to check Azure login
check_azure_login() {
    print_status "Checking Azure login status..."
    
    if ! az account show &> /dev/null; then
        print_status "Not logged into Azure. Starting login process..."
        az login
    else
        print_success "Already logged into Azure"
        
        # Show current account
        CURRENT_ACCOUNT=$(az account show --query "name" --output tsv)
        print_status "Current account: $CURRENT_ACCOUNT"
    fi
    
    # Get subscription ID
    SUBSCRIPTION_ID=$(az account show --query "id" --output tsv)
    print_success "Using subscription: $SUBSCRIPTION_ID"
}

# Function to create Azure service principal
create_service_principal() {
    print_status "Creating Azure service principal for GitHub Actions..."
    
    # Check if service principal already exists
    SP_NAME="scrapemaster-github-actions"
    
    if az ad sp list --display-name "$SP_NAME" --query "[0].appId" --output tsv | grep -q .; then
        print_warning "Service principal '$SP_NAME' already exists"
        read -p "Do you want to create a new one? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Using existing service principal"
            return
        fi
        
        # Delete existing service principal
        print_status "Deleting existing service principal..."
        EXISTING_SP_ID=$(az ad sp list --display-name "$SP_NAME" --query "[0].appId" --output tsv)
        az ad sp delete --id "$EXISTING_SP_ID"
    fi
    
    print_status "Creating new service principal..."
    
    # Create service principal
    SP_OUTPUT=$(az ad sp create-for-rbac \
        --name "$SP_NAME" \
        --role contributor \
        --scopes "/subscriptions/$SUBSCRIPTION_ID" \
        --sdk-auth)
    
    print_success "Service principal created successfully"
    
    # Store the output for later use
    echo "$SP_OUTPUT" > /tmp/azure-credentials.json
    
    echo
    print_warning "IMPORTANT: Save this Azure credentials JSON:"
    echo "----------------------------------------"
    echo "$SP_OUTPUT"
    echo "----------------------------------------"
    echo
}

# Function to set up GitHub secrets
setup_github_secrets() {
    print_status "Setting up GitHub secrets..."
    
    if [ "$GITHUB_CLI_AVAILABLE" = true ]; then
        # Check if logged into GitHub
        if ! gh auth status &> /dev/null; then
            print_status "Not logged into GitHub. Starting login process..."
            gh auth login
        else
            print_success "Already logged into GitHub"
        fi
        
        # Set secrets using GitHub CLI
        print_status "Setting GitHub secrets using CLI..."
        
        # Azure credentials
        if [ -f "/tmp/azure-credentials.json" ]; then
            gh secret set AZURE_CREDENTIALS < /tmp/azure-credentials.json
            print_success "Set AZURE_CREDENTIALS"
        else
            print_error "Azure credentials file not found"
            return 1
        fi
        
        # Load environment variables
        if [ -f ".env" ]; then
            source .env
            
            echo "$SUPABASE_URL" | gh secret set SUPABASE_URL
            print_success "Set SUPABASE_URL"
            
            echo "$SUPABASE_KEY" | gh secret set SUPABASE_KEY
            print_success "Set SUPABASE_KEY"
            
            echo "$AZURE_OPENAI_API_KEY" | gh secret set AZURE_OPENAI_API_KEY
            print_success "Set AZURE_OPENAI_API_KEY"
            
            echo "$AZURE_OPENAI_ENDPOINT" | gh secret set AZURE_OPENAI_ENDPOINT
            print_success "Set AZURE_OPENAI_ENDPOINT"
            
            echo "$SUBSCRIPTION_ID" | gh secret set AZURE_SUBSCRIPTION_ID
            print_success "Set AZURE_SUBSCRIPTION_ID"
            
        else
            print_error ".env file not found. Please create it first."
            return 1
        fi
        
        print_success "All GitHub secrets set successfully using CLI"
        
    else
        # Manual setup instructions
        print_warning "GitHub CLI not available. Please set up secrets manually:"
        echo
        echo "1. Go to your GitHub repository"
        echo "2. Click Settings → Secrets and variables → Actions"
        echo "3. Add these secrets:"
        echo
        echo "   AZURE_CREDENTIALS:"
        if [ -f "/tmp/azure-credentials.json" ]; then
            cat /tmp/azure-credentials.json
        else
            echo "   (Use the JSON output from the service principal creation)"
        fi
        echo
        
        if [ -f ".env" ]; then
            source .env
            echo "   SUPABASE_URL: $SUPABASE_URL"
            echo "   SUPABASE_KEY: $SUPABASE_KEY"
            echo "   AZURE_OPENAI_API_KEY: $AZURE_OPENAI_API_KEY"
            echo "   AZURE_OPENAI_ENDPOINT: $AZURE_OPENAI_ENDPOINT"
            echo "   AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
        fi
        echo
        
        read -p "Press Enter after you've set up the secrets manually..."
    fi
}

# Function to create Azure resource group
create_resource_group() {
    print_status "Creating Azure resource group..."
    
    RESOURCE_GROUP="scrapemaster-rg"
    LOCATION="East US"
    
    if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        print_warning "Resource group '$RESOURCE_GROUP' already exists"
    else
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
        print_success "Resource group '$RESOURCE_GROUP' created successfully"
    fi
}

# Function to commit and push changes
commit_and_push() {
    print_status "Committing and pushing GitHub Actions workflow..."
    
    # Check if there are changes to commit
    if git diff --quiet && git diff --staged --quiet; then
        print_warning "No changes to commit"
    else
        # Add GitHub Actions workflow and related files
        git add .github/workflows/azure-deploy.yml
        git add azure-container-apps.bicep
        git add azure-app-service.bicep
        git add azure-parameters.json
        git add AZURE_DEPLOYMENT_GUIDE.md
        git add AZURE_QUICK_REFERENCE.md
        git add GITHUB_ACTIONS_SETUP.md
        
        # Commit changes
        git commit -m "Add Azure deployment configuration and GitHub Actions workflow

- Add GitHub Actions workflow for automated Azure deployment
- Add Bicep templates for Azure Container Apps and App Service
- Add comprehensive deployment documentation
- Configure automated CI/CD pipeline"
        
        # Push to GitHub
        git push origin main
        
        print_success "Changes committed and pushed to GitHub"
    fi
}

# Function to trigger first deployment
trigger_deployment() {
    print_status "Triggering first deployment..."
    
    if [ "$GITHUB_CLI_AVAILABLE" = true ]; then
        read -p "Do you want to trigger the first deployment now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Triggering GitHub Actions workflow..."
            gh workflow run azure-deploy.yml
            print_success "Deployment triggered! Check the Actions tab in your GitHub repository."
            
            # Wait a moment and show the workflow run
            sleep 5
            print_status "Recent workflow runs:"
            gh run list --workflow=azure-deploy.yml --limit 3
        fi
    else
        print_status "To trigger deployment manually:"
        echo "1. Go to your GitHub repository"
        echo "2. Click on Actions tab"
        echo "3. Click on 'Deploy to Azure Container Apps' workflow"
        echo "4. Click 'Run workflow'"
        echo "5. Select 'prod' environment and click 'Run workflow'"
    fi
}

# Function to show next steps
show_next_steps() {
    echo
    print_success "🎉 GitHub Actions setup completed successfully!"
    echo
    echo "📋 What was set up:"
    echo "✅ Azure service principal for GitHub Actions"
    echo "✅ GitHub repository secrets"
    echo "✅ Azure resource group"
    echo "✅ GitHub Actions workflow"
    echo "✅ Deployment documentation"
    echo
    echo "🚀 Next steps:"
    echo "1. Monitor your deployment in GitHub Actions"
    echo "2. Check Azure Portal for resource creation"
    echo "3. Access your application URLs after deployment"
    echo "4. Set up custom domain (optional)"
    echo "5. Configure monitoring and alerts"
    echo
    echo "📖 Useful resources:"
    echo "- GitHub Actions: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/actions"
    echo "- Azure Portal: https://portal.azure.com"
    echo "- Documentation: ./GITHUB_ACTIONS_SETUP.md"
    echo
    echo "🐛 Troubleshooting:"
    echo "- Check workflow logs in GitHub Actions"
    echo "- Verify secrets are set correctly"
    echo "- Ensure Azure subscription has sufficient permissions"
}

# Main function
main() {
    echo "🚀 GitHub Actions Setup for Azure Deployment"
    echo "============================================="
    echo
    
    check_prerequisites
    check_azure_login
    create_service_principal
    setup_github_secrets
    create_resource_group
    commit_and_push
    trigger_deployment
    show_next_steps
    
    # Cleanup temporary files
    rm -f /tmp/azure-credentials.json
}

# Run main function
main
