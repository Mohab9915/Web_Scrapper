/**
 * API client for the backend server
 */
import { supabase } from './supabase';

/**
 * Utility function to convert snake_case to camelCase
 */
function snakeToCamel(str) {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Recursively transform keys in an object from snake_case to camelCase
 */
function transformKeys(data) {
  if (Array.isArray(data)) {
    return data.map(item => transformKeys(item));
  }

  if (data !== null && typeof data === 'object') {
    const transformed = {};

    Object.keys(data).forEach(key => {
      const camelKey = snakeToCamel(key);
      transformed[camelKey] = transformKeys(data[key]);
    });

    return transformed;
  }

  return data;
}



// Backend API URL - use environment variable or fallback to local development
export const API_URL = process.env.REACT_APP_API_URL
  ? `${process.env.REACT_APP_API_URL}/api/v1`
  : 'http://localhost:8000/api/v1';

// Debug logging for API URL configuration
console.log('🔧 API Configuration Debug:');
console.log('  - REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
console.log('  - NODE_ENV:', process.env.NODE_ENV);
console.log('  - Final API_URL:', API_URL);

// Function to get authentication headers
async function getAuthHeaders() {
  try {
    console.log('🔑 Getting auth headers...');
    const { data: { session }, error } = await supabase.auth.getSession();
    console.log('🔑 Session:', session ? 'Present' : 'Missing');
    console.log('🔑 Error:', error);

    if (error || !session) {
      console.log('🔑 No valid session, returning empty headers');
      return {};
    }

    const headers = {
      'Authorization': `Bearer ${session.access_token}`
    };
    console.log('🔑 Auth headers created:', headers);
    return headers;
  } catch (error) {
    console.error('🔑 Error getting auth headers:', error);
    return {};
  }
}

// Get Azure OpenAI credentials from environment variables or localStorage
const getAzureOpenAICredentials = () => {
  // First try environment variables (for production deployment)
  const envApiKey = process.env.REACT_APP_AZURE_OPENAI_API_KEY;
  const envEndpoint = process.env.REACT_APP_AZURE_OPENAI_ENDPOINT;

  // Fallback to localStorage (for development)
  const localApiKey = localStorage.getItem('azureApiKey') || '';
  const localEndpoint = localStorage.getItem('azureEndpoint') || '';

  return {
    api_key: envApiKey || localApiKey,
    endpoint: envEndpoint || localEndpoint,
  };
};

// Azure OpenAI model configuration
const AZURE_EMBEDDING_MODEL = "text-embedding-ada-002";

/**
 * Error handling wrapper for fetch requests
 */
async function fetchWithErrorHandling(url, options = {}) {
  try {
    console.log('🔄 Making API request to:', url);
    console.log('📤 Request options:', options);

    // Get authentication headers
    const authHeaders = await getAuthHeaders();

    // Add default headers and timeout
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
        ...options.headers
      },
      ...options
    };

    // Add timeout to prevent hanging requests
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    const response = await fetch(url, {
      ...defaultOptions,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorData;
      let responseText = '';
      try {
        responseText = await response.text(); // Get text first
        errorData = JSON.parse(responseText); // Try to parse as JSON
      } catch (e) {
        // Failed to parse as JSON
        errorData = null; 
      }

      let errorMessage;
      if (errorData) { // If JSON parsing was successful
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail && typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (errorData.detail && Array.isArray(errorData.detail)) {
          // Handle Pydantic validation errors which come as an array
          const firstError = errorData.detail[0];
          if (firstError && firstError.msg) {
            errorMessage = `Validation error: ${firstError.msg} at ${firstError.loc.join('.')}`;
          } else {
            errorMessage = 'Validation error in request';
          }
        } else if (errorData.message && typeof errorData.message === 'string') {
          errorMessage = errorData.message;
        } else {
          // If we can't extract a string message, stringify the entire object
          try {
            errorMessage = `API error: ${JSON.stringify(errorData)}`;
          } catch (stringifyError) {
            errorMessage = `API error (unparseable JSON object): ${response.status}`;
          }
        }
      } else { // If JSON parsing failed, use the responseText or a generic message
        if (responseText && responseText.length < 500 && !responseText.trim().startsWith('<') && responseText.trim() !== '') { // Avoid long HTML pages and empty strings
          errorMessage = responseText;
        } else {
          errorMessage = `API error: ${response.status} ${response.statusText || 'Server error'}`;
        }
      }
      throw new Error(errorMessage);
    }

    // Check if response is empty and handle JSON parsing errors
    let text = '';
    try {
      // Get response text first
      text = await response.text();
      console.log('📥 Raw response text (first 500 chars):', text.substring(0, 500));

      // If empty response, return empty object
      if (!text || text.trim() === '') {
        console.warn('⚠️ Empty response received from API');
        return {};
      }

      // Parse JSON and transform snake_case keys to camelCase
      const data = JSON.parse(text);
      console.log('📊 Parsed JSON data:', data);
      
      const transformedData = transformKeys(data);
      console.log('🔄 Transformed data:', transformedData);
      
      return transformedData;
    } catch (jsonError) {
      console.error('❌ Error parsing JSON response:', jsonError);
      console.error('📄 Response text that failed to parse:', text);
      return {};
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error('❌ Request timeout:', url);
      throw new Error('Request timeout - please try again');
    }
    console.error('❌ API request failed:', error);
    throw error;
  }
}

/**
 * Get all projects
 */
export async function getProjects() {
  return fetchWithErrorHandling(`${API_URL}/projects/`);
}

/**
 * Get a project by ID
 */
export async function getProjectById(id) {
  return fetchWithErrorHandling(`${API_URL}/projects/${id}`);
}

/**
 * Create a new project
 */
export async function createProject(name, initialUrls) {
  return fetchWithErrorHandling(`${API_URL}/projects/`, {
    method: 'POST',
    body: JSON.stringify({ name, initial_urls: initialUrls }),
  });
}

/**
 * Update a project's name
 */
export async function updateProjectName(id, name) {
  return fetchWithErrorHandling(`${API_URL}/projects/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
}

/**
 * Update a project's RAG status
 */
export async function updateProjectRAGStatus(id, enabled) {
  return fetchWithErrorHandling(`${API_URL}/projects/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rag_enabled: enabled }),
  });
}

/**
 * Delete a project
 */
export async function deleteProject(id) {
  return fetchWithErrorHandling(`${API_URL}/projects/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Get all scraped sessions for a project
 */
export async function getScrapedSessions(projectId) {
  return fetchWithErrorHandling(`${API_URL}/projects/${projectId}/sessions`);
}

/**
 * Initiate interactive scraping
 */
export async function initiateInteractiveScrape(projectId, url) {
  try {
    // First, try to use the backend API
    return await fetchWithErrorHandling(
      `${API_URL}/projects/${projectId}/initiate-interactive-scrape`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initial_url: url }),
      }
    );
  } catch (error) {
    console.warn('Backend API for interactive scraping not available, using direct URL:', error);

    // Fallback: If the backend doesn't support this endpoint yet, just use the URL directly
    // Generate a random session ID if crypto.randomUUID() is not available
    const sessionId = typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    return {
      interactive_target_url: url,
      session_id: sessionId
    };
  }
}

/**
 * Execute scraping on a URL
 */
export async function executeScrape(projectId, url, sessionId, forceRefresh = false, displayFormat = 'table', conditions = '') {
  // Generate a random session ID if not provided
  const finalSessionId = sessionId || (
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  );

  // Get the latest Azure OpenAI credentials
  const credentials = getAzureOpenAICredentials();
  
  console.log('🚀 Starting scrape execution with params:', {
    projectId,
    url,
    sessionId: finalSessionId,
    forceRefresh,
    displayFormat,
    conditions
  });

  // Include Azure OpenAI credentials for embedding generation
  const rawResult = await fetchWithErrorHandling(
    `${API_URL}/projects/${projectId}/execute-scrape`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_page_url: url,
        session_id: finalSessionId,
        force_refresh: forceRefresh, // Add force_refresh parameter
        display_format: displayFormat,
        conditions: conditions, // Pass the conditions to the backend
        api_keys: {
          ...credentials,
          deployment_name: AZURE_EMBEDDING_MODEL
        }
      }),
    }
  );

  console.log('📦 Raw result from API:', rawResult);
  console.log('📊 Raw result keys:', Object.keys(rawResult));
  console.log('🔍 Checking for tabular data in different formats:');
  console.log('  - rawResult.tabularData:', rawResult.tabularData);
  console.log('  - rawResult.tabular_data:', rawResult.tabular_data);
  console.log('  - rawResult.fields:', rawResult.fields);
  console.log('  - rawResult.formatted_data:', rawResult.formatted_data);

  return rawResult;
}

/**
 * Delete a scraped session
 */
export async function deleteScrapedSession(projectId, sessionId) {
  return fetchWithErrorHandling(
    `${API_URL}/projects/${projectId}/sessions/${sessionId}`,
    {
      method: 'DELETE',
    }
  );
}

/**
 * Get cache statistics
 */
export async function fetchCacheStats() {
  return fetchWithErrorHandling(`${API_URL}/cache/stats`);
}

/**
 * Query the RAG API with the appropriate credentials
 */
export async function queryRagApi(projectId, userMessage, modelName) {
  // Use Azure OpenAI for all queries - credentials come from environment
  const requestBody = {
    query: userMessage,
    model_name: modelName || 'gpt-4o'
  };

  return fetchWithErrorHandling(
    `${API_URL}/projects/${projectId}/query-rag`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    }
  );
}

/**
 * Query the Enhanced RAG API with intelligent formatting and structured data processing
 */
export async function queryEnhancedRagApi(projectId, userMessage, modelName) {
  const requestBody = {
    query: userMessage,
    model_name: modelName || 'gpt-4o'
  };

  return fetchWithErrorHandling(
    `${API_URL}/projects/${projectId}/enhanced-query-rag`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    }
  );
}

/**
 * Get chat messages for a project/conversation
 */
export async function getChatMessages(projectId, conversationId = null) {
  let url = `${API_URL}/projects/${projectId}/chat`;
  if (conversationId) {
    url += `?conversation_id=${conversationId}`;
  }
  return fetchWithErrorHandling(url);
}



/**
 * Send a chat message and get a response
 */
export async function sendChatMessage(projectId, content, conversationId = null, sessionId = null) {
  let url = `${API_URL}/projects/${projectId}/chat`;
  const params = new URLSearchParams();

  if (conversationId) {
    params.append('conversation_id', conversationId);
  }
  if (sessionId) {
    params.append('session_id', sessionId);
  }

  // Add query parameters to the URL
  if (params.toString()) {
    url += `?${params.toString()}`;
  }

  // The message body includes only content - Azure credentials come from environment
  const messageBody = {
    content: content
  };

  return fetchWithErrorHandling(url, {
    method: 'POST',
    body: JSON.stringify(messageBody)
  });
}

/**
 * Get all conversations for a project
 */
export async function getProjectConversations(projectId, limit = 50) {
  return fetchWithErrorHandling(
    `${API_URL}/projects/${projectId}/conversations?limit=${limit}`
  );
}

/**
 * Create a new conversation
 */
export async function createConversation(projectId, sessionId = null) {
  let url = `${API_URL}/projects/${projectId}/conversations`;
  if (sessionId) {
    url += `?session_id=${sessionId}`;
  }

  return fetchWithErrorHandling(url, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

/**
 * Delete a conversation
 */
export async function deleteConversation(projectId, conversationId) {
  return fetchWithErrorHandling(
    `${API_URL}/projects/${projectId}/conversations/${conversationId}`,
    {
      method: 'DELETE',
    }
  );
}

/**
 * Get messages for a specific conversation
 */
export async function getConversationMessages(projectId, conversationId, limit = 100) {
  return fetchWithErrorHandling(
    `${API_URL}/projects/${projectId}/conversations/${conversationId}/messages?limit=${limit}`
  );
}

/**
 * Get project URLs
 */
export async function getProjectUrls(projectId) {
  return fetchWithErrorHandling(`${API_URL}/projects/${projectId}/urls`);
}
