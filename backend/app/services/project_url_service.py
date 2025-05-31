"""
Service for project URL management.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException

from ..database import supabase
from ..models.project_url import ProjectUrlCreate, ProjectUrlUpdate, ProjectUrlResponse

class ProjectUrlService:
    """Service for project URL management."""

    async def get_urls_by_project(self, project_id: UUID) -> List[ProjectUrlResponse]:
        """
        Get all URLs for a project.

        Args:
            project_id (UUID): Project ID

        Returns:
            List[ProjectUrlResponse]: List of project URLs
        """
        # Check if project exists
        project_response = supabase.table("projects").select("id").eq("id", str(project_id)).single().execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get URLs for the project
        urls_response = supabase.table("project_urls").select("*").eq("project_id", str(project_id)).execute()

        project_urls_with_status = []
        for url_data in urls_response.data:
            # Use the status from the project_urls table directly
            # This table maintains the overall status of the URL (pending, processing, completed, failed)
            # The scrape_sessions table status is for individual scraping sessions
            project_url_response_data = url_data.copy()

            # Ensure status is set (fallback to pending if somehow missing)
            if not project_url_response_data.get("status"):
                project_url_response_data["status"] = "pending"

            # Convert to response model
            project_urls_with_status.append(ProjectUrlResponse(**project_url_response_data))

        return project_urls_with_status

    async def create_project_url(self, project_url: ProjectUrlCreate) -> ProjectUrlResponse:
        """
        Create a new project URL.

        Args:
            project_url (ProjectUrlCreate): Project URL data

        Returns:
            ProjectUrlResponse: Created project URL
        """
        # Check if project exists
        project_response = supabase.table("projects").select("id").eq("id", str(project_url.project_id)).single().execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if URL already exists for this project
        url_response = supabase.table("project_urls").select("*").eq("project_id", str(project_url.project_id)).eq("url", project_url.url).execute()
        if url_response.data:
            # Update existing URL
            response = supabase.table("project_urls").update({
                "conditions": project_url.conditions,
                "display_format": project_url.display_format,
                "rag_enabled": project_url.rag_enabled  # Added rag_enabled
            }).eq("project_id", str(project_url.project_id)).eq("url", project_url.url).execute()
        else:
            # Create new URL
            response = supabase.table("project_urls").insert({
                "project_id": str(project_url.project_id),
                "url": project_url.url,
                "conditions": project_url.conditions,
                "display_format": project_url.display_format,
                "rag_enabled": project_url.rag_enabled  # Added rag_enabled
            }).execute()

        # Return created/updated URL
        return ProjectUrlResponse(**response.data[0])

    async def delete_project_url(self, project_id: UUID, url_id: str) -> bool:
        """
        Delete a specific project URL and all associated data.
        This includes:
        - The URL entry in project_urls table
        - All scraping sessions for this URL
        - All RAG data (markdowns and embeddings) associated with this URL

        Args:
            project_id (UUID): Project ID
            url_id (str): URL ID (can be an integer or UUID)

        Returns:
            bool: True if deleted, False if not found
        """
        # Check if project exists
        project_response = supabase.table("projects").select("id").eq("id", str(project_id)).single().execute()
        if not project_response.data:
            return False

        # Get all URLs for the project
        urls_response = supabase.table("project_urls").select("*").eq("project_id", str(project_id)).execute()

        # Find the URL with the matching ID
        # This is needed because the frontend uses integer IDs but the backend uses UUIDs
        url_to_delete = None
        for url in urls_response.data:
            # Try to match by ID (could be UUID or integer)
            if str(url.get("id")) == str(url_id):
                url_to_delete = url
                break

        if not url_to_delete:
            return False

        # Get the actual URL string
        url_string = url_to_delete.get("url")

        # 1. Get all scraping sessions for this URL
        sessions_response = supabase.table("scrape_sessions").select("id", "unique_scrape_identifier").eq("project_id", str(project_id)).eq("url", url_string).execute()

        # 2. Delete RAG data for each session
        for session in sessions_response.data:
            unique_scrape_identifier = session.get("unique_scrape_identifier")
            if unique_scrape_identifier:
                print(f"Deleting RAG data for unique_scrape_identifier: {unique_scrape_identifier}")
                # Delete associated embeddings
                supabase.table("embeddings").delete().eq("unique_name", unique_scrape_identifier).execute()
                # Delete associated markdown
                supabase.table("markdowns").delete().eq("unique_name", unique_scrape_identifier).execute()

        # 3. Delete all scraping sessions for this URL
        supabase.table("scrape_sessions").delete().eq("project_id", str(project_id)).eq("url", url_string).execute()

        # 4. Delete the URL entry
        response = supabase.table("project_urls").delete().eq("id", url_to_delete["id"]).eq("project_id", str(project_id)).execute()

        return len(response.data) > 0

    async def delete_all_project_urls(self, project_id: UUID) -> bool:
        """
        Delete all URLs for a project.

        Args:
            project_id (UUID): Project ID

        Returns:
            bool: True if deleted, False if project not found
        """
        # Check if project exists
        project_response = supabase.table("projects").select("id").eq("id", str(project_id)).single().execute()
        if not project_response.data:
            return False

        # Delete all URLs for the project
        response = supabase.table("project_urls").delete().eq("project_id", str(project_id)).execute()

        # Also delete all scrape sessions for the project
        sessions_response = supabase.table("scrape_sessions").delete().eq("project_id", str(project_id)).execute()

        return True
