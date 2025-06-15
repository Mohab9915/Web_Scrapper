"""
Service for project management.
"""
from typing import List, Optional
from uuid import UUID

from ..database import supabase
from ..models.project import ProjectCreate, ProjectUpdate, ProjectResponse

class ProjectService:
    """Service for project management."""

    async def get_user_projects(self, user_id: UUID) -> List[ProjectResponse]:
        """
        Get all projects for a specific user.

        Args:
            user_id (UUID): User ID

        Returns:
            List[ProjectResponse]: List of user's projects
        """
        response = supabase.table("projects").select("*").eq("user_id", str(user_id)).execute()
        projects = []

        for project_data in response.data:
            # Get scraped sessions count for this project
            sessions_response = supabase.table("scrape_sessions").select("id").eq("project_id", project_data["id"]).execute()
            scraped_sessions_count = len(sessions_response.data)

            # Determine RAG status
            rag_status = "Enabled" if project_data.get("rag_enabled", False) else "Disabled"

            project_data["scraped_sessions_count"] = scraped_sessions_count
            project_data["rag_status"] = rag_status

            projects.append(ProjectResponse(**project_data))

        return projects

    async def get_all_projects(self) -> List[ProjectResponse]:
        """
        Get all projects with optimized session count query.

        Returns:
            List[ProjectResponse]: List of projects
        """
        # Fetch all projects
        response = supabase.table("projects").select("*").execute()
        projects = response.data

        if not projects:
            return []

        # OPTIMIZED: Get session counts for all projects in a single query
        project_ids = [project["id"] for project in projects]
        sessions_response = supabase.table("scrape_sessions").select("project_id").in_("project_id", project_ids).execute()

        # Count sessions per project
        session_counts = {}
        for session in sessions_response.data:
            project_id = session["project_id"]
            session_counts[project_id] = session_counts.get(project_id, 0) + 1

        # Process each project with the session count
        for project in projects:
            project["scraped_sessions_count"] = session_counts.get(project["id"], 0)
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

    async def create_project(self, project_data: ProjectCreate, user_id: UUID) -> ProjectResponse:
        """
        Create a new project for a specific user.

        Args:
            project_data (ProjectCreate): Project data
            user_id (UUID): User ID

        Returns:
            ProjectResponse: Created project
        """
        # Get caching preference from the project data or default to True
        caching_enabled = True  # Default to True for backward compatibility

        project_insert_data = {
            "user_id": str(user_id),
            "name": project_data.name,
            "rag_enabled": False,
            "caching_enabled": caching_enabled
        }

        print(f"🔍 Creating project with data: {project_insert_data}")

        response = supabase.table("projects").insert(project_insert_data).execute()

        print(f"🔍 Supabase response: {response}")
        print(f"🔍 Response data: {response.data}")
        print(f"🔍 Response error: {getattr(response, 'error', None)}")

        if not response.data:
            error_detail = getattr(response, 'error', 'Unknown error')
            raise HTTPException(status_code=400, detail=f"Failed to create project: {error_detail}")

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
