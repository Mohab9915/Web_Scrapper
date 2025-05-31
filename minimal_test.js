/**
 * Minimal test script for scraping functionality
 * This script uses CommonJS modules for better compatibility
 */

const http = require('http');

// Configuration
const API_URL = 'localhost';
const API_PORT = 8000;
const API_PATH = '/api/v1/health';

/**
 * Simple function to make an HTTP GET request
 */
function makeRequest(path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: API_URL,
      port: API_PORT,
      path: path,
      method: 'GET'
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          data: data
        });
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.end();
  });
}

/**
 * Main test function
 */
async function runTest() {
  console.log('🧪 Starting minimal scraping test...');

  try {
    // Check if API is available
    console.log('📋 Checking API health...');
    const healthResponse = await makeRequest(API_PATH);
    console.log(`✅ API health status: ${healthResponse.statusCode}`);
    console.log(`   Response: ${healthResponse.data}`);

    console.log('\n🎉 Minimal test completed successfully!\n');
    return true;
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    return false;
  }
}
/**
 * Minimal test script for scraping functionality
 * This script uses CommonJS modules for better compatibility
 */

const http = require('http');

// Configuration
const API_URL = 'localhost';
const API_PORT = 8000;
const API_PATH = '/api/v1/projects';

/**
 * Simple function to make an HTTP GET request
 */
function makeRequest(path, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: API_URL,
      port: API_PORT,
      path: path,
      method: method
    };

    if (data) {
      options.headers = {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      };
    }

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          data: data
        });
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    if (data) {
      req.write(data);
    }

    req.end();
  });
}

/**
 * Main test function
 */
async function runTest() {
  console.log('🧪 Starting minimal scraping test...');

  try {
    // Get projects
    console.log('📋 Checking for projects...');
    const projectsResponse = await makeRequest(API_PATH);
    console.log(`✅ Projects API status: ${projectsResponse.statusCode}`);

    if (projectsResponse.statusCode === 200) {
      try {
        const projects = JSON.parse(projectsResponse.data);
        console.log(`   Found ${projects.length} projects`);

        // If no projects exist, create one
        if (projects.length === 0) {
          console.log('   Creating a test project...');
          const projectData = JSON.stringify({
            name: `Test Project ${new Date().toISOString()}`,
            initial_urls: ['https://example.com']
          });

          const createResponse = await makeRequest(API_PATH, 'POST', projectData);
          console.log(`   Project creation status: ${createResponse.statusCode}`);

          if (createResponse.statusCode === 200) {
            console.log('   Project created successfully');
          }
        }
      } catch (parseError) {
        console.log(`   Error parsing projects: ${parseError.message}`);
        console.log(`   Raw response: ${projectsResponse.data.substring(0, 100)}...`);
      }
    }

    console.log('\n🎉 Minimal test completed successfully!\n');
    return true;
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    return false;
  }
}

// Run the test
runTest().then(success => {
  if (!success) {
    process.exit(1);
  }
}).catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
});
// Run the test
runTest().then(success => {
  if (!success) {
    process.exit(1);
  }
}).catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
});
