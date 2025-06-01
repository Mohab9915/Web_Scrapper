// Azure App Service Deployment Template (Alternative to Container Apps)
// Interactive Agentic Web Scraper & RAG System

@description('Location for all resources')
param location string = resourceGroup().location

@description('Name prefix for all resources')
param namePrefix string = 'scrapemaster'

@description('Environment name (dev, staging, prod)')
param environment string = 'prod'

@description('Supabase URL')
@secure()
param supabaseUrl string

@description('Supabase API Key')
@secure()
param supabaseKey string

@description('Azure OpenAI API Key')
@secure()
param azureOpenAIApiKey string

@description('Azure OpenAI Endpoint')
param azureOpenAIEndpoint string = 'https://practicehub3994533910.cognitiveservices.azure.com/'

@description('App Service Plan SKU')
@allowed(['B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1v2', 'P2v2', 'P3v2'])
param appServicePlanSku string = 'B2'

// Variables
var appServicePlanName = '${namePrefix}-plan-${environment}'
var backendAppName = '${namePrefix}-backend-${environment}-${uniqueString(resourceGroup().id)}'
var frontendAppName = '${namePrefix}-frontend-${environment}-${uniqueString(resourceGroup().id)}'
var applicationInsightsName = '${namePrefix}-insights-${environment}'
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

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: appServicePlanSku
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Backend App Service
resource backendAppService 'Microsoft.Web/sites@2022-09-01' = {
  name: backendAppName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'SUPABASE_URL'
          value: supabaseUrl
        }
        {
          name: 'SUPABASE_KEY'
          value: supabaseKey
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: azureOpenAIApiKey
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: azureOpenAIEndpoint
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: '2024-12-01-preview'
        }
        {
          name: 'AZURE_CHAT_MODEL'
          value: 'gpt-4o'
        }
        {
          name: 'AZURE_EMBEDDING_MODEL'
          value: 'text-embedding-ada-002'
        }
        {
          name: 'BROWSER_CONTROL_TYPE'
          value: 'simulated'
        }
        {
          name: 'EMBEDDING_BATCH_SIZE'
          value: '20'
        }
        {
          name: 'WEB_CACHE_EXPIRY_HOURS'
          value: '24'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.properties.ConnectionString
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
      ]
      healthCheckPath: '/health'
    }
    httpsOnly: true
  }
}

// Frontend App Service (Static Web App alternative)
resource frontendAppService 'Microsoft.Web/sites@2022-09-01' = {
  name: frontendAppName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'NODE|18-lts'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'REACT_APP_API_URL'
          value: 'https://${backendAppService.properties.defaultHostName}'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.properties.ConnectionString
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'PRE_BUILD_COMMAND'
          value: 'cd new-front && npm install'
        }
        {
          name: 'BUILD_COMMAND'
          value: 'cd new-front && npm run build:prod'
        }
        {
          name: 'POST_BUILD_COMMAND'
          value: 'cp -r new-front/build/* /home/site/wwwroot/'
        }
      ]
    }
    httpsOnly: true
  }
}

// Auto-scaling settings for App Service Plan
resource autoScaleSettings 'Microsoft.Insights/autoscalesettings@2022-10-01' = {
  name: '${appServicePlanName}-autoscale'
  location: location
  properties: {
    profiles: [
      {
        name: 'Default'
        capacity: {
          minimum: '1'
          maximum: '5'
          default: '2'
        }
        rules: [
          {
            metricTrigger: {
              metricName: 'CpuPercentage'
              metricResourceUri: appServicePlan.id
              timeGrain: 'PT1M'
              statistic: 'Average'
              timeWindow: 'PT5M'
              timeAggregation: 'Average'
              operator: 'GreaterThan'
              threshold: 70
            }
            scaleAction: {
              direction: 'Increase'
              type: 'ChangeCount'
              value: '1'
              cooldown: 'PT5M'
            }
          }
          {
            metricTrigger: {
              metricName: 'CpuPercentage'
              metricResourceUri: appServicePlan.id
              timeGrain: 'PT1M'
              statistic: 'Average'
              timeWindow: 'PT5M'
              timeAggregation: 'Average'
              operator: 'LessThan'
              threshold: 30
            }
            scaleAction: {
              direction: 'Decrease'
              type: 'ChangeCount'
              value: '1'
              cooldown: 'PT5M'
            }
          }
        ]
      }
    ]
    enabled: true
    targetResourceUri: appServicePlan.id
  }
}

// Alert rules
resource cpuAlertRule 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${namePrefix}-high-cpu-alert'
  location: 'global'
  properties: {
    description: 'Alert when CPU usage is high'
    severity: 2
    enabled: true
    scopes: [
      appServicePlan.id
    ]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighCPU'
          metricName: 'CpuPercentage'
          operator: 'GreaterThan'
          threshold: 80
          timeAggregation: 'Average'
        }
      ]
    }
  }
}

// Outputs
output backendUrl string = 'https://${backendAppService.properties.defaultHostName}'
output frontendUrl string = 'https://${frontendAppService.properties.defaultHostName}'
output applicationInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey
output applicationInsightsConnectionString string = applicationInsights.properties.ConnectionString
output resourceGroupName string = resourceGroup().name
output appServicePlanName string = appServicePlan.name
