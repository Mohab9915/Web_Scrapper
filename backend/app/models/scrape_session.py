"""
Scrape session models for request/response validation.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class ScrapedSessionBase(BaseModel):
    """Base model for scraped session data."""
    url: HttpUrl

class ScrapedSessionCreate(ScrapedSessionBase):
    """Model for creating a new scraped session."""
    project_id: UUID
    session_id: str

class ScrapedSessionResponse(ScrapedSessionBase):
    """Model for scraped session response."""
    id: UUID
    project_id: UUID
    scraped_at: Optional[datetime] = None # Made Optional to handle potential NULLs from DB
    status: str  # 'Scraped', 'Embedded for RAG', 'Error'
    markdown_content: Optional[str] = Field(default=None, alias="raw_markdown") # Aliased from raw_markdown
    structured_data: Optional[Dict[str, Any]] = None
    download_link_json: Optional[str] = None
    download_link_csv: Optional[str] = None
    display_format: Optional[str] = "table"  # Display format: 'table', 'paragraph', or 'raw'
    tabular_data: Optional[List[Dict[str, Any]]] = None  # Structured data in tabular format
    fields: Optional[List[str]] = None  # List of fields extracted
    formatted_tabular_data: Optional[Dict[str, Any]] = None  # Data formatted according to display_format

    class Config:
        from_attributes = True

class ProjectUrlWithSessionResponse(BaseModel):
    """Model for project URL with its latest scrape session data."""
    # Project URL fields
    id: UUID
    project_id: UUID
    url: HttpUrl
    conditions: Optional[str] = None
    display_format: Optional[str] = "table"
    created_at: Optional[datetime] = None
    status: Optional[str] = "pending"
    rag_enabled: Optional[bool] = False
    last_scraped_session_id: Optional[UUID] = None

    # Latest scrape session data
    latest_scrape_data: Optional[ScrapedSessionResponse] = None

    class Config:
        from_attributes = True


class InteractiveScrapingInitiate(BaseModel):
    """Model for initiating interactive scraping."""
    initial_url: HttpUrl

class InteractiveScrapingResponse(BaseModel):
    """Model for interactive scraping response."""
    interactive_target_url: HttpUrl
    session_id: str

class ExecuteScrapeRequest(BaseModel):
    """Model for executing scraping request."""
    current_page_url: str  # Changed from HttpUrl to str to avoid serialization issues
    session_id: str
    api_keys: Optional[Dict[str, str]] = None  # Should contain 'api_key' and 'endpoint' for Azure OpenAI
    force_refresh: Optional[bool] = False  # Whether to bypass cache and fetch fresh content
    display_format: Optional[str] = "table"  # Display format: 'table', 'paragraph', or 'raw'
    conditions: Optional[str] = None  # Comma-separated list of fields to extract

class ExecuteScrapeResponse(BaseModel):
    """Model for executing scraping response."""
    status: str
    message: str
    download_links: Optional[Dict[str, str]] = None
    rag_status: Optional[str] = None
    embedding_cost_if_any: Optional[float] = None
    tabular_data: Optional[List[Dict[str, Any]]] = None  # Structured data in tabular format
    fields: Optional[List[str]] = None  # List of fields extracted
    display_format: Optional[str] = "table"  # Display format used: 'table', 'paragraph', or 'raw'
    formatted_data: Optional[Dict[str, Any]] = None  # Data formatted according to display_format
