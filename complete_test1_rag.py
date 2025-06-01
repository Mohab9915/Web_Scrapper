#!/usr/bin/env python3
"""
Complete RAG ingestion for test1 project with structured data only.
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

async def complete_test1_rag():
    """Complete RAG ingestion for test1 project"""
    print("🔧 COMPLETING TEST1 PROJECT RAG INGESTION")
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
    
    # Get sessions for this project
    sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).execute()
    
    for session in sessions_response.data:
        print(f"\n🔍 Session: {session['id'][:8]}...")
        print(f"   URL: {session['url']}")
        print(f"   Status: {session['status']}")
        
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
                
                # Check if markdown entry exists
                markdown_response = supabase.table("markdowns").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
                
                if markdown_response.data:
                    # Update existing entry
                    supabase.table("markdowns").update({
                        "markdown": structured_content
                    }).eq("unique_name", session['unique_scrape_identifier']).execute()
                    print("   ✅ Updated existing markdown entry")
                else:
                    # Create new entry
                    supabase.table("markdowns").insert({
                        "unique_name": session['unique_scrape_identifier'],
                        "url": session['url'],
                        "markdown": structured_content
                    }).execute()
                    print("   ✅ Created new markdown entry")
                
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

async def test_test1_rag():
    """Test RAG functionality for test1 project"""
    print("\n🧪 TESTING TEST1 PROJECT RAG")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Get test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if project_response.data:
        project = project_response.data[0]
        
        # Check RAG-ingested sessions
        rag_sessions = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        
        if rag_sessions.data:
            print(f"✅ Found {len(rag_sessions.data)} RAG-ingested sessions")
            
            test_queries = [
                "How many countries are in the dataset?",
                "What is the capital of Andorra?",
                "Which country has the largest area?",
                "List 3 countries with their populations",
                "What is the smallest country by area?"
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
                    
                    print(f"✅ Answer: {result.answer[:150]}...")
                    print(f"📊 Sources: {len(result.source_documents)} documents")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
        else:
            print("❌ No RAG-ingested sessions found")

def final_verification():
    """Final verification of both fixes"""
    print("\n🎯 FINAL VERIFICATION")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Check test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if project_response.data:
        project = project_response.data[0]
        
        print(f"📋 Project: {project['name']}")
        print(f"RAG Enabled: {project['rag_enabled']}")
        
        # Check project URLs and conditions
        project_urls_response = supabase.table("project_urls").select("*").eq("project_id", project['id']).execute()
        
        for url_entry in project_urls_response.data:
            print(f"\n🔗 URL: {url_entry['url']}")
            print(f"📋 Conditions: {url_entry.get('conditions', 'N/A')}")
            print(f"🎨 Display Format: {url_entry.get('display_format', 'N/A')}")
            print(f"📊 Status: {url_entry.get('status', 'N/A')}")
            
            # Check session data
            if url_entry.get('last_scraped_session_id'):
                session_response = supabase.table("scrape_sessions").select("*").eq("id", url_entry['last_scraped_session_id']).execute()
                
                if session_response.data:
                    session = session_response.data[0]
                    print(f"🔍 Session Status: {session['status']}")
                    
                    # Check data structure
                    if session.get('structured_data_json'):
                        try:
                            structured_data = json.loads(session['structured_data_json'])
                            
                            if 'listings' in structured_data:
                                listings = structured_data['listings']
                                print(f"📊 Data: {len(listings)} countries")
                                
                                if listings:
                                    sample = listings[0]
                                    print(f"📝 Sample: {sample}")
                                    
                                    # Verify conditions match data
                                    conditions = url_entry.get('conditions', '').split(',')
                                    conditions = [c.strip() for c in conditions if c.strip()]
                                    
                                    print(f"🎯 Conditions: {conditions}")
                                    print(f"📊 Data Fields: {list(sample.keys())}")
                                    
                                    missing = [c for c in conditions if c not in sample]
                                    if missing:
                                        print(f"❌ Missing fields: {missing}")
                                    else:
                                        print(f"✅ All conditions match data fields")
                        
                        except Exception as e:
                            print(f"❌ Error parsing data: {e}")
        
        # Check RAG status
        rag_sessions = supabase.table("scrape_sessions").select("count").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        rag_count = len(rag_sessions.data) if rag_sessions.data else 0
        
        print(f"\n🤖 RAG Status:")
        print(f"   RAG Enabled: {project['rag_enabled']}")
        print(f"   RAG-ingested Sessions: {rag_count}")
        
        if project['rag_enabled'] and rag_count > 0:
            print(f"   ✅ RAG system is ready")
        elif project['rag_enabled'] and rag_count == 0:
            print(f"   ⚠️  RAG enabled but no ingested sessions")
        else:
            print(f"   ℹ️  RAG not enabled")

async def main():
    """Main function"""
    await complete_test1_rag()
    await test_test1_rag()
    final_verification()

if __name__ == "__main__":
    asyncio.run(main())
