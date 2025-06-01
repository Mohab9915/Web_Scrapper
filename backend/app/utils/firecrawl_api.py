"""
Utility functions for Firecrawl API integration.
"""
import os
import httpx
import json
import asyncio
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import HTTPException

from ..database import supabase
from ..config import settings
from .logging_utils import ( # logging_utils is in the same 'utils' directory
    get_correlation_id,
    log_firecrawl_request,
    log_firecrawl_response,
    log_firecrawl_error
)

# Load environment variables
load_dotenv()

# Firecrawl API configuration
FIRECRAWL_API_KEY = "fc-48fd12dae3e2494abf33101d4b9474d0"  # Hardcoded for now to ensure it's correct
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1"

# Print the API key to verify it's loaded correctly (will be removed in production)
print(f"Using Firecrawl API Key: {FIRECRAWL_API_KEY}")

# Azure OpenAI model configuration
AZURE_EMBEDDING_MODEL = "text-embedding-ada-002"
AZURE_CHAT_MODEL = "model-router"  # Default, can be overridden by deployment_name in requests

# Cache statistics
CACHE_STATS = {
    "hit_count": 0,
    "miss_count": 0
}

async def get_cache_entry(url: str) -> Optional[Dict[str, Any]]:
    """
    Get a cached web page entry if it exists and is not expired.

    Args:
        url (str): URL to check in cache

    Returns:
        Optional[Dict[str, Any]]: Cached entry or None if not found or expired
    """
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
    Scrape a URL using the Firecrawl API with caching.

    Args:
        url (str): URL to scrape
        formats (List[str]): Output formats (default: ["markdown"])
        force_refresh (bool): Force refresh the cache (default: False)

    Returns:
        Dict[str, Any]: Scraped data

    Raises:
        HTTPException: If the API request fails
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
                response_size=len(cache_entry["content"]),
                cache_hit=True,
                additional_info={"formats": formats}
            )
            # Return cached content
            return json.loads(cache_entry["content"])

    # Cache miss or force refresh, update stats
    CACHE_STATS["miss_count"] += 1

    if not FIRECRAWL_API_KEY:
        log_firecrawl_error(
            correlation_id=correlation_id,
            url=url,
            error_type="configuration_error",
            error_message="Firecrawl API key not configured"
        )
        raise HTTPException(status_code=500, detail="Firecrawl API key not configured")

    # Prepare the request payload
    payload = {
        "url": url,
        "formats": formats,
        "onlyMainContent": True,  # Focus on the main content of the page
        "removeBase64Images": True,  # Remove base64 encoded images to reduce size
        "blockAds": True,  # Block ads for cleaner content
    }

    # Log the request
    log_firecrawl_request(
        correlation_id=correlation_id,
        url=url,
        method="POST",
        payload={
            "url": url,
            "formats": formats,
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer [REDACTED]"
            }
        },
        additional_info={"force_refresh": force_refresh}
    )

    try:
        # Make the API request with retry logic for rate limiting
        max_retries = 3
        retry_delay = 1  # Initial delay in seconds

        for attempt in range(max_retries):
            start_time = time.time()
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout to 120 seconds
                    response = await client.post(
                        f"{FIRECRAWL_API_URL}/scrape",
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {FIRECRAWL_API_KEY}"
                        }
                    )

                response_time = time.time() - start_time

                # Handle different status codes
                if response.status_code == 200:
                    # Success, break the retry loop
                    break
                elif response.status_code == 429:
                    # Rate limiting, implement exponential backoff
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        log_firecrawl_error(
                            correlation_id=correlation_id,
                            url=url,
                            error_type="rate_limit",
                            error_message=f"Rate limit exceeded, retrying in {wait_time} seconds...",
                            additional_info={"attempt": attempt + 1, "max_retries": max_retries}
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        log_firecrawl_error(
                            correlation_id=correlation_id,
                            url=url,
                            error_type="rate_limit_max_retries",
                            error_message="Rate limit exceeded after maximum retries"
                        )
                        raise HTTPException(
                            status_code=429,
                            detail="Firecrawl API rate limit exceeded after multiple retries"
                        )
                elif response.status_code == 402:
                    log_firecrawl_error(
                        correlation_id=correlation_id,
                        url=url,
                        error_type="payment_required",
                        error_message="Payment required"
                    )
                    raise HTTPException(status_code=402, detail="Firecrawl API payment required")
                elif response.status_code == 401 or response.status_code == 403:
                    log_firecrawl_error(
                        correlation_id=correlation_id,
                        url=url,
                        error_type="authentication_error",
                        error_message="Authentication failed"
                    )
                    raise HTTPException(status_code=response.status_code, detail="Firecrawl API authentication failed")
                else:
                    log_firecrawl_error(
                        correlation_id=correlation_id,
                        url=url,
                        error_type="api_error",
                        error_message=f"API error: {response.text}",
                        additional_info={"status_code": response.status_code}
                    )
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Firecrawl API error: {response.text}"
                    )
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    log_firecrawl_error(
                        correlation_id=correlation_id,
                        url=url,
                        error_type="connection_error",
                        error_message=f"Connection error: {str(e)}",
                        additional_info={"attempt": attempt + 1, "max_retries": max_retries}
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    log_firecrawl_error(
                        correlation_id=correlation_id,
                        url=url,
                        error_type="connection_error_max_retries",
                        error_message=f"Connection error after maximum retries: {str(e)}"
                    )
                    raise HTTPException(status_code=500, detail=f"Error connecting to Firecrawl API: {str(e)}")
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    log_firecrawl_error(
                        correlation_id=correlation_id,
                        url=url,
                        error_type="timeout",
                        error_message=f"Timeout error, retrying in {wait_time} seconds...",
                        additional_info={"attempt": attempt + 1, "max_retries": max_retries}
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    log_firecrawl_error(
                        correlation_id=correlation_id,
                        url=url,
                        error_type="timeout_max_retries",
                        error_message="Timeout error after maximum retries"
                    )
                    raise HTTPException(status_code=504, detail="Firecrawl API request timed out after multiple retries")

        # Parse the response
        result = response.json()
        response_size = len(response.content)

        if not result.get("success", False):
            error_message = result.get("error", "Unknown error")
            log_firecrawl_error(
                correlation_id=correlation_id,
                url=url,
                error_type="api_success_false",
                error_message=error_message
            )
            raise HTTPException(status_code=500, detail=f"Firecrawl API error: {error_message}")

        # Get the data
        data = result.get("data", {})

        # Log successful response
        log_firecrawl_response(
            correlation_id=correlation_id,
            url=url,
            status_code=response.status_code,
            response_time=response_time,
            response_size=response_size,
            cache_hit=False,
            additional_info={
                "formats": formats,
                "attempt": attempt + 1,
                "data_size": len(json.dumps(data))
            }
        )

        # Save to cache
        await save_to_cache(url, data)

        return data
    except httpx.RequestError as e:
        log_firecrawl_error(
            correlation_id=correlation_id,
            url=url,
            error_type="request_error",
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error connecting to Firecrawl API: {str(e)}")
    except httpx.TimeoutException:
        log_firecrawl_error(
            correlation_id=correlation_id,
            url=url,
            error_type="timeout",
            error_message="Request timed out"
        )
        raise HTTPException(status_code=504, detail="Firecrawl API request timed out")
    except Exception as e:
        if isinstance(e, HTTPException):
            # Already logged and formatted
            raise e

        log_firecrawl_error(
            correlation_id=correlation_id,
            url=url,
            error_type="unexpected_error",
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def extract_structured_data(url: str, schema: Optional[Dict[str, Any]] = None, prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract structured data from a URL using the Firecrawl API.

    Args:
        url (str): URL to scrape
        schema (Optional[Dict[str, Any]]): JSON schema for extraction
        prompt (Optional[str]): Natural language prompt for extraction

    Returns:
        Dict[str, Any]: Extracted structured data

    Raises:
        HTTPException: If the API request fails
    """
    if not FIRECRAWL_API_KEY:
        raise HTTPException(status_code=500, detail="Firecrawl API key not configured")

    # Prepare the request payload
    payload = {
        "url": url,
        "formats": ["json"],
        "onlyMainContent": True,
        "jsonOptions": {}
    }

    # Add schema or prompt to jsonOptions
    if schema:
        payload["jsonOptions"]["schema"] = schema
    elif prompt:
        payload["jsonOptions"]["prompt"] = prompt
    else:
        # Default extraction prompt if neither schema nor prompt is provided
        payload["jsonOptions"]["prompt"] = "Extract the main content and key information from this page."

    try:
        # Make the API request
        async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout to 120 seconds
            response = await client.post(
                f"{FIRECRAWL_API_URL}/scrape",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}"
                }
            )

            # Check for errors
            if response.status_code == 402:
                raise HTTPException(status_code=402, detail="Firecrawl API payment required")
            elif response.status_code == 429:
                raise HTTPException(status_code=429, detail="Firecrawl API rate limit exceeded")
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Firecrawl API error: {response.text}"
                )

            # Parse the response
            result = response.json()

            if not result.get("success", False):
                error_message = result.get("error", "Unknown error")
                raise HTTPException(status_code=500, detail=f"Firecrawl API error: {error_message}")

            data = result.get("data", {})
            return {
                "json": data.get("json", {}),
                "metadata": data.get("metadata", {})
            }
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Firecrawl API: {str(e)}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Firecrawl API request timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
