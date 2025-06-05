"""
API endpoints for project management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from ..models.project import ProjectCreate, ProjectUpdate, ProjectResponse
from ..services.project_service import ProjectService
from ..dependencies.auth import get_current_user, get_current_user_id
from ..models.auth import UserResponse

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    current_user_id: UUID = Depends(get_current_user_id),
    project_service: ProjectService = Depends()
):
    """
    Get all projects for the authenticated user.

    Args:
        current_user_id: ID of the authenticated user
        project_service: Project service instance

    Returns:
        List[ProjectResponse]: List of user's projects
    """
    return await project_service.get_user_projects(current_user_id)

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    project_service: ProjectService = Depends()
):
    """
    Create a new project for the authenticated user.

    Args:
        project: Project data
        current_user_id: ID of the authenticated user
        project_service: Project service instance

    Returns:
        ProjectResponse: Created project
    """
    return await project_service.create_project(project, current_user_id)

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
    Enable RAG for a project and ingest all existing scraped sessions.

    Args:
        project_id (UUID): Project ID

    Returns:
        ProjectResponse: Updated project

    Raises:
        HTTPException: If project not found
    """
    from ..database import supabase
    from ..services.enhanced_rag_service import EnhancedRAGService
    import json
    import os

    # First, enable RAG for the project
    project_update = ProjectUpdate(rag_enabled=True)
    updated_project = await project_service.update_project(project_id, project_update)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Then, ingest all existing scraped sessions using the same logic as the working manual ingestion
    try:
        # Get all scraped sessions that haven't been RAG ingested yet
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", str(project_id)).eq("status", "scraped").execute()
        sessions = sessions_response.data or []

        if sessions:
            print(f"Found {len(sessions)} scraped sessions to ingest for project {project_id}")

            # Use Enhanced RAG service (same as working manual ingestion)
            enhanced_rag_service = EnhancedRAGService()

            # Get Azure credentials (same as working manual ingestion)
            azure_credentials = {
                "api_key": os.getenv("AZURE_OPENAI_API_KEY", "dummy_key"),
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "dummy_endpoint"),
                "deployment_name": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
            }

            ingested_count = 0
            for session in sessions:
                session_id = session["id"]

                try:
                    # Check if session has structured data (same as working manual ingestion)
                    if not session.get('structured_data_json'):
                        print(f"Session {session_id} has no structured data to ingest")
                        continue

                    # Parse structured data (same as working manual ingestion)
                    structured_data = json.loads(session['structured_data_json']) if isinstance(session['structured_data_json'], str) else session['structured_data_json']

                    # Perform ingestion (same as working manual ingestion)
                    success = await enhanced_rag_service.ingest_structured_content(
                        project_id=project_id,
                        session_id=UUID(session_id),
                        structured_data=structured_data,
                        embedding_api_keys=azure_credentials
                    )

                    if success:
                        # Update session status (same as working manual ingestion)
                        supabase.table('scrape_sessions').update({
                            'status': 'rag_ingested'
                        }).eq('id', session_id).execute()

                        ingested_count += 1
                        print(f"Successfully ingested session {session_id}")
                    else:
                        print(f"RAG ingestion completed with warnings for session {session_id}")

                except Exception as e:
                    print(f"Error ingesting session {session_id}: {str(e)}")
                    continue

            print(f"Successfully ingested {ingested_count} out of {len(sessions)} sessions")
        else:
            print(f"No scraped sessions found for project {project_id}")

    except Exception as e:
        print(f"Error during RAG ingestion: {str(e)}")
        # Don't fail the entire request if ingestion fails, RAG is still enabled

    return updated_project
