"""Simple direct scraping test that doesn't rely on the full backend integration."""

import asyncio
import requests
import json
from datetime import datetime

# Configuration
API_URL = 'http://localhost:8000/api/v1'
TEST_URL = 'https://example.com'

async def test_direct_scrape():
    """Test direct scraping functionality without complex dependencies."""
    print("\n=== Testing Direct Scraping ===\n")

    try:
        # Simple health check - most FastAPI apps have a root path that returns something
        print("1. Checking API availability...")
        response = requests.get(API_URL)
        print(f"   API check status: {response.status_code}")

        # Consider any response as success - we just want to verify the server is running
        if response.status_code >= 500:
            print("   API check failed with server error. Check if the server is running.")
            return False

        # Simple scraping test
        print("\n2. Testing basic scraping...")
        response = requests.post(
            f"{API_URL}/scrape-url",
            json={"url": TEST_URL}
        )

        if response.status_code == 200:
            result = response.json()
            print("   Scraping successful!")
            print(f"   Content length: {len(str(result))}")
            return True
        else:
            print(f"   Scraping failed with status code: {response.status_code}")
            try:
                print(f"   Error: {response.json()}")
            except:
                print(f"   Error response: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"Error in direct scrape test: {str(e)}")
        return False

def create_test_project():
    """Create a test project for scraping."""
    try:
        project_name = f"Test Direct Scrape {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        response = requests.post(
            f"{API_URL}/projects",
            json={"name": project_name, "initial_urls": [TEST_URL]}
        )

        if response.status_code == 200:
            project_data = response.json()
            print(f"Project created: {project_data['id']} - {project_data['name']}")
            return project_data['id']
        else:
            print(f"Failed to create project: {response.text}")
            return None
    except Exception as e:
        print(f"Error creating project: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(test_direct_scrape())
