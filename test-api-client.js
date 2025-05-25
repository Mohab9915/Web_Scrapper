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
localStorage.setItem('azureApiKey', 'BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC');
localStorage.setItem('azureEndpoint', 'https://practicehub3994533910.services.ai.azure.com');
localStorage.setItem('openaiApiKey', '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');

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