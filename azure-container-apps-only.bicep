// Azure Container Apps Deployment Template (Phase 2)
// Deploys container apps after images are built and pushed

@description('Location for all resources')
param location string = resourceGroup().location

@description('Name prefix for all resources')
param namePrefix string = 'scrapemaster'

@description('Environment name (dev, staging, prod)')
param environment string = 'prod'

@description('Container Registry Login Server')
param containerRegistryLoginServer string

@description('Container Registry Name')
param containerRegistryName string

@description('Container App Environment ID')
param containerAppEnvironmentId string

@description('Backend Image Tag')
param backendImageTag string = 'latest'

@description('Frontend Image Tag')
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
param azureOpenAIEndpoint string = 'https://practicehub3994533910.cognitiveservices.azure.com/'

// Variables
var backendAppName = '${namePrefix}-backend-${environment}'
var frontendAppName = '${namePrefix}-frontend-${environment}'

// Get existing container registry for credentials
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

// Backend Container App
resource backendContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: backendAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnvironmentId
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
      secrets: [
        {
          name: 'supabase-url'
          value: supabaseUrl
        }
        {
          name: 'supabase-key'
          value: supabaseKey
        }
        {
          name: 'azure-openai-api-key'
          value: azureOpenAIApiKey
        }
        {
          name: 'container-registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
      registries: [
        {
          server: containerRegistryLoginServer
          username: containerRegistry.name
          passwordSecretRef: 'container-registry-password'
        }
      ]
    }
    template: {
      containers: [
        {
          image: '${containerRegistryLoginServer}/scrapemaster/backend:${backendImageTag}'
          name: 'backend'
          env: [
            {
              name: 'SUPABASE_URL'
              secretRef: 'supabase-url'
            }
            {
              name: 'SUPABASE_KEY'
              secretRef: 'supabase-key'
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'azure-openai-api-key'
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
              name: 'AZURE_OPENAI_MODEL'
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
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 30
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 5
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
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
}

// Frontend Container App
resource frontendContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: frontendAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnvironmentId
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
      secrets: [
        {
          name: 'container-registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
      registries: [
        {
          server: containerRegistryLoginServer
          username: containerRegistry.name
          passwordSecretRef: 'container-registry-password'
        }
      ]
    }
    template: {
      containers: [
        {
          image: '${containerRegistryLoginServer}/scrapemaster/frontend:${frontendImageTag}'
          name: 'frontend'
          env: [
            {
              name: 'REACT_APP_API_URL'
              value: 'https://${backendContainerApp.properties.configuration.ingress.fqdn}'
            }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: 80
              }
              initialDelaySeconds: 30
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: 80
              }
              initialDelaySeconds: 5
              periodSeconds: 5
            }
          ]
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
}

// Outputs
output backendUrl string = 'https://${backendContainerApp.properties.configuration.ingress.fqdn}'
output frontendUrl string = 'https://${frontendContainerApp.properties.configuration.ingress.fqdn}'
output backendAppName string = backendContainerApp.name
output frontendAppName string = frontendContainerApp.name
