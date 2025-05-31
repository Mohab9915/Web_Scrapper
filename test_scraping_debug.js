// Test script to verify scraping functionality and debug logs
// Define API base URL with fallback
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

  async function testScraping() {
  console.log('🧪 Starting scraping test...');
  console.log(`Using API endpoint: ${API_BASE_URL}`);

  try {
    // Check if API is available
    try {
      console.log('🔍 Checking if API server is running...');
      await fetch(`${API_BASE_URL}/health`, { timeout: 5000 });
    } catch (connectionError) {
      console.error('❌ API server is not running. Please start the backend server first.');
      console.error(`Error: ${connectionError.message}`);
      console.log('\nTry running the backend server with:');
      console.log('  cd backend && python -m app.main');
      return false;
    }

    // First, get or create a test project
    console.log('📋 Fetching projects...');
    const projectsResponse = await fetch(`${API_BASE_URL}/api/v1/projects`);
    let projects = await projectsResponse.json();
    console.log('Projects:', projects);
    
    let testProject;
    if (projects.length === 0) {
      console.log('🆕 Creating test project...');
      const createResponse = await fetch(`${API_BASE_URL}/api/v1/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Test Scraping Debug',
          initial_urls: ['https://example.com']
        })
      });
      testProject = await createResponse.json();
      console.log('Created project:', testProject);
    } else {
      testProject = projects[0];
      console.log('Using existing project:', testProject);
    }
    
    // Test scraping
    console.log('🕷️ Testing scraping...');
    const scrapeResponse = await fetch(`${API_BASE_URL}/api/v1/scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: testProject.id,
        urls: ['https://example.com'],
        max_depth: 1,
        strategy: 'basic'
      })
    });
    
    console.log('Scrape response status:', scrapeResponse.status);
    const scrapeResult = await scrapeResponse.json();
    console.log('Scrape result:', JSON.stringify(scrapeResult, null, 2));
    
    // Check if session was created
    console.log('📊 Checking scraping sessions...');
    const sessionsResponse = await fetch(`${API_BASE_URL}/api/v1/projects/${testProject.id}/scraping-sessions`);
    const sessions = await sessionsResponse.json();
    console.log('Sessions:', JSON.stringify(sessions, null, 2));
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test
testScraping();
