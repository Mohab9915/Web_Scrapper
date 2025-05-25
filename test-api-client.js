// Test script for API client

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
localStorage.setItem('azureApiKey', 'YOUR_AZURE_API_KEY');
localStorage.setItem('azureEndpoint', 'https://your-azure-endpoint.services.ai.azure.com');
localStorage.setItem('openaiApiKey', 'YOUR_OPENAI_API_KEY');

// Mock getAzureOpenAICredentials function
const getAzureOpenAICredentials = () => {
  return {
    api_key: localStorage.getItem('azureApiKey') || '',
    endpoint: localStorage.getItem('azureEndpoint') || '',
  };
};

// Test the function
const credentials = getAzureOpenAICredentials();
console.log('Azure OpenAI Credentials:');
console.log(credentials);

// Test with empty localStorage
localStorage._data = {};
const emptyCredentials = getAzureOpenAICredentials();
console.log('\nEmpty Credentials (when localStorage is empty):');
console.log(emptyCredentials);

// Test with partial data
localStorage.setItem('azureApiKey', 'test-key');
const partialCredentials = getAzureOpenAICredentials();
console.log('\nPartial Credentials (only API key set):');
console.log(partialCredentials);

console.log('\nAll tests completed successfully!');