"""
API endpoints for web cache management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..utils.firecrawl_api import get_cache_stats
from ..models.web_cache import WebCacheStats

router = APIRouter(tags=["cache"])

@router.get("/cache/stats", response_model=WebCacheStats)
async def get_web_cache_stats():
    """
    Get web cache statistics.
    
    Returns:
        WebCacheStats: Cache statistics
    """
    stats = await get_cache_stats()
    return WebCacheStats(
        total_entries=stats["total_entries"],
        hit_count=stats["hit_count"],
        miss_count=stats["miss_count"],
        hit_rate=stats["hit_rate"]
    )
