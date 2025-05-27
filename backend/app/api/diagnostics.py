"""
Diagnostic endpoints for system status and troubleshooting.
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

# Import the system resource checker
from ..utils.system_check import check_system_resources

# Create a router
router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

@router.get("/system-resources")
async def get_system_resources() -> Dict[str, Any]:
    """
    Get system resource information.
    
    Returns:
        Dict[str, Any]: System resource information
    """
    return check_system_resources()

@router.get("/browser-check")
async def check_browser_compatibility() -> Dict[str, Any]:
    """
    Check browser compatibility for web scraping.
    
    Returns:
        Dict[str, Any]: Browser compatibility information
    """
    # Import here to avoid circular imports
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig
        
        # Basic configuration for testing browser launch
        # Using compatible parameters for the installed crawl4ai version
        config = BrowserConfig(
            headless=True,
            java_script_enabled=True,
            ignore_https_errors=True,
            extra_args=[               # Browser launch arguments for stability
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # Try to launch the browser
        success = True
        error = None
        browser_info = {}
        
        try:
            # Create async context and immediately close it to test browser launch
            import asyncio
            async def test_browser():
                async with AsyncWebCrawler(config=config) as crawler:
                    browser_info.update(await crawler.get_browser_info())
                    return True
                
            # Run the test
            success = asyncio.run(test_browser())
        except Exception as e:
            success = False
            error = str(e)
        
        # Check system resources
        resources = check_system_resources()
        
        return {
            "browser_launch_success": success,
            "error": error,
            "browser_info": browser_info,
            "system_resources": resources
        }
    except ImportError as e:
        return {
            "browser_launch_success": False,
            "error": f"Crawl4AI not properly installed: {str(e)}",
            "system_resources": check_system_resources()
        }
