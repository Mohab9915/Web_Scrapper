"""
Models for web page caching.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class WebCacheEntry(BaseModel):
    """
    Model for a cached web page.
    """
    url: str
    content: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    cache_hit_count: int = 0
    
class WebCacheStats(BaseModel):
    """
    Statistics for web page cache.
    """
    total_entries: int
    hit_count: int
    miss_count: int
    hit_rate: float  # hit_count / (hit_count + miss_count)
