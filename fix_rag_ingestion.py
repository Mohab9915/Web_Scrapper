#!/usr/bin/env python3
"""
Fix RAG ingestion for existing scraped data.
This script will properly ingest scraped sessions into the RAG system.
"""
import asyncio
import json
import sys
import os
from uuid import UUID
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import get_supabase_client
from app.services.rag_service import RAGService

async def fix_rag_ingestion():
    """Fix RAG ingestion for projects with scraped data but missing RAG processing"""
    print("🔧 FIXING RAG INGESTION ISSUES")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    # Get Azure credentials from environment or use defaults
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    print(f"Azure endpoint configured: {'Yes' if azure_credentials['endpoint'] else 'No'}")
    print(f"Azure API key configured: {'Yes' if azure_credentials['api_key'] else 'No'}")
    
    # Find projects with RAG enabled but sessions not RAG-ingested
    print("\n🔍 Finding projects needing RAG ingestion...")
    
    rag_projects = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    for project in rag_projects.data:
        print(f"\n📋 Project: {project['name']} (ID: {project['id']})")
        
        # Get scraped sessions that are not RAG-ingested
        scraped_sessions = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "scraped").execute()
        
        if not scraped_sessions.data:
            print("  ✅ No sessions needing RAG ingestion")
            continue
        
        print(f"  📊 Found {len(scraped_sessions.data)} sessions needing RAG ingestion")
        
        for session in scraped_sessions.data:
            print(f"\n  🔄 Processing session: {session['id']}")
            print(f"     URL: {session['url']}")
            
            try:
                # Get the markdown content
                markdown_response = supabase.table("markdowns").select("markdown").eq("unique_name", session['unique_scrape_identifier']).execute()
                
                if not markdown_response.data:
                    print("     ❌ No markdown content found, skipping...")
                    continue
                
                markdown_content = markdown_response.data[0]['markdown']
                print(f"     📄 Markdown content: {len(markdown_content)} characters")
                
                # Get structured data
                structured_data = None
                if session.get('structured_data_json'):
                    try:
                        if isinstance(session['structured_data_json'], str):
                            structured_data = json.loads(session['structured_data_json'])
                        else:
                            structured_data = session['structured_data_json']
                        
                        # Check data quality
                        listings = structured_data.get('listings', [])
                        tabular_data = structured_data.get('tabular_data', [])
                        
                        if listings:
                            print(f"     📊 Found {len(listings)} listings in structured data")
                        elif tabular_data:
                            print(f"     📊 Found {len(tabular_data)} items in tabular data")
                        else:
                            print("     ⚠️  Structured data exists but no listings/tabular_data found")
                            
                    except Exception as e:
                        print(f"     ❌ Error parsing structured data: {e}")
                        structured_data = None
                
                # Perform RAG ingestion
                print("     🚀 Starting RAG ingestion...")

                success = await rag_service.ingest_scraped_content(
                    project_id=UUID(project['id']),
                    session_id=UUID(session['id']),
                    markdown_content=markdown_content,
                    azure_credentials=azure_credentials if azure_credentials['api_key'] else None,
                    structured_data=structured_data
                )
                
                if success:
                    print("     ✅ RAG ingestion completed successfully!")
                    
                    # Verify the ingestion
                    updated_session = supabase.table("scrape_sessions").select("status").eq("id", session['id']).single().execute()
                    if updated_session.data and updated_session.data['status'] == 'rag_ingested':
                        print("     ✅ Session status updated to 'rag_ingested'")
                    else:
                        print("     ⚠️  Session status not updated properly")
                    
                    # Check embeddings
                    embeddings_response = supabase.table("embeddings").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
                    embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
                    print(f"     📊 Embeddings created: {embeddings_count}")
                    
                else:
                    print("     ❌ RAG ingestion failed")
                    
            except Exception as e:
                print(f"     ❌ Error processing session: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n🎉 RAG ingestion fix completed!")

async def test_rag_functionality():
    """Test RAG functionality after fixing ingestion"""
    print("\n🧪 TESTING RAG FUNCTIONALITY")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    # Get Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Find a project with RAG enabled and rag_ingested sessions
    rag_projects = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    for project in rag_projects.data:
        # Check if this project has rag_ingested sessions
        rag_sessions = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        
        if rag_sessions.data:
            print(f"\n🧪 Testing RAG for project: {project['name']}")
            
            test_queries = [
                "How many countries are there?",
                "What is the capital of France?",
                "Which country has the largest area?",
                "List some countries and their populations"
            ]
            
            for query in test_queries:
                print(f"\n  Query: {query}")
                try:
                    if azure_credentials['api_key']:
                        result = await rag_service.query_rag(
                            project_id=UUID(project['id']),
                            query=query,
                            azure_credentials=azure_credentials,
                            llm_model='gpt-4o'
                        )
                        print(f"  Answer: {result.answer[:200]}...")
                        print(f"  Sources: {len(result.source_documents)} documents")
                    else:
                        print("  ⚠️  Skipping query test - no Azure credentials")
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
            
            break  # Test only the first available project
    
    print("\n✅ RAG functionality test completed!")

async def main():
    """Main function"""
    await fix_rag_ingestion()
    await test_rag_functionality()

if __name__ == "__main__":
    asyncio.run(main())
