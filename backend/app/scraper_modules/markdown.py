# markdown.py

import asyncio
from typing import List
from ..database import supabase # Import supabase client from the main app's database module
from .utils import generate_unique_name
from crawl4ai import AsyncWebCrawler, BrowserConfig


async def get_fit_markdown_async(url: str) -> str:
    """
    Async function using crawl4ai's AsyncWebCrawler to produce the regular raw markdown.
    (Reverting from the 'fit' approach back to normal.)
    """
    
    # Configure browser without unsupported timeout arguments
    config = BrowserConfig(
        headless=True,
        extra_args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--single-process",
            "--disable-gpu"
        ]
    )

    try:
        async with AsyncWebCrawler(config=config) as crawler:
            # Use longer timeout for scraping operations
            result = await crawler.arun(
                url=url,
                page_timeout=300000,  # 5 minutes page timeout
                delay_before_return_html=3.0  # Wait 3 seconds for dynamic content
            )
            if result.success:
                return result.markdown
            else:
                # Optionally, log this error to a file or logging service
                return ""
    except Exception as e:
        # Optionally, log this error to a file or logging service
        return ""


def fetch_fit_markdown(url: str) -> str:
    """
    Synchronous wrapper around get_fit_markdown_async().
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_fit_markdown_async(url))
    finally:
        loop.close()

def read_raw_data(unique_name: str) -> str:
    """
    Query the 'markdowns' table for the row with this unique_name,
    and return the 'markdown' field.
    """
    response = supabase.table("markdowns").select("markdown").eq("unique_name", unique_name).execute() # Changed table and column
    data = response.data
    if data and len(data) > 0:
        return data[0]["markdown"] # Changed column
    return ""

def save_raw_data(unique_name: str, url: str, raw_data: str) -> None:
    """
    Save or update the row in supabase with unique_name, url, and markdown.
    If a row with unique_name doesn't exist, it inserts; otherwise it might upsert.
    """
    # The 'markdowns' table has unique_name as primary key.
    # Upsert on unique_name.
    supabase.table("markdowns").upsert({ # Changed table
        "unique_name": unique_name,
        "url": url,
        "markdown": raw_data # Changed column name to match 'markdowns' table
    }, on_conflict="unique_name").execute() # Conflict on primary key unique_name
    # Optionally, log this information

async def fetch_and_store_markdowns(urls: List[str]) -> List[str]: # Changed to async
    """
    For each URL:
      1) Generate unique_name
      2) Check if there's already a row in supabase with that unique_name
      3) If not found or if raw_data is empty, fetch fit_markdown
      4) Save to supabase
    Return a list of unique_names (one per URL).
    """
    unique_names = []

    for url in urls:
        unique_name = generate_unique_name(url)
        # check if we already have raw_data in supabase
        # read_raw_data is synchronous, needs to be called carefully in async context
        # For Supabase client, if it's synchronous, it might block.
        # Assuming supabase client calls are synchronous for now.
        # If supabase client is async, read_raw_data should be async too.
        # For now, let's assume read_raw_data and save_raw_data are quick enough or will be made async later if they block.
        raw_data = read_raw_data(unique_name) # This is sync
        if raw_data:
            pass # Optionally, log that existing data was found
        else:
            # fetch fit markdown
            fit_md = await get_fit_markdown_async(url) # Changed to await async version
            # Optionally, log the fetched markdown if needed for debugging, but not in production
            save_raw_data(unique_name, url, fit_md) # This is sync
        unique_names.append(unique_name)

    return unique_names
