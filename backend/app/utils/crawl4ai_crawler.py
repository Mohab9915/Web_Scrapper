"""
Utility functions for web scraping using the crawl4ai framework.
"""
import json
import asyncio
import time
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

# Import crawl4ai framework classes
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter
except ImportError:
    raise ImportError("crawl4ai framework is not installed. Install it with 'pip install crawl4ai'")

# Import database conditionally to allow standalone testing
try:
    from app.database import supabase
    from app.config import settings
    from app.utils.logging_utils import (
        get_correlation_id,
        log_firecrawl_request,
        log_firecrawl_response,
        log_firecrawl_error
    )
    DATABASE_AVAILABLE = True
except ImportError:
    print("Warning: Database modules not available. Running in standalone mode.")
    DATABASE_AVAILABLE = False
    
    # Define fallback functions and settings when database is not available
    def get_correlation_id():
        return f"local-{int(time.time())}"
    
    def log_firecrawl_request(*args, **kwargs):
        print(f"[LOG] Firecrawl request: {kwargs}")
    
    def log_firecrawl_response(*args, **kwargs):
        print(f"[LOG] Firecrawl response: {kwargs}")
    
    def log_firecrawl_error(*args, **kwargs):
        print(f"[LOG] Firecrawl error: {kwargs}")
    
    # Fallback settings
    class Settings:
        WEB_CACHE_EXPIRY_HOURS = 24
    
    settings = Settings()

# Cache statistics
CACHE_STATS = {
    "hit_count": 0,
    "miss_count": 0
}

# Azure OpenAI model configuration
AZURE_EMBEDDING_MODEL = "text-embedding-ada-002"
AZURE_CHAT_MODEL = "gpt-4o-mini"  # Default, can be overridden by deployment_name in requests

# Reusing the cache functions
# In-memory cache for standalone mode
MEMORY_CACHE = {}

async def get_cache_entry(url: str) -> Optional[Dict[str, Any]]:
    """
    Get a cached web page entry if it exists and is not expired.

    Args:
        url (str): URL to check in cache

    Returns:
        Optional[Dict[str, Any]]: Cached entry or None if not found or expired
    """
    if not DATABASE_AVAILABLE:
        # Use in-memory cache when database is not available
        if url not in MEMORY_CACHE:
            return None
            
        cache_entry = MEMORY_CACHE[url]
        
        # Check if the entry is expired
        expires_at = datetime.fromisoformat(cache_entry["expires_at"].replace("Z", "+00:00") if "Z" in cache_entry["expires_at"] else cache_entry["expires_at"])
        if expires_at < datetime.now(timezone.utc):
            # Entry is expired, return None
            return None
            
        # Update hit count
        cache_entry["cache_hit_count"] += 1
        
        # Update global stats
        CACHE_STATS["hit_count"] += 1
        
        return cache_entry
    else:
        try:
            # Query the web_cache table for the URL
            response = supabase.table("web_cache").select("*").eq("url", url).execute()

            if not response.data:
                return None

            cache_entry = response.data[0]

            # Check if the entry is expired
            expires_at = datetime.fromisoformat(cache_entry["expires_at"].replace("Z", "+00:00"))
            if expires_at < datetime.now(timezone.utc):
                # Entry is expired, return None
                return None

            # Update hit count
            supabase.table("web_cache").update({"cache_hit_count": cache_entry["cache_hit_count"] + 1}).eq("url", url).execute()

            # Update global stats
            CACHE_STATS["hit_count"] += 1

            return cache_entry
        except Exception as e:
            print(f"Error checking cache: {e}")
            return None

async def save_to_cache(url: str, content: Dict[str, Any]) -> bool:
    """
    Save a web page to the cache.

    Args:
        url (str): URL of the page
        content (Dict[str, Any]): Content to cache

    Returns:
        bool: True if successful, False otherwise
    """
    if not DATABASE_AVAILABLE:
        try:
            # Calculate expiration time
            expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.WEB_CACHE_EXPIRY_HOURS)
            
            # Create or update cache entry
            MEMORY_CACHE[url] = {
                "url": url,
                "content": json.dumps(content),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires_at.isoformat(),
                "cache_hit_count": 0
            }
            
            return True
        except Exception as e:
            print(f"Error saving to in-memory cache: {e}")
            return False
    else:
        try:
            # Calculate expiration time
            expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.WEB_CACHE_EXPIRY_HOURS)

            # Check if entry already exists
            response = supabase.table("web_cache").select("*").eq("url", url).execute()

            if response.data:
                # Update existing entry
                supabase.table("web_cache").update({
                    "content": json.dumps(content),
                    "expires_at": expires_at.isoformat(),
                    "cache_hit_count": 0  # Reset hit count for fresh content
                }).eq("url", url).execute()
            else:
                # Insert new entry
                supabase.table("web_cache").insert({
                    "url": url,
                    "content": json.dumps(content),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "expires_at": expires_at.isoformat(),
                    "cache_hit_count": 0
                }).execute()

            return True
        except Exception as e:
            print(f"Error saving to cache: {e}")
            return False

async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dict[str, Any]: Cache statistics
    """
    if not DATABASE_AVAILABLE:
        # Calculate stats from memory cache
        total_entries = len(MEMORY_CACHE)
        total_requests = CACHE_STATS["hit_count"] + CACHE_STATS["miss_count"]
        hit_rate = CACHE_STATS["hit_count"] / total_requests if total_requests > 0 else 0
        
        return {
            "total_entries": total_entries,
            "hit_count": CACHE_STATS["hit_count"],
            "miss_count": CACHE_STATS["miss_count"],
            "hit_rate": hit_rate
        }
    else:
        try:
            # Get total entries
            response = supabase.table("web_cache").select("count", count="exact").execute()
            total_entries = response.count if response.count is not None else 0

            # Calculate hit rate
            total_requests = CACHE_STATS["hit_count"] + CACHE_STATS["miss_count"]
            hit_rate = CACHE_STATS["hit_count"] / total_requests if total_requests > 0 else 0

            return {
                "total_entries": total_entries,
                "hit_count": CACHE_STATS["hit_count"],
                "miss_count": CACHE_STATS["miss_count"],
                "hit_rate": hit_rate
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {
                "total_entries": 0,
                "hit_count": CACHE_STATS["hit_count"],
                "miss_count": CACHE_STATS["miss_count"],
                "hit_rate": 0
            }

async def scrape_url(url: str, formats: List[str] = ["markdown"], force_refresh: bool = False) -> Dict[str, Any]:
    """
    Scrape a URL using the crawl4ai framework with caching.

    Args:
        url (str): URL to scrape
        formats (List[str]): Output formats (default: ["markdown"])
        force_refresh (bool): Force refresh the cache (default: False)

    Returns:
        Dict[str, Any]: Scraped data

    Raises:
        HTTPException: If the scraping fails
    """
    # Generate correlation ID for this request
    correlation_id = get_correlation_id()

    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        log_firecrawl_error(
            correlation_id=correlation_id,
            url=url,
            error_type="validation_error",
            error_message="Invalid URL format"
        )
        raise HTTPException(status_code=400, detail="Invalid URL format. URL must start with http:// or https://")

    # Check cache first if not forcing refresh
    if not force_refresh:
        cache_entry = await get_cache_entry(url)
        if cache_entry:
            # Log cache hit
            log_firecrawl_response(
                correlation_id=correlation_id,
                url=url,
                status_code=200,
                response_time=0.0,  # No API call made
                response_size=len(cache_entry["content"]) if isinstance(cache_entry["content"], str) else len(json.dumps(cache_entry["content"])),
                cache_hit=True,
                additional_info={"formats": formats}
            )
            # Return cached content
            content = cache_entry["content"]
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # If content is not valid JSON, return it as is
                    return {"markdown": content}
            return content

    # Cache miss or force refresh, update stats
    CACHE_STATS["miss_count"] += 1

    # Log the request
    log_firecrawl_request(
        correlation_id=correlation_id,
        url=url,
        method="crawl4ai",
        payload={
            "url": url,
            "formats": formats,
        },
        additional_info={"force_refresh": force_refresh}
    )

    try:
        start_time = time.time()
        
        # Configure browser options
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True,  # Enable JavaScript for dynamic sites
            text_mode=True,           # Disable images for faster crawling
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            # Removed timeout parameter as it's not supported
        )
        
        # Configure crawler options
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS if force_refresh else CacheMode.ENABLED,
            word_count_threshold=1,  # Include all content regardless of word count
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
            ),
            # Removed max_retries parameter as it's not supported in CrawlerRunConfig
            page_timeout=60000  # Add page timeout (60 seconds) here instead of in BrowserConfig
        )
        
        # Initialize the crawler with retry logic
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    # Fetch the page
                    result = await crawler.arun(url, config=crawler_config)
                    
                    if not result.success:
                        error_message = result.error_message or "Unknown error"
                        log_firecrawl_error(
                            correlation_id=correlation_id,
                            url=url,
                            error_type="crawl_error",
                            error_message=error_message
                        )
                        
                        # If this is the last attempt, raise the exception
                        if attempt == max_attempts - 1:
                            raise HTTPException(status_code=500, detail=f"Error crawling page: {error_message}")
                        else:
                            print(f"Attempt {attempt+1} failed: {error_message}. Retrying...")
                            await asyncio.sleep(1)  # Wait before retrying
                            continue
                    
                    # If we got here, the crawl was successful
                    break
            except Exception as browser_error:
                # Handle browser-specific errors
                print(f"Browser error on attempt {attempt+1}: {str(browser_error)}")
                
                # If this is the last attempt, re-raise the exception
                if attempt == max_attempts - 1:
                    raise
                
                # Otherwise wait and retry
                await asyncio.sleep(1)  # Wait before retrying
        
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
        page_description = ""
        
        # Add metadata
        content["metadata"] = {
            "title": page_title,
            "description": page_description,
            "url": url,
            "crawledAt": datetime.now(timezone.utc).isoformat()
        }
        
        response_time = time.time() - start_time
        response_size = len(json.dumps(content))

        # Log successful response
        log_firecrawl_response(
            correlation_id=correlation_id,
            url=url,
            status_code=200,  # Always 200 for successful crawl
            response_time=response_time,
            response_size=response_size,
            cache_hit=False,
            additional_info={
                "formats": formats,
                "data_size": response_size
            }
        )

        # Save to cache
        await save_to_cache(url, content)

        return content
    except Exception as e:
        log_firecrawl_error(
            correlation_id=correlation_id,
            url=url,
            error_type="crawl_error",
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error crawling page with crawl4ai: {str(e)}")

async def extract_structured_data(url: str, schema: Optional[Dict[str, Any]] = None, prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract structured data from a URL using the crawl4ai framework.

    Args:
        url (str): URL to scrape
        schema (Optional[Dict[str, Any]]): JSON schema for extraction
        prompt (Optional[str]): Natural language prompt for extraction

    Returns:
        Dict[str, Any]: Extracted structured data

    Raises:
        HTTPException: If the extraction fails
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
        
        # Add extraction strategy based on provided schema or prompt
        if schema:
            from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
            crawler_config.extraction_strategy = JsonCssExtractionStrategy(schema)
        elif prompt:
            # Check if we have API keys for LLM extraction
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            azure_api_key = os.environ.get("AZURE_API_KEY")
            
            if openai_api_key or azure_api_key:
                # We have API keys, use LLM extraction
                from crawl4ai.extraction_strategy import LLMExtractionStrategy
                from crawl4ai import LLMConfig
                
                # Configure LLM options (using environment variables for API keys)
                # Default to OpenAI, but can be configured with environment variables
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
                # No API keys, use simple extraction
                print("Warning: No API keys found for LLM extraction. Using simple extraction instead.")
                from crawl4ai.extraction_strategy import ExtractionStrategy
                
                # Create a custom extraction strategy
                class SimpleExtractionStrategy(ExtractionStrategy):
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
                            "note": "This is a fallback extraction because no API keys were found for LLM extraction.",
                            "prompt_used": self.prompt
                        })]
                
                # Use the simple extraction strategy with the prompt
                crawler_config.extraction_strategy = SimpleExtractionStrategy(prompt=prompt)
        else:
            # Default extraction if neither schema nor prompt is provided
            # Use a simple extraction strategy that doesn't require API keys
            from crawl4ai.extraction_strategy import ExtractionStrategy
            
            # Create a custom extraction strategy
            class SimpleExtractionStrategy(ExtractionStrategy):
                def __init__(self):
                    super().__init__()
                
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
                        "content": content
                    })]
            
            # Use the simple extraction strategy
            crawler_config.extraction_strategy = SimpleExtractionStrategy()
        
        # Initialize the crawler and fetch the page
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url, config=crawler_config)
            
            if not result.success:
                raise HTTPException(status_code=500, detail=f"Crawl failed: {result.error_message}")
                
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
        raise HTTPException(status_code=500, detail=f"Error extracting structured data with crawl4ai: {str(e)}")