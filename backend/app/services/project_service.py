"""
Service for project management.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import Depends

from app.database import supabase
from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse

class ProjectService:
    """Service for project management."""

    async def get_all_projects(self) -> List[ProjectResponse]:
        """
        Get all projects.

        Returns:
            List[ProjectResponse]: List of projects
        """
        response = supabase.table("projects").select("*").execute()
        projects = response.data

        # Get scraped sessions count for each project
        for project in projects:
            sessions_response = supabase.table("scrape_sessions").select("id").eq("project_id", project["id"]).execute()
            project["scraped_sessions_count"] = len(sessions_response.data)
            project["rag_status"] = "Enabled" if project["rag_enabled"] else "Disabled"

            # Ensure caching_enabled is present (for backward compatibility)
            if "caching_enabled" not in project:
                project["caching_enabled"] = True

        return [ProjectResponse(**project) for project in projects]

    async def get_project_by_id(self, project_id: UUID) -> Optional[ProjectResponse]:
        """
        Get a specific project.

        Args:
            project_id (UUID): Project ID

        Returns:
            Optional[ProjectResponse]: Project data or None if not found
        """
        response = supabase.table("projects").select("*").eq("id", str(project_id)).single().execute()
        if not response.data:
            return None

        project = response.data
        sessions_response = supabase.table("scrape_sessions").select("id").eq("project_id", str(project_id)).execute()
        project["scraped_sessions_count"] = len(sessions_response.data)
        project["rag_status"] = "Enabled" if project["rag_enabled"] else "Disabled"

        # Ensure caching_enabled is present (for backward compatibility)
        if "caching_enabled" not in project:
            project["caching_enabled"] = True

        return ProjectResponse(**project)

    async def create_project(self, project_data: ProjectCreate) -> ProjectResponse:
        """
        Create a new project.

        Args:
            project_data (ProjectCreate): Project data

        Returns:
            ProjectResponse: Created project
        """
        # Get caching preference from the project data or default to True
        caching_enabled = True  # Default to True for backward compatibility

        response = supabase.table("projects").insert({
            "name": project_data.name,
            "rag_enabled": False,
            "caching_enabled": caching_enabled
        }).execute()

        project = response.data[0]
        project["scraped_sessions_count"] = 0
        project["rag_status"] = "Disabled"

        # If initial URLs are provided, we could trigger scraping here
        # But for now, we'll just return the created project

        return ProjectResponse(**project)

    async def update_project(self, project_id: UUID, project_update: ProjectUpdate) -> Optional[ProjectResponse]:
        """
        Update a project.

        Args:
            project_id (UUID): Project ID
            project_update (ProjectUpdate): Project update data

        Returns:
            Optional[ProjectResponse]: Updated project or None if not found
        """
        update_data = {}
        if project_update.name is not None:
            update_data["name"] = project_update.name

        if project_update.rag_enabled is not None:
            update_data["rag_enabled"] = project_update.rag_enabled

            # If enabling RAG, we should process existing sessions
            if project_update.rag_enabled:
                # This would be handled by a background task in a real implementation
                # For now, we'll just update the status of existing sessions
                supabase.table("scrape_sessions").update({
                    "status": "rag_ingested"
                }).eq("project_id", str(project_id)).execute()

        if project_update.caching_enabled is not None:
            update_data["caching_enabled"] = project_update.caching_enabled

        if not update_data:
            # Nothing to update
            return await self.get_project_by_id(project_id)

        response = supabase.table("projects").update(update_data).eq("id", str(project_id)).execute()
        if not response.data:
            return None

        return await self.get_project_by_id(project_id)

    async def delete_project(self, project_id: UUID) -> bool:
        """
        Delete a project.

        Args:
            project_id (UUID): Project ID

        Returns:
            bool: True if deleted, False if not found
        """
        # Delete project (cascade will delete associated sessions)
        response = supabase.table("projects").delete().eq("id", str(project_id)).execute()
        return len(response.data) > 0
