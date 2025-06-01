#!/usr/bin/env python3
"""
Fix missing markdown entries in the markdowns table and complete RAG ingestion.
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

async def fix_missing_markdown():
    """Fix missing markdown entries and complete RAG ingestion"""
    print("🔧 FIXING MISSING MARKDOWN ENTRIES")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    # Get Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    print(f"Azure credentials: {'✅ Available' if azure_credentials['api_key'] else '❌ Missing'}")
    
    # Find sessions with raw_markdown but no markdowns table entry
    sessions_response = supabase.table("scrape_sessions").select("*").execute()
    
    fixed_count = 0
    
    for session in sessions_response.data:
        # Check if markdown entry exists
        markdown_response = supabase.table("markdowns").select("id").eq("unique_name", session['unique_scrape_identifier']).execute()
        
        if not markdown_response.data and session.get('raw_markdown'):
            print(f"\n🔧 Fixing session: {session['id']}")
            print(f"   URL: {session['url']}")
            print(f"   Project: {session['project_id']}")
            
            # Create markdown content from structured data if available
            markdown_content = session['raw_markdown']
            
            # If we have structured data, enhance the markdown
            if session.get('structured_data_json'):
                try:
                    if isinstance(session['structured_data_json'], str):
                        data = json.loads(session['structured_data_json'])
                    else:
                        data = session['structured_data_json']
                    
                    # Convert structured data to better markdown for RAG
                    enhanced_content = ""
                    
                    if 'listings' in data and data['listings']:
                        enhanced_content += "# Countries and Territories Data\n\n"
                        enhanced_content += f"This dataset contains information about {len(data['listings'])} countries and territories.\n\n"
                        
                        for i, item in enumerate(data['listings'], 1):
                            enhanced_content += f"## {i}. {item.get('country', 'Unknown Country')}\n\n"
                            
                            if 'capital' in item:
                                enhanced_content += f"**Capital:** {item['capital']}\n\n"
                            if 'population' in item:
                                enhanced_content += f"**Population:** {item['population']}\n\n"
                            if 'area' in item:
                                enhanced_content += f"**Area:** {item['area']} square kilometers\n\n"
                            
                            # Add any other fields
                            for key, value in item.items():
                                if key not in ['country', 'capital', 'population', 'area'] and value:
                                    enhanced_content += f"**{key.title()}:** {value}\n\n"
                            
                            enhanced_content += "---\n\n"
                    
                    elif 'tabular_data' in data and data['tabular_data']:
                        enhanced_content += "# Tabular Data\n\n"
                        enhanced_content += f"This dataset contains {len(data['tabular_data'])} records.\n\n"
                        
                        for i, item in enumerate(data['tabular_data'], 1):
                            enhanced_content += f"## Record {i}\n\n"
                            for key, value in item.items():
                                enhanced_content += f"**{key.title()}:** {value}\n\n"
                            enhanced_content += "---\n\n"
                    
                    if enhanced_content:
                        # Combine original markdown with enhanced structured content
                        markdown_content = enhanced_content + "\n\n# Original Content\n\n" + markdown_content
                        print(f"   ✅ Enhanced with structured data ({len(data.get('listings', data.get('tabular_data', [])))} items)")
                    
                except Exception as e:
                    print(f"   ⚠️  Could not enhance with structured data: {e}")
            
            # Save to markdowns table
            try:
                supabase.table("markdowns").insert({
                    "unique_name": session['unique_scrape_identifier'],
                    "url": session['url'],
                    "markdown": markdown_content
                }).execute()
                
                print(f"   ✅ Created markdown entry ({len(markdown_content)} characters)")
                fixed_count += 1
                
                # Now attempt RAG ingestion if the project has RAG enabled
                project_response = supabase.table("projects").select("rag_enabled").eq("id", session['project_id']).single().execute()
                
                if project_response.data and project_response.data['rag_enabled']:
                    print("   🚀 Starting RAG ingestion...")
                    
                    # Get structured data for ingestion
                    structured_data = None
                    if session.get('structured_data_json'):
                        try:
                            if isinstance(session['structured_data_json'], str):
                                structured_data = json.loads(session['structured_data_json'])
                            else:
                                structured_data = session['structured_data_json']
                        except:
                            pass
                    
                    success = await rag_service.ingest_scraped_content(
                        project_id=UUID(session['project_id']),
                        session_id=UUID(session['id']),
                        markdown_content=markdown_content,
                        azure_credentials=azure_credentials if azure_credentials['api_key'] else None,
                        structured_data=structured_data
                    )
                    
                    if success:
                        print("   ✅ RAG ingestion completed!")
                        
                        # Verify the status update
                        updated_session = supabase.table("scrape_sessions").select("status").eq("id", session['id']).single().execute()
                        if updated_session.data:
                            print(f"   Status: {updated_session.data['status']}")
                    else:
                        print("   ❌ RAG ingestion failed")
                
            except Exception as e:
                print(f"   ❌ Error creating markdown entry: {e}")
    
    print(f"\n🎉 Fixed {fixed_count} missing markdown entries!")
    
    # Test RAG functionality
    await test_rag_queries()

async def test_rag_queries():
    """Test RAG queries after fixing the data"""
    print("\n🧪 TESTING RAG QUERIES")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    # Get Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Find a project with RAG enabled and rag_ingested sessions
    projects_response = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    for project in projects_response.data:
        # Check if this project has rag_ingested sessions
        rag_sessions = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        
        if rag_sessions.data:
            print(f"\n🧪 Testing project: {project['name']}")
            
            test_queries = [
                "How many countries are in the dataset?",
                "What is the capital of France?",
                "Which country has the largest area?",
                "List the first 5 countries with their capitals",
                "What is the population of Russia?"
            ]
            
            for query in test_queries:
                print(f"\n  ❓ Query: {query}")
                try:
                    result = await rag_service.query_rag(
                        project_id=UUID(project['id']),
                        query=query,
                        azure_credentials=azure_credentials,
                        llm_model='gpt-4o'
                    )
                    
                    print(f"  ✅ Answer: {result.answer[:300]}...")
                    print(f"  📊 Sources: {len(result.source_documents)} documents")
                    
                    if result.source_documents:
                        print(f"  🔗 Sample source: {result.source_documents[0]['metadata']['url']}")
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
            
            break  # Test only the first available project
    
    print("\n✅ RAG testing completed!")

async def main():
    """Main function"""
    await fix_missing_markdown()

if __name__ == "__main__":
    asyncio.run(main())
