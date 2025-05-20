/**
 * API client for the backend server
 */

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

// Backend API URL
export const API_URL = 'http://localhost:8000/api/v1';

// Azure OpenAI credentials
const AZURE_OPENAI_CREDENTIALS = {
  api_key: 'BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC',
  endpoint: 'https://practicehub3994533910.services.ai.azure.com',
};

// Azure OpenAI model configuration
const AZURE_EMBEDDING_MODEL = "text-embedding-ada-002";
const AZURE_CHAT_MODEL = "gpt-4o-mini";

/**
 * Error handling wrapper for fetch requests
 */
async function fetchWithErrorHandling(url, options) {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));

      // Handle different error formats
      let errorMessage;
      if (typeof errorData === 'string') {
        errorMessage = errorData;
      } else if (errorData && typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (errorData && Array.isArray(errorData.detail)) {
        // Handle Pydantic validation errors which come as an array
        const firstError = errorData.detail[0];
        if (firstError && firstError.msg) {
          errorMessage = `Validation error: ${firstError.msg} at ${firstError.loc.join('.')}`;
        } else {
          errorMessage = 'Validation error in request';
        }
      } else if (errorData && typeof errorData.message === 'string') {
        errorMessage = errorData.message;
      } else {
        // If we can't extract a string message, stringify the entire object
        try {
          errorMessage = `API error: ${JSON.stringify(errorData)}`;
        } catch (e) {
          errorMessage = `API error: ${response.status}`;
        }
      }

      throw new Error(errorMessage);
    }

    // Check if response is empty and handle JSON parsing errors
    try {
      // Get response text first
      const text = await response.text();

      // If empty response, return empty object
      if (!text || text.trim() === '') {
        console.warn('Empty response received from API');
        return {};
      }

      // Parse JSON and transform snake_case keys to camelCase
      const data = JSON.parse(text);
      return transformKeys(data);
    } catch (jsonError) {
      console.error('Error parsing JSON response:', jsonError);
      return {};
    }
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

/**
 * Get all projects
 */
export async function getProjects() {
  return fetchWithErrorHandling(`${API_URL}/projects`);
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
  return fetchWithErrorHandling(`${API_URL}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
export async function executeScrape(projectId, url, sessionId, forceRefresh = false) {
  // Generate a random session ID if not provided
  const finalSessionId = sessionId || (
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  );

  // Include Azure OpenAI credentials for embedding generation
  return fetchWithErrorHandling(
    `${API_URL}/projects/${projectId}/execute-scrape`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_page_url: url,
        session_id: finalSessionId,
        force_refresh: forceRefresh, // Add force_refresh parameter
        api_keys: {
          ...AZURE_OPENAI_CREDENTIALS,
          deployment_name: AZURE_EMBEDDING_MODEL
        }
      }),
    }
  );
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
