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
    console.log('🔑 [getAuthHeaders] Getting auth headers...');
    
    // Check if supabase is initialized
    if (!supabase) {
      console.error('🔴 [getAuthHeaders] Supabase client is not initialized');
      return {};
    }
    
    // Debug: Check if supabase.auth is available
    if (!supabase.auth) {
      console.error('🔴 [getAuthHeaders] supabase.auth is not available');
      return {};
    }
    
    // Get the current session
    console.log('🔑 [getAuthHeaders] Calling supabase.auth.getSession()...');
    const { data: { session }, error } = await supabase.auth.getSession();
    
    console.log('🔑 [getAuthHeaders] Session data:', {
      hasSession: !!session,
      user: session?.user?.email || 'No user',
      accessToken: session?.access_token ? `${session.access_token.substring(0, 10)}...` : 'No token',
      expiresAt: session?.expires_at ? new Date(session.expires_at * 1000).toISOString() : 'N/A',
      error: error ? error.message : 'No error'
    });

    if (error) {
      console.error('🔴 [getAuthHeaders] Error getting session:', error);
      return {};
    }
    
    if (!session?.access_token) {
      console.error('🔴 [getAuthHeaders] No access token in session');
      // Try to get the token from localStorage as a fallback
      try {
        const storedSession = JSON.parse(localStorage.getItem(`sb-${process.env.REACT_APP_SUPABASE_URL.split('//')[1].split('.')[0]}-auth-token`));
        console.log('🔍 [getAuthHeaders] Fallback - Stored session from localStorage:', storedSession);
        if (storedSession?.access_token) {
          console.log('🟡 [getAuthHeaders] Using token from localStorage');
          return {
            'Authorization': `Bearer ${storedSession.access_token}`,
            'Content-Type': 'application/json',
          };
        }
      } catch (e) {
        console.error('🔴 [getAuthHeaders] Error getting token from localStorage:', e);
      }
      return {};
    }

    const headers = {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    };
    
    console.log('🟢 [getAuthHeaders] Returning headers with auth token');
    return headers;
    
  } catch (error) {
    console.error('🔴 [getAuthHeaders] Unexpected error getting auth headers:', {
      error: error.toString(),
      stack: error.stack,
      message: error.message
    });
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
  const requestId = Math.random().toString(36).substring(2, 8);
  const startTime = Date.now();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout for scraping operations
  
  try {
    console.log(`🔄 [${requestId}] ${options.method || 'GET'} ${url}`);
    
    // Get authentication headers
    console.log(`🔑 [${requestId}] Getting auth headers...`);
    const authHeaders = await getAuthHeaders();
    
    // Prepare request options
    const requestOptions = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
        ...options.headers,
      },
      credentials: 'include', // Important for cookies, authorization headers with TLS
      signal: controller.signal, // Add AbortController signal
      ...options,
    };
    
    console.log(`🔍 [${requestId}] Request options:`, {
      method: requestOptions.method,
      headers: Object.keys(requestOptions.headers).reduce((acc, key) => ({
        ...acc,
        [key]: key.toLowerCase() === 'authorization' 
          ? `${requestOptions.headers[key].substring(0, 20)}...` 
          : requestOptions.headers[key]
      }), {}),
      credentials: requestOptions.credentials,
      body: requestOptions.body ? (typeof requestOptions.body === 'string' 
        ? requestOptions.body.substring(0, 100) + '...' 
        : '[Object]') : undefined
    });
    
    // Log request details
    console.log(`📤 [${requestId}] Request:`, {
      method: requestOptions.method,
      url,
      headers: {
        ...requestOptions.headers,
        // Don't log the full auth token for security
        ...(requestOptions.headers.Authorization ? {
          Authorization: `${requestOptions.headers.Authorization.substring(0, 20)}...`
        } : {})
      },
      body: requestOptions.body ? JSON.parse(requestOptions.body) : null
    });

    let response;
    try {
      console.log(`🌐 [${requestId}] Making fetch request to:`, url);
      response = await fetch(url, requestOptions);
      clearTimeout(timeoutId); // Clear the timeout if request succeeds
    } catch (error) {
      clearTimeout(timeoutId); // Clear the timeout if request fails
      console.error(`❌ [${requestId}] Network error during fetch:`, {
        error: error.toString(),
        message: error.message,
        name: error.name,
        stack: error.stack,
        url,
        method: requestOptions.method,
        headers: requestOptions.headers
      });
      
      if (error.name === 'AbortError') {
        throw new Error(`Request timed out after 5 minutes (${url})`);
      }
      
      throw new Error(`Network error: ${error.message}`);
    }
    
    const responseTime = Date.now() - startTime;
    
    // Clone the response so we can safely read the body for debugging
    const responseClone = response.clone();

    // Read body from the clone only – keeps the original stream intact
    const debugText = await responseClone.text();

    // Log response details using the cloned body
    let responseData;
    try {
      responseData = debugText ? JSON.parse(debugText) : null;
    } catch (e) {
      responseData = debugText;
    }

    console.log(`📥 [${requestId}] Response (${response.status} in ${responseTime}ms):`, {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries([...response.headers.entries()]),
      data: responseData
    });

    if (!response.ok) {
      const errorDetails = {
        status: response.status,
        statusText: response.statusText,
        url,
        error: responseData || 'No error details available',
        headers: Object.fromEntries([...response.headers.entries()])
      };

      console.error(`🔴 [${requestId}] API request failed:`, errorDetails);

      // Create a more detailed error object
      let errorMessage = 'API request failed';
      
      if (responseData) {
        if (typeof responseData === 'string') {
          errorMessage = responseData;
        } else if (responseData.detail) {
          errorMessage = Array.isArray(responseData.detail) 
            ? `Validation error: ${responseData.detail.map(d => d.msg).join(', ')}`
            : String(responseData.detail);
        } else if (responseData.message) {
          errorMessage = responseData.message;
        } else if (typeof responseData === 'object') {
          errorMessage = JSON.stringify(responseData);
        }
      } else if (debugText) {
        errorMessage = debugText.length < 500 ? debugText : 'Response too large to display';
      } else {
        errorMessage = `HTTP ${response.status} ${response.statusText}`;
      }

      const error = new Error(errorMessage);
      error.details = errorDetails;
      error.status = response.status;
      error.response = responseData;
      
      // Log additional info for 401/403 errors
      if (response.status === 401 || response.status === 403) {
        console.error('🔴 Authentication/Authorization Error:', {
          url,
          hasAuthHeader: !!requestOptions.headers.Authorization,
          authHeaderLength: requestOptions.headers.Authorization ? requestOptions.headers.Authorization.length : 0,
          authHeaderPrefix: requestOptions.headers.Authorization ? 
            requestOptions.headers.Authorization.substring(0, 20) + '...' : 'None'
        });
      }

      throw error;
    }

    // Process successful response
    if (response.status === 204 || response.status === 205) {
      // No content response
      return null;
    }

    // Get response text from the original response stream (first time it's read)
    const text = await response.text();
    console.log(`📄 [${requestId}] Raw response (${text.length} chars):`, text.length > 500 ? text.substring(0, 500) + '...' : text);

    // If empty response, return null
    if (!text || text.trim() === '') {
      console.warn(`⚠️ [${requestId}] Empty response received from API`);
      return null;
    }

    try {
      // Parse JSON and transform snake_case keys to camelCase
      const data = JSON.parse(text);
      const transformedData = transformKeys(data);
      console.log(`✅ [${requestId}] Successfully parsed and transformed response`);
      return transformedData;
    } catch (jsonError) {
      console.error(`❌ [${requestId}] Error parsing JSON response:`, jsonError);
      console.error(`📄 [${requestId}] Response text that failed to parse:`, text);
      throw new Error(`Failed to parse response: ${jsonError.message}`);
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
