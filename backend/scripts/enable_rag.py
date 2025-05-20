"""
Script to enable RAG for a project and process scraped content.
"""
import asyncio
import sys
import os
from uuid import UUID

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import supabase
from app.services.rag_service import RAGService

async def enable_rag_for_project(project_id: str):
    """
    Enable RAG for a project and process scraped content.
    
    Args:
        project_id (str): Project ID
    """
    try:
        # Check if project exists
        project_response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        if not project_response.data:
            print(f"Project {project_id} not found")
            return
        
        # Update project to enable RAG
        supabase.table("projects").update({
            "rag_enabled": True
        }).eq("id", project_id).execute()
        
        print(f"RAG enabled for project {project_id}")
        
        # Get all scrape sessions for this project
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
        if not sessions_response.data:
            print(f"No scrape sessions found for project {project_id}")
            return
        
        print(f"Found {len(sessions_response.data)} scrape sessions")
        
        # Update all sessions to be RAG ingested
        for session in sessions_response.data:
            supabase.table("scrape_sessions").update({
                "status": "rag_ingested"
            }).eq("id", session["id"]).execute()
            print(f"Updated session {session['id']} to status 'rag_ingested'")
        
        print(f"All sessions updated for project {project_id}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python enable_rag.py <project_id>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    asyncio.run(enable_rag_for_project(project_id))
