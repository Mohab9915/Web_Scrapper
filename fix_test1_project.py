#!/usr/bin/env python3
"""
Fix the test1 project specifically and complete its RAG ingestion.
"""
import asyncio
import json
import sys
import os
from uuid import UUID

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import get_supabase_client
from app.services.rag_service import RAGService

async def fix_test1_project():
    """Fix the test1 project RAG ingestion"""
    print("🔧 FIXING TEST1 PROJECT")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    # Get Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Get test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if not project_response.data:
        print("❌ test1 project not found")
        return
    
    project = project_response.data[0]
    print(f"📋 Project: {project['name']} (ID: {project['id']})")
    print(f"RAG Enabled: {project['rag_enabled']}")
    
    # Get the session
    sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).execute()
    
    if not sessions_response.data:
        print("❌ No sessions found for test1 project")
        return
    
    session = sessions_response.data[0]
    print(f"\n🔍 Session: {session['id']}")
    print(f"URL: {session['url']}")
    print(f"Status: {session['status']}")
    
    # Check if markdown exists in markdowns table
    markdown_response = supabase.table("markdowns").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
    
    if markdown_response.data:
        print("✅ Markdown entry exists")
        markdown_content = markdown_response.data[0]['markdown']
        print(f"Markdown length: {len(markdown_content)} characters")
        
        # Now perform RAG ingestion
        if session['status'] != 'rag_ingested':
            print("\n🚀 Starting RAG ingestion...")
            
            # Get structured data
            structured_data = None
            if session.get('structured_data_json'):
                try:
                    if isinstance(session['structured_data_json'], str):
                        structured_data = json.loads(session['structured_data_json'])
                    else:
                        structured_data = session['structured_data_json']
                    
                    print(f"Structured data: {len(structured_data.get('listings', []))} countries")
                except Exception as e:
                    print(f"Error parsing structured data: {e}")
            
            success = await rag_service.ingest_scraped_content(
                project_id=UUID(project['id']),
                session_id=UUID(session['id']),
                markdown_content=markdown_content,
                azure_credentials=azure_credentials,
                structured_data=structured_data
            )
            
            if success:
                print("✅ RAG ingestion completed!")
                
                # Verify status
                updated_session = supabase.table("scrape_sessions").select("status").eq("id", session['id']).single().execute()
                if updated_session.data:
                    print(f"New status: {updated_session.data['status']}")
                    
                    # Check embeddings
                    embeddings_response = supabase.table("embeddings").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
                    embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
                    print(f"Embeddings: {embeddings_count} chunks")
            else:
                print("❌ RAG ingestion failed")
        else:
            print("✅ Session already RAG-ingested")
    else:
        print("❌ No markdown entry found")
    
    # Test RAG queries for test1 project
    print("\n🧪 TESTING RAG QUERIES FOR TEST1 PROJECT")
    print("=" * 50)
    
    test_queries = [
        "How many countries are there?",
        "What is the capital of Andorra?",
        "Which countries have the smallest areas?",
        "List some European countries and their populations"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        try:
            result = await rag_service.query_rag(
                project_id=UUID(project['id']),
                query=query,
                azure_credentials=azure_credentials,
                llm_model='gpt-4o'
            )
            
            print(f"✅ Answer: {result.answer[:200]}...")
            print(f"📊 Sources: {len(result.source_documents)} documents")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def check_frontend_display():
    """Check the frontend display logic"""
    print("\n🖥️  CHECKING FRONTEND DISPLAY LOGIC")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Get test1 project data as the frontend would
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if not project_response.data:
        print("❌ test1 project not found")
        return
    
    project = project_response.data[0]
    
    # Get project URLs
    urls_response = supabase.table("project_urls").select("*").eq("project_id", project['id']).execute()
    print(f"📋 Project URLs: {len(urls_response.data)}")
    
    for url_entry in urls_response.data:
        print(f"\n🔗 URL: {url_entry['url']}")
        print(f"Conditions: {url_entry.get('conditions', 'N/A')}")
        print(f"Display Format: {url_entry.get('display_format', 'N/A')}")
        
        # Get the latest scrape session for this URL
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("url", url_entry['url']).order("scraped_at", desc=True).limit(1).execute()
        
        if sessions_response.data:
            session = sessions_response.data[0]
            print(f"✅ Latest session found: {session['id']}")
            print(f"Status: {session['status']}")
            
            # Check structured data
            if session.get('structured_data_json'):
                try:
                    if isinstance(session['structured_data_json'], str):
                        data = json.loads(session['structured_data_json'])
                    else:
                        data = session['structured_data_json']
                    
                    print(f"Structured data keys: {list(data.keys())}")
                    
                    if 'listings' in data:
                        print(f"Listings count: {len(data['listings'])}")
                        if data['listings']:
                            sample = data['listings'][0]
                            print(f"Sample listing keys: {list(sample.keys())}")
                            print(f"Sample listing: {sample}")
                            
                            # Check if all expected fields are present
                            expected_fields = ['country', 'capital', 'population', 'area']
                            missing_fields = [field for field in expected_fields if field not in sample]
                            if missing_fields:
                                print(f"⚠️  Missing fields: {missing_fields}")
                            else:
                                print("✅ All expected fields present")
                    
                    if 'tabular_data' in data:
                        print(f"Tabular data count: {len(data['tabular_data'])}")
                        if data['tabular_data']:
                            sample = data['tabular_data'][0]
                            print(f"Sample tabular keys: {list(sample.keys())}")
                            print(f"Sample tabular: {sample}")
                
                except Exception as e:
                    print(f"❌ Error parsing structured data: {e}")
            else:
                print("❌ No structured data found")
        else:
            print("❌ No sessions found for this URL")

async def main():
    """Main function"""
    await fix_test1_project()
    check_frontend_display()

if __name__ == "__main__":
    asyncio.run(main())
