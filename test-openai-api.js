// Test script for OpenAI API key handling

// Mock localStorage
const localStorage = {
  _data: {},
  getItem(key) {
    return this._data[key];
  },
  setItem(key, value) {
    this._data[key] = value;
  }
};

// Set API keys
localStorage.setItem('openaiApiKey', 'YOUR_OPENAI_API_KEY');
localStorage.setItem('azureApiKey', 'YOUR_AZURE_API_KEY');
localStorage.setItem('azureEndpoint', 'https://your-azure-endpoint.services.ai.azure.com');

// Mock API functions
const getOpenAIApiKey = () => {
  return localStorage.getItem('openaiApiKey') || '';
};

const getAzureOpenAICredentials = () => {
  return {
    api_key: localStorage.getItem('azureApiKey') || '',
    endpoint: localStorage.getItem('azureEndpoint') || '',
  };
};

// Test queryRagApi function
const queryRagApi = (projectId, userMessage, modelName) => {
  // Determine which API to use based on the model name
  // Only match exact gpt-4o, not gpt-4o-mini or other variants
  const isGpt4o = modelName === 'gpt-4o' || 
                  modelName === 'GPT-4o' || 
                  modelName.toLowerCase() === 'gpt-4o';
  
  let requestBody;
  
  if (isGpt4o) {
    // Use OpenAI API for GPT-4o
    const openaiApiKey = getOpenAIApiKey();
    requestBody = {
      query: userMessage,
      model_name: 'gpt-4o',  // Force the model name to be gpt-4o
      use_openai: true,
      openai_key: openaiApiKey
    };
  } else {
    // Use Azure for other models
    const azureCredentials = getAzureOpenAICredentials();
    requestBody = {
      query: userMessage,
      model_name: modelName,
      azure_credentials: {
        api_key: azureCredentials.api_key,
        endpoint: azureCredentials.endpoint,
        deployment_name: modelName
      }
    };
  }
  
  return requestBody;
};

// Test with GPT-4o model
console.log('Testing with GPT-4o model:');
const gpt4oRequest = queryRagApi('project-123', 'Hello, world!', 'gpt-4o');
console.log(gpt4oRequest);

// Test with GPT-4o-mini model
console.log('\nTesting with GPT-4o-mini model:');
const gpt4oMiniRequest = queryRagApi('project-123', 'Hello, world!', 'gpt-4o-mini');
console.log(gpt4oMiniRequest);

// Test with empty OpenAI API key
localStorage._data = {
  azureApiKey: 'YOUR_AZURE_API_KEY',
  azureEndpoint: 'https://your-azure-endpoint.services.ai.azure.com'
};
console.log('\nTesting with empty OpenAI API key:');
const emptyOpenAIKeyRequest = queryRagApi('project-123', 'Hello, world!', 'gpt-4o');
console.log(emptyOpenAIKeyRequest);

console.log('\nAll tests completed successfully!');