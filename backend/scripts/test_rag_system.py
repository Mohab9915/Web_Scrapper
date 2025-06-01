"""
Test script to verify RAG system functionality.
This script tests the complete RAG pipeline from query to response.
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

load_dotenv()

async def test_rag_system():
    """
    Test the RAG system with a sample query.
    """
    print("=== RAG SYSTEM TEST ===\n")
    
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
    
    print(f"Using Azure endpoint: {azure_credentials['endpoint']}")
    print(f"API key present: {'Yes' if azure_credentials['api_key'] else 'No'}")
    print()
    
    # Get all projects with RAG enabled
    projects_response = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    if not projects_response.data:
        print("No projects with RAG enabled found.")
        return
    
    rag_service = RAGService()
    
    for project in projects_response.data:
        project_id = project["id"]
        project_name = project["name"]
        
        print(f"Testing project: {project_name} ({project_id})")
        print("-" * 50)
        
        # Check if project has RAG data
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).eq("status", "rag_ingested").execute()
        
        if not sessions_response.data:
            print("  No RAG-processed data found. Skipping...")
            continue
        
        print(f"  Found {len(sessions_response.data)} RAG-processed sessions")
        
        # Test queries
        test_queries = [
            "What is this about?",
            "Tell me about the content",
            "What information is available?",
            "Summarize the main points"
        ]
        
        for query in test_queries:
            print(f"\n  Testing query: '{query}'")
            try:
                response = await rag_service.query_rag(
                    project_id=UUID(project_id),
                    query=query,
                    llm_model="gpt-4o-mini",
                    azure_credentials=azure_credentials
                )
                
                print(f"    Response: {response.answer[:200]}{'...' if len(response.answer) > 200 else ''}")
                print(f"    Cost: ${response.generation_cost:.4f}")
                print(f"    Sources: {len(response.source_documents) if response.source_documents else 0}")
                
                if response.source_documents:
                    for i, doc in enumerate(response.source_documents[:2]):  # Show first 2 sources
                        print(f"      Source {i+1}: {doc['metadata']['url']} (similarity: {doc['metadata']['similarity']:.4f})")
                
            except Exception as e:
                print(f"    ERROR: {e}")
        
        print("\n" + "="*60 + "\n")

async def test_specific_project(project_id: str, query: str):
    """
    Test RAG system with a specific project and query.
    """
    print(f"=== TESTING SPECIFIC PROJECT: {project_id} ===\n")
    
    # Get Azure credentials
    azure_credentials = {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    }
    
    if not azure_credentials["api_key"] or not azure_credentials["endpoint"]:
        print("ERROR: Azure OpenAI credentials not found in environment variables.")
        return
    
    rag_service = RAGService()
    
    try:
        print(f"Query: '{query}'")
        print("-" * 50)
        
        response = await rag_service.query_rag(
            project_id=UUID(project_id),
            query=query,
            llm_model="gpt-4o-mini",
            azure_credentials=azure_credentials
        )
        
        print(f"Response: {response.answer}")
        print(f"Cost: ${response.generation_cost:.4f}")
        print(f"Sources: {len(response.source_documents) if response.source_documents else 0}")
        
        if response.source_documents:
            print("\nSource Documents:")
            for i, doc in enumerate(response.source_documents):
                print(f"  {i+1}. URL: {doc['metadata']['url']}")
                print(f"     Similarity: {doc['metadata']['similarity']:.4f}")
                print(f"     Content: {doc['content'][:200]}{'...' if len(doc['content']) > 200 else ''}")
                print()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Test all projects
        asyncio.run(test_rag_system())
    elif len(sys.argv) == 3:
        # Test specific project with query
        project_id = sys.argv[1]
        query = sys.argv[2]
        asyncio.run(test_specific_project(project_id, query))
    else:
        print("Usage:")
        print("  python test_rag_system.py                    # Test all projects")
        print("  python test_rag_system.py <project_id> <query>  # Test specific project")
        sys.exit(1)
