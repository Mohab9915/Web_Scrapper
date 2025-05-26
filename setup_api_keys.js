// Script to set up API keys in localStorage from .env file
// This script can be included in your HTML to automatically load API keys

// Function to load API keys from .env file
function loadApiKeysFromEnv() {
  // This is a simplified version - in a real app, you'd need a server-side component
  // to read the .env file and pass the values to the frontend
  
  // For demonstration purposes, you can manually set these values
  // based on your .env file contents
  const azureApiKey = 'YOUR_AZURE_API_KEY'; // Replace with your actual key
  const azureEndpoint = 'YOUR_AZURE_ENDPOINT'; // Replace with your actual endpoint
  const openaiApiKey = 'YOUR_OPENAI_API_KEY'; // Replace with your actual key
  
  // Store in localStorage
  localStorage.setItem('azureApiKey', azureApiKey);
  localStorage.setItem('azureEndpoint', azureEndpoint);
  localStorage.setItem('openaiApiKey', openaiApiKey);
  
  console.log('API keys loaded from environment');
}

// Call the function to load API keys
loadApiKeysFromEnv();