"""
Direct test script for the scraping functionality.
This script tests the scraping functionality directly without relying on the Settings class.
"""
import asyncio
import os
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Set up environment variables for Supabase
os.environ['SUPABASE_URL'] = 'https://slkzwhpfeauezoojlvou.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNsa3p3aHBmZWF1ZXpvb2psdm91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMTQ0NTEsImV4cCI6MjA2Mjc5MDQ1MX0.uLsJt6GijTe_2MJ0Ckoux9wQrp-Kr6mR43wXPrCYYDQ'

# Import crawl4ai framework classes
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.extraction_strategy import ExtractionStrategy

# Import supabase client
from supabase import create_client

# Create supabase client
supabase = create_client(
    os.environ.get('SUPABASE_URL'),
    os.environ.get('SUPABASE_KEY')
)

async def scrape_url(url: str, formats: List[str] = ["markdown"], force_refresh: bool = False) -> Dict[str, Any]:
    """
    Scrape a URL using the crawl4ai framework.
    
    Args:
        url (str): URL to scrape
        formats (List[str]): Output formats (default: ["markdown"])
        force_refresh (bool): Force refresh the cache (default: False)
        
    Returns:
        Dict[str, Any]: Scraped data
    """
    print(f"Scraping URL: {url} (force_refresh={force_refresh})")
    
    try:
        # Configure browser options
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True,
            text_mode=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Configure crawler options
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS if force_refresh else CacheMode.ENABLED,
            word_count_threshold=1,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
            )
        )
        
        # Initialize the crawler
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Fetch the page
            result = await crawler.arun(url, config=crawler_config)
            
            if not result.success:
                error_message = result.error_message or "Unknown error"
                print(f"Error crawling page: {error_message}")
                raise ValueError(f"Error crawling page: {error_message}")
            
            # Process the results based on requested formats
            content = {}
            
            if "html" in formats or hasattr(result, "html"):
                content["html"] = result.html if hasattr(result, "html") else ""
            
            if "markdown" in formats or not formats:
                # Check if markdown attribute exists and has raw_markdown property
                if hasattr(result, "markdown") and hasattr(result.markdown, "raw_markdown"):
                    content["markdown"] = result.markdown.raw_markdown
                elif hasattr(result, "markdown") and isinstance(result.markdown, str):
                    content["markdown"] = result.markdown
                else:
                    # Fallback to empty string if markdown is not available
                    content["markdown"] = ""
                
            # Get metadata from the page title or crawler results
            page_title = result.title if hasattr(result, "title") else "Untitled Page"
            
            # Add metadata
            content["metadata"] = {
                "title": page_title,
                "description": "",
                "url": url,
                "crawledAt": datetime.now(timezone.utc).isoformat()
            }
            
            return content
    except Exception as e:
        print(f"Error crawling page: {str(e)}")
        raise

async def extract_structured_data(url: str, prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract structured data from a URL using the crawl4ai framework.
    
    Args:
        url (str): URL to scrape
        prompt (Optional[str]): Natural language prompt for extraction
        
    Returns:
        Dict[str, Any]: Extracted structured data
    """
    print(f"Extracting structured data from URL: {url}")
    
    try:
        # Configure browser options
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True,
            text_mode=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        # Configure crawler options
        crawler_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        
        # Use a simple extraction strategy that doesn't require API keys
        # Create a custom extraction strategy
        class MockExtractionStrategy(ExtractionStrategy):
            def __init__(self, prompt=None):
                super().__init__()
                self.prompt = prompt
            
            def extract(self, html, url=None, **kwargs):
                # Simple extraction that returns a JSON string with basic page info
                import re
                
                # Extract title
                title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                title = title_match.group(1) if title_match else "Untitled Page"
                
                # Extract content (simple approach)
                # Remove HTML tags and get text
                content = re.sub(r'<[^>]+>', ' ', html)
                content = re.sub(r'\s+', ' ', content).strip()
                
                # Limit content length
                content = content[:500] + "..." if len(content) > 500 else content
                
                # Return as JSON string in a list
                return [json.dumps({
                    "title": title,
                    "content": content,
                    "prompt_used": self.prompt
                })]
        
        # Use the mock extraction strategy
        crawler_config.extraction_strategy = MockExtractionStrategy(prompt=prompt)
        
        # Initialize the crawler and fetch the page
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url, config=crawler_config)
            
            if not result.success:
                raise ValueError(f"Crawl failed: {result.error_message}")
                
            # Extract the structured data
            structured_data = {}
            if hasattr(result, "extracted_content") and result.extracted_content:
                try:
                    structured_data = json.loads(result.extracted_content)
                except json.JSONDecodeError as e:
                    print(f"Error parsing extracted content: {e}")
                    print(f"Raw content: {result.extracted_content}")
                    # Try to extract JSON from the text if it's not valid JSON
                    import re
                    json_match = re.search(r'\[\s*{.*}\s*\]', result.extracted_content, re.DOTALL)
                    if json_match:
                        try:
                            structured_data = json.loads(json_match.group(0))
                        except json.JSONDecodeError:
                            # If still can't parse, return the raw content
                            structured_data = {"raw": result.extracted_content}
                    else:
                        structured_data = {"raw": result.extracted_content}
            
            # Get page metadata
            metadata = {
                "title": result.title if hasattr(result, "title") else "Untitled Page",
                "url": url,
                "crawledAt": datetime.now(timezone.utc).isoformat()
            }
            
            # Format the response
            response = {
                "json": structured_data,
                "metadata": metadata
            }
            
            # Add tabular data for compatibility with the existing code
            if isinstance(structured_data, list):
                response["tabular_data"] = structured_data
            
            return response
    except Exception as e:
        print(f"Error extracting structured data: {str(e)}")
        raise

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