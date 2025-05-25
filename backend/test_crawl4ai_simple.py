"""
Simple test script for crawl4ai integration.
This script tests the basic functionality of the crawl4ai crawler.
"""
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

async def test_scrape():
    """Test basic scraping functionality."""
    print("\n=== Testing basic scraping ===")
    test_url = "https://www.example.com"
    
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
            cache_mode=CacheMode.ENABLED,
            word_count_threshold=1,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
            )
        )
        
        # Initialize the crawler
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Fetch the page
            result = await crawler.arun(test_url, config=crawler_config)
            
            if not result.success:
                print(f"Error: {result.error_message}")
                return False
            
            # Process the results
            content = {}
            
            if hasattr(result, "html"):
                content["html"] = result.html
            
            if hasattr(result, "markdown"):
                if hasattr(result.markdown, "raw_markdown"):
                    content["markdown"] = result.markdown.raw_markdown
                elif isinstance(result.markdown, str):
                    content["markdown"] = result.markdown
            
            # Get metadata
            page_title = result.title if hasattr(result, "title") else "Untitled Page"
            
            # Add metadata
            content["metadata"] = {
                "title": page_title,
                "url": test_url
            }
            
            print(f"Scraping successful!")
            print(f"Title: {content['metadata']['title']}")
            print(f"Markdown content length: {len(content.get('markdown', ''))}")
            print(f"Markdown content preview: {content.get('markdown', '')[:100]}...")
            
            return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_scrape())