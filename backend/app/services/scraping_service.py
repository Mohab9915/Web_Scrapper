"""
Service for web scraping.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from fastapi import Depends, BackgroundTasks, HTTPException, Response
from datetime import datetime
import json
import csv
import io

from app.database import supabase
from app.models.scrape_session import ScrapedSessionResponse, InteractiveScrapingResponse, ExecuteScrapeResponse, ExecuteScrapeRequest
from app.utils.browser_control import launch_browser_session
from app.utils.text_processing import structure_scraped_data, format_data_for_display
from app.utils.crawl4ai_crawler import scrape_url, extract_structured_data, AZURE_EMBEDDING_MODEL, AZURE_CHAT_MODEL
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

        sessions = []
        for session in response.data:
            # Create a copy of the session data to modify
            session_data = dict(session)

            # Parse the structured_data_json field
            if "structured_data_json" in session_data and session_data["structured_data_json"]:
                try:
                    structured_data = json.loads(session_data["structured_data_json"])
                    session_data["structured_data"] = structured_data

                    # Extract tabular data
                    if "tabular_data" in structured_data:
                        session_data["tabular_data"] = structured_data["tabular_data"]

                        # Extract fields from the first row of tabular data
                        if structured_data["tabular_data"] and len(structured_data["tabular_data"]) > 0:
                            session_data["fields"] = list(structured_data["tabular_data"][0].keys())
                except Exception as e:
                    print(f"Error parsing structured_data_json: {e}")

            # Parse the formatted_tabular_data field
            if "formatted_tabular_data" in session_data and session_data["formatted_tabular_data"]:
                try:
                    formatted_data = json.loads(session_data["formatted_tabular_data"])
                    session_data["formatted_tabular_data"] = formatted_data
                except Exception as e:
                    print(f"Error parsing formatted_tabular_data: {e}")

            # Generate download links
            session_data["download_link_json"] = f"/download/{project_id}/{session_data['id']}/json"
            session_data["download_link_csv"] = f"/download/{project_id}/{session_data['id']}/csv"

            # Create the response object
            sessions.append(ScrapedSessionResponse(**session_data))

        return sessions

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
        request: ExecuteScrapeRequest,
        background_tasks: BackgroundTasks,
        rag_enabled: bool = False
    ) -> ExecuteScrapeResponse:
        """
        Execute scraping on a specific URL using Crawl4AI framework.

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

        # Extract parameters from the request
        current_page_url = request.current_page_url
        session_id = request.session_id
        api_keys = request.api_keys
        force_refresh = request.force_refresh
        display_format = request.display_format or "table"
        request_conditions = request.conditions  # Get conditions from the request if provided

        try:
            # Check if caching is enabled for this project
            caching_enabled = project.get("caching_enabled", True)  # Default to True for backward compatibility

            # Determine whether to use cache:
            # - If caching is disabled for the project, always force refresh
            # - If force_refresh is True in the request, bypass cache
            use_force_refresh = force_refresh or not caching_enabled

            # Use Crawl4AI framework to scrape the page with caching
            try:
                scrape_result = await scrape_url(
                    current_page_url,
                    formats=["markdown", "html"],
                    force_refresh=use_force_refresh
                )
            except Exception as e:
                print(f"Error scraping URL with crawl4ai: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to scrape URL: {str(e)}")

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

        # Get conditions from the request, project, or URL
        # Priority order:
        # 1. Conditions from the request (highest priority)
        # 2. Conditions from the database
        # 3. Default conditions (lowest priority)
        conditions = None

        # First, check if conditions were provided in the request
        if request_conditions and request_conditions.strip():
            conditions = request_conditions.strip()
            print(f"Using conditions from request: {conditions}")
        else:
            # If not in request, try to get from database
            try:
                # Check if the project has URLs with conditions
                project_urls_response = supabase.table("project_urls").select("conditions").eq("project_id", str(project_id)).eq("url", current_page_url).execute()
                if project_urls_response.data and project_urls_response.data[0].get("conditions"):
                    conditions = project_urls_response.data[0].get("conditions")
                    print(f"Using conditions from database: {conditions}")
                else:
                    # Only use default conditions if no conditions were found anywhere
                    conditions = "title, description, price, content"
                    print(f"No conditions found for URL {current_page_url}, using default conditions: {conditions}")
            except Exception as e:
                print(f"Error getting conditions from database: {e}")
                # Default conditions if there's an error
                conditions = "title, description, price, content"
                print(f"Using default conditions due to error: {conditions}")

        # Structure the scraped data with conditions and Azure credentials
        try:
            structured_data = await structure_scraped_data(
                markdown_content,
                conditions,
                api_keys if api_keys else None
            )
        except Exception as e:
            print(f"Error structuring scraped data: {e}")
            # Create a basic structured data object if structuring fails
            structured_data = {
                "tabular_data": [{"content": markdown_content}]
            }

        # Create a new scrape session
        # Ensure session_id is a valid UUID
        try:
            # Try to parse the session_id as a UUID
            uuid_obj = UUID(session_id)
            session_id_str = str(uuid_obj)
        except ValueError:
            # If it's not a valid UUID, generate a new one
            session_id_str = str(uuid4())
            print(f"Invalid UUID format for session_id: {session_id}, using generated UUID: {session_id_str}")

        # Extract fields from conditions
        fields = [field.strip() for field in conditions.split(',')] if conditions else []

        # Get tabular data from structured data
        tabular_data = structured_data.get("tabular_data", [])

        # Format data for display based on the specified format
        formatted_data = await format_data_for_display(tabular_data, fields, display_format)

        session_data = {
            "id": session_id_str,
            "project_id": str(project_id),
            "url": current_page_url,
            "raw_markdown": markdown_content,
            "structured_data_json": json.dumps(structured_data),
            "status": "scraped",
            "display_format": display_format,
            "formatted_tabular_data": json.dumps(formatted_data)
        }

        session_response = supabase.table("scrape_sessions").insert(session_data).execute()
        if not session_response.data:
            raise HTTPException(status_code=500, detail="Failed to create scrape session")

        session = session_response.data[0]

        # If RAG is enabled, process the scraped content in the background
        embedding_cost = 0.0
        if rag_enabled:
            # Check if Azure OpenAI credentials are provided
            if not api_keys:
                raise HTTPException(status_code=400, detail="Azure OpenAI credentials are required for RAG processing. Please configure your API key and endpoint in the frontend Settings.")
            
            if 'api_key' not in api_keys or not api_keys.get('api_key'):
                raise HTTPException(status_code=400, detail="Azure OpenAI API key is missing. Please set your API key in the frontend Settings.")
                
            if 'endpoint' not in api_keys or not api_keys.get('endpoint'):
                raise HTTPException(status_code=400, detail="Azure OpenAI endpoint is missing. Please set your endpoint URL in the frontend Settings.")

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
                embedding_api_keys,
                structured_data  # Pass structured data for focused RAG ingestion
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

        # No need to extract fields and tabular data again, already done above

        # We'll store the display format in the session data for now
        # since the project_urls table might not exist yet
        try:
            # Try to update project_urls table if it exists
            try:
                # Check if the URL exists in project_urls
                project_url_response = supabase.table("project_urls").select("*").eq("project_id", str(project_id)).eq("url", current_page_url).execute()

                if project_url_response.data:
                    # Update existing entry
                    supabase.table("project_urls").update({
                        "conditions": conditions,
                        "display_format": display_format
                    }).eq("project_id", str(project_id)).eq("url", current_page_url).execute()
                else:
                    # Insert new entry
                    supabase.table("project_urls").insert({
                        "project_id": str(project_id),
                        "url": current_page_url,
                        "conditions": conditions,
                        "display_format": display_format
                    }).execute()
            except Exception as e:
                print(f"Warning: Could not update project_urls table: {e}")
                print("This is expected if the table doesn't exist yet.")

            # Store display format and formatted tabular data in the session data
            supabase.table("scrape_sessions").update({
                "display_format": display_format,
                "formatted_tabular_data": json.dumps(formatted_data)
            }).eq("id", session_id_str).execute()

        except Exception as e:
            print(f"Error updating session data: {e}")

        # Add PDF download link
        download_links["pdf"] = f"/download/{project_id}/{session['id']}/pdf"

        return ExecuteScrapeResponse(
            status="success",
            message=f"Page {current_page_url} scraped successfully using Crawl4AI framework.",
            download_links=download_links,
            rag_status=session_status,
            embedding_cost_if_any=embedding_cost,
            tabular_data=tabular_data,
            fields=fields,
            display_format=display_format,
            formatted_data=formatted_data
        )

    async def get_session(self, session_id: UUID) -> ScrapedSessionResponse:
        """
        Get a scraping session by ID.

        Args:
            session_id (UUID): Session ID

        Returns:
            ScrapedSessionResponse: Scraping session

        Raises:
            HTTPException: If session not found
        """
        response = supabase.table("scrape_sessions").select("*").eq("id", str(session_id)).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Create a copy of the session data to modify
        session_data = dict(response.data)

        # Parse the structured_data_json field
        if "structured_data_json" in session_data and session_data["structured_data_json"]:
            try:
                structured_data = json.loads(session_data["structured_data_json"])
                session_data["structured_data"] = structured_data

                # Extract tabular data
                if "tabular_data" in structured_data:
                    session_data["tabular_data"] = structured_data["tabular_data"]

                    # Extract fields from the first row of tabular data
                    if structured_data["tabular_data"] and len(structured_data["tabular_data"]) > 0:
                        session_data["fields"] = list(structured_data["tabular_data"][0].keys())
            except Exception as e:
                print(f"Error parsing structured_data_json: {e}")

        # Parse the formatted_tabular_data field
        if "formatted_tabular_data" in session_data and session_data["formatted_tabular_data"]:
            try:
                formatted_data = json.loads(session_data["formatted_tabular_data"])
                session_data["formatted_tabular_data"] = formatted_data
            except Exception as e:
                print(f"Error parsing formatted_tabular_data: {e}")

        # Generate download links
        project_id = session_data["project_id"]
        session_data["download_link_json"] = f"/download/{project_id}/{session_data['id']}/json"
        session_data["download_link_csv"] = f"/download/{project_id}/{session_data['id']}/csv"

        return ScrapedSessionResponse(**session_data)

    async def delete_session(self, project_id: UUID, session_id: UUID) -> bool:
        """
        Delete a scraped session.
        Also deletes any associated RAG data (markdowns and embeddings).

        Args:
            project_id (UUID): Project ID
            session_id (UUID): Session ID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            # Get the session to retrieve the unique_scrape_identifier
            session_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("id", str(session_id)).eq("project_id", str(project_id)).single().execute()

            if not session_response.data:
                return False

            unique_scrape_identifier = session_response.data.get("unique_scrape_identifier")

            if unique_scrape_identifier:
                print(f"Deleting RAG data for unique_scrape_identifier: {unique_scrape_identifier}")
                # Delete associated embeddings
                supabase.table("embeddings").delete().eq("unique_name", unique_scrape_identifier).execute()

                # Delete associated markdown
                supabase.table("markdowns").delete().eq("unique_name", unique_scrape_identifier).execute()

            # Delete the session
            response = supabase.table("scrape_sessions").delete().eq("id", str(session_id)).eq("project_id", str(project_id)).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deleting session and associated RAG data: {e}")
            return False

    async def delete_session_by_id(self, session_id: UUID) -> bool:
        """
        Delete a scraping session by ID without requiring a project ID.
        Also deletes any associated RAG data (markdowns and embeddings).

        Args:
            session_id (UUID): Session ID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            # Get the session to retrieve the unique_scrape_identifier
            session_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("id", str(session_id)).single().execute()

            if not session_response.data:
                return False

            unique_scrape_identifier = session_response.data.get("unique_scrape_identifier")

            if unique_scrape_identifier:
                print(f"Deleting RAG data for unique_scrape_identifier: {unique_scrape_identifier}")
                # Delete associated embeddings
                supabase.table("embeddings").delete().eq("unique_name", unique_scrape_identifier).execute()

                # Delete associated markdown
                supabase.table("markdowns").delete().eq("unique_name", unique_scrape_identifier).execute()

            # Delete the session
            response = supabase.table("scrape_sessions").delete().eq("id", str(session_id)).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deleting session and associated RAG data: {e}")
            return False

    async def get_download_file(self, project_id: UUID, session_id: UUID, format: str):
        """
        Download scraped data in JSON, CSV, or PDF format.

        Args:
            project_id (UUID): Project ID
            session_id (UUID): Session ID
            format (str): Format ('json', 'csv', or 'pdf')

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

        # Get display format preference
        display_format = "table"  # Default

        # First try to get from session data (our fallback storage)
        try:
            if "display_format" in session and session["display_format"]:
                display_format = session["display_format"]
            else:
                # Try to get from project_urls table if it exists
                try:
                    project_url_response = supabase.table("project_urls").select("display_format").eq("project_id", str(project_id)).eq("url", session["url"]).execute()
                    if project_url_response.data:
                        display_format = project_url_response.data[0].get("display_format", "table")
                except Exception as e:
                    print(f"Warning: Could not get display format from project_urls: {e}")
                    print("This is expected if the table doesn't exist yet.")
        except Exception as e:
            print(f"Error getting display format: {e}")

        # Parse structured data
        structured_data = json.loads(session.get("structured_data_json", "{}"))
        tabular_data = structured_data.get("tabular_data", [])

        # Get fields from the first row of tabular data or from structured data
        fields = []
        if tabular_data and len(tabular_data) > 0:
            fields = list(tabular_data[0].keys())

        if format == "json":
            # Return JSON file
            # If display format is not table, format the data accordingly
            if display_format != "table" and tabular_data:
                formatted_data = await format_data_for_display(tabular_data, fields, display_format)
                if display_format == "paragraph":
                    content = json.dumps({"paragraph_data": formatted_data["paragraph_data"]})
                elif display_format == "raw":
                    content = json.dumps({"raw_data": formatted_data["raw_data"]})
                else:
                    content = json.dumps({"tabular_data": tabular_data})
            else:
                content = session.get("structured_data_json", "{}")

            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=scraped_data_{session_id}.json"}
            )
        elif format == "csv":
            # Convert JSON to CSV
            output = io.StringIO()
            writer = csv.writer(output)

            if tabular_data and len(tabular_data) > 0:
                # Write header
                writer.writerow(fields)

                # Write rows
                for row in tabular_data:
                    writer.writerow([row.get(field, "") for field in fields])
            else:
                # Fallback to old format
                writer.writerow(structured_data.keys())
                writer.writerow(structured_data.values())

            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=scraped_data_{session_id}.csv"}
            )
        elif format == "pdf":
            # For PDF, we'll use the paragraph format
            formatted_data = await format_data_for_display(tabular_data, fields, "paragraph")
            paragraph_data = formatted_data["paragraph_data"]

            # Create a simple HTML document that can be converted to PDF
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Scraped Data</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    pre {{ white-space: pre-wrap; background-color: #f5f5f5; padding: 10px; }}
                </style>
            </head>
            <body>
                <h1>Scraped Data from {session["url"]}</h1>
                <pre>{paragraph_data}</pre>
            </body>
            </html>
            """

            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f"attachment; filename=scraped_data_{session_id}.html"}
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
