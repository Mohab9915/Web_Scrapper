"""
Test script for crawl4ai scraping functionality.
"""
import asyncio
import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

# Import crawl4ai framework classes
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

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

async def main():
    """Main test function."""
    # Test URL
    test_url = "https://www.example.com"
    
    # Test basic scraping
    print("\n=== Testing basic scraping ===")
    try:
        result = await scrape_url(test_url)
        print(f"Scraping successful!")
        print(f"Title: {result['metadata']['title']}")
        print(f"Markdown content length: {len(result.get('markdown', ''))}")
        print(f"Markdown content preview: {result.get('markdown', '')[:100]}...")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())