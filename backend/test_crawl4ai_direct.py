"""
Direct test script for crawl4ai functionality.
This script tests the crawl4ai functionality directly without relying on the database.
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
        
        # Add extraction strategy based on provided prompt
        if prompt:
            from crawl4ai.extraction_strategy import LLMExtractionStrategy
            from crawl4ai import LLMConfig
            
            # Configure LLM options (using environment variables for API keys)
            llm_provider = os.environ.get("CRAWL4AI_LLM_PROVIDER", "openai/gpt-4o")
            
            # Create LLM config
            llm_config = LLMConfig(provider=llm_provider)
            
            # Create extraction strategy with prompt
            crawler_config.extraction_strategy = LLMExtractionStrategy(
                llm_config=llm_config,
                schema=None,
                extraction_type="prompt",
                instruction=prompt,
                extra_args={"temperature": 0, "top_p": 0.9, "max_tokens": 2000}
            )
        else:
            # Default extraction if no prompt is provided
            from crawl4ai.extraction_strategy import RegexExtractionStrategy
            crawler_config.extraction_strategy = RegexExtractionStrategy()
        
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

async def test_basic_scraping():
    """Test basic scraping functionality."""
    print("\n=== Testing basic scraping ===")
    test_url = "https://www.example.com"
    try:
        result = await scrape_url(test_url)
        print(f"Scraping successful!")
        print(f"Title: {result['metadata']['title']}")
        print(f"Markdown content length: {len(result.get('markdown', ''))}")
        print(f"Markdown content preview: {result.get('markdown', '')[:100]}...")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

async def test_structured_data():
    """Test structured data extraction."""
    print("\n=== Testing structured data extraction ===")
    test_url = "https://www.example.com"
    try:
        # Custom prompt for extraction
        prompt = """
        Extract the title and main content from this webpage.
        Return the data as a JSON object with 'title' and 'content' fields.
        """
        
        result = await extract_structured_data(test_url, prompt)
        
        print(f"Extraction successful!")
        print(f"Title: {result['metadata']['title']}")
        print(f"Extracted data: {json.dumps(result['json'], indent=2)}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

async def main():
    """Main test function."""
    # Run tests one by one
    await test_basic_scraping()
    
    # Wait a bit between tests to ensure browser is properly closed
    await asyncio.sleep(2)
    
    # Run the second test
    await test_structured_data()

if __name__ == "__main__":
    asyncio.run(main())