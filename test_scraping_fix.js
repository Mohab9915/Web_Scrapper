// Test script to verify the scraping functionality and debugging logs
const BASE_URL = 'http://localhost:8000';

async function testScrapingFlow() {
    console.log('🔍 Testing scraping flow with debugging...');
    
    try {
        // 1. Test backend health
        console.log('\n1️⃣ Testing backend health...');
        const healthResponse = await fetch(`${BASE_URL}/health`);
        console.log('Health status:', healthResponse.status);
        
        // 2. Get projects
        console.log('\n2️⃣ Fetching projects...');
        const projectsResponse = await fetch(`${BASE_URL}/api/v1/projects`);
        const projects = await projectsResponse.json();
        console.log('Projects found:', projects.length);
        
        if (projects.length === 0) {
            console.log('❌ No projects found. Creating a test project...');
            
            // Create a test project
            const createResponse = await fetch(`${BASE_URL}/api/v1/projects`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: 'Test Scraping Project',
                    initial_urls: ['https://example.com']
                })
            });
            
            if (!createResponse.ok) {
                throw new Error(`Failed to create project: ${createResponse.status}`);
            }
            
            const newProject = await createResponse.json();
            console.log('✅ Created test project:', newProject.id);
            
            // Test scraping with the new project
            console.log('\n3️⃣ Testing scraping...');
            const scrapeResponse = await fetch(`${BASE_URL}/api/v1/scrape`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: newProject.id,
                    urls: ['https://example.com'],
                    ai_model: 'gpt-4o-mini'
                })
            });
            
            if (!scrapeResponse.ok) {
                throw new Error(`Scraping failed: ${scrapeResponse.status}`);
            }
            
            const scrapeResult = await scrapeResponse.json();
            console.log('✅ Scraping completed:', scrapeResult);
            
        } else {
            console.log('✅ Found existing projects, testing with first project...');
            const firstProject = projects[0];
            
            // Test scraping with existing project
            console.log('\n3️⃣ Testing scraping...');
            const scrapeResponse = await fetch(`${BASE_URL}/api/v1/scrape`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: firstProject.id,
                    urls: ['https://example.com'],
                    ai_model: 'gpt-4o-mini'
                })
            });
            
            if (!scrapeResponse.ok) {
                throw new Error(`Scraping failed: ${scrapeResponse.status}`);
            }
            
            const scrapeResult = await scrapeResponse.json();
            console.log('✅ Scraping completed:', scrapeResult);
        }
        
        console.log('\n🎉 All tests passed! Backend is working correctly.');
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

// Run the test
testScrapingFlow();
