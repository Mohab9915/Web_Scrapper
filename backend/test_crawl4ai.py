"""
Test script for crawl4ai integration.
This script bypasses database dependencies to test the crawler directly.
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

# In-memory cache for testing
MEMORY_CACHE = {}
CACHE_STATS = {"hit_count": 0, "miss_count": 0}

class Settings:
    WEB_CACHE_EXPIRY_HOURS = 24

settings = Settings()

def get_correlation_id():
    """Generate a simple correlation ID for logging."""
    import time
    return f"test-{int(time.time())}"

def log_message(message: str):
    """Simple logging function."""
    print(f"[LOG] {message}")

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
    # Generate correlation ID for this request
    correlation_id = get_correlation_id()
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        log_message(f"Invalid URL format: {url}")
        raise ValueError("Invalid URL format. URL must start with http:// or https://")
    
    # Check cache first if not forcing refresh
    if not force_refresh and url in MEMORY_CACHE:
        cache_entry = MEMORY_CACHE[url]
        expires_at = datetime.fromisoformat(cache_entry["expires_at"])
        if expires_at > datetime.now(timezone.utc):
            log_message(f"Cache hit for URL: {url}")
            CACHE_STATS["hit_count"] += 1
            return json.loads(cache_entry["content"]) if isinstance(cache_entry["content"], str) else cache_entry["content"]
    
    # Cache miss or force refresh
    CACHE_STATS["miss_count"] += 1
    log_message(f"Scraping URL: {url} (force_refresh={force_refresh})")
    
    try:
        import time
        start_time = time.time()
        
        # Configure browser options
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True,  # Enable JavaScript for dynamic sites
            text_mode=True,           # Disable images for faster crawling
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Configure crawler options
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS if force_refresh else CacheMode.ENABLED,
            word_count_threshold=1,  # Include all content regardless of word count
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
                log_message(f"Error crawling page: {error_message}")
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
            
            response_time = time.time() - start_time
            log_message(f"Scraping completed in {response_time:.2f} seconds")
            
            # Save to cache
            expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.WEB_CACHE_EXPIRY_HOURS)
            MEMORY_CACHE[url] = {
                "url": url,
                "content": json.dumps(content),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires_at.isoformat(),
                "cache_hit_count": 0
            }
            
            return content
    except Exception as e:
        log_message(f"Error crawling page: {str(e)}")
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
            # For country data, use a specific prompt
            from crawl4ai.extraction_strategy import LLMExtractionStrategy
            from crawl4ai import LLMConfig
            
            # Configure LLM options
            llm_provider = os.environ.get("CRAWL4AI_LLM_PROVIDER", "openai/gpt-4o")
            llm_config = LLMConfig(provider=llm_provider)
            
            # Create a default prompt for extracting country data
            default_prompt = """
            Extract a list of countries and their capitals from the webpage content.
            Return the data as a JSON array where each object has 'name' and 'capital' fields.
            Example:
            [
                {"name": "United States", "capital": "Washington, D.C."},
                {"name": "Canada", "capital": "Ottawa"},
                ...
            ]
            """
            
            # Create extraction strategy with default prompt
            crawler_config.extraction_strategy = LLMExtractionStrategy(
                llm_config=llm_config,
                schema=None,
                extraction_type="prompt",
                instruction=default_prompt,
                extra_args={"temperature": 0, "top_p": 0.9, "max_tokens": 2000}
            )
        
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
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

async def test_caching():
    """Test caching functionality."""
    print("\n=== Testing caching ===")
    test_url = "https://www.example.com"
    try:
        print("First request (should use cache if previously scraped):")
        start_time = asyncio.get_event_loop().time()
        result = await scrape_url(test_url)
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"Request completed in {elapsed:.2f} seconds")
        
        print("\nSecond request with force_refresh=True (should bypass cache):")
        start_time = asyncio.get_event_loop().time()
        result = await scrape_url(test_url, force_refresh=True)
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"Request completed in {elapsed:.2f} seconds")
        
        print(f"\nCache stats: {CACHE_STATS}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

async def test_structured_data():
    """Test structured data extraction."""
    print("\n=== Testing structured data extraction ===")
    try:
        # Use a URL that has country data
        countries_url = "https://www.worldometers.info/geography/alphabetical-list-of-countries/"
        
        # Custom prompt for extraction
        prompt = """
        Extract a list of countries from the webpage.
        For each country, extract:
        - name: The name of the country
        - population: The population of the country (if available)
        
        Return the data as a JSON array of objects.
        """
        
        result = await extract_structured_data(countries_url, prompt)
        
        print(f"Extraction successful!")
        print(f"Title: {result['metadata']['title']}")
        
        # Print the first few items
        if "json" in result and isinstance(result["json"], list):
            print(f"Extracted {len(result['json'])} items")
            print("First 3 items:")
            for i, item in enumerate(result["json"][:3]):
                print(f"  {i+1}. {item}")
        else:
            print("No structured data extracted or data is not in expected format")
            print(f"Result: {result}")
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
    
    await test_caching()
    
    # Wait a bit between tests
    await asyncio.sleep(2)
    
    await test_structured_data()

if __name__ == "__main__":
    asyncio.run(main())