#!/usr/bin/env python3
"""
Update RAG system to use only structured data by updating existing markdown entries.
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

async def update_rag_to_structured_only():
    """Update existing RAG entries to use only structured data"""
    print("🔧 UPDATING RAG TO USE STRUCTURED DATA ONLY")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    # Get Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Find all RAG-ingested sessions
    sessions_response = supabase.table("scrape_sessions").select("*").eq("status", "rag_ingested").execute()
    
    for session in sessions_response.data:
        print(f"\n🔄 Processing session: {session['id'][:8]}...")
        print(f"   URL: {session['url']}")
        
        # Get structured data
        if session.get('structured_data_json'):
            try:
                if isinstance(session['structured_data_json'], str):
                    structured_data = json.loads(session['structured_data_json'])
                else:
                    structured_data = session['structured_data_json']
                
                # Create clean structured content for RAG
                structured_content = ""
                
                if 'listings' in structured_data and structured_data['listings']:
                    listings = structured_data['listings']
                    structured_content += f"# Dataset: {len(listings)} Countries and Territories\n\n"
                    
                    for i, item in enumerate(listings, 1):
                        country_name = item.get('country', f'Country {i}')
                        structured_content += f"## {country_name}\n\n"
                        
                        for key, value in item.items():
                            if key != 'country' and value:  # Don't repeat country name
                                structured_content += f"- **{key.title()}**: {value}\n"
                        structured_content += "\n"
                
                elif 'tabular_data' in structured_data and structured_data['tabular_data']:
                    tabular_data = structured_data['tabular_data']
                    structured_content += f"# Dataset: {len(tabular_data)} Records\n\n"
                    
                    for i, item in enumerate(tabular_data, 1):
                        structured_content += f"## Record {i}\n\n"
                        for key, value in item.items():
                            if value:
                                structured_content += f"- **{key.title()}**: {value}\n"
                        structured_content += "\n"
                
                if structured_content:
                    print(f"   📄 Created structured content: {len(structured_content)} characters")
                    
                    # Update the markdown entry with structured content only
                    try:
                        supabase.table("markdowns").update({
                            "markdown": structured_content
                        }).eq("unique_name", session['unique_scrape_identifier']).execute()
                        print("   ✅ Updated markdown with structured content")
                        
                        # Clear and regenerate embeddings
                        supabase.table("embeddings").delete().eq("unique_name", session['unique_scrape_identifier']).execute()
                        print("   🗑️  Cleared old embeddings")
                        
                        # Regenerate embeddings with new structured content
                        from app.utils.embedding import generate_embeddings_batch
                        from app.utils.text_processing import chunk_text
                        
                        # Chunk the structured content
                        chunks = chunk_text(structured_content)
                        print(f"   📄 Created {len(chunks)} chunks")
                        
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
                        
                        print(f"   ✅ Stored {len(embeddings)} new embeddings")
                        
                    except Exception as e:
                        print(f"   ❌ Error updating RAG data: {e}")
                
            except Exception as e:
                print(f"   ❌ Error processing structured data: {e}")

async def test_structured_rag():
    """Test RAG with structured data only"""
    print("\n🧪 TESTING STRUCTURED RAG")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Test with test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if project_response.data:
        project = project_response.data[0]
        print(f"Testing project: {project['name']}")
        
        # Check if it has RAG-ingested sessions
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        
        if sessions_response.data:
            print(f"Found {len(sessions_response.data)} RAG-ingested sessions")
            
            test_queries = [
                "How many countries are in the dataset?",
                "What is the capital of Andorra?",
                "Which countries have areas larger than 1 million square kilometers?",
                "List 5 European countries with their populations",
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
                    
                    print(f"✅ Answer: {result.answer[:200]}...")
                    print(f"📊 Sources: {len(result.source_documents)} documents")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
        else:
            print("❌ No RAG-ingested sessions found for test1 project")
    else:
        print("❌ test1 project not found")

def verify_frontend_fix():
    """Verify that the frontend data display issue is fixed"""
    print("\n🖥️  VERIFYING FRONTEND FIX")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Check test1 project specifically
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if project_response.data:
        project = project_response.data[0]
        
        # Get project URLs
        project_urls_response = supabase.table("project_urls").select("*").eq("project_id", project['id']).execute()
        
        for url_entry in project_urls_response.data:
            print(f"\n🔗 URL: {url_entry['url']}")
            print(f"📋 Conditions: {url_entry.get('conditions', 'N/A')}")
            
            # Get the session data
            if url_entry.get('last_scraped_session_id'):
                session_response = supabase.table("scrape_sessions").select("*").eq("id", url_entry['last_scraped_session_id']).execute()
                
                if session_response.data:
                    session = session_response.data[0]
                    
                    if session.get('structured_data_json'):
                        try:
                            structured_data = json.loads(session['structured_data_json'])
                            
                            if 'listings' in structured_data and structured_data['listings']:
                                actual_fields = list(structured_data['listings'][0].keys())
                                conditions = url_entry.get('conditions', '').split(',')
                                conditions = [c.strip() for c in conditions if c.strip()]
                                
                                print(f"📊 Data fields: {actual_fields}")
                                print(f"🎯 Conditions: {conditions}")
                                
                                # Check field matching
                                missing_fields = [c for c in conditions if c not in actual_fields]
                                if missing_fields:
                                    print(f"❌ Missing fields: {missing_fields}")
                                else:
                                    print(f"✅ All condition fields exist in data")
                                
                                # Show sample data that would be displayed
                                print(f"📝 Sample data that will be displayed:")
                                sample_item = structured_data['listings'][0]
                                for condition in conditions:
                                    value = sample_item.get(condition, 'N/A')
                                    print(f"   {condition}: {value}")
                        
                        except Exception as e:
                            print(f"❌ Error parsing data: {e}")

async def main():
    """Main function"""
    await update_rag_to_structured_only()
    await test_structured_rag()
    verify_frontend_fix()

if __name__ == "__main__":
    asyncio.run(main())
