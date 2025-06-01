# 🚀 Azure Deployment Guide - Interactive Agentic Web Scraper & RAG System

This comprehensive guide covers deploying your Interactive Agentic Web Scraper & RAG System to Microsoft Azure using multiple deployment options.

## 📋 Prerequisites

### Required Tools
- **Azure CLI** (latest version)
- **Docker** (for container deployments)
- **Git** (for source control)
- **Node.js 18+** (for frontend builds)
- **Python 3.12** (for backend development)

### Azure Services Required
- **Azure Subscription** (with appropriate permissions)
- **Azure OpenAI Service** (already configured)
- **Supabase Database** (already configured)

### Install Azure CLI
```bash
# Windows (using winget)
winget install Microsoft.AzureCLI

# macOS (using Homebrew)
brew install azure-cli

# Linux (Ubuntu/Debian)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

## 🎯 Deployment Options

### Option 1: Azure Container Apps (Recommended)
**Best for**: Production workloads, auto-scaling, serverless containers
**Pros**: Serverless, auto-scaling, cost-effective, managed infrastructure
**Cons**: Newer service, fewer customization options

### Option 2: Azure App Service
**Best for**: Traditional web applications, easier deployment
**Pros**: Mature service, easy deployment, built-in CI/CD
**Cons**: Less flexible than containers, higher cost for scaling

### Option 3: Azure Kubernetes Service (AKS)
**Best for**: Complex applications, full container orchestration
**Pros**: Full Kubernetes features, maximum flexibility
**Cons**: More complex setup and management

## 🚀 Quick Start - Azure Container Apps Deployment

### Step 1: Login to Azure
```bash
# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "your-subscription-id"
```

### Step 2: Prepare Environment
```bash
# Clone your repository (if not already done)
git clone <your-repo-url>
cd studio-master

# Make deployment script executable
chmod +x deploy-azure.sh

# Verify your .env file has the correct Azure credentials
cat .env
```

### Step 3: Deploy to Azure Container Apps
```bash
# Run the automated deployment script
./deploy-azure.sh

# Or deploy manually step by step:
# 1. Create resource group
az group create --name scrapemaster-rg --location "East US"

# 2. Deploy infrastructure
az deployment group create \
  --resource-group scrapemaster-rg \
  --template-file azure-container-apps.bicep \
  --parameters @azure-parameters.json
```

### Step 4: Build and Push Container Images
```bash
# Get container registry details
REGISTRY_NAME=$(az deployment group show \
  --resource-group scrapemaster-rg \
  --name scrapemaster-deployment \
  --query "properties.outputs.containerRegistryName.value" -o tsv)

# Login to container registry
az acr login --name $REGISTRY_NAME

# Build and push images
docker build -f Dockerfile.backend -t $REGISTRY_NAME.azurecr.io/scrapemaster/backend:latest .
docker push $REGISTRY_NAME.azurecr.io/scrapemaster/backend:latest

docker build -f Dockerfile.frontend -t $REGISTRY_NAME.azurecr.io/scrapemaster/frontend:latest .
docker push $REGISTRY_NAME.azurecr.io/scrapemaster/frontend:latest
```

## 🔧 Alternative: Azure App Service Deployment

### Step 1: Deploy Infrastructure
```bash
# Deploy App Service infrastructure
az deployment group create \
  --resource-group scrapemaster-rg \
  --template-file azure-app-service.bicep \
  --parameters \
    supabaseUrl="$SUPABASE_URL" \
    supabaseKey="$SUPABASE_KEY" \
    azureOpenAIApiKey="$AZURE_OPENAI_API_KEY"
```

### Step 2: Deploy Backend (Python App)
```bash
# Deploy backend using ZIP deployment
cd backend
zip -r ../backend-deploy.zip . -x "venv/*" "__pycache__/*" "*.pyc"
cd ..

az webapp deployment source config-zip \
  --resource-group scrapemaster-rg \
  --name scrapemaster-backend-prod \
  --src backend-deploy.zip
```

### Step 3: Deploy Frontend (React App)
```bash
# Build and deploy frontend
cd new-front
npm install
npm run build:azure

# Create deployment package
zip -r ../frontend-deploy.zip build/*
cd ..

az webapp deployment source config-zip \
  --resource-group scrapemaster-rg \
  --name scrapemaster-frontend-prod \
  --src frontend-deploy.zip
```

## 🔐 Security Configuration

### Environment Variables Security
```bash
# Store secrets in Azure Key Vault (recommended)
az keyvault create \
  --name scrapemaster-vault \
  --resource-group scrapemaster-rg \
  --location "East US"

# Add secrets to Key Vault
az keyvault secret set \
  --vault-name scrapemaster-vault \
  --name "supabase-key" \
  --value "$SUPABASE_KEY"

az keyvault secret set \
  --vault-name scrapemaster-vault \
  --name "azure-openai-key" \
  --value "$AZURE_OPENAI_API_KEY"
```

### Network Security
```bash
# Configure custom domain and SSL (optional)
az webapp config hostname add \
  --webapp-name scrapemaster-frontend-prod \
  --resource-group scrapemaster-rg \
  --hostname yourdomain.com

# Enable HTTPS only
az webapp update \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --https-only true
```

## 📊 Monitoring and Logging

### Application Insights Setup
```bash
# Application Insights is automatically configured in the Bicep templates
# View logs in Azure Portal or using CLI:

# View application logs
az monitor app-insights query \
  --app scrapemaster-insights-prod \
  --analytics-query "requests | limit 50"

# View performance metrics
az monitor app-insights metrics show \
  --app scrapemaster-insights-prod \
  --metric requests/count
```

### Health Monitoring
```bash
# Check application health
curl https://your-backend-url.azurecontainerapps.io/health
curl https://your-frontend-url.azurecontainerapps.io/

# View container logs
az containerapp logs show \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --follow
```

## 🔄 CI/CD Pipeline Setup

### GitHub Actions (Recommended)
The repository includes `.github/workflows/deploy.yml` for automated deployments.

### Azure DevOps Alternative
```yaml
# azure-pipelines.yml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

stages:
- stage: Build
  jobs:
  - job: BuildAndTest
    steps:
    - task: Docker@2
      inputs:
        command: 'buildAndPush'
        repository: 'scrapemaster/backend'
        dockerfile: 'Dockerfile.backend'
        containerRegistry: 'scrapemasterregistry'

- stage: Deploy
  jobs:
  - job: DeployToAzure
    steps:
    - task: AzureContainerApps@1
      inputs:
        azureSubscription: 'your-service-connection'
        resourceGroup: 'scrapemaster-rg'
        containerAppName: 'scrapemaster-backend-prod'
```

## 🎯 Performance Optimization

### Auto-scaling Configuration
```bash
# Configure auto-scaling rules
az containerapp revision set-mode \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --mode Single

# Set scaling rules
az containerapp update \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --min-replicas 1 \
  --max-replicas 10
```

### CDN Setup (Optional)
```bash
# Create Azure CDN for frontend assets
az cdn profile create \
  --name scrapemaster-cdn \
  --resource-group scrapemaster-rg \
  --sku Standard_Microsoft

az cdn endpoint create \
  --name scrapemaster-frontend \
  --profile-name scrapemaster-cdn \
  --resource-group scrapemaster-rg \
  --origin your-frontend-url.azurecontainerapps.io
```

## 🐛 Troubleshooting

### Common Issues

1. **Container startup failures**
   ```bash
   # Check container logs
   az containerapp logs show --name scrapemaster-backend-prod --resource-group scrapemaster-rg
   ```

2. **Database connection issues**
   ```bash
   # Test Supabase connectivity
   curl -H "apikey: $SUPABASE_KEY" "$SUPABASE_URL/rest/v1/projects"
   ```

3. **Azure OpenAI API issues**
   ```bash
   # Test Azure OpenAI connectivity
   curl -H "api-key: $AZURE_OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        "$AZURE_OPENAI_ENDPOINT/openai/deployments/gpt-4o/chat/completions?api-version=2024-12-01-preview"
   ```

### Debug Commands
```bash
# Check resource status
az resource list --resource-group scrapemaster-rg --output table

# View deployment history
az deployment group list --resource-group scrapemaster-rg --output table

# Check container app status
az containerapp show --name scrapemaster-backend-prod --resource-group scrapemaster-rg
```

## 💰 Cost Optimization

### Resource Sizing Recommendations
- **Development**: B1 App Service Plan or 0.25 CPU Container Apps
- **Production**: B2/S1 App Service Plan or 0.5-1.0 CPU Container Apps
- **High Traffic**: P1v2+ App Service Plan or auto-scaling Container Apps

### Cost Monitoring
```bash
# Set up budget alerts
az consumption budget create \
  --budget-name scrapemaster-budget \
  --amount 100 \
  --time-grain Monthly \
  --time-period start-date=2024-01-01 \
  --resource-group scrapemaster-rg
```

## 📞 Support and Next Steps

### Post-Deployment Checklist
- [ ] Verify all endpoints are accessible
- [ ] Test web scraping functionality
- [ ] Test RAG system with sample queries
- [ ] Configure monitoring alerts
- [ ] Set up backup strategy
- [ ] Document custom domain setup (if needed)
- [ ] Configure CI/CD pipeline

### Useful Resources
- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure OpenAI Service Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)

### Getting Help
- Azure Support Portal
- GitHub Issues (for application-specific problems)
- Azure Community Forums
