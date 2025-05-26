// Setup Azure OpenAI credentials in localStorage for the frontend
// Run this in the browser console or as a script

// Azure OpenAI credentials from .env file
const azureCredentials = {
  azureApiKey: 'BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC',
  azureEndpoint: 'https://practicehub3994533910.services.ai.azure.com',
  openaiApiKey: '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'
};

// Set credentials in localStorage
localStorage.setItem('azureApiKey', azureCredentials.azureApiKey);
localStorage.setItem('azureEndpoint', azureCredentials.azureEndpoint);
localStorage.setItem('openaiApiKey', azureCredentials.openaiApiKey);

console.log('Azure OpenAI credentials have been set in localStorage');
console.log('Azure API Key:', localStorage.getItem('azureApiKey') ? 'Set' : 'Not set');
console.log('Azure Endpoint:', localStorage.getItem('azureEndpoint') ? 'Set' : 'Not set');
console.log('OpenAI API Key:', localStorage.getItem('openaiApiKey') ? 'Set' : 'Not set');
