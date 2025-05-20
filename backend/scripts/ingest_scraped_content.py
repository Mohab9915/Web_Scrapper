"""
Script to ingest scraped content into the RAG system.
This script processes the raw_markdown content from scrape_sessions and creates embeddings for RAG.
"""
import asyncio
import sys
import os
from uuid import UUID
import httpx

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

        # Azure OpenAI credentials
        azure_credentials = {
            'api_key': 'BuVHZw4d7OmEwH5QIsvw8gsKLyRxNUow4PT1gYg83iukV6JLRVL8JQQJ99BDACHYHv6XJ3w3AAAAACOGR8LC',
            'endpoint': 'https://practicehub3994533910.services.ai.azure.com',
            'deployment_name': 'text-embedding-ada-002'
        }

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

            # Check if markdown already exists for this session
            markdown_response = supabase.table("markdowns").select("*").eq("unique_name", unique_scrape_identifier).execute()
            if markdown_response.data:
                print(f"Markdown already exists for session {session_id}, deleting existing entries")
                supabase.table("markdowns").delete().eq("unique_name", unique_scrape_identifier).execute()

            # Check if embeddings already exist for this session
            embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_scrape_identifier).execute()
            if embeddings_response.data:
                print(f"Embeddings already exist for session {session_id}, deleting existing entries")
                supabase.table("embeddings").delete().eq("unique_name", unique_scrape_identifier).execute()

            # Insert into markdowns table
            print(f"Inserting markdown content into markdowns table")
            markdown_response = supabase.table("markdowns").insert({
                "unique_name": unique_scrape_identifier,
                "url": url,
                "markdown": markdown_content
            }).execute()

            if not markdown_response.data:
                print(f"Failed to insert markdown content for session {session_id}")
                continue

            print(f"Markdown content inserted successfully")

            # Chunk the markdown content
            chunks = await chunk_text(markdown_content)
            print(f"Created {len(chunks)} chunks")

            # Generate embeddings for each chunk
            for i, chunk in enumerate(chunks):
                print(f"Generating embedding for chunk {i+1}/{len(chunks)}")
                embedding = await generate_embeddings(chunk, azure_credentials)

                # Insert into embeddings table
                supabase.table("embeddings").insert({
                    "unique_name": unique_scrape_identifier,
                    "chunk_id": i,
                    "content": chunk,
                    "embedding": embedding
                }).execute()

                print(f"Embedding {i+1} inserted successfully")

            print(f"All embeddings inserted successfully for session {session_id}")

            # Update session status
            supabase.table("scrape_sessions").update({
                "status": "rag_ingested"
            }).eq("id", session_id).execute()

            print(f"Session {session_id} updated to status 'rag_ingested'")

        print(f"\nAll sessions processed for project {project_id}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ingest_scraped_content.py <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    asyncio.run(ingest_scraped_content_for_project(project_id))
