@description('Name prefix for all resources')
param namePrefix string = 'scrapemaster'

@description('Environment name (dev, staging, prod)')
param environment string = 'prod'

@description('Container registry login server')
param containerRegistryLoginServer string

@description('Container registry name')
param containerRegistryName string

@description('Container app environment resource ID')
param containerAppEnvironmentId string

@description('Backend image tag')
param backendImageTag string = 'latest'

@description('Frontend image tag')
param frontendImageTag string = 'latest'

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
@secure()
param azureOpenAIEndpoint string

var backendAppName = '${namePrefix}-backend-${environment}'
var frontendAppName = '${namePrefix}-frontend-${environment}'

// Backend Container App
resource backendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: backendAppName
  location: resourceGroup().location
  properties: {
    environmentId: containerAppEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      registries: [
        {
          server: containerRegistryLoginServer
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: '${containerRegistryLoginServer}/scrapemaster/backend:${backendImageTag}'
          env: [
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
              name: 'AZURE_OPENAI_MODEL'
              value: 'gpt-4o'
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING_MODEL'
              value: 'text-embedding-ada-002'
            }
            {
              name: 'PORT'
              value: '8000'
            }
          ]
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Frontend Container App
resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: frontendAppName
  location: resourceGroup().location
  properties: {
    environmentId: containerAppEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        allowInsecure: false
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      registries: [
        {
          server: containerRegistryLoginServer
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: '${containerRegistryLoginServer}/scrapemaster/frontend:${frontendImageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Grant ACR pull permissions to backend app
resource backendAcrAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(backendApp.id, containerRegistryName, 'AcrPull')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: backendApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant ACR pull permissions to frontend app
resource frontendAcrAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(frontendApp.id, containerRegistryName, 'AcrPull')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: frontendApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output backendUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output frontendUrl string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
output backendAppName string = backendApp.name
output frontendAppName string = frontendApp.name
