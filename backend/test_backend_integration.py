"""
Test script for the backend integration.
This script tests the integration with the actual backend code.
"""
import asyncio
import os
import sys
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from unittest.mock import MagicMock

# Set up environment variables for Supabase
os.environ['SUPABASE_URL'] = 'https://slkzwhpfeauezoojlvou.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNsa3p3aHBmZWF1ZXpvb2psdm91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMTQ0NTEsImV4cCI6MjA2Mjc5MDQ1MX0.uLsJt6GijTe_2MJ0Ckoux9wQrp-Kr6mR43wXPrCYYDQ'

# Add the backend directory to the path
sys.path.append('/home/mohab/Downloads/studio-master_backup/studio-master/backend')

# Import the modules
try:
    from app.services.scraping_service import ScrapingService
    from app.utils.crawl4ai_crawler import scrape_url
    from app.database import supabase
    from app.models.project import ProjectCreate
    
    async def create_test_project():
        """Create a test project in the database."""
        print("Creating a test project...")
        
        # Generate a unique project ID
        project_id = str(uuid.uuid4())
        
        # Create the project directly in the database
        data = {
            "id": project_id,
            "name": "Test Project",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "rag_enabled": False
        }
        
        # Insert the project into the database
        result = supabase.table("projects").insert(data).execute()
        
        if len(result.data) > 0:
            print(f"Test project created with ID: {project_id}")
            return project_id
        else:
            print("Failed to create test project")
            return None
    
    async def test_backend_integration():
        """Test the backend integration."""
        print("\n=== Testing backend integration ===")
        test_url = "https://www.example.com"
        
        try:
            # Call the scrape_url function directly
            result = await scrape_url(test_url)
            
            print(f"Direct scraping successful!")
            print(f"Title: {result['metadata']['title']}")
            print(f"Markdown content length: {len(result.get('markdown', ''))}")
            
            # Create a test project
            project_id = await create_test_project()
            if not project_id:
                print("Skipping ScrapingService test due to project creation failure")
                return False
            
            # Create a ScrapingService instance
            service = ScrapingService()
            
            # Mock the necessary dependencies
            background_tasks = MagicMock()
            
            # Call the execute_scrape method
            print("\n=== Testing ScrapingService.execute_scrape ===")
            try:
                # Create an ExecuteScrapeRequest object
                from app.models.scrape_session import ExecuteScrapeRequest
                
                request = ExecuteScrapeRequest(
                    current_page_url=test_url,
                    session_id=str(uuid.uuid4()),
                    api_keys={"openai": "mock_key"},
                    force_refresh=False
                )
                
                response = await service.execute_scrape(
                    background_tasks=background_tasks,
                    project_id=project_id,
                    request=request
                )
                
                print(f"ScrapingService test completed!")
                print(f"Response: {response}")
            except Exception as e:
                print(f"Error in ScrapingService.execute_scrape: {str(e)}")
            
            return True
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    if __name__ == "__main__":
        asyncio.run(test_backend_integration())
except Exception as e:
    print(f"Error importing modules: {str(e)}")