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

class ProjectUrlBase(BaseModel):
    """Base model for project URL data."""
    url: str
    conditions: str
    display_format: DisplayFormat = DisplayFormat.TABLE

class ProjectUrlCreate(ProjectUrlBase):
    """Model for creating a new project URL."""
    project_id: UUID

class ProjectUrlUpdate(BaseModel):
    """Model for updating a project URL."""
    conditions: Optional[str] = None
    display_format: Optional[DisplayFormat] = None

class ProjectUrlResponse(ProjectUrlBase):
    """Model for project URL response."""
    id: UUID
    project_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
