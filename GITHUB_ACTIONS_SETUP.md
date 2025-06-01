# 🚀 GitHub Actions Setup Guide for Azure Deployment

This guide will help you set up automated deployment using GitHub Actions for your Interactive Agentic Web Scraper & RAG System.

## 📋 Prerequisites

- [x] GitHub repository (you already have this)
- [x] Azure subscription
- [x] Azure CLI installed locally
- [ ] GitHub CLI installed (optional but recommended)

## Step 1: Install GitHub CLI (Optional but Recommended)

### Windows
```bash
winget install GitHub.cli
```

### macOS
```bash
brew install gh
```

### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

## Step 2: Login to GitHub CLI

```bash
gh auth login
```

Follow the prompts to authenticate with your GitHub account.

## Step 3: Create Azure Service Principal for GitHub Actions

This creates a service principal that GitHub Actions will use to deploy to Azure:

```bash
# Login to Azure
az login

# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
echo "Subscription ID: $SUBSCRIPTION_ID"

# Create service principal with contributor role
az ad sp create-for-rbac \
  --name "scrapemaster-github-actions" \
  --role contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --sdk-auth
```

**Important**: Copy the entire JSON output from this command. You'll need it in the next step.

The output should look like this:
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

## Step 4: Set Up GitHub Secrets

### Option A: Using GitHub CLI (Recommended)

```bash
# Set Azure credentials (paste the JSON from Step 3)
gh secret set AZURE_CREDENTIALS --body '{
  "clientId": "your-client-id",
  "clientSecret": "your-client-secret",
  "subscriptionId": "your-subscription-id",
  "tenantId": "your-tenant-id",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}'

# Set your application secrets
gh secret set SUPABASE_URL --body "https://slkzwhpfeauezoojlvou.supabase.co"
gh secret set SUPABASE_KEY --body "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNsa3p3aHBmZWF1ZXpvb2psdm91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMTQ0NTEsImV4cCI6MjA2Mjc5MDQ1MX0.uLsJt6GijTe_2MJ0Ckoux9wQrp-Kr6mR43wXPrCYYDQ"
gh secret set AZURE_OPENAI_API_KEY --body "BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC"
gh secret set AZURE_OPENAI_ENDPOINT --body "https://practicehub3994533910.cognitiveservices.azure.com/"
gh secret set AZURE_SUBSCRIPTION_ID --body "$SUBSCRIPTION_ID"
```

### Option B: Using GitHub Web Interface

1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Secrets and variables** → **Actions**
4. Click **New repository secret** for each secret:

| Secret Name | Value |
|-------------|-------|
| `AZURE_CREDENTIALS` | The entire JSON output from Step 3 |
| `SUPABASE_URL` | `https://slkzwhpfeauezoojlvou.supabase.co` |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNsa3p3aHBmZWF1ZXpvb2psdm91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMTQ0NTEsImV4cCI6MjA2Mjc5MDQ1MX0.uLsJt6GijTe_2MJ0Ckoux9wQrp-Kr6mR43wXPrCYYDQ` |
| `AZURE_OPENAI_API_KEY` | `BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC` |
| `AZURE_OPENAI_ENDPOINT` | `https://practicehub3994533910.cognitiveservices.azure.com/` |
| `AZURE_SUBSCRIPTION_ID` | Your subscription ID from Step 3 |

## Step 5: Commit and Push Your Code

```bash
# Add all the new deployment files
git add .github/workflows/azure-deploy.yml
git add azure-container-apps.bicep
git add azure-app-service.bicep
git add azure-parameters.json
git add AZURE_DEPLOYMENT_GUIDE.md
git add AZURE_QUICK_REFERENCE.md

# Commit the changes
git commit -m "Add Azure deployment configuration and GitHub Actions workflow"

# Push to GitHub
git push origin main
```

## Step 6: Create Azure Resource Group (One-time Setup)

Before the first deployment, create the resource group:

```bash
az group create --name scrapemaster-rg --location "East US"
```

## Step 7: Trigger Your First Deployment

### Option A: Automatic Deployment (Push to main)

The workflow will automatically run when you push to the `main` branch:

```bash
# Make any change and push
git add .
git commit -m "Trigger first Azure deployment"
git push origin main
```

### Option B: Manual Deployment (Workflow Dispatch)

1. Go to your GitHub repository
2. Click on **Actions** tab
3. Click on **Deploy to Azure Container Apps** workflow
4. Click **Run workflow**
5. Select environment (prod) and click **Run workflow**

### Option C: Using GitHub CLI

```bash
gh workflow run azure-deploy.yml
```

## Step 8: Monitor Your Deployment

### In GitHub:
1. Go to **Actions** tab in your repository
2. Click on the running workflow
3. Watch the deployment progress in real-time

### In Azure Portal:
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your resource group: `scrapemaster-rg`
3. Monitor the resources being created

## Step 9: Access Your Deployed Application

After successful deployment, you'll find the URLs in:

1. **GitHub Actions Summary**: Check the deployment summary in the workflow run
2. **Azure Portal**: Go to Container Apps and find the application URLs
3. **Command Line**:
   ```bash
   # Get backend URL
   az containerapp show \
     --name scrapemaster-backend-prod \
     --resource-group scrapemaster-rg \
     --query "properties.configuration.ingress.fqdn" \
     --output tsv

   # Get frontend URL
   az containerapp show \
     --name scrapemaster-frontend-prod \
     --resource-group scrapemaster-rg \
     --query "properties.configuration.ingress.fqdn" \
     --output tsv
   ```

## 🔧 Workflow Features

Your GitHub Actions workflow includes:

- ✅ **Automatic builds** on push to main
- ✅ **Manual deployment** with environment selection
- ✅ **Docker image building** and pushing to Azure Container Registry
- ✅ **Infrastructure deployment** using Bicep templates
- ✅ **Health checks** after deployment
- ✅ **Deployment summary** with URLs and monitoring links
- ✅ **Automatic cleanup** of old container images

## 🐛 Troubleshooting

### Common Issues:

1. **Authentication Failed**
   ```bash
   # Verify your service principal
   az ad sp show --id "your-client-id"
   ```

2. **Resource Group Not Found**
   ```bash
   # Create the resource group
   az group create --name scrapemaster-rg --location "East US"
   ```

3. **Container Registry Access Denied**
   ```bash
   # Check if the registry exists
   az acr list --resource-group scrapemaster-rg
   ```

4. **Workflow Fails**
   - Check the GitHub Actions logs
   - Verify all secrets are set correctly
   - Ensure Azure subscription has sufficient permissions

### Debug Commands:

```bash
# Check workflow status
gh run list --workflow=azure-deploy.yml

# View workflow logs
gh run view --log

# Check Azure resources
az resource list --resource-group scrapemaster-rg --output table
```

## 🔄 Making Updates

After initial setup, any push to the `main` branch will automatically:

1. Build new Docker images
2. Push them to Azure Container Registry
3. Update your Container Apps with the new images
4. Run health checks
5. Provide deployment summary

## 🎯 Next Steps

1. **Custom Domain**: Set up a custom domain for your application
2. **Environment Variables**: Add environment-specific configurations
3. **Monitoring**: Set up alerts and monitoring dashboards
4. **Scaling**: Configure auto-scaling rules based on your needs
5. **Security**: Implement additional security measures

## 📞 Getting Help

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Azure Container Apps**: https://docs.microsoft.com/en-us/azure/container-apps/
- **Troubleshooting**: Check the workflow logs and Azure Portal for detailed error messages
