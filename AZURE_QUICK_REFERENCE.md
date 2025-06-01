# 🚀 Azure Deployment Quick Reference

## 📋 Prerequisites Checklist
- [ ] Azure CLI installed (`az --version`)
- [ ] Docker installed (`docker --version`)
- [ ] Azure subscription with appropriate permissions
- [ ] `.env` file configured with your credentials
- [ ] Supabase database set up and accessible
- [ ] Azure OpenAI service deployed and accessible

## ⚡ Quick Start Commands

### 1. Setup (First Time Only)
```bash
# Run the setup script
./setup-azure.sh

# Or manually:
az login
az account set --subscription "your-subscription-id"
```

### 2. Deploy to Azure Container Apps (Recommended)
```bash
# Automated deployment
./deploy-azure.sh

# Manual deployment
az group create --name scrapemaster-rg --location "East US"
az deployment group create \
  --resource-group scrapemaster-rg \
  --template-file azure-container-apps.bicep \
  --parameters @azure-parameters.json
```

### 3. Deploy to Azure App Service (Alternative)
```bash
az deployment group create \
  --resource-group scrapemaster-rg \
  --template-file azure-app-service.bicep \
  --parameters @azure-parameters.json
```

## 🔧 Management Commands

### Check Status
```bash
# Container Apps
az containerapp list --resource-group scrapemaster-rg --output table

# App Service
az webapp list --resource-group scrapemaster-rg --output table
```

### View Logs
```bash
# Container Apps
az containerapp logs show \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --follow

# App Service
az webapp log tail \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg
```

### Scale Applications
```bash
# Container Apps - Auto-scaling
az containerapp update \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --min-replicas 1 \
  --max-replicas 10

# App Service - Manual scaling
az appservice plan update \
  --name scrapemaster-plan-prod \
  --resource-group scrapemaster-rg \
  --sku P1v2
```

### Update Applications
```bash
# Build and push new images
docker build -f Dockerfile.backend -t registry.azurecr.io/scrapemaster/backend:latest .
docker push registry.azurecr.io/scrapemaster/backend:latest

# Update container app
az containerapp update \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --image registry.azurecr.io/scrapemaster/backend:latest
```

## 🔐 Security Commands

### Manage Secrets
```bash
# Create Key Vault
az keyvault create \
  --name scrapemaster-vault \
  --resource-group scrapemaster-rg \
  --location "East US"

# Add secrets
az keyvault secret set \
  --vault-name scrapemaster-vault \
  --name "azure-openai-key" \
  --value "your-api-key"
```

### Configure HTTPS
```bash
# Enable HTTPS only
az containerapp update \
  --name scrapemaster-frontend-prod \
  --resource-group scrapemaster-rg \
  --ingress external \
  --target-port 80 \
  --allow-insecure false
```

## 📊 Monitoring Commands

### View Metrics
```bash
# Application Insights queries
az monitor app-insights query \
  --app scrapemaster-insights-prod \
  --analytics-query "requests | limit 50"

# Container metrics
az monitor metrics list \
  --resource scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --resource-type Microsoft.App/containerApps
```

### Set Up Alerts
```bash
# CPU alert
az monitor metrics alert create \
  --name "High CPU Usage" \
  --resource-group scrapemaster-rg \
  --scopes "/subscriptions/your-sub-id/resourceGroups/scrapemaster-rg" \
  --condition "avg Percentage CPU > 80" \
  --description "Alert when CPU usage is high"
```

## 🐛 Troubleshooting Commands

### Debug Container Issues
```bash
# Check container status
az containerapp revision list \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg

# Get container logs
az containerapp logs show \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --tail 100

# Execute commands in container
az containerapp exec \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --command "/bin/bash"
```

### Test Connectivity
```bash
# Test backend health
curl https://your-backend-url.azurecontainerapps.io/health

# Test Azure OpenAI
curl -H "api-key: $AZURE_OPENAI_API_KEY" \
     "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=2024-12-01-preview"

# Test Supabase
curl -H "apikey: $SUPABASE_KEY" "$SUPABASE_URL/rest/v1/"
```

## 💰 Cost Management

### View Costs
```bash
# Current month costs
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --resource-group scrapemaster-rg

# Set budget
az consumption budget create \
  --budget-name scrapemaster-budget \
  --amount 100 \
  --time-grain Monthly \
  --resource-group scrapemaster-rg
```

### Optimize Resources
```bash
# Scale down for development
az containerapp update \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --min-replicas 0 \
  --max-replicas 1

# Use smaller SKU
az appservice plan update \
  --name scrapemaster-plan-prod \
  --resource-group scrapemaster-rg \
  --sku B1
```

## 🧹 Cleanup Commands

### Stop Applications
```bash
# Scale to zero (Container Apps)
az containerapp update \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --min-replicas 0 \
  --max-replicas 0

# Stop App Service
az webapp stop \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg
```

### Delete Resources
```bash
# Delete specific resource
az containerapp delete \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --yes

# Delete entire resource group (CAUTION!)
az group delete \
  --name scrapemaster-rg \
  --yes \
  --no-wait
```

## 🔄 CI/CD Commands

### GitHub Actions
```bash
# Set up GitHub secrets
gh secret set AZURE_CREDENTIALS --body "$(az ad sp create-for-rbac --sdk-auth)"
gh secret set SUPABASE_URL --body "$SUPABASE_URL"
gh secret set AZURE_OPENAI_API_KEY --body "$AZURE_OPENAI_API_KEY"

# Trigger deployment
gh workflow run azure-deploy.yml
```

### Manual Deployment
```bash
# Build images locally
docker build -f Dockerfile.backend -t scrapemaster-backend .
docker build -f Dockerfile.frontend -t scrapemaster-frontend .

# Tag and push to registry
docker tag scrapemaster-backend registry.azurecr.io/scrapemaster/backend:latest
docker push registry.azurecr.io/scrapemaster/backend:latest
```

## 📞 Useful URLs

### Azure Portal Links
- **Resource Group**: `https://portal.azure.com/#@/resource/subscriptions/{subscription-id}/resourceGroups/scrapemaster-rg`
- **Container Apps**: `https://portal.azure.com/#@/resource/subscriptions/{subscription-id}/resourceGroups/scrapemaster-rg/providers/Microsoft.App/containerApps`
- **Application Insights**: `https://portal.azure.com/#@/resource/subscriptions/{subscription-id}/resourceGroups/scrapemaster-rg/providers/Microsoft.Insights/components`

### Application URLs (After Deployment)
- **Frontend**: `https://scrapemaster-frontend-prod.{region}.azurecontainerapps.io`
- **Backend API**: `https://scrapemaster-backend-prod.{region}.azurecontainerapps.io`
- **API Documentation**: `https://scrapemaster-backend-prod.{region}.azurecontainerapps.io/docs`

## 🆘 Emergency Commands

### Rollback Deployment
```bash
# List revisions
az containerapp revision list \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg

# Activate previous revision
az containerapp revision activate \
  --name scrapemaster-backend-prod \
  --resource-group scrapemaster-rg \
  --revision scrapemaster-backend-prod--previous-revision-name
```

### Quick Health Check
```bash
# Check all resources
az resource list --resource-group scrapemaster-rg --output table

# Test endpoints
curl -f https://your-backend-url/health && echo "✅ Backend OK" || echo "❌ Backend Failed"
curl -f https://your-frontend-url && echo "✅ Frontend OK" || echo "❌ Frontend Failed"
```
