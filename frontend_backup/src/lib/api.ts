'use client';

import type { Project, ScrapedSession, ChatMessage } from '@/types';

/**
 * Utility function to convert snake_case to camelCase
 */
function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Recursively transform keys in an object from snake_case to camelCase
 */
function transformKeys<T>(data: any): T {
  if (Array.isArray(data)) {
    return data.map(item => transformKeys(item)) as unknown as T;
  }

  if (data !== null && typeof data === 'object') {
    const transformed: Record<string, any> = {};

    Object.keys(data).forEach(key => {
      const camelKey = snakeToCamel(key);
      transformed[camelKey] = transformKeys(data[key]);
    });

    return transformed as T;
  }

  return data as T;
}

// Backend API URL
export const API_URL = 'http://localhost:8000/api/v1';

// Azure OpenAI credentials
const AZURE_OPENAI_CREDENTIALS = {
  api_key: 'YOUR_AZURE_API_KEY',
  endpoint: 'https://practicehub3994533910.services.ai.azure.com',
};

// Azure OpenAI model configuration
const AZURE_EMBEDDING_MODEL = "text-embedding-ada-002";
const AZURE_CHAT_MODEL = "gpt-4o-mini";

/**
 * Error handling wrapper for fetch requests
 */
async function fetchWithErrorHandling<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));

      // Handle different error formats
      let errorMessage: string;
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
        return {} as T;
      }

      // Parse JSON and transform snake_case keys to camelCase
      const data = JSON.parse(text);
      return transformKeys<T>(data);
    } catch (jsonError) {
      console.error('Error parsing JSON response:', jsonError);
      return {} as T;
    }
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

/**
 * Get all projects
 */
export async function getProjects(): Promise<Project[]> {
  return fetchWithErrorHandling<Project[]>(`${API_URL}/projects`);
}

/**
 * Get a project by ID
 */
export async function getProjectById(id: string): Promise<Project> {
  return fetchWithErrorHandling<Project>(`${API_URL}/projects/${id}`);
}

/**
 * Create a new project
 */
export async function createProject(name: string, initialUrls?: string[]): Promise<Project> {
  return fetchWithErrorHandling<Project>(`${API_URL}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, initial_urls: initialUrls }),
  });
}

/**
 * Update a project's name
 */
export async function updateProjectName(id: string, name: string): Promise<Project> {
  return fetchWithErrorHandling<Project>(`${API_URL}/projects/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
}

/**
 * Update a project's RAG status
 */
export async function updateProjectRAGStatus(id: string, enabled: boolean): Promise<Project> {
  return fetchWithErrorHandling<Project>(`${API_URL}/projects/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rag_enabled: enabled }),
  });
}

/**
 * Delete a project
 */
export async function deleteProject(id: string): Promise<void> {
  return fetchWithErrorHandling<void>(`${API_URL}/projects/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Get all scraped sessions for a project
 */
export async function getScrapedSessions(projectId: string): Promise<ScrapedSession[]> {
  return fetchWithErrorHandling<ScrapedSession[]>(`${API_URL}/projects/${projectId}/sessions`);
}

/**
 * Initiate interactive scraping
 */
export async function initiateInteractiveScrape(
  projectId: string,
  url: string
): Promise<{ interactive_target_url: string, session_id: string }> {
  try {
    // First, try to use the backend API
    return await fetchWithErrorHandling<{ interactive_target_url: string, session_id: string }>(
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
    // This allows the feature to work even without backend support
    const sessionId = `session_${Date.now()}`;
    return {
      interactive_target_url: url,
      session_id: sessionId
    };
  }
}

/**
 * Execute scraping on a URL
 */
export async function executeScrape(
  projectId: string,
  url: string,
  sessionId?: string,
  forceRefresh: boolean = false
): Promise<ScrapedSession> {
  // Generate a proper UUID for session_id if not provided
  const finalSessionId = sessionId || crypto.randomUUID();

  // Include Azure OpenAI credentials for embedding generation
  return fetchWithErrorHandling<ScrapedSession>(
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
export async function deleteScrapedSession(projectId: string, sessionId: string): Promise<void> {
  return fetchWithErrorHandling<void>(
    `${API_URL}/projects/${projectId}/sessions/${sessionId}`,
    {
      method: 'DELETE',
    }
  );
}

/**
 * Get chat messages for a project
 */
export async function getChatMessages(projectId: string): Promise<ChatMessage[]> {
  return fetchWithErrorHandling<ChatMessage[]>(`${API_URL}/projects/${projectId}/chat`);
}

/**
 * Post a chat message and get a response
 */
export async function postChatMessage(projectId: string, content: string): Promise<ChatMessage> {
  // Include Azure OpenAI credentials for chat completion
  return fetchWithErrorHandling<ChatMessage>(
    `${API_URL}/projects/${projectId}/chat`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content,
        azure_credentials: {
          ...AZURE_OPENAI_CREDENTIALS,
          deployment_name: AZURE_CHAT_MODEL
        }
      }),
    }
  );
}

/**
 * Query the RAG system
 */
export async function queryRAG(projectId: string, query: string): Promise<{
  answer: string;
  generation_cost: number;
  source_documents?: Array<{ content: string; metadata: { url: string; similarity: number } }>;
}> {
  return fetchWithErrorHandling(
    `${API_URL}/projects/${projectId}/query-rag`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        model_deployment: AZURE_CHAT_MODEL,
        azure_credentials: {
          ...AZURE_OPENAI_CREDENTIALS,
          deployment_name: AZURE_CHAT_MODEL
        }
      }),
    }
  );
}

/**
 * Helper function to integrate custom scraping code
 *
 * This function allows you to use your own scraping code while still integrating
 * with the project's session management and database storage.
 *
 * @param projectId - The ID of the project to associate the scraped content with
 * @param url - The URL that was scraped
 * @param scrapedContent - The content that was scraped (markdown format preferred)
 * @param structuredData - Optional structured data extracted from the content
 * @param sessionId - Optional session ID (will be generated if not provided)
 * @returns The created scrape session
 */
export async function saveScrapedContent(
  projectId: string,
  url: string,
  scrapedContent: string,
  structuredData?: Record<string, any>,
  sessionId?: string
): Promise<ScrapedSession> {
  // Generate a proper UUID for session_id if not provided
  const finalSessionId = sessionId || crypto.randomUUID();

  // Create a request that mimics the execute-scrape endpoint but with pre-scraped content
  return fetchWithErrorHandling<ScrapedSession>(
    `${API_URL}/projects/${projectId}/save-scraped-content`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        session_id: finalSessionId,
        scraped_content: scrapedContent,
        structured_data: structuredData || {},
        api_keys: {
          ...AZURE_OPENAI_CREDENTIALS,
          deployment_name: AZURE_EMBEDDING_MODEL
        }
      }),
    }
  ).catch(error => {
    // If the save-scraped-content endpoint doesn't exist yet, fall back to the execute-scrape endpoint
    console.warn('save-scraped-content endpoint not available, using execute-scrape as fallback:', error);

    // This is a fallback that will work with the existing backend
    return fetchWithErrorHandling<ScrapedSession>(
      `${API_URL}/projects/${projectId}/execute-scrape`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_page_url: url,
          session_id: finalSessionId,
          pre_scraped_content: scrapedContent,
          structured_data: structuredData || {},
          api_keys: {
            ...AZURE_OPENAI_CREDENTIALS,
            deployment_name: AZURE_EMBEDDING_MODEL
          }
        }),
      }
    );
  });
}

/**
 * Get cache statistics
 */
export interface CacheStats {
  total_entries: number;
  hit_count: number;
  miss_count: number;
  hit_rate: number;
}

export async function fetchCacheStats(): Promise<CacheStats> {
  return fetchWithErrorHandling<CacheStats>(`${API_URL}/cache/stats`);
}
