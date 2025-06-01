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
import asyncio # Added for loop.run_in_executor
import os # Added for os.environ manipulation

from ..database import supabase
from ..models.scrape_session import ScrapedSessionResponse, InteractiveScrapingResponse, ExecuteScrapeResponse, ExecuteScrapeRequest
from ..utils.browser_control import launch_browser_session # Keep for interactive, if still used
# Removed: from app.utils.text_processing import structure_scraped_data, format_data_for_display
# Removed: from app.utils.crawl4ai_crawler import scrape_url, extract_structured_data, AZURE_EMBEDDING_MODEL, AZURE_CHAT_MODEL
from ..utils.text_processing import format_data_for_display # Added import

# New imports from Scrape_Master modules
from ..scraper_modules.markdown import fetch_and_store_markdowns, read_raw_data
from ..scraper_modules.scraper import scrape_urls as new_scrape_structured_data # aliased
from ..scraper_modules.assets import AZURE_CHAT_MODEL, AZURE_EMBEDDING_MODEL # Keep AZURE_EMBEDDING_MODEL if RAG uses it
# Note: AZURE_CHAT_MODEL might not be used by the new scraper logic directly, review if needed for RAG or other parts.
# The new scraper uses LiteLLM, so model selection is handled differently.

from .rag_service import RAGService
# Need to handle text_processing functions if they are still required
# For now, assuming new scraper modules handle their formatting, or it's simplified.
# If format_data_for_display is crucial, it needs to be re-evaluated.
# For structure_scraped_data, its role is now taken by new_scrape_structured_data + LLM call.

class ScrapingService:
    """Service for web scraping."""

    def __init__(self, rag_service: RAGService = Depends()):
        self.rag_service = rag_service

    async def get_sessions_by_project(self, project_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all URLs for a project, including their latest scrape session data if available.
        Args:
            project_id (UUID): Project ID
        Returns:
            List[Dict[str, Any]]: List of URLs with their status and latest scrape data.
        """
        # Get project URLs first
        project_urls_response = supabase.table("project_urls").select(
            "id, project_id, url, conditions, display_format, created_at, status, rag_enabled, last_scraped_session_id"
        ).eq("project_id", str(project_id)).order("created_at", desc=True).execute()

        if not project_urls_response.data:
            return []

        results = []
        for pu_entry in project_urls_response.data:
            session_data_for_model = {}
            raw_session_data = None

            # Get the session data separately if last_scraped_session_id exists
            if pu_entry.get("last_scraped_session_id"):
                try:
                    session_response = supabase.table("scrape_sessions").select(
                        "id, project_id, url, scraped_at, status, raw_markdown, structured_data_json, display_format, formatted_tabular_data"
                    ).eq("id", pu_entry["last_scraped_session_id"]).single().execute()

                    if session_response.data:
                        raw_session_data = session_response.data
                        print(f"Found session data for URL {pu_entry['url']}: {raw_session_data['id']}")
                except Exception as e:
                    print(f"Error fetching session data for {pu_entry['url']}: {e}")
                    raw_session_data = None

            if raw_session_data and isinstance(raw_session_data, dict) and raw_session_data.get("id"):
                print(f"Processing session data for URL {pu_entry['url']}: {raw_session_data['id']}")
                print(f"Session has raw_markdown: {bool(raw_session_data.get('raw_markdown'))}")
                print(f"Session has structured_data_json: {bool(raw_session_data.get('structured_data_json'))}")

                # Copy raw data to prepare for model instantiation
                session_data_for_model = dict(raw_session_data)

                # Reconstruct derived fields for ScrapedSessionResponse
                # structured_data, tabular_data, fields

                # Get fields from project_urls.conditions first, as this is the source of truth for desired columns
                conditions_str = pu_entry.get("conditions", "")
                session_fields = [field.strip() for field in conditions_str.split(',')] if conditions_str else []
                session_data_for_model["fields"] = session_fields

                if "structured_data_json" in session_data_for_model and session_data_for_model["structured_data_json"]:
                    try:
                        structured_data = json.loads(session_data_for_model["structured_data_json"])
                        session_data_for_model["structured_data"] = structured_data  # Keep the parsed dict
                        
                        current_tabular_data = []
                        if isinstance(structured_data.get("listings"), list):
                            current_tabular_data = structured_data["listings"]
                        elif isinstance(structured_data, list): # Should not happen with current LLM output but robust
                            current_tabular_data = structured_data
                        elif isinstance(structured_data, dict):
                            # If it's a dict, and not 'listings', treat the dict itself as a single row
                            current_tabular_data = [structured_data]
                        
                        session_data_for_model["tabular_data"] = current_tabular_data
                        
                        # If fields were not derived from conditions (e.g. conditions were empty), 
                        # try to get them from the first row of the reconstructed tabular_data.
                        # However, conditions should be the primary source.
                        if not session_fields and current_tabular_data and isinstance(current_tabular_data[0], dict):
                            session_data_for_model["fields"] = list(current_tabular_data[0].keys())
                        
                    except Exception as e:
                        print(f"Error parsing structured_data_json for session {session_data_for_model.get('id')}: {e}")
                        session_data_for_model["structured_data"] = None # Nullify on error
                        session_data_for_model["tabular_data"] = []
                        # Fields are already set from conditions or will remain empty if conditions were empty
                else: 
                    session_data_for_model["structured_data"] = None
                    session_data_for_model["tabular_data"] = []
                    # Fields are already set from conditions or will remain empty if conditions were empty

                # formatted_tabular_data (already fetched as JSON string, parse it)
                if "formatted_tabular_data" in session_data_for_model and session_data_for_model["formatted_tabular_data"]:
                    try:
                        # Ensure it's a string before trying to load if it might already be parsed by some Supabase clients
                        if isinstance(session_data_for_model["formatted_tabular_data"], str):
                           session_data_for_model["formatted_tabular_data"] = json.loads(session_data_for_model["formatted_tabular_data"])
                        # If it's already a dict (parsed by Supabase client), use as is.
                        elif not isinstance(session_data_for_model["formatted_tabular_data"], dict):
                            print(f"Warning: formatted_tabular_data for session {session_data_for_model.get('id')} is not a string or dict. Type: {type(session_data_for_model['formatted_tabular_data'])}")
                            session_data_for_model["formatted_tabular_data"] = None # Nullify if unexpected type
                    except Exception as e:
                        print(f"Error parsing formatted_tabular_data for session {session_data_for_model.get('id')}: {e}")
                        session_data_for_model["formatted_tabular_data"] = None # Nullify on error
                else:
                     session_data_for_model["formatted_tabular_data"] = None


                # Download links
                session_id_str = str(session_data_for_model['id'])
                session_data_for_model["download_link_json"] = f"/download/{project_id}/{session_id_str}/json"
                session_data_for_model["download_link_csv"] = f"/download/{project_id}/{session_id_str}/csv"
                # Note: ScrapedSessionResponse model doesn't have download_link_pdf, so it won't be used by Pydantic

                # Ensure all required fields for ScrapedSessionResponse are present before instantiation
                # id, project_id, url, created_at (for scraped_at), status are directly from DB select
                # If any are missing, Pydantic will raise error. The explicit select should prevent this.
                # The model expects 'url' as HttpUrl, 'id' as UUID, 'project_id' as UUID.
                # Data from Supabase for these fields should be compatible.
                # 'created_at' will be used for 'scraped_at' due to alias.

            # Clean pu_entry by removing the joined data before spreading
            pu_data_cleaned = {k: v for k, v in pu_entry.items() if k != 'latest_session_data'}
            
            final_session_data_obj = None
            if session_data_for_model and session_data_for_model.get("id"):
                try:
                    print(f"Attempting to create ScrapedSessionResponse for session {session_data_for_model.get('id')}")
                    print(f"Session data keys: {list(session_data_for_model.keys())}")
                    final_session_data_obj = ScrapedSessionResponse(**session_data_for_model)
                    print(f"✓ Successfully created ScrapedSessionResponse")
                except Exception as e: # Catch Pydantic validation error
                    print(f"✗ Pydantic validation error for session {session_data_for_model.get('id')}: {e}")
                    print(f"Session data for debugging: {session_data_for_model}")
                    # Continue without the session data rather than failing completely
                    final_session_data_obj = None
            
            print(f"Adding result with latest_scrape_data: {type(final_session_data_obj)}")
            if final_session_data_obj:
                print(f"Session object has raw_markdown: {bool(getattr(final_session_data_obj, 'markdown_content', None))}")
                print(f"Session object has structured_data: {bool(getattr(final_session_data_obj, 'structured_data', None))}")

            results.append({
                **pu_data_cleaned,
                "latest_scrape_data": final_session_data_obj
            })
            
        return results

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
        rag_enabled_for_project = project.get("rag_enabled", False) # RAG enabled for the whole project

        # Extract parameters from the request
        current_page_url = request.current_page_url

        # Validate URL format
        if not current_page_url or not isinstance(current_page_url, str):
            raise HTTPException(status_code=400, detail="URL is required and must be a valid string")

        # Basic URL validation
        if not (current_page_url.startswith('http://') or current_page_url.startswith('https://')):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

        # session_id from request is for interactive scraping, we'll generate a new one for this execution
        api_keys = request.api_keys
        force_refresh = request.force_refresh
        display_format = request.display_format or "table"
        request_conditions = request.conditions

        # Determine if RAG is enabled for this specific URL
        # This will be fetched/updated later, default to project setting for now
        rag_enabled_for_url = rag_enabled_for_project

        # Manage project_urls entry
        project_url_entry = None
        try:
            project_url_response = supabase.table("project_urls").select("*").eq("project_id", str(project_id)).eq("url", current_page_url).execute()
            if project_url_response.data and len(project_url_response.data) > 0:
                project_url_entry = project_url_response.data[0]
                rag_enabled_for_url = project_url_entry.get("rag_enabled", rag_enabled_for_project) # Use URL specific RAG setting if available
                # If re-scraping, delete old session and its RAG data
                if project_url_entry.get("last_scraped_session_id"):
                    old_session_id = project_url_entry["last_scraped_session_id"]
                    print(f"Deleting old scrape session {old_session_id} for URL {current_page_url}")
                    await self.delete_session_by_id(UUID(old_session_id)) # delete_session_by_id handles RAG data deletion
                
                # Update status to 'processing'
                supabase.table("project_urls").update({"status": "processing"}).eq("id", project_url_entry["id"]).execute()
            else:
                # Insert new entry with 'pending' status, will be updated to 'processing'
                new_project_url_data = {
                    "project_id": str(project_id),
                    "url": current_page_url,
                    "conditions": request_conditions or "title, description, price, content", # Default conditions if not provided
                    "display_format": display_format,
                    "status": "processing", # Start as processing
                    "rag_enabled": rag_enabled_for_url # Use project's RAG setting by default for new URLs
                }
                insert_response = supabase.table("project_urls").insert(new_project_url_data).execute()
                if insert_response.data:
                    project_url_entry = insert_response.data[0]
                else:
                    raise HTTPException(status_code=500, detail="Failed to create project URL entry.")
        except Exception as e:
            print(f"Error managing project_urls entry: {e}")
            raise HTTPException(status_code=500, detail=f"Error managing project_urls entry: {str(e)}")

        # Generate a new session_id for this scrape execution
        current_session_id = str(uuid4())

        try:
            # Check if caching is enabled for this project
            caching_enabled = project.get("caching_enabled", True)
            use_force_refresh = force_refresh or not caching_enabled

            # --- New Scraper Logic ---
            # 1. Fetch and store markdown
            # fetch_and_store_markdowns expects a list of URLs.
            # It internally calls crawl4ai's AsyncWebCrawler.
            print(f"Attempting to fetch markdown for URL: {current_page_url} with new scraper logic.")
            unique_names_list = await fetch_and_store_markdowns([current_page_url])
            if not unique_names_list:
                raise HTTPException(status_code=500, detail="Failed to generate unique name or initial markdown fetch failed.")
            unique_name = unique_names_list[0]

            # 2. Read the stored raw markdown
            # read_raw_data is synchronous. Call it using run_in_executor.
            loop = asyncio.get_event_loop()
            markdown_content = await loop.run_in_executor(None, read_raw_data, unique_name)
            # Removed incorrect line: markdown_content = await read_raw_data(unique_name)


            if not markdown_content:
                markdown_content = f"# Failed to scrape content from {current_page_url}\n\nThe scraping operation did not return any content."
                # Update status to failed if markdown is empty after fetch
                if project_url_entry:
                    supabase.table("project_urls").update({"status": "failed"}).eq("id", project_url_entry["id"]).execute()
                # Also update session if one was to be created
                # For now, we'll let it proceed to create a session with this error message.

            # Ensure page title is at the start of markdown_content (if possible)
            # The new scraper's markdown might already include it. This part might need review.
            # For now, let's assume markdown_content is complete.

        except Exception as e:
            if project_url_entry:
                supabase.table("project_urls").update({"status": "failed"}).eq("id", project_url_entry["id"]).execute()
            print(f"Error during markdown fetching stage with new scraper: {e}")
            raise HTTPException(status_code=500, detail=f"Failed during markdown fetching: {str(e)}")

        # Determine conditions (fields to extract)
        conditions_str = request_conditions
        if not conditions_str and project_url_entry and project_url_entry.get("conditions"):
            conditions_str = project_url_entry["conditions"]
        if not conditions_str: # Fallback to default
            conditions_str = "title, description, price, content" # Default from old logic
        
        fields = [field.strip() for field in conditions_str.split(',')] # Renamed fields_list to fields

        # Update conditions in project_urls if they changed or were defaulted
        if project_url_entry and project_url_entry.get("conditions") != conditions_str:
             supabase.table("project_urls").update({"conditions": conditions_str}).eq("id", project_url_entry["id"]).execute()

        # Set API keys as environment variables for LiteLLM, if provided in request
        # This is a temporary workaround for backend usage. Proper config management is better.
        if api_keys:
            for key_name, key_value in api_keys.items():
                # Ensure key_name matches expected env var names like OPENAI_API_KEY, GEMINI_API_KEY
                # This part needs to be robust. For now, assuming direct match or specific handling.
                # Example: if api_keys = {"OPENAI_API_KEY": "sk-...", "model_name": "gpt-4o-mini"}
                if key_value: # Only set if value is provided
                    os.environ[key_name.upper()] = key_value # Make sure it's upper, e.g. openai_api_key -> OPENAI_API_KEY

        # Create new scrape session FIRST (before calling scraper modules)
        session_data = {
            "id": current_session_id,
            "project_id": str(project_id),
            "url": current_page_url,
            "scraped_at": datetime.now().isoformat(),  # Convert datetime to ISO string
            "raw_markdown": markdown_content,
            "structured_data_json": "{}",  # Placeholder, will be updated after LLM processing
            "status": "scraped", # Use valid status value (only "scraped" and "rag_ingested" are allowed)
            "display_format": display_format,
            "formatted_tabular_data": "{}",  # Placeholder, will be updated after LLM processing
            # unique_scrape_identifier will be generated by Supabase trigger or set if needed
        }

        print(f"🔄 Creating session with ID: {current_session_id}")
        session_response = supabase.table("scrape_sessions").insert(session_data).execute()
        if not session_response.data:
            print(f"❌ Failed to create session - no data returned")
            if project_url_entry:
                supabase.table("project_urls").update({"status": "failed"}).eq("id", project_url_entry["id"]).execute()
            raise HTTPException(status_code=500, detail="Failed to create scrape session")

        created_session = session_response.data[0]
        print(f"✅ Session created successfully: {created_session['id']}")
        print(f"📝 Session unique_scrape_identifier: {created_session.get('unique_scrape_identifier', 'N/A')}")

        # 3. Parse structured data using LLM via new_scrape_structured_data
        # Use gpt-4o - excellent accuracy for data extraction
        selected_model_name = "gpt-4o"  # Best model for accurate data extraction

        # Set up Azure OpenAI environment variables for LiteLLM
        # Use provided credentials or fallback to environment variables
        azure_api_key = None
        azure_endpoint = None
        azure_api_version = "2024-05-01-preview"

        if api_keys and api_keys.get("api_key") and api_keys.get("endpoint"):
            azure_api_key = api_keys["api_key"]
            azure_endpoint = api_keys["endpoint"]
            azure_api_version = api_keys.get("api_version", "2024-12-01-preview")
        else:
            # Fallback to environment variables
            azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

        use_azure_for_structuring = azure_api_key and azure_endpoint

        # Check if content is too large for LLM processing (>50KB)
        # Increased limit to allow LLM processing for more content
        content_too_large = len(markdown_content) > 50000

        if content_too_large:
            print(f"Content is large ({len(markdown_content)} chars), using fallback extraction even with Azure credentials")
            use_azure_for_structuring = False

        if use_azure_for_structuring:
            # Set Azure AI environment variables for LiteLLM
            # Remove trailing slash from endpoint if present
            clean_endpoint = azure_endpoint.rstrip('/')
            os.environ["AZURE_AI_API_KEY"] = azure_api_key
            os.environ["AZURE_AI_API_BASE"] = clean_endpoint

            # Also set Azure OpenAI environment variables for backward compatibility
            os.environ["AZURE_OPENAI_API_KEY"] = azure_api_key
            os.environ["AZURE_OPENAI_ENDPOINT"] = azure_endpoint
            os.environ["AZURE_OPENAI_API_VERSION"] = azure_api_version
            os.environ["AZURE_OPENAI_API_BASE"] = clean_endpoint

            # Don't set deployment name - use standard OpenAI model instead
            # This avoids LiteLLM mapping issues with custom deployment names

            # Also set the OPENAI_API_KEY for the Scrape_Master module compatibility
            os.environ["OPENAI_API_KEY"] = azure_api_key
        else:
            print("Azure OpenAI credentials not provided, using fallback data structuring")

        structured_data_results = None
        print(f"🧠 Starting LLM processing with Azure: {use_azure_for_structuring}")
        try:
            if use_azure_for_structuring:
                print(f"🔑 Using Azure OpenAI for data structuring")
                print(f"📊 Content length: {len(markdown_content)} chars")
                print(f"🎯 Fields to extract: {fields}")
                print(f"🤖 Model: {selected_model_name}")

                # Use Azure OpenAI for data structuring
                # new_scrape_structured_data returns: total_input_tokens, total_output_tokens, total_cost, parsed_results
                # parsed_results is a list of dicts: [{"unique_name": uniq, "parsed_data": parsed}]
                print(f"🚀 Calling LLM with unique_name: {unique_name}")
                _, _, _, parsed_results_list = await loop.run_in_executor(None, new_scrape_structured_data, [unique_name], fields, selected_model_name) # Used fields
                print(f"📥 LLM call completed. Results: {len(parsed_results_list) if parsed_results_list else 0}")

                if parsed_results_list and parsed_results_list[0].get("parsed_data"):
                    structured_data_raw = parsed_results_list[0]["parsed_data"]
                    print(f"✅ Got structured data from LLM: {type(structured_data_raw)}")
                    # The 'parsed_data' from Scrape_Master is already the structured dict/Pydantic model
                    # It's often a container like {"listings": [...]}
                    if hasattr(structured_data_raw, "model_dump"): # Pydantic model
                        structured_data = structured_data_raw.model_dump()
                        print(f"📋 Converted Pydantic model to dict")
                    elif isinstance(structured_data_raw, str): # JSON string
                        structured_data = json.loads(structured_data_raw)
                        print(f"📋 Parsed JSON string to dict")
                    else: # Already a dict
                        structured_data = structured_data_raw
                        print(f"📋 Using dict as-is")
                    print(f"📊 Final structured data keys: {list(structured_data.keys()) if isinstance(structured_data, dict) else 'Not a dict'}")
                else:
                    print(f"❌ No valid parsed data from LLM")
                    structured_data = {"error": "Failed to parse structured data with Azure OpenAI."}
                    tabular_data = []
            else:
                # Fallback: Simple data extraction from markdown without LLM
                print("🔄 Using fallback data structuring (no Azure OpenAI)")
                structured_data, tabular_data = await self._extract_data_fallback(markdown_content, fields)
                print(f"📊 Fallback extraction completed: {len(tabular_data) if tabular_data else 0} items")

        except Exception as e:
            print(f"❌ Exception in LLM processing: {e}")
            print(f"🔍 Exception type: {type(e)}")
            import traceback
            print(f"📋 Full traceback: {traceback.format_exc()}")

            if use_azure_for_structuring:
                print(f"🔄 Error structuring data with Azure OpenAI, falling back to simple extraction: {e}")
                # Fallback to simple extraction if Azure fails
                try:
                    print(f"🔄 Attempting fallback extraction...")
                    structured_data, tabular_data = await self._extract_data_fallback(markdown_content, fields)
                    print(f"✅ Fallback extraction succeeded")
                except Exception as fallback_error:
                    print(f"❌ Fallback extraction also failed: {fallback_error}")
                    structured_data = {"error": f"Both Azure OpenAI and fallback extraction failed: {str(e)}", "raw_markdown_preview": markdown_content[:500]}
                    tabular_data = []
            else:
                print(f"❌ Error with fallback data structuring: {e}")
                structured_data = {"error": f"Fallback extraction failed: {str(e)}", "raw_markdown_preview": markdown_content[:500]}
                tabular_data = []

        # Continue with existing logic for processing structured_data
        if 'tabular_data' not in locals() and isinstance(structured_data, dict) and 'error' not in structured_data:

                # The Scrape_Master format is often {"listings": [...]}.
                # The old format expected {"tabular_data": [...]}. We need to adapt.
                # For now, let's assume the new 'structured_data' is the primary output.
                # If it contains 'listings', we can map that to 'tabular_data'.
                tabular_data = [] # Default to empty list
                if isinstance(structured_data, list):
                    # If structured_data is already a list, use it directly
                    tabular_data = structured_data
                elif isinstance(structured_data, dict):
                    # Check for a "listings" key
                    if "listings" in structured_data and isinstance(structured_data.get("listings"), list):
                        tabular_data = structured_data["listings"]
                    else:
                        # Try to find another key that holds a list of dicts (potential items)
                        found_list_in_dict = False
                        for key, value in structured_data.items():
                            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                # Heuristic: if items in this list seem to match the requested fields, use this list
                                # Or if no fields were specified (e.g. "all"), take the first list of dicts.
                                if not fields or all(f in value[0] for f in fields):
                                    tabular_data = value
                                    found_list_in_dict = True
                                    break
                        if not found_list_in_dict:
                            # If no specific list of items found, and the structured_data dict itself matches the fields,
                            # treat the entire dict as a single-item list.
                            if not fields or all(f in structured_data for f in fields):
                                tabular_data = [structured_data]
                            # else:
                                # If the dict doesn't match fields and no inner list was suitable,
                                # tabular_data remains empty. A warning could be logged here.
                                # print(f"Warning: LLM output (execute_scrape) is a dict but couldn't find a clear list of items or direct field matches for fields: {fields}. Structured data: {structured_data}")
                # If structured_data is not a list or dict, tabular_data remains []

        # format_data_for_display is from old text_processing, may need replacement or adaptation
        # For now, let's create a simplified formatted_data or pass raw tabular_data
        # The Scrape_Master streamlit app handles display directly from the structured JSON.
        # Use the format_data_for_display utility to prepare the formatted_data dictionary
        formatted_data = await format_data_for_display(
            tabular_data=tabular_data,
            fields=fields,
            display_format=display_format,
            full_markdown_content=markdown_content
        )

        # Update the session with the actual structured data and formatted data
        print(f"🔄 Updating session {created_session['id']} with processed data")
        print(f"📊 Structured data size: {len(json.dumps(structured_data))} chars")
        print(f"📋 Formatted data size: {len(json.dumps(formatted_data))} chars")

        try:
            update_response = supabase.table("scrape_sessions").update({
                "structured_data_json": json.dumps(structured_data),
                "formatted_tabular_data": json.dumps(formatted_data),
                "status": "scraped"  # Update status to scraped
            }).eq("id", created_session["id"]).execute()

            if update_response.data:
                print(f"✅ Session updated successfully")
            else:
                print(f"⚠️ Session update returned no data")

        except Exception as e:
            print(f"❌ Failed to update session: {e}")
            raise

        # Clean up environment variables if set
        if api_keys:
            for key_name in api_keys.keys():
                if key_name.upper() in os.environ:
                    del os.environ[key_name.upper()]

        # Clean up Azure AI and Azure OpenAI environment variables
        azure_env_vars = [
            "AZURE_AI_API_KEY", "AZURE_AI_API_BASE",
            "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_API_BASE", "OPENAI_API_TYPE", "OPENAI_API_VERSION", "OPENAI_API_KEY"
        ]
        for env_var in azure_env_vars:
            if env_var in os.environ:
                del os.environ[env_var]

        # Update project_urls with the new session_id and status
        if project_url_entry:
            supabase.table("project_urls").update({
                "last_scraped_session_id": created_session["id"],
                "status": "processing_rag" if rag_enabled_for_url else "completed", # Set to processing_rag or completed
                "display_format": display_format # Also update display_format
            }).eq("id", project_url_entry["id"]).execute()

        embedding_cost = 0.0
        rag_status_message = "RAG not enabled for this URL."

        if rag_enabled_for_url:
            # Prepare embedding API keys (can work with or without Azure credentials)
            embedding_api_keys = {}
            if api_keys and api_keys.get('api_key') and api_keys.get('endpoint'):
                embedding_api_keys = {**api_keys, "deployment_name": AZURE_EMBEDDING_MODEL}
                rag_status_message = "Processing for RAG"  # Frontend expects this exact string
            else:
                rag_status_message = "Processing for RAG"  # Frontend expects this exact string
            
            # Pass project_url_entry_id to RAG service for status updates
            project_url_id_for_rag = project_url_entry["id"] if project_url_entry else None

            # Use enhanced RAG service for better structured data processing
            from .enhanced_rag_service import EnhancedRAGService
            enhanced_rag = EnhancedRAGService()

            background_tasks.add_task(
                enhanced_rag.ingest_structured_content,
                project_id,
                created_session["id"],
                structured_data,
                embedding_api_keys,
                project_url_id_for_rag # Pass the ID of the project_urls entry
            )
            num_tokens = len(markdown_content) / 4
            embedding_cost = (num_tokens / 1000) * 0.0001
        else: # RAG not enabled for URL
            if project_url_entry: # Ensure status is 'completed' if RAG is not run
                 supabase.table("project_urls").update({"status": "completed"}).eq("id", project_url_entry["id"]).execute()


        download_links = {
            "json": f"/download/{project_id}/{created_session['id']}/json",
            "csv": f"/download/{project_id}/{created_session['id']}/csv",
            "pdf": f"/download/{project_id}/{created_session['id']}/pdf"
        }

        return ExecuteScrapeResponse(
            status="success",
            message=f"Page {current_page_url} scraped. Status: {rag_status_message}",
            session_id=str(created_session["id"]),  # Add session_id to response
            download_links=download_links,
            rag_status=rag_status_message,
            embedding_cost_if_any=embedding_cost,
            tabular_data=tabular_data,
            tabularData=tabular_data,  # Add camelCase version for frontend compatibility
            fields=fields,
            display_format=display_format,
            displayFormat=display_format,  # Add camelCase version for frontend compatibility
            formatted_data=formatted_data,
            formattedData=formatted_data  # Add camelCase version for frontend compatibility
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

                # Extract tabular data (check both 'tabular_data' and 'listings' keys)
                tabular_data = None
                if "tabular_data" in structured_data:
                    tabular_data = structured_data["tabular_data"]
                elif "listings" in structured_data:
                    tabular_data = structured_data["listings"]

                if tabular_data:
                    session_data["tabular_data"] = tabular_data

                    # Extract fields from the first row of tabular data
                    if tabular_data and len(tabular_data) > 0:
                        session_data["fields"] = list(tabular_data[0].keys())
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

    async def _extract_data_fallback(self, markdown_content: str, fields: List[str]) -> tuple:
        """
        Fallback data extraction method that works without LLM.
        Extracts structured data from markdown using simple pattern matching.
        Specifically designed for the countries page format.

        Args:
            markdown_content (str): Raw markdown content
            fields (List[str]): Fields to extract

        Returns:
            tuple: (structured_data, tabular_data)
        """
        try:
            import re

            # Initialize result structure
            tabular_data = []

            print(f"Fallback extraction processing {len(markdown_content)} characters")

            # For the countries page, look for the specific pattern:
            # ### Country Name
            # **Capital:** City Name
            # **Population:** Number
            # **Area (km2):** Number

            # Split content by country headers (###)
            country_sections = re.split(r'\n###\s+', markdown_content)

            print(f"Found {len(country_sections)} potential country sections")

            for i, section in enumerate(country_sections):
                if i == 0:
                    # Skip the first section (header content)
                    continue

                # Extract country name (first line)
                lines = section.strip().split('\n')
                if not lines:
                    continue

                country_name = lines[0].strip()

                # Initialize country data with user-specified field names
                country_data = {}

                # Map country name to user-requested field
                # Check if user requested 'name', 'country', 'title', etc.
                name_field = None
                for field in fields:
                    if field.lower() in ['name', 'country', 'title', 'item_name', 'product_name']:
                        name_field = field
                        break

                # If no name-like field requested, use 'country' as fallback
                if name_field:
                    country_data[name_field] = country_name
                else:
                    country_data['country'] = country_name

                # Extract capital, population, and area from the section
                # Join all lines to handle multi-line formatting
                section_text = ' '.join(lines[1:])

                # Only extract fields that the user requested
                for field in fields:
                    field_lower = field.lower()

                    # Skip name field as it's already handled above
                    if field_lower in ['name', 'country', 'title', 'item_name', 'product_name']:
                        continue

                    # Map user field to website data
                    if field_lower in ['capital', 'city']:
                        capital_match = re.search(r'\*\*Capital:\*\*\s*([^*]+?)(?:\s*\*\*|$)', section_text)
                        if capital_match:
                            country_data[field] = capital_match.group(1).strip()

                    elif field_lower in ['population', 'people', 'inhabitants']:
                        population_match = re.search(r'\*\*Population:\*\*\s*([^*]+?)(?:\s*\*\*|$)', section_text)
                        if population_match:
                            country_data[field] = population_match.group(1).strip()

                    elif field_lower in ['area', 'size', 'surface', 'land_area']:
                        area_match = re.search(r'\*\*Area \([^)]*\):\*\*\s*([^*]+?)(?:\s*\*\*|$)', section_text)
                        if area_match:
                            country_data[field] = area_match.group(1).strip()

                    # If field not found, add empty value to maintain structure
                    if field not in country_data:
                        country_data[field] = ""

                # Only add if we have at least country name and one other field
                if len(country_data) > 1:
                    tabular_data.append(country_data)

            # Create structured data
            structured_data = {
                "listings": tabular_data,
                "extraction_method": "fallback_user_focused_pattern_matching",
                "total_items": len(tabular_data),
                "requested_fields": fields
            }

            print(f"Fallback extraction found {len(tabular_data)} countries")

            # Show sample of extracted data
            if tabular_data:
                print(f"Sample country: {tabular_data[0]}")
                if len(tabular_data) > 1:
                    print(f"Last country: {tabular_data[-1]}")

            return structured_data, tabular_data

        except Exception as e:
            print(f"Error in fallback data extraction: {e}")
            import traceback
            traceback.print_exc()

            # Return minimal structure
            structured_data = {
                "error": f"Fallback extraction failed: {str(e)}",
                "raw_preview": markdown_content[:500]
            }
            return structured_data, []

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
        # Check both 'tabular_data' and 'listings' keys for compatibility
        tabular_data = structured_data.get("tabular_data", [])
        if not tabular_data and "listings" in structured_data:
            tabular_data = structured_data["listings"]

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
