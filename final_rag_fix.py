#!/usr/bin/env python3
"""
Final fix for RAG ingestion - handle duplicate key issue and complete test1 project.
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

async def final_rag_fix():
    """Final fix for RAG ingestion"""
    print("🔧 FINAL RAG INGESTION FIX")
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
    
    # Get sessions that need RAG ingestion
    sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "scraped").execute()
    
    for session in sessions_response.data:
        print(f"\n🔍 Processing session: {session['id'][:8]}...")
        print(f"   URL: {session['url']}")
        
        if session.get('structured_data_json'):
            try:
                if isinstance(session['structured_data_json'], str):
                    structured_data = json.loads(session['structured_data_json'])
                else:
                    structured_data = session['structured_data_json']
                
                # Create structured content for RAG
                structured_content = ""
                
                if 'listings' in structured_data and structured_data['listings']:
                    listings = structured_data['listings']
                    structured_content += f"# Countries Dataset\n\n"
                    structured_content += f"This dataset contains information about {len(listings)} countries and territories.\n\n"
                    
                    for i, item in enumerate(listings, 1):
                        country_name = item.get('country', f'Country {i}')
                        structured_content += f"## {country_name}\n\n"
                        
                        if 'capital' in item and item['capital']:
                            structured_content += f"Capital: {item['capital']}\n"
                        if 'population' in item and item['population']:
                            structured_content += f"Population: {item['population']}\n"
                        if 'area' in item and item['area']:
                            structured_content += f"Area: {item['area']} square kilometers\n"
                        
                        structured_content += "\n"
                
                print(f"   📄 Created structured content: {len(structured_content)} characters")
                
                # Handle markdown entry (upsert to avoid duplicate key error)
                try:
                    supabase.table("markdowns").upsert({
                        "unique_name": session['unique_scrape_identifier'],
                        "url": session['url'],
                        "markdown": structured_content
                    }, on_conflict="unique_name").execute()
                    print("   ✅ Updated/created markdown entry")
                except Exception as e:
                    print(f"   ❌ Error with markdown: {e}")
                    continue
                
                # Clear existing embeddings
                supabase.table("embeddings").delete().eq("unique_name", session['unique_scrape_identifier']).execute()
                print("   🗑️  Cleared old embeddings")
                
                # Perform RAG ingestion with structured data only
                success = await rag_service.ingest_scraped_content(
                    project_id=UUID(project['id']),
                    session_id=UUID(session['id']),
                    markdown_content=structured_content,
                    azure_credentials=azure_credentials,
                    structured_data=structured_data
                )
                
                if success:
                    print("   ✅ RAG ingestion completed successfully!")
                    
                    # Verify status
                    updated_session = supabase.table("scrape_sessions").select("status").eq("id", session['id']).single().execute()
                    if updated_session.data:
                        print(f"   Status: {updated_session.data['status']}")
                    
                    # Check embeddings
                    embeddings_response = supabase.table("embeddings").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
                    embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
                    print(f"   📊 Embeddings: {embeddings_count} chunks")
                else:
                    print("   ❌ RAG ingestion failed")
                
            except Exception as e:
                print(f"   ❌ Error processing session: {e}")

async def comprehensive_test():
    """Comprehensive test of both fixes"""
    print("\n🧪 COMPREHENSIVE TESTING")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Test 1: Frontend Data Display
    print("\n1️⃣ TESTING FRONTEND DATA DISPLAY")
    print("-" * 40)
    
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if project_response.data:
        project = project_response.data[0]
        
        # Simulate the API call that frontend makes
        project_urls_response = supabase.table("project_urls").select(
            "id, project_id, url, conditions, display_format, created_at, status, rag_enabled, last_scraped_session_id"
        ).eq("project_id", str(project['id'])).order("created_at", desc=True).execute()
        
        for pu_entry in project_urls_response.data:
            print(f"URL: {pu_entry['url']}")
            print(f"Conditions: {pu_entry.get('conditions', 'N/A')}")
            
            if pu_entry.get("last_scraped_session_id"):
                session_response = supabase.table("scrape_sessions").select(
                    "id, project_id, url, scraped_at, status, raw_markdown, structured_data_json, display_format, formatted_tabular_data"
                ).eq("id", pu_entry["last_scraped_session_id"]).single().execute()
                
                if session_response.data:
                    raw_session_data = session_response.data
                    
                    if raw_session_data.get("structured_data_json"):
                        structured_data = json.loads(raw_session_data["structured_data_json"])
                        
                        # Extract tabular data (what frontend uses)
                        current_tabular_data = []
                        if isinstance(structured_data.get("listings"), list):
                            current_tabular_data = structured_data["listings"]
                        
                        # Extract fields
                        fields = []
                        if current_tabular_data and isinstance(current_tabular_data[0], dict):
                            fields = list(current_tabular_data[0].keys())
                        
                        print(f"✅ Frontend will receive:")
                        print(f"   Tabular data: {len(current_tabular_data)} items")
                        print(f"   Fields: {fields}")
                        
                        if current_tabular_data:
                            sample = current_tabular_data[0]
                            print(f"   Sample item: {sample}")
                            
                            # Check what will be displayed based on conditions
                            conditions = pu_entry.get('conditions', '').split(',')
                            conditions = [c.strip() for c in conditions if c.strip()]
                            
                            print(f"   Display will show these fields: {conditions}")
                            print(f"   Sample display values:")
                            for condition in conditions:
                                value = sample.get(condition, 'N/A')
                                print(f"      {condition}: {value}")
    
    # Test 2: RAG System
    print("\n2️⃣ TESTING RAG SYSTEM")
    print("-" * 40)
    
    if project_response.data:
        project = project_response.data[0]
        
        # Check RAG-ingested sessions
        rag_sessions = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        
        if rag_sessions.data:
            print(f"✅ Found {len(rag_sessions.data)} RAG-ingested sessions")
            
            test_queries = [
                "How many countries are in the dataset?",
                "What is the capital of Andorra?",
                "Which countries have areas larger than 1 million square kilometers?",
                "List 3 European countries with their capitals"
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
                    
                    print(f"✅ Answer: {result.answer[:100]}...")
                    print(f"📊 Sources: {len(result.source_documents)} documents")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
        else:
            print("❌ No RAG-ingested sessions found")

def summary_report():
    """Generate final summary report"""
    print("\n📋 FINAL SUMMARY REPORT")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Check test1 project status
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if project_response.data:
        project = project_response.data[0]
        
        print(f"📋 Project: {project['name']}")
        print(f"🤖 RAG Enabled: {project['rag_enabled']}")
        
        # Check sessions
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).execute()
        scraped_count = len([s for s in sessions_response.data if s['status'] == 'scraped'])
        rag_count = len([s for s in sessions_response.data if s['status'] == 'rag_ingested'])
        
        print(f"📊 Sessions:")
        print(f"   Total: {len(sessions_response.data)}")
        print(f"   Scraped: {scraped_count}")
        print(f"   RAG-ingested: {rag_count}")
        
        # Check project URLs
        project_urls_response = supabase.table("project_urls").select("*").eq("project_id", project['id']).execute()
        
        print(f"🔗 URLs: {len(project_urls_response.data)}")
        
        for url_entry in project_urls_response.data:
            print(f"   {url_entry['url']}")
            print(f"      Conditions: {url_entry.get('conditions', 'N/A')}")
            print(f"      Status: {url_entry.get('status', 'N/A')}")
        
        # Final status
        print(f"\n🎯 FINAL STATUS:")
        
        if rag_count > 0:
            print(f"   ✅ RAG System: Working")
        else:
            print(f"   ❌ RAG System: Needs attention")
        
        # Check if conditions match data
        conditions_ok = True
        for url_entry in project_urls_response.data:
            if url_entry.get('last_scraped_session_id'):
                session_response = supabase.table("scrape_sessions").select("structured_data_json").eq("id", url_entry['last_scraped_session_id']).execute()
                
                if session_response.data and session_response.data[0].get('structured_data_json'):
                    try:
                        structured_data = json.loads(session_response.data[0]['structured_data_json'])
                        if 'listings' in structured_data and structured_data['listings']:
                            actual_fields = list(structured_data['listings'][0].keys())
                            conditions = url_entry.get('conditions', '').split(',')
                            conditions = [c.strip() for c in conditions if c.strip()]
                            
                            missing = [c for c in conditions if c not in actual_fields]
                            if missing:
                                conditions_ok = False
                    except:
                        pass
        
        if conditions_ok:
            print(f"   ✅ Data Display: Working")
        else:
            print(f"   ❌ Data Display: Needs attention")

async def main():
    """Main function"""
    await final_rag_fix()
    await comprehensive_test()
    summary_report()

if __name__ == "__main__":
    asyncio.run(main())
