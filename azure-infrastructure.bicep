// Azure Infrastructure Deployment Template (Phase 1)
// Creates registry, environment, and supporting resources WITHOUT container apps

@description('Location for all resources')
param location string = resourceGroup().location

@description('Name prefix for all resources')
param namePrefix string = 'scrapemaster'

@description('Environment name (dev, staging, prod)')
param environment string = 'prod'

@description('Container Registry Name')
param containerRegistryName string = '${namePrefix}${uniqueString(resourceGroup().id)}'

// Variables
var containerAppEnvironmentName = '${namePrefix}-env-${environment}'
var logAnalyticsWorkspaceName = '${namePrefix}-logs-${environment}'

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Container Apps Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// Outputs
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerRegistryName string = containerRegistry.name
output containerAppEnvironmentId string = containerAppEnvironment.id
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id
output resourceGroupName string = resourceGroup().name
