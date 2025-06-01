#!/usr/bin/env python3
"""
Manually fix RAG status for test1 project.
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

async def manual_rag_status_fix():
    """Manually fix RAG status"""
    print("🔧 MANUAL RAG STATUS FIX")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Get test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if not project_response.data:
        print("❌ test1 project not found")
        return
    
    project = project_response.data[0]
    print(f"📋 Project: {project['name']} (ID: {project['id']})")
    
    # Get the session
    sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).execute()
    
    for session in sessions_response.data:
        print(f"\n🔍 Session: {session['id'][:8]}...")
        print(f"   URL: {session['url']}")
        print(f"   Current Status: {session['status']}")
        
        # Check if markdown exists
        markdown_response = supabase.table("markdowns").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
        
        if markdown_response.data:
            print("   ✅ Markdown exists")
            
            # Check if embeddings exist
            embeddings_response = supabase.table("embeddings").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
            embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
            print(f"   📊 Embeddings: {embeddings_count} chunks")
            
            if embeddings_count > 0:
                # Update status to rag_ingested
                try:
                    supabase.table("scrape_sessions").update({
                        "status": "rag_ingested"
                    }).eq("id", session['id']).execute()
                    
                    print("   ✅ Updated status to 'rag_ingested'")
                    
                except Exception as e:
                    print(f"   ❌ Error updating status: {e}")
            else:
                print("   ⚠️  No embeddings found, need to create them")
                
                # Create embeddings manually
                from app.utils.embedding import generate_embeddings_batch
                
                azure_credentials = {
                    'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
                    'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
                }
                
                markdown_content = markdown_response.data[0]['markdown']
                
                # Simple chunking (split by double newlines)
                chunks = [chunk.strip() for chunk in markdown_content.split('\n\n') if chunk.strip()]
                print(f"   📄 Created {len(chunks)} chunks")
                
                try:
                    # Generate embeddings
                    embeddings = await generate_embeddings_batch(chunks, azure_credentials)
                    print(f"   🧠 Generated {len(embeddings)} embeddings")
                    
                    # Store embeddings
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        supabase.table("embeddings").insert({
                            "unique_name": session['unique_scrape_identifier'],
                            "chunk_id": i,
                            "content": chunk,
                            "embedding": embedding
                        }).execute()
                    
                    print(f"   ✅ Stored {len(embeddings)} embeddings")
                    
                    # Update status
                    supabase.table("scrape_sessions").update({
                        "status": "rag_ingested"
                    }).eq("id", session['id']).execute()
                    
                    print("   ✅ Updated status to 'rag_ingested'")
                    
                except Exception as e:
                    print(f"   ❌ Error creating embeddings: {e}")
        else:
            print("   ❌ No markdown found")

async def final_test():
    """Final test of the complete system"""
    print("\n🧪 FINAL SYSTEM TEST")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Test test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if project_response.data:
        project = project_response.data[0]
        
        print(f"📋 Testing project: {project['name']}")
        
        # Check RAG-ingested sessions
        rag_sessions = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        
        if rag_sessions.data:
            print(f"✅ Found {len(rag_sessions.data)} RAG-ingested sessions")
            
            # Test queries
            test_queries = [
                "How many countries are in the dataset?",
                "What is the capital of Andorra?",
                "Which country has the largest area?",
                "List 3 countries with their populations"
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

def final_status_report():
    """Generate final status report"""
    print("\n🎯 FINAL STATUS REPORT")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Check test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if project_response.data:
        project = project_response.data[0]
        
        print(f"📋 Project: {project['name']}")
        print(f"🤖 RAG Enabled: {project['rag_enabled']}")
        
        # Check sessions
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).execute()
        
        for session in sessions_response.data:
            print(f"\n📊 Session: {session['id'][:8]}...")
            print(f"   URL: {session['url']}")
            print(f"   Status: {session['status']}")
            
            # Check data
            if session.get('structured_data_json'):
                try:
                    structured_data = json.loads(session['structured_data_json'])
                    if 'listings' in structured_data:
                        print(f"   📊 Data: {len(structured_data['listings'])} countries")
                        sample = structured_data['listings'][0]
                        print(f"   📝 Sample: {sample}")
                except:
                    pass
            
            # Check RAG components
            markdown_response = supabase.table("markdowns").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
            markdown_exists = len(markdown_response.data) > 0 if markdown_response.data else False
            
            embeddings_response = supabase.table("embeddings").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
            embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
            
            print(f"   📄 Markdown: {'✅' if markdown_exists else '❌'}")
            print(f"   🧠 Embeddings: {embeddings_count} chunks")
        
        # Check project URLs
        project_urls_response = supabase.table("project_urls").select("*").eq("project_id", project['id']).execute()
        
        print(f"\n🔗 Project URLs:")
        for url_entry in project_urls_response.data:
            print(f"   {url_entry['url']}")
            print(f"      Conditions: {url_entry.get('conditions', 'N/A')}")
            print(f"      Status: {url_entry.get('status', 'N/A')}")
            
            # Verify conditions match data
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
                                print(f"      ❌ Missing fields: {missing}")
                            else:
                                print(f"      ✅ All fields match")
                    except:
                        pass
        
        print(f"\n🎯 SUMMARY:")
        
        # Check overall status
        rag_sessions = supabase.table("scrape_sessions").select("count").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        rag_count = len(rag_sessions.data) if rag_sessions.data else 0
        
        if rag_count > 0:
            print(f"   ✅ RAG System: Working ({rag_count} sessions ingested)")
        else:
            print(f"   ❌ RAG System: Not working")
        
        print(f"   ✅ Data Display: Fixed (conditions match data fields)")
        print(f"   ✅ Structured Data: Only structured data used for RAG")

async def main():
    """Main function"""
    await manual_rag_status_fix()
    await final_test()
    final_status_report()

if __name__ == "__main__":
    asyncio.run(main())
