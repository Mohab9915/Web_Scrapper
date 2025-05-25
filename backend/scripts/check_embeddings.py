"""
Script to check if embeddings exist for a project.
"""
import asyncio
import sys
import os
from uuid import UUID

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import supabase

async def check_embeddings_for_project(project_id: str):
    """
    Check if embeddings exist for a project.
    
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
        print(f"RAG enabled: {project_response.data['rag_enabled']}")
        
        # Get all scrape sessions for this project
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
        if not sessions_response.data:
            print(f"No scrape sessions found for project {project_id}")
            return
        
        print(f"Found {len(sessions_response.data)} scrape sessions")
        
        # Check each session
        for session in sessions_response.data:
            print(f"Session {session['id']} status: {session['status']}")
            print(f"Session URL: {session['url']}")
            print(f"Session unique identifier: {session['unique_scrape_identifier']}")
            
            # Check if markdowns exist for this session
            markdown_response = supabase.table("markdowns").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
            print(f"Found {len(markdown_response.data)} markdown entries")
            
            # Check if embeddings exist for this session
            embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
            print(f"Found {len(embeddings_response.data)} embedding entries")
            
            if len(embeddings_response.data) == 0:
                print("No embeddings found for this session. Creating embeddings...")
                
                # Get the markdown content
                if len(markdown_response.data) > 0:
                    markdown_content = markdown_response.data[0]['markdown']
                    print(f"Markdown content length: {len(markdown_content)} characters")
                    
                    # Create a sample embedding entry
                    from app.services.rag_service import generate_embeddings
                    
                    # Azure OpenAI credentials
                    azure_credentials = {
                        'api_key': 'YOUR_AZURE_API_KEY',
                        'endpoint': 'https://your-azure-endpoint.services.ai.azure.com',
                        'deployment_name': 'text-embedding-ada-002'
                    }
                    
                    # Generate a sample embedding
                    sample_text = markdown_content[:1000]  # Use first 1000 characters
                    embedding = await generate_embeddings(sample_text, azure_credentials)
                    
                    # Insert into embeddings table
                    supabase.table("embeddings").insert({
                        "unique_name": session['unique_scrape_identifier'],
                        "chunk_id": 0,
                        "content": sample_text,
                        "embedding": embedding
                    }).execute()
                    
                    print("Sample embedding created successfully")
                else:
                    print("No markdown content found for this session")
            
            print("-" * 50)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_embeddings.py <project_id>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    asyncio.run(check_embeddings_for_project(project_id))
