from fastapi import APIRouter, HTTPException
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from ..database import supabase

router = APIRouter()

class ProjectSettingsUpdate(BaseModel):
    rag_enabled: Optional[bool] = None
    caching_enabled: Optional[bool] = None
    # Add other project-specific settings here if needed in the future

class ProjectSettingsResponse(BaseModel):
    project_id: UUID
    rag_enabled: bool
    caching_enabled: bool
    # Add other settings

@router.get("/projects/{project_id}/settings", response_model=ProjectSettingsResponse)
async def get_project_settings(project_id: UUID):
    """
    Get settings for a specific project.
    """
    project_response = supabase.table("projects").select("id, rag_enabled, caching_enabled").eq("id", str(project_id)).single().execute()
    if not project_response.data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    settings = project_response.data
    return ProjectSettingsResponse(
        project_id=settings["id"],
        rag_enabled=settings.get("rag_enabled", False), # Default to False if not set
        caching_enabled=settings.get("caching_enabled", True) # Default to True if not set
    )

@router.put("/projects/{project_id}/settings", response_model=ProjectSettingsResponse)
async def update_project_settings(project_id: UUID, settings_update: ProjectSettingsUpdate):
    """
    Update settings for a specific project.
    """
    update_data = settings_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No settings provided to update.")

    # First, check if project exists
    project_check = supabase.table("projects").select("id").eq("id", str(project_id)).single().execute()
    if not project_check.data:
        raise HTTPException(status_code=404, detail="Project not found")

    response = supabase.table("projects").update(update_data).eq("id", str(project_id)).execute()
    
    if not response.data:
        # This case might indicate an issue with the update or RLS, though .update() often returns data on success.
        # Fetch the updated settings to confirm and return
        updated_settings_response = await get_project_settings(project_id)
        if updated_settings_response: # Check if fetch was successful
             return updated_settings_response
        raise HTTPException(status_code=500, detail="Failed to update project settings or retrieve them post-update.")

    # Supabase update typically returns a list of updated records
    updated_settings = response.data[0]
    return ProjectSettingsResponse(
        project_id=updated_settings["id"],
        rag_enabled=updated_settings.get("rag_enabled", False),
        caching_enabled=updated_settings.get("caching_enabled", True)
    )
