#!/bin/bash

# Deployment Monitoring Script
# Monitors GitHub Actions deployment progress

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

# Function to get latest run ID
get_latest_run_id() {
    gh run list --workflow=azure-deploy.yml --limit 1 --json databaseId --jq '.[0].databaseId'
}

# Function to get run status
get_run_status() {
    local run_id=$1
    gh run view $run_id --json status --jq '.status'
}

# Function to get run conclusion
get_run_conclusion() {
    local run_id=$1
    gh run view $run_id --json conclusion --jq '.conclusion'
}

# Function to display progress
display_progress() {
    local run_id=$1
    
    echo "======================================"
    echo "🚀 AZURE DEPLOYMENT MONITOR"
    echo "======================================"
    echo "Run ID: $run_id"
    echo "Time: $(date)"
    echo "======================================"
    
    # Get job details
    gh run view --job=$(gh run view $run_id --json jobs --jq '.jobs[0].id') 2>/dev/null || {
        echo "Getting job details..."
        return
    }
    
    echo ""
}

# Function to check Azure resources
check_azure_resources() {
    print_status "Checking Azure resources..."
    
    # Check resource group
    if az group show --name scrapemaster-rg &> /dev/null; then
        print_success "Resource group 'scrapemaster-rg' exists"
    else
        print_error "Resource group 'scrapemaster-rg' not found"
    fi
    
    # Check container registry
    if az acr show --name scrapemasterregistry --resource-group scrapemaster-rg &> /dev/null; then
        print_success "Container registry exists"
        
        # List repositories
        REPOS=$(az acr repository list --name scrapemasterregistry --output tsv 2>/dev/null || echo "")
        if [ ! -z "$REPOS" ]; then
            print_success "Container images: $REPOS"
        fi
    else
        print_warning "Container registry not found (will be created during deployment)"
    fi
    
    # Check container apps
    BACKEND_APP=$(az containerapp show --name scrapemaster-backend-prod --resource-group scrapemaster-rg --query "name" --output tsv 2>/dev/null || echo "")
    FRONTEND_APP=$(az containerapp show --name scrapemaster-frontend-prod --resource-group scrapemaster-rg --query "name" --output tsv 2>/dev/null || echo "")
    
    if [ ! -z "$BACKEND_APP" ]; then
        print_success "Backend container app exists"
    else
        print_warning "Backend container app not found (will be created)"
    fi
    
    if [ ! -z "$FRONTEND_APP" ]; then
        print_success "Frontend container app exists"
    else
        print_warning "Frontend container app not found (will be created)"
    fi
    
    echo ""
}

# Main monitoring function
monitor_deployment() {
    local run_id=$(get_latest_run_id)
    local status=""
    local conclusion=""
    local iteration=0
    
    print_status "Starting deployment monitoring for run ID: $run_id"
    print_status "Press Ctrl+C to stop monitoring"
    echo ""
    
    while true; do
        clear
        iteration=$((iteration + 1))
        
        # Display progress
        display_progress $run_id
        
        # Get current status
        status=$(get_run_status $run_id)
        conclusion=$(get_run_conclusion $run_id)
        
        echo "Status: $status"
        if [ "$conclusion" != "null" ]; then
            echo "Conclusion: $conclusion"
        fi
        echo ""
        
        # Check if deployment is complete
        if [ "$status" = "completed" ]; then
            if [ "$conclusion" = "success" ]; then
                print_success "🎉 Deployment completed successfully!"
                
                # Get deployment URLs
                echo ""
                print_status "Getting application URLs..."
                
                BACKEND_URL=$(az containerapp show \
                    --name scrapemaster-backend-prod \
                    --resource-group scrapemaster-rg \
                    --query "properties.configuration.ingress.fqdn" \
                    --output tsv 2>/dev/null || echo "Not available yet")
                
                FRONTEND_URL=$(az containerapp show \
                    --name scrapemaster-frontend-prod \
                    --resource-group scrapemaster-rg \
                    --query "properties.configuration.ingress.fqdn" \
                    --output tsv 2>/dev/null || echo "Not available yet")
                
                echo ""
                echo "🌐 APPLICATION URLS:"
                echo "   Frontend:  https://$FRONTEND_URL"
                echo "   Backend:   https://$BACKEND_URL"
                echo "   API Docs:  https://$BACKEND_URL/docs"
                echo ""
                
                # Test endpoints
                print_status "Testing endpoints..."
                if curl -f -s "https://$BACKEND_URL/health" > /dev/null 2>&1; then
                    print_success "Backend health check passed"
                else
                    print_warning "Backend health check failed (may still be starting)"
                fi
                
                break
            else
                print_error "❌ Deployment failed with conclusion: $conclusion"
                print_status "Check the logs for details:"
                echo "gh run view $run_id --log"
                break
            fi
        fi
        
        # Show Azure resources status
        check_azure_resources
        
        # Show iteration info
        echo "Monitoring iteration: $iteration"
        echo "Next check in 30 seconds..."
        echo ""
        echo "💡 To view detailed logs: gh run view $run_id --log"
        echo "💡 To view in browser: https://github.com/Mohab9915/Web_Scrapper/actions/runs/$run_id"
        
        # Wait 30 seconds
        sleep 30
    done
}

# Handle Ctrl+C
trap 'echo -e "\n${YELLOW}Monitoring stopped by user${NC}"; exit 0' INT

# Start monitoring
monitor_deployment
