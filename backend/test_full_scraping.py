"""
Full test script for the scraping functionality.
This script tests the scraping functionality with the actual database connection.
"""
import asyncio
import os
import sys
import json
from uuid import uuid4
from datetime import datetime

# Set up environment variables for Supabase
os.environ['SUPABASE_URL'] = 'https://slkzwhpfeauezoojlvou.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNsa3p3aHBmZWF1ZXpvb2psdm91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMTQ0NTEsImV4cCI6MjA2Mjc5MDQ1MX0.uLsJt6GijTe_2MJ0Ckoux9wQrp-Kr6mR43wXPrCYYDQ'

# Add the backend directory to the path
sys.path.append('/home/mohab/Downloads/studio-master_backup/studio-master/backend')

# Import the modules
# from app.utils.crawl4ai_crawler import scrape_url, extract_structured_data # Commented out due to deletion

async def test_scrape_url():
    """Test the scrape_url function."""
    print("\n=== Testing scrape_url function ===")
    test_url = "https://www.example.com"
    
    try:
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

async def main():
    """Run all tests."""
    await test_scrape_url()
    
    # Wait a bit between tests
    await asyncio.sleep(2)
    
    await test_extract_structured_data()

if __name__ == "__main__":
    asyncio.run(main())
