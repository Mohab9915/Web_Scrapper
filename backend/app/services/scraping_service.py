"""
Service for web scraping.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import Depends, BackgroundTasks, HTTPException, Response
from datetime import datetime
import json
import csv
import io

from app.database import supabase
from app.models.scrape_session import ScrapedSessionResponse, InteractiveScrapingResponse, ExecuteScrapeResponse
from app.utils.browser_control import launch_browser_session
from app.utils.text_processing import structure_scraped_data
from app.utils.firecrawl_api import scrape_url, AZURE_EMBEDDING_MODEL, AZURE_CHAT_MODEL
from app.services.rag_service import RAGService

class ScrapingService:
    """Service for web scraping."""

    def __init__(self, rag_service: RAGService = Depends()):
        self.rag_service = rag_service

    async def get_sessions_by_project(self, project_id: UUID) -> List[ScrapedSessionResponse]:
        """
        Get all scraped sessions for a project.

        Args:
            project_id (UUID): Project ID

        Returns:
            List[ScrapedSessionResponse]: List of scraped sessions
        """
        response = supabase.table("scrape_sessions").select("*").eq("project_id", str(project_id)).execute()
        return [ScrapedSessionResponse(**session) for session in response.data]

    async def initiate_interactive_scrape(self, project_id: UUID, initial_url: str) -> InteractiveScrapingResponse:
        """
        Start an interactive scraping session.

        Args:
            project_id (UUID): Project ID
            initial_url (str): Initial URL

        Returns:
            InteractiveScrapingResponse: Response with browser URL and session ID

        Raises:
            HTTPException: If project not found
        """
        # Check if project exists
        project_response = supabase.table("projects").select("id").eq("id", str(project_id)).single().execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Launch browser session (in a real implementation, this would launch a controlled browser)
        browser_url, session_id = await launch_browser_session(initial_url)

        return InteractiveScrapingResponse(
            interactive_target_url=browser_url,
            session_id=session_id
        )

    async def execute_scrape(
        self,
        project_id: UUID,
        current_page_url: str,
        session_id: str,
        api_keys: Optional[Dict[str, str]],
        background_tasks: BackgroundTasks,
        force_refresh: bool = False
    ) -> ExecuteScrapeResponse:
        """
        Execute scraping on a specific URL using Firecrawl API.

        Args:
            project_id (UUID): Project ID
            current_page_url (str): URL to scrape
            session_id (str): Session ID
            api_keys (Optional[Dict[str, str]]): API keys
            background_tasks (BackgroundTasks): Background tasks

        Returns:
            ExecuteScrapeResponse: Response with scraping results

        Raises:
            HTTPException: If project not found or scraping fails
        """
        # Check if project exists and get RAG status
        project_response = supabase.table("projects").select("*").eq("id", str(project_id)).single().execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        project = project_response.data
        rag_enabled = project["rag_enabled"]

        try:
            # Use the force_refresh parameter from the request, or force refresh if RAG is enabled and force_refresh is True
            # This allows the frontend to control whether to bypass the cache
            use_force_refresh = force_refresh

            # Use Firecrawl API to scrape the page with caching
            scrape_result = await scrape_url(
                current_page_url,
                formats=["markdown", "html"],
                force_refresh=use_force_refresh
            )

            # Extract markdown content from the result
            markdown_content = scrape_result.get("markdown", "")

            # If no markdown content was returned, create a fallback message
            if not markdown_content:
                markdown_content = f"# Failed to scrape content from {current_page_url}\n\nThe scraping operation did not return any content."

            # Get metadata from the result
            metadata = scrape_result.get("metadata", {})
            page_title = metadata.get("title", "Untitled Page")

            # Add page title to the markdown content if it's not already there
            if not markdown_content.startswith(f"# {page_title}"):
                markdown_content = f"# {page_title}\n\n{markdown_content}"

        except HTTPException as e:
            # Re-raise HTTP exceptions with their original status code and detail
            raise e
        except Exception as e:
            # Handle other errors
            error_message = str(e)
            raise HTTPException(status_code=500, detail=f"Failed to scrape URL: {error_message}")

        # Structure the scraped data
        structured_data = await structure_scraped_data(markdown_content)

        # Create a new scrape session
        session_data = {
            "id": session_id,
            "project_id": str(project_id),
            "url": current_page_url,
            "raw_markdown": markdown_content,
            "structured_data_json": json.dumps(structured_data),
            "status": "scraped"
        }

        session_response = supabase.table("scrape_sessions").insert(session_data).execute()
        if not session_response.data:
            raise HTTPException(status_code=500, detail="Failed to create scrape session")

        session = session_response.data[0]

        # If RAG is enabled, process the scraped content in the background
        embedding_cost = 0.0
        if rag_enabled:
            # Check if Azure OpenAI credentials are provided
            if not api_keys or 'api_key' not in api_keys or 'endpoint' not in api_keys:
                raise HTTPException(status_code=400, detail="Azure OpenAI credentials (api_key and endpoint) are required for RAG processing")

            # Ensure the correct embedding model is used
            embedding_api_keys = {
                **api_keys,
                "deployment_name": AZURE_EMBEDDING_MODEL
            }

            # Process the scraped content in the background
            background_tasks.add_task(
                self.rag_service.ingest_scraped_content,
                project_id,
                session["id"],
                markdown_content,
                embedding_api_keys
            )
            session_status = "Processing for RAG"

            # Calculate approximate embedding cost
            # Azure OpenAI embedding costs approximately $0.0001 per 1K tokens
            # A simple approximation: 1 token ≈ 4 characters
            num_tokens = len(markdown_content) / 4
            embedding_cost = (num_tokens / 1000) * 0.0001
        else:
            session_status = "Scraped"

        # Generate download links
        download_links = {
            "json": f"/download/{project_id}/{session['id']}/json",
            "csv": f"/download/{project_id}/{session['id']}/csv"
        }

        return ExecuteScrapeResponse(
            status="success",
            message=f"Page {current_page_url} scraped successfully using Firecrawl API.",
            download_links=download_links,
            rag_status=session_status,
            embedding_cost_if_any=embedding_cost
        )

    async def delete_session(self, project_id: UUID, session_id: UUID) -> bool:
        """
        Delete a scraped session.

        Args:
            project_id (UUID): Project ID
            session_id (UUID): Session ID

        Returns:
            bool: True if deleted, False if not found
        """
        # Delete session
        response = supabase.table("scrape_sessions").delete().eq("id", str(session_id)).eq("project_id", str(project_id)).execute()
        return len(response.data) > 0

    async def get_download_file(self, project_id: UUID, session_id: UUID, format: str):
        """
        Download scraped data in JSON or CSV format.

        Args:
            project_id (UUID): Project ID
            session_id (UUID): Session ID
            format (str): Format ('json' or 'csv')

        Returns:
            Response: File download response

        Raises:
            HTTPException: If session not found
        """
        # Get session data
        session_response = supabase.table("scrape_sessions").select("*").eq("id", str(session_id)).eq("project_id", str(project_id)).single().execute()
        if not session_response.data:
            raise HTTPException(status_code=404, detail="Session not found")

        session = session_response.data

        if format == "json":
            # Return JSON file
            content = session.get("structured_data_json", "{}")
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=scraped_data_{session_id}.json"}
            )
        else:  # format == "csv"
            # Convert JSON to CSV
            structured_data = json.loads(session.get("structured_data_json", "{}"))
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(structured_data.keys())

            # Write values
            writer.writerow(structured_data.values())

            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=scraped_data_{session_id}.csv"}
            )
