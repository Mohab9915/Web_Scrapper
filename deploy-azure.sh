#!/bin/bash

# Azure Deployment Script for Interactive Agentic Web Scraper & RAG System
# This script deploys the application to Azure Container Apps

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP_NAME="scrapemaster-rg"
LOCATION="East US"
SUBSCRIPTION_ID=""
CONTAINER_REGISTRY_NAME="scrapemasterregistry$(date +%s)"
DEPLOYMENT_NAME="scrapemaster-deployment-$(date +%Y%m%d-%H%M%S)"

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if logged into Azure
    if ! az account show &> /dev/null; then
        print_error "Not logged into Azure. Please run 'az login' first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to set subscription
set_subscription() {
    if [ -z "$SUBSCRIPTION_ID" ]; then
        print_status "Available subscriptions:"
        az account list --output table
        echo
        read -p "Enter your subscription ID: " SUBSCRIPTION_ID
    fi
    
    print_status "Setting subscription to $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
    print_success "Subscription set successfully"
}

# Function to create resource group
create_resource_group() {
    print_status "Creating resource group: $RESOURCE_GROUP_NAME"
    
    if az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
        print_warning "Resource group already exists"
    else
        az group create \
            --name "$RESOURCE_GROUP_NAME" \
            --location "$LOCATION"
        print_success "Resource group created successfully"
    fi
}

# Function to build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Get container registry login server
    REGISTRY_LOGIN_SERVER=$(az acr show --name "$CONTAINER_REGISTRY_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query "loginServer" --output tsv)
    
    # Login to container registry
    az acr login --name "$CONTAINER_REGISTRY_NAME"
    
    # Build and push backend image
    print_status "Building backend image..."
    docker build -f Dockerfile.backend -t "$REGISTRY_LOGIN_SERVER/scrapemaster/backend:latest" .
    docker push "$REGISTRY_LOGIN_SERVER/scrapemaster/backend:latest"
    
    # Build and push frontend image
    print_status "Building frontend image..."
    docker build -f Dockerfile.frontend -t "$REGISTRY_LOGIN_SERVER/scrapemaster/frontend:latest" .
    docker push "$REGISTRY_LOGIN_SERVER/scrapemaster/frontend:latest"
    
    print_success "Docker images built and pushed successfully"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure using Bicep template..."
    
    # Read environment variables
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please create it with your configuration."
        exit 1
    fi
    
    source .env
    
    # Deploy using Bicep template
    az deployment group create \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --template-file "azure-container-apps.bicep" \
        --name "$DEPLOYMENT_NAME" \
        --parameters \
            namePrefix="scrapemaster" \
            environment="prod" \
            supabaseUrl="$SUPABASE_URL" \
            supabaseKey="$SUPABASE_KEY" \
            azureOpenAIApiKey="$AZURE_OPENAI_API_KEY" \
            azureOpenAIEndpoint="$AZURE_OPENAI_ENDPOINT" \
            containerRegistryName="$CONTAINER_REGISTRY_NAME"
    
    print_success "Infrastructure deployed successfully"
}

# Function to get deployment outputs
get_deployment_outputs() {
    print_status "Getting deployment outputs..."
    
    BACKEND_URL=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$DEPLOYMENT_NAME" \
        --query "properties.outputs.backendUrl.value" \
        --output tsv)
    
    FRONTEND_URL=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$DEPLOYMENT_NAME" \
        --query "properties.outputs.frontendUrl.value" \
        --output tsv)
    
    print_success "Deployment completed successfully!"
    echo
    echo "🌐 Application URLs:"
    echo "   Frontend: $FRONTEND_URL"
    echo "   Backend:  $BACKEND_URL"
    echo "   API Docs: $BACKEND_URL/docs"
    echo
    echo "📊 Monitoring:"
    echo "   Azure Portal: https://portal.azure.com"
    echo "   Resource Group: $RESOURCE_GROUP_NAME"
}

# Function to setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring and alerts..."
    
    # Create action group for alerts
    az monitor action-group create \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "scrapemaster-alerts" \
        --short-name "sm-alerts"
    
    # Create metric alerts for high CPU usage
    az monitor metrics alert create \
        --name "High CPU Usage" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME" \
        --condition "avg Percentage CPU > 80" \
        --description "Alert when CPU usage is high" \
        --action "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/microsoft.insights/actionGroups/scrapemaster-alerts"
    
    print_success "Monitoring setup completed"
}

# Main deployment function
main() {
    echo "🚀 Starting Azure deployment for Interactive Agentic Web Scraper & RAG System"
    echo "=================================================================="
    
    check_prerequisites
    set_subscription
    create_resource_group
    deploy_infrastructure
    build_and_push_images
    get_deployment_outputs
    setup_monitoring
    
    echo
    print_success "🎉 Deployment completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Test your application at the provided URLs"
    echo "2. Configure custom domain (optional)"
    echo "3. Set up CI/CD pipeline for automated deployments"
    echo "4. Monitor application performance in Azure Portal"
}

# Handle script arguments
case "${1:-}" in
    "clean")
        print_warning "Cleaning up resources..."
        az group delete --name "$RESOURCE_GROUP_NAME" --yes --no-wait
        print_success "Cleanup initiated"
        ;;
    "logs")
        print_status "Fetching application logs..."
        az containerapp logs show \
            --name "scrapemaster-backend-prod" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --follow
        ;;
    "status")
        print_status "Checking deployment status..."
        az containerapp show \
            --name "scrapemaster-backend-prod" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --output table
        ;;
    *)
        main
        ;;
esac
