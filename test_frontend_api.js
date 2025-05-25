// Test script for frontend API service
// Run with Node.js: node test_frontend_api.js

// Use dynamic import for node-fetch (ESM module)
import('node-fetch').then(({ default: fetch }) => {
  // Main function will be called after fetch is imported
  runTests(fetch);
});

// UUID import
import('uuid').then(({ v4: uuidv4 }) => {
  global.uuidv4 = uuidv4;
});

// Backend API URL
const API_URL = 'http://localhost:8001/api/v1';

// Azure OpenAI credentials
const AZURE_OPENAI_CREDENTIALS = {
  api_key: 'YOUR_AZURE_API_KEY',
  endpoint: 'https://your-azure-endpoint.services.ai.azure.com',
};

// Helper function to print separator
function printSeparator() {
  console.log('\n' + '='.repeat(80) + '\n');
}

// Helper function for fetch with error handling
async function fetchWithErrorHandling(url, options = {}, fetchFn) {
  try {
    const response = await fetchFn(url, options);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

// Test getting projects
async function testGetProjects(fetchFn) {
  console.log('Testing getProjects()...');

  try {
    const projects = await fetchWithErrorHandling(`${API_URL}/projects`, {}, fetchFn);
    console.log('Projects:', JSON.stringify(projects, null, 2));
    return projects;
  } catch (error) {
    console.error('Failed to get projects:', error);
    return null;
  }
}

// Test creating a project
async function testCreateProject(fetchFn) {
  console.log('Testing createProject()...');

  const projectName = `Test Project ${Date.now()}`;

  try {
    const project = await fetchWithErrorHandling(`${API_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: projectName }),
    }, fetchFn);

    console.log('Project created:', JSON.stringify(project, null, 2));
    return project;
  } catch (error) {
    console.error('Failed to create project:', error);
    return null;
  }
}

// Test updating a project's RAG status
async function testUpdateProjectRAGStatus(projectId, enabled, fetchFn) {
  console.log(`Testing updateProjectRAGStatus(${projectId}, ${enabled})...`);

  try {
    const project = await fetchWithErrorHandling(`${API_URL}/projects/${projectId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rag_enabled: enabled }),
    }, fetchFn);

    console.log('Project updated:', JSON.stringify(project, null, 2));
    return project;
  } catch (error) {
    console.error('Failed to update project RAG status:', error);
    return null;
  }
}

// Test executing a scrape
async function testExecuteScrape(projectId, fetchFn) {
  console.log(`Testing executeScrape(${projectId})...`);

  const sessionId = global.uuidv4();

  try {
    const result = await fetchWithErrorHandling(`${API_URL}/projects/${projectId}/execute-scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_page_url: 'http://example.com',
        session_id: sessionId,
        api_keys: {
          ...AZURE_OPENAI_CREDENTIALS,
          deployment_name: 'text-embedding-ada-002'
        }
      }),
    }, fetchFn);

    console.log('Scrape executed:', JSON.stringify(result, null, 2));
    return sessionId;
  } catch (error) {
    console.error('Failed to execute scrape:', error);
    return null;
  }
}

// Test querying RAG
async function testQueryRAG(projectId, fetchFn) {
  console.log(`Testing queryRAG(${projectId})...`);

  try {
    const result = await fetchWithErrorHandling(`${API_URL}/projects/${projectId}/query-rag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: 'What is the main topic of the scraped content?',
        model_deployment: 'gpt-4o-mini',
        azure_credentials: {
          ...AZURE_OPENAI_CREDENTIALS,
          deployment_name: 'gpt-4o-mini'
        }
      }),
    }, fetchFn);

    console.log('RAG query result:', JSON.stringify(result, null, 2));
    return result;
  } catch (error) {
    console.error('Failed to query RAG:', error);
    return null;
  }
}

// Main function to run all tests
async function runTests(fetchFn) {
  try {
    // Test getting projects
    const projects = await testGetProjects(fetchFn);
    printSeparator();

    // Test creating a project
    const project = await testCreateProject(fetchFn);
    if (!project) {
      console.log('Project creation failed. Exiting.');
      return;
    }
    printSeparator();

    // Test updating a project's RAG status
    const updatedProject = await testUpdateProjectRAGStatus(project.id, true, fetchFn);
    if (!updatedProject) {
      console.log('RAG enablement failed. Exiting.');
      return;
    }
    printSeparator();

    // Wait for RAG to be enabled
    console.log('Waiting for RAG to be enabled...');
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Test executing a scrape
    const sessionId = await testExecuteScrape(project.id, fetchFn);
    if (!sessionId) {
      console.log('Scrape execution failed. Exiting.');
      return;
    }
    printSeparator();

    // Wait for scrape to be processed
    console.log('Waiting for scrape to be processed...');
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Test querying RAG
    const ragResult = await testQueryRAG(project.id, fetchFn);
    if (!ragResult) {
      console.log('RAG query failed. Exiting.');
      return;
    }
    printSeparator();

    console.log('All frontend API tests passed successfully!');
  } catch (error) {
    console.error('Test failed:', error);
  }
}
