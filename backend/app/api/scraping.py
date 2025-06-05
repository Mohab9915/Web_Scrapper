"""
API endpoints for web scraping.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
from uuid import UUID

from ..models.scrape_session import (
    ScrapedSessionResponse, ProjectUrlWithSessionResponse, InteractiveScrapingInitiate,
    InteractiveScrapingResponse, ExecuteScrapeRequest, ExecuteScrapeResponse
)
from ..services.scraping_service import ScrapingService
from ..dependencies.auth import get_current_user, get_current_user_id
from ..models.auth import UserResponse

router = APIRouter(tags=["scraping"])

@router.get("/projects/{project_id}/sessions", response_model=List[ProjectUrlWithSessionResponse])
async def get_scraped_sessions(
    project_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    scraping_service: ScrapingService = Depends()
):
    """
    Get all project URLs with their latest scrape session data for the authenticated user.

    Args:
        project_id (UUID): Project ID
        current_user_id (UUID): ID of the authenticated user

    Returns:
        List[ProjectUrlWithSessionResponse]: List of project URLs with session data
    """
    return await scraping_service.get_sessions_by_project(project_id, current_user_id)

@router.post("/projects/{project_id}/initiate-interactive-scrape", response_model=InteractiveScrapingResponse)
async def initiate_interactive_scrape(
    project_id: UUID,
    request: InteractiveScrapingInitiate,
    scraping_service: ScrapingService = Depends()
):
    """
    Start an interactive scraping session.

    Args:
        project_id (UUID): Project ID
        request (InteractiveScrapingInitiate): Request data

    Returns:
        InteractiveScrapingResponse: Response with browser URL and session ID
    """
    return await scraping_service.initiate_interactive_scrape(project_id, request.initial_url)

@router.post("/projects/{project_id}/execute-scrape", response_model=ExecuteScrapeResponse)
async def execute_scrape(
    project_id: UUID,
    request: ExecuteScrapeRequest,
    background_tasks: BackgroundTasks,
    scraping_service: ScrapingService = Depends()
):
    """
    Execute scraping on a specific URL.

    Args:
        project_id (UUID): Project ID
        request (ExecuteScrapeRequest): Request data
        background_tasks (BackgroundTasks): Background tasks

    Returns:
        ExecuteScrapeResponse: Response with scraping results
    """
    return await scraping_service.execute_scrape(
        project_id,
        request,
        background_tasks
    )

@router.delete("/projects/{project_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scraped_session(
    project_id: UUID,
    session_id: UUID,
    scraping_service: ScrapingService = Depends()
):
    """
    Delete a scraped session.

    Args:
        project_id (UUID): Project ID
        session_id (UUID): Session ID

    Raises:
        HTTPException: If session not found
    """
    success = await scraping_service.delete_session(project_id, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return None

@router.get("/download/{project_id}/{session_id}/{format}")
async def download_scraped_data(
    project_id: UUID,
    session_id: UUID,
    format: str,
    scraping_service: ScrapingService = Depends()
):
    """
    Download scraped data in JSON, CSV, or PDF format.

    Args:
        project_id (UUID): Project ID
        session_id (UUID): Session ID
        format (str): Format ('json', 'csv', or 'pdf')

    Returns:
        Response: File download response

    Raises:
        HTTPException: If format is invalid or session not found
    """
    if format not in ["json", "csv", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format. Must be 'json', 'csv', or 'pdf'")

    return await scraping_service.get_download_file(project_id, session_id, format)
