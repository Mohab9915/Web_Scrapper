"""
Test script for the scraping service.
This script tests the scraping functionality with mock database connections.
"""
import asyncio
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.append('/home/mohab/Downloads/studio-master_backup/studio-master/backend')

# Mock the database connection
class MockSupabase:
    def __init__(self):
        self.data = {}
    
    def table(self, table_name):
        return MockTable(self, table_name)

class MockTable:
    def __init__(self, supabase, table_name):
        self.supabase = supabase
        self.table_name = table_name
        self.conditions = {}
    
    def select(self, *args, **kwargs):
        return self
    
    def eq(self, field, value):
        self.conditions[field] = value
        return self
    
    def execute(self):
        # Return empty data for simplicity
        return MagicMock(data=[], count=0)
    
    def insert(self, data):
        return self
    
    def update(self, data):
        return self

# Set up mock environment variables
os.environ['SUPABASE_URL'] = 'https://example.supabase.co'
os.environ['SUPABASE_KEY'] = 'mock_key'

# Now import the modules
# from app.utils.crawl4ai_crawler import scrape_url, extract_structured_data # Commented out due to deletion
from app.services.scraping_service import ScrapingService

async def test_scrape_url():
    """Test the scrape_url function."""
    print("\n=== Testing scrape_url function ===")
    test_url = "https://www.example.com"
    
    try:
        # Patch the supabase client
        with patch('app.utils.crawl4ai_crawler.supabase', MockSupabase()):
            # Call the scrape_url function
            result = await scrape_url(test_url)
            
            print(f"Scraping successful!")
            print(f"Title: {result['metadata']['title']}")
            print(f"Markdown content length: {len(result.get('markdown', ''))}")
            print(f"Markdown content preview: {result.get('markdown', '')[:100]}...")
            
            return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

async def test_extract_structured_data():
    """Test the extract_structured_data function."""
    print("\n=== Testing extract_structured_data function ===")
    test_url = "https://www.example.com"
    
    try:
        # Patch the supabase client
        with patch('app.utils.crawl4ai_crawler.supabase', MockSupabase()):
            # Call the extract_structured_data function
            prompt = """
            Extract the title and main content from this webpage.
            Return the data as a JSON object with 'title' and 'content' fields.
            """
            
            result = await extract_structured_data(test_url, prompt=prompt)
            
            print(f"Extraction successful!")
            print(f"Title: {result['metadata']['title']}")
            print(f"Extracted data: {json.dumps(result['json'], indent=2)}")
            
            return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

async def test_scraping_service():
    """Test the ScrapingService class."""
    print("\n=== Testing ScrapingService class ===")
    
    try:
        # Patch the supabase client
        with patch('app.database.supabase', MockSupabase()), \
             patch('app.services.scraping_service.supabase', MockSupabase()):
            
            # Create a ScrapingService instance
            service = ScrapingService()
            
            # Mock the necessary dependencies
            background_tasks = MagicMock()
            
            # Call the execute_scrape method
            response = await service.execute_scrape(
                background_tasks=background_tasks,
                project_id="00000000-0000-0000-0000-000000000000",
                url="https://www.example.com",
                conditions="title, content",
                force_refresh=False,
                api_keys={"openai": "mock_key"}
            )
            
            print(f"ScrapingService test completed!")
            print(f"Response: {response}")
            
            return True
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    await test_scrape_url()
    await test_extract_structured_data()
    # Uncomment to test the full service (may require more mocking)
    # await test_scraping_service()

if __name__ == "__main__":
    asyncio.run(main())
