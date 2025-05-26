"""
Script to ingest scraped content into the RAG system.
This script processes the raw_markdown content from scrape_sessions and creates embeddings for RAG.
"""
import asyncio
import sys
import os
import json
from uuid import UUID
import httpx
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import supabase
from app.services.rag_service import RAGService, generate_embeddings, chunk_text
from app.utils.websocket_manager import manager

async def ingest_scraped_content_for_project(project_id: str):
    """
    Ingest scraped content into the RAG system for a project.

    Args:
        project_id (str): Project ID
    """
    try:
        print(f"Starting RAG ingestion for project {project_id}")
        
        # Check if project exists
        project_response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        if not project_response.data:
            print(f"Project {project_id} not found")
            return

        print(f"Project {project_id} found: {project_response.data['name']}")

        # Enable RAG for the project if not already enabled
        if not project_response.data['rag_enabled']:
            supabase.table("projects").update({
                "rag_enabled": True
            }).eq("id", project_id).execute()
            print(f"RAG enabled for project {project_id}")
        else:
            print(f"RAG already enabled for project {project_id}")

        # Get all scrape sessions for this project
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
        if not sessions_response.data:
            print(f"No scrape sessions found for project {project_id}")
            return

        print(f"Found {len(sessions_response.data)} scrape sessions")

        # Azure OpenAI credentials - get from environment variables
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        azure_credentials = {
            'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
            'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'deployment_name': os.getenv('AZURE_EMBEDDING_MODEL', 'text-embedding-ada-002')
        }
        
        # Check if credentials are available
        if not azure_credentials['api_key'] or not azure_credentials['endpoint']:
            print("Warning: Azure OpenAI credentials not found in environment variables")
            print("Make sure AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are set")
            azure_credentials = None

        # Process each session
        for session in sessions_response.data:
            session_id = session['id']
            url = session['url']
            unique_scrape_identifier = session['unique_scrape_identifier']

            print(f"\nProcessing session {session_id} for URL: {url}")
            print(f"Session status: {session['status']}")

            # Process all sessions regardless of status
            print(f"Processing session {session_id} regardless of status")

            # Check if raw_markdown exists
            if not session.get('raw_markdown'):
                print(f"No raw_markdown found for session {session_id}, skipping")
                continue

            markdown_content = session['raw_markdown']
            print(f"Found raw_markdown content ({len(markdown_content)} characters)")

            # Check for structured data to use instead of full markdown
            structured_data = None
            if session.get('structured_data_json'):
                try:
                    import json
                    structured_data = json.loads(session['structured_data_json'])
                    print(f"Found structured data, will use it for RAG ingestion instead of full markdown")
                except Exception as e:
                    print(f"Error parsing structured_data_json: {e}")
                    structured_data = None

            # Use RAG service for ingestion
            from app.services.rag_service import RAGService
            rag_service = RAGService()
            
            try:
                await rag_service.ingest_scraped_content(
                    project_id=UUID(project_id),
                    session_id=UUID(session_id),
                    markdown_content=markdown_content,
                    azure_credentials=azure_credentials,
                    structured_data=structured_data
                )
                print(f"Content ingested successfully via RAG service for session {session_id}")
            except Exception as e:
                print(f"Failed to ingest content via RAG service for session {session_id}: {e}")
                continue

            # Update session status
            supabase.table("scrape_sessions").update({
                "status": "rag_ingested"
            }).eq("id", session_id).execute()

            print(f"Session {session_id} updated to status 'rag_ingested'")

        print(f"\nAll sessions processed for project {project_id}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ingest_scraped_content.py <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    asyncio.run(ingest_scraped_content_for_project(project_id))
