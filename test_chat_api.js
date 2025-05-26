// Test script for the chat API
// Using global fetch - works in modern browsers and recent Node.js versions
// If running in an older Node.js environment without global fetch, 
// you may need to uncomment the next line and install node-fetch
// const fetch = require('node-fetch');

// Configuration (replace with your actual values)
const API_URL = 'http://localhost:8000'; // Adjust based on your backend URL
const PROJECT_ID = '5f41c7b3-4c13-4a41-9a8e-756da6410111'; // Replace with an actual project ID

// Azure OpenAI credentials (replace with your actual values or load from environment)
const AZURE_API_KEY = process.env.AZURE_OPENAI_API_KEY || 'your-azure-api-key';
const AZURE_ENDPOINT = process.env.AZURE_OPENAI_ENDPOINT || 'https://your-endpoint.openai.azure.com/';

// Test function to create a conversation
async function createConversation() {
  try {
    const response = await fetch(`${API_URL}/projects/${PROJECT_ID}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Error creating conversation:', errorData);
      return null;
    }

    const data = await response.json();
    console.log('Conversation created successfully:', data);
    return data.conversation_id;
  } catch (error) {
    console.error('Error creating conversation:', error);
    return null;
  }
}

// Test function to send a message
async function sendMessage(conversationId, content) {
  try {
    // Build URL with params
    let url = `${API_URL}/projects/${PROJECT_ID}/chat`;
    const params = new URLSearchParams();
    
    if (conversationId) {
      params.append('conversation_id', conversationId);
      console.log('Using conversation ID:', conversationId);
    }
    
    // Add Azure credentials as query parameters
    params.append('azure_api_key', AZURE_API_KEY);
    params.append('azure_endpoint', AZURE_ENDPOINT);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    // Prepare message payload
    const messageBody = { content };
    
    console.log('Sending message to URL:', url);
    console.log('Message body:', JSON.stringify(messageBody, null, 2));
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(messageBody)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Error (${response.status}): ${errorText}`);
      try {
        const errorData = JSON.parse(errorText);
        console.error('Parsed error:', JSON.stringify(errorData, null, 2));
      } catch (e) {
        console.error('Raw error text:', errorText);
      }
      return null;
    }

    const data = await response.json();
    console.log('Message sent successfully, response:', JSON.stringify(data, null, 2));
    return data;
  } catch (error) {
    console.error('Error sending message:', error);
    return null;
  }
}

// Run the test
async function runTest() {
  console.log('Creating a new conversation...');
  const conversationId = await createConversation();
  
  if (!conversationId) {
    console.error('Failed to create conversation, test aborted.');
    return;
  }
  
  console.log('Sending a test message...');
  await sendMessage(conversationId, 'Hello, this is a test message!');
}

runTest().catch(console.error);
