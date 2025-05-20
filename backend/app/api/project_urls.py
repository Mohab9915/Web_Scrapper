"""
API endpoints for project URLs management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.models.project_url import ProjectUrlResponse, ProjectUrlCreate, ProjectUrlUpdate
from app.services.project_url_service import ProjectUrlService

router = APIRouter(tags=["project_urls"])

@router.get("/projects/{project_id}/urls", response_model=List[ProjectUrlResponse])
async def get_project_urls(project_id: UUID, project_url_service: ProjectUrlService = Depends()):
    """
    Get all URLs for a project.

    Args:
        project_id (UUID): Project ID

    Returns:
        List[ProjectUrlResponse]: List of project URLs
    """
    return await project_url_service.get_urls_by_project(project_id)

@router.post("/projects/{project_id}/urls", response_model=ProjectUrlResponse, status_code=status.HTTP_201_CREATED)
async def create_project_url(
    project_id: UUID,
    project_url: ProjectUrlCreate,
    project_url_service: ProjectUrlService = Depends()
):
    """
    Create a new project URL.

    Args:
        project_id (UUID): Project ID
        project_url (ProjectUrlCreate): Project URL data

    Returns:
        ProjectUrlResponse: Created project URL
    """
    # Override the project_id from the path
    project_url.project_id = project_id
    return await project_url_service.create_project_url(project_url)

@router.delete("/projects/{project_id}/urls", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_project_urls(project_id: UUID, project_url_service: ProjectUrlService = Depends()):
    """
    Delete all URLs for a project.

    Args:
        project_id (UUID): Project ID

    Raises:
        HTTPException: If project not found
    """
    success = await project_url_service.delete_all_project_urls(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None

@router.delete("/projects/{project_id}/urls/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_url(
    project_id: UUID,
    url_id: str,
    project_url_service: ProjectUrlService = Depends()
):
    """
    Delete a specific project URL.

    Args:
        project_id (UUID): Project ID
        url_id (str): URL ID (can be an integer or UUID)

    Raises:
        HTTPException: If URL not found
    """
    success = await project_url_service.delete_project_url(project_id, url_id)
    if not success:
        raise HTTPException(status_code=404, detail="URL not found")
    return None
