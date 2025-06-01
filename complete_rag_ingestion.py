#!/usr/bin/env python3
"""
Complete RAG ingestion for sessions that have markdown but aren't marked as rag_ingested.
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
# We'll use the RAG service directly instead of manual embedding creation

async def complete_rag_ingestion():
    """Complete RAG ingestion for sessions with markdown but not rag_ingested status"""
    print("🔧 COMPLETING RAG INGESTION")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Get Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Find sessions that have markdown entries but status is not rag_ingested
    sessions_response = supabase.table("scrape_sessions").select("*").eq("status", "scraped").execute()
    
    for session in sessions_response.data:
        # Check if markdown entry exists
        markdown_response = supabase.table("markdowns").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
        
        if markdown_response.data:
            print(f"\n🔧 Processing session: {session['id']}")
            print(f"   URL: {session['url']}")
            print(f"   Project: {session['project_id']}")
            
            markdown_content = markdown_response.data[0]['markdown']
            print(f"   Markdown: {len(markdown_content)} characters")
            
            # Check if embeddings already exist
            embeddings_response = supabase.table("embeddings").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
            embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
            print(f"   📊 Current embeddings: {embeddings_count} chunks")
            
            # Update session status to rag_ingested
            try:
                supabase.table("scrape_sessions").update({
                    "status": "rag_ingested"
                }).eq("id", session['id']).execute()
                
                print("   ✅ Updated status to 'rag_ingested'")
                
            except Exception as e:
                print(f"   ❌ Error updating status: {e}")

async def test_all_rag_projects():
    """Test RAG functionality for all projects"""
    print("\n🧪 TESTING ALL RAG PROJECTS")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    # Get Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Get all projects with RAG enabled
    projects_response = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    for project in projects_response.data:
        print(f"\n🧪 Testing project: {project['name']} (ID: {project['id']})")
        
        # Check RAG-ingested sessions
        rag_sessions = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        
        if not rag_sessions.data:
            print("   ❌ No RAG-ingested sessions found")
            continue
        
        print(f"   ✅ Found {len(rag_sessions.data)} RAG-ingested sessions")
        
        # Test a simple query
        test_query = "How many items are in the dataset?"
        
        try:
            result = await rag_service.query_rag(
                project_id=UUID(project['id']),
                query=test_query,
                azure_credentials=azure_credentials,
                llm_model='gpt-4o'
            )
            
            print(f"   ✅ Query successful: {result.answer[:100]}...")
            print(f"   📊 Sources: {len(result.source_documents)} documents")
            
        except Exception as e:
            print(f"   ❌ Query failed: {e}")

def check_data_display_issue():
    """Check the data display issue in detail"""
    print("\n🖥️  ANALYZING DATA DISPLAY ISSUE")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Get test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if not project_response.data:
        print("❌ test1 project not found")
        return
    
    project = project_response.data[0]
    print(f"📋 Project: {project['name']}")
    
    # Get sessions
    sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).execute()
    
    for session in sessions_response.data:
        print(f"\n📊 Session: {session['id'][:8]}...")
        print(f"   URL: {session['url']}")
        print(f"   Status: {session['status']}")
        
        # Analyze structured data
        if session.get('structured_data_json'):
            try:
                if isinstance(session['structured_data_json'], str):
                    data = json.loads(session['structured_data_json'])
                else:
                    data = session['structured_data_json']
                
                print(f"   📋 Structured data keys: {list(data.keys())}")
                
                if 'listings' in data and data['listings']:
                    listings = data['listings']
                    print(f"   📊 Listings count: {len(listings)}")
                    
                    # Analyze field distribution
                    all_fields = set()
                    for item in listings:
                        all_fields.update(item.keys())
                    
                    print(f"   🔍 All fields found: {sorted(all_fields)}")
                    
                    # Check field completeness
                    field_stats = {}
                    for field in all_fields:
                        count = sum(1 for item in listings if field in item and item[field])
                        field_stats[field] = count
                    
                    print("   📈 Field completeness:")
                    for field, count in sorted(field_stats.items()):
                        percentage = (count / len(listings)) * 100
                        print(f"      {field}: {count}/{len(listings)} ({percentage:.1f}%)")
                    
                    # Show sample data
                    print("   📝 Sample entries:")
                    for i, item in enumerate(listings[:3]):
                        print(f"      {i+1}. {item}")
                
                # Check if the issue is in the frontend data processing
                print("\n   🔍 Frontend data simulation:")
                
                # Simulate how the frontend processes this data
                tabular_data = data.get('tabular_data', [])
                if not tabular_data and 'listings' in data:
                    tabular_data = data['listings']
                
                print(f"   Tabular data for frontend: {len(tabular_data)} items")
                
                if tabular_data:
                    # Check what fields would be displayed
                    sample_item = tabular_data[0]
                    print(f"   Sample item keys: {list(sample_item.keys())}")
                    print(f"   Sample item values: {sample_item}")
                    
                    # Check if country field exists
                    if 'country' in sample_item:
                        print("   ✅ 'country' field is present")
                    else:
                        print("   ❌ 'country' field is missing!")
                        print(f"   Available fields: {list(sample_item.keys())}")
                
            except Exception as e:
                print(f"   ❌ Error analyzing structured data: {e}")

async def main():
    """Main function"""
    await complete_rag_ingestion()
    await test_all_rag_projects()
    check_data_display_issue()

if __name__ == "__main__":
    asyncio.run(main())
