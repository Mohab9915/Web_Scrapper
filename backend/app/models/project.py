"""
Project models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ProjectBase(BaseModel):
    """Base model for project data."""
    name: str

class ProjectCreate(ProjectBase):
    """Model for creating a new project."""
    initial_urls: Optional[List[str]] = None

class ProjectUpdate(BaseModel):
    """Model for updating a project."""
    name: Optional[str] = None
    rag_enabled: Optional[bool] = None
    caching_enabled: Optional[bool] = None

class ProjectResponse(ProjectBase):
    """Model for project response."""
    id: UUID
    created_at: datetime
    rag_status: str  # 'Enabled', 'Disabled', 'Enabling'
    scraped_sessions_count: int
    caching_enabled: bool = True  # Default to True for backward compatibility

    class Config:
        from_attributes = True
