"""
API endpoints for project management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(project_service: ProjectService = Depends()):
    """
    Get all projects.
    
    Returns:
        List[ProjectResponse]: List of projects
    """
    return await project_service.get_all_projects()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, project_service: ProjectService = Depends()):
    """
    Create a new project.
    
    Args:
        project (ProjectCreate): Project data
        
    Returns:
        ProjectResponse: Created project
    """
    return await project_service.create_project(project)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, project_service: ProjectService = Depends()):
    """
    Get a specific project.
    
    Args:
        project_id (UUID): Project ID
        
    Returns:
        ProjectResponse: Project data
        
    Raises:
        HTTPException: If project not found
    """
    project = await project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, project_update: ProjectUpdate, project_service: ProjectService = Depends()):
    """
    Update a project.
    
    Args:
        project_id (UUID): Project ID
        project_update (ProjectUpdate): Project update data
        
    Returns:
        ProjectResponse: Updated project
        
    Raises:
        HTTPException: If project not found
    """
    updated_project = await project_service.update_project(project_id, project_update)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project

@router.patch("/{project_id}", response_model=ProjectResponse)
async def patch_project(project_id: UUID, project_update: ProjectUpdate, project_service: ProjectService = Depends()):
    """
    Partially update a project.
    
    Args:
        project_id (UUID): Project ID
        project_update (ProjectUpdate): Project update data
        
    Returns:
        ProjectResponse: Updated project
        
    Raises:
        HTTPException: If project not found
    """
    updated_project = await project_service.update_project(project_id, project_update)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID, project_service: ProjectService = Depends()):
    """
    Delete a project.
    
    Args:
        project_id (UUID): Project ID
        
    Raises:
        HTTPException: If project not found
    """
    success = await project_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None

@router.post("/{project_id}/enable-rag", response_model=ProjectResponse)
async def enable_rag(project_id: UUID, project_service: ProjectService = Depends()):
    """
    Enable RAG for a project.
    
    Args:
        project_id (UUID): Project ID
        
    Returns:
        ProjectResponse: Updated project
        
    Raises:
        HTTPException: If project not found
    """
    project_update = ProjectUpdate(rag_enabled=True)
    updated_project = await project_service.update_project(project_id, project_update)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project
