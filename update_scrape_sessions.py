"""
Script to update the status of scrape sessions for a project.
"""
import os
import sys
from supabase import create_client, Client

def update_scrape_sessions(project_id):
    """
    Update the status of scrape sessions for a project.
    
    Args:
        project_id (str): Project ID
    """
    # Initialize Supabase client
    url = "https://slkzwhpfeauezoojlvou.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNsa3p3aHBmZWF1ZXpvb2psdm91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTY2NTY3NzYsImV4cCI6MjAzMjIzMjc3Nn0.Nh1qdoK3yFVdEbTGcJ1XA8TUYAcJ9jgv7kvMmX4hPLg"
    supabase = create_client(url, key)
    
    # Get all scrape sessions for the project
    sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
    sessions = sessions_response.data
    
    if not sessions:
        print(f"No scrape sessions found for project {project_id}")
        return
    
    print(f"Found {len(sessions)} scrape sessions for project {project_id}")
    
    # Update the status of each session to "rag_ingested"
    for session in sessions:
        session_id = session["id"]
        update_response = supabase.table("scrape_sessions").update({"status": "rag_ingested"}).eq("id", session_id).execute()
        if update_response.data:
            print(f"Updated session {session_id} to status 'rag_ingested'")
        else:
            print(f"Failed to update session {session_id}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_scrape_sessions.py <project_id>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    update_scrape_sessions(project_id)