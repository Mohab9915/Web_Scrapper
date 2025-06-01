"""
Project URL models for request/response validation.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class DisplayFormat(str, Enum):
    """Display format for scraped data."""
    TABLE = "table"
    PARAGRAPH = "paragraph"
    RAW = "raw"

class ScrapeStatus(str, Enum):
    """Status of a scrape session."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSING_RAG = "processing_rag"
    RUNNING = "running"
    COMPLETE = "complete"
    COMPLETED = "completed"  # Added for project_urls table
    FAILED = "failed"
    SCRAPED = "scraped"
    EMBEDDED_FOR_RAG = "embedded for RAG"
    RAG_INGESTED = "rag_ingested"
    ERROR = "error"

class ProjectUrlBase(BaseModel):
    """Base model for project URL data."""
    url: str
    conditions: str
    display_format: DisplayFormat = DisplayFormat.TABLE
    rag_enabled: bool = False

class ProjectUrlCreateRequest(ProjectUrlBase):
    """Model for creating a new project URL via API (without project_id)."""
    pass

class ProjectUrlCreate(ProjectUrlBase):
    """Model for creating a new project URL."""
    project_id: UUID

class ProjectUrlUpdate(BaseModel):
    """Model for updating a project URL."""
    conditions: Optional[str] = None
    display_format: Optional[DisplayFormat] = None
    rag_enabled: Optional[bool] = None

class ProjectUrlResponse(ProjectUrlBase):
    """Model for project URL response."""
    id: UUID
    project_id: UUID
    created_at: datetime
    status: ScrapeStatus = ScrapeStatus.PENDING # Default status
    rag_enabled: bool # rag_enabled is now part of ProjectUrlBase

    class Config:
        from_attributes = True
