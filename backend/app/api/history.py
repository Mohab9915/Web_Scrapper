"""
API endpoints for scraping history management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.services.scraping_service import ScrapingService

router = APIRouter(tags=["history"])

@router.delete("/projects/{project_id}/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_item(
    project_id: UUID,
    history_id: int,
    scraping_service: ScrapingService = Depends()
):
    """
    Delete a specific history item.

    Args:
        project_id (UUID): Project ID
        history_id (int): History item ID

    Raises:
        HTTPException: If history item not found
    """
    # Since history items are stored in the scrape_sessions table,
    # we'll delete the corresponding scrape session
    try:
        # Get the scrape session by ID
        session = await scraping_service.get_session(history_id)

        # Check if the session belongs to the project
        if str(session.project_id) != str(project_id):
            raise HTTPException(status_code=404, detail="History item not found for this project")

        # Delete the session
        success = await scraping_service.delete_session_by_id(history_id)
        if not success:
            raise HTTPException(status_code=404, detail="History item not found")

        return None
    except Exception as e:
        # If the session doesn't exist or there's another error, return 404
        raise HTTPException(status_code=404, detail="History item not found")
