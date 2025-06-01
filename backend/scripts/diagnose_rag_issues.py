"""
Diagnostic script to identify and fix RAG system issues.
This script checks for sessions that should have RAG data but don't.
"""
import asyncio
import sys
import os
from uuid import UUID
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import supabase
from app.services.rag_service import RAGService
from app.utils.embedding import generate_embeddings

load_dotenv()

async def diagnose_rag_issues():
    """
    Diagnose RAG system issues by checking data consistency.
    """
    print("=== RAG SYSTEM DIAGNOSTIC ===\n")
    
    # Get all projects with RAG enabled
    projects_response = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    if not projects_response.data:
        print("No projects with RAG enabled found.")
        return
    
    for project in projects_response.data:
        project_id = project["id"]
        project_name = project["name"]
        
        print(f"Checking project: {project_name} ({project_id})")
        print("-" * 50)
        
        # Get all scrape sessions for this project
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
        
        if not sessions_response.data:
            print("  No scrape sessions found.")
            continue
        
        for session in sessions_response.data:
            session_id = session["id"]
            session_status = session["status"]
            session_url = session["url"]
            unique_identifier = session["unique_scrape_identifier"]
            
            print(f"  Session: {session_id}")
            print(f"    URL: {session_url}")
            print(f"    Status: {session_status}")
            print(f"    Unique ID: {unique_identifier}")
            
            # Check if markdown exists
            markdown_response = supabase.table("markdowns").select("*").eq("unique_name", unique_identifier).execute()
            markdown_exists = len(markdown_response.data) > 0
            
            # Check if embeddings exist
            embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_identifier).execute()
            embeddings_count = len(embeddings_response.data)
            
            print(f"    Markdown exists: {markdown_exists}")
            print(f"    Embeddings count: {embeddings_count}")
            
            # Identify issues
            issues = []
            if session_status == "scraped" and not markdown_exists:
                issues.append("Session marked as scraped but no markdown found")
            if session_status == "scraped" and embeddings_count == 0:
                issues.append("Session marked as scraped but no embeddings found - needs RAG processing")
            if session_status == "rag_ingested" and embeddings_count == 0:
                issues.append("Session marked as rag_ingested but no embeddings found")
            if markdown_exists and embeddings_count == 0:
                issues.append("Markdown exists but no embeddings - incomplete RAG processing")
            
            if issues:
                print(f"    ISSUES FOUND:")
                for issue in issues:
                    print(f"      - {issue}")
            else:
                print(f"    Status: OK")
            
            print()
        
        print()

async def fix_rag_issues():
    """
    Attempt to fix identified RAG issues by processing stuck sessions.
    """
    print("=== FIXING RAG ISSUES ===\n")
    
    # Get Azure credentials
    azure_credentials = {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    }
    
    if not azure_credentials["api_key"] or not azure_credentials["endpoint"]:
        print("ERROR: Azure OpenAI credentials not found in environment variables.")
        print("Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")
        return
    
    # Get all projects with RAG enabled
    projects_response = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    rag_service = RAGService()
    
    for project in projects_response.data:
        project_id = project["id"]
        project_name = project["name"]
        
        print(f"Processing project: {project_name} ({project_id})")
        
        # Get sessions that need RAG processing
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).eq("status", "scraped").execute()
        
        for session in sessions_response.data:
            session_id = session["id"]
            session_url = session["url"]
            unique_identifier = session["unique_scrape_identifier"]
            raw_markdown = session.get("raw_markdown", "")
            
            if not raw_markdown:
                print(f"  Skipping session {session_id} - no raw markdown content")
                continue
            
            print(f"  Processing session: {session_id}")
            print(f"    URL: {session_url}")
            
            try:
                # Check if embeddings already exist
                embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_identifier).execute()
                if embeddings_response.data:
                    print(f"    Embeddings already exist, updating status to rag_ingested")
                    supabase.table("scrape_sessions").update({"status": "rag_ingested"}).eq("id", session_id).execute()
                    continue
                
                # Process structured data if available
                structured_data = None
                if session.get("structured_data_json"):
                    try:
                        import json
                        structured_data = json.loads(session["structured_data_json"])
                    except:
                        pass
                
                # Ingest content into RAG system
                success = await rag_service.ingest_scraped_content(
                    project_id=UUID(project_id),
                    session_id=UUID(session_id),
                    markdown_content=raw_markdown,
                    azure_credentials=azure_credentials,
                    structured_data=structured_data
                )
                
                if success:
                    print(f"    Successfully processed session {session_id}")
                else:
                    print(f"    Failed to process session {session_id}")
                    
            except Exception as e:
                print(f"    Error processing session {session_id}: {e}")
        
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_rag_issues.py [diagnose|fix]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "diagnose":
        asyncio.run(diagnose_rag_issues())
    elif action == "fix":
        asyncio.run(fix_rag_issues())
    else:
        print("Invalid action. Use 'diagnose' or 'fix'")
        sys.exit(1)
