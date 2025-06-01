#!/usr/bin/env python3
"""
Fix both the data display issue and RAG ingestion to use only structured data.
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

async def fix_conditions_mismatch():
    """Fix the conditions field mismatch that's causing empty country names"""
    print("🔧 FIXING CONDITIONS FIELD MISMATCH")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Get all project URLs with mismatched conditions
    project_urls_response = supabase.table("project_urls").select("*").execute()
    
    fixed_count = 0
    
    for url_entry in project_urls_response.data:
        print(f"\n🔍 Checking URL: {url_entry['url']}")
        print(f"   Current conditions: {url_entry.get('conditions', 'N/A')}")
        
        # Get the latest session for this URL
        if url_entry.get('last_scraped_session_id'):
            session_response = supabase.table("scrape_sessions").select("*").eq("id", url_entry['last_scraped_session_id']).execute()
            
            if session_response.data:
                session = session_response.data[0]
                
                # Check structured data to get actual fields
                if session.get('structured_data_json'):
                    try:
                        if isinstance(session['structured_data_json'], str):
                            structured_data = json.loads(session['structured_data_json'])
                        else:
                            structured_data = session['structured_data_json']
                        
                        # Get actual fields from the data
                        actual_fields = []
                        if 'listings' in structured_data and structured_data['listings']:
                            actual_fields = list(structured_data['listings'][0].keys())
                        elif isinstance(structured_data, list) and structured_data:
                            actual_fields = list(structured_data[0].keys())
                        elif isinstance(structured_data, dict):
                            actual_fields = list(structured_data.keys())
                        
                        if actual_fields:
                            print(f"   Actual fields in data: {actual_fields}")
                            
                            # Check if conditions match actual fields
                            current_conditions = url_entry.get('conditions', '').split(',')
                            current_conditions = [c.strip() for c in current_conditions if c.strip()]
                            
                            # Check for common mismatches
                            needs_fix = False
                            new_conditions = []
                            
                            for condition in current_conditions:
                                if condition == 'name' and 'country' in actual_fields:
                                    new_conditions.append('country')
                                    needs_fix = True
                                    print(f"   🔧 Mapping 'name' → 'country'")
                                elif condition in actual_fields:
                                    new_conditions.append(condition)
                                else:
                                    # Try to find a close match
                                    if condition.lower() in [f.lower() for f in actual_fields]:
                                        matching_field = next(f for f in actual_fields if f.lower() == condition.lower())
                                        new_conditions.append(matching_field)
                                        needs_fix = True
                                        print(f"   🔧 Mapping '{condition}' → '{matching_field}'")
                                    else:
                                        print(f"   ⚠️  Field '{condition}' not found in data")
                            
                            # Add missing important fields
                            important_fields = ['country', 'capital', 'population', 'area']
                            for field in important_fields:
                                if field in actual_fields and field not in new_conditions:
                                    new_conditions.append(field)
                                    needs_fix = True
                                    print(f"   ➕ Adding missing field: '{field}'")
                            
                            if needs_fix:
                                new_conditions_str = ', '.join(new_conditions)
                                print(f"   ✅ Updating conditions: {new_conditions_str}")
                                
                                # Update the project_urls entry
                                supabase.table("project_urls").update({
                                    "conditions": new_conditions_str
                                }).eq("id", url_entry['id']).execute()
                                
                                fixed_count += 1
                            else:
                                print(f"   ✅ Conditions already correct")
                        
                    except Exception as e:
                        print(f"   ❌ Error parsing structured data: {e}")
    
    print(f"\n🎉 Fixed {fixed_count} project URLs with mismatched conditions!")

async def fix_rag_structured_data_only():
    """Fix RAG ingestion to use only structured data, not full markdown"""
    print("\n🔧 FIXING RAG TO USE ONLY STRUCTURED DATA")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    # Get Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Find RAG-enabled projects with rag_ingested sessions
    projects_response = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    for project in projects_response.data:
        print(f"\n📋 Project: {project['name']}")
        
        # Get rag_ingested sessions
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        
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
                    
                    # Create structured data content for RAG (no full markdown)
                    structured_content = ""
                    
                    if 'listings' in structured_data and structured_data['listings']:
                        structured_content += f"# Dataset: {len(structured_data['listings'])} Countries\n\n"
                        
                        for i, item in enumerate(structured_data['listings'], 1):
                            structured_content += f"## {i}. {item.get('country', 'Unknown')}\n"
                            
                            for key, value in item.items():
                                if key != 'country':  # Don't repeat country name
                                    structured_content += f"**{key.title()}**: {value}\n"
                            structured_content += "\n"
                    
                    elif 'tabular_data' in structured_data and structured_data['tabular_data']:
                        structured_content += f"# Dataset: {len(structured_data['tabular_data'])} Records\n\n"
                        
                        for i, item in enumerate(structured_data['tabular_data'], 1):
                            structured_content += f"## Record {i}\n"
                            for key, value in item.items():
                                structured_content += f"**{key.title()}**: {value}\n"
                            structured_content += "\n"
                    
                    if structured_content:
                        print(f"   📄 Created structured content: {len(structured_content)} characters")
                        
                        # Clear existing embeddings
                        supabase.table("embeddings").delete().eq("unique_name", session['unique_scrape_identifier']).execute()
                        print("   🗑️  Cleared old embeddings")
                        
                        # Update markdown table with structured content only
                        supabase.table("markdowns").update({
                            "markdown": structured_content
                        }).eq("unique_name", session['unique_scrape_identifier']).execute()
                        print("   📝 Updated markdown with structured content only")
                        
                        # Re-ingest with structured data only
                        success = await rag_service.ingest_scraped_content(
                            project_id=UUID(project['id']),
                            session_id=UUID(session['id']),
                            markdown_content=structured_content,
                            azure_credentials=azure_credentials,
                            structured_data=structured_data
                        )
                        
                        if success:
                            print("   ✅ RAG re-ingestion completed with structured data only")
                        else:
                            print("   ❌ RAG re-ingestion failed")
                    
                except Exception as e:
                    print(f"   ❌ Error processing structured data: {e}")

async def test_fixes():
    """Test both fixes"""
    print("\n🧪 TESTING FIXES")
    print("=" * 60)
    
    supabase = get_supabase_client()
    rag_service = RAGService()
    
    # Test 1: Check if conditions are now correct
    print("\n1️⃣ Testing conditions fix...")
    project_urls_response = supabase.table("project_urls").select("*").execute()
    
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
                        
                        print(f"URL: {url_entry['url'][:50]}...")
                        print(f"  Conditions: {conditions}")
                        print(f"  Actual fields: {actual_fields}")
                        
                        # Check if all conditions exist in actual fields
                        missing = [c for c in conditions if c not in actual_fields]
                        if missing:
                            print(f"  ❌ Missing fields: {missing}")
                        else:
                            print(f"  ✅ All conditions match actual fields")
                except:
                    pass
    
    # Test 2: Test RAG with structured data
    print("\n2️⃣ Testing RAG with structured data only...")
    
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', '')
    }
    
    # Find a RAG-enabled project
    projects_response = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    for project in projects_response.data:
        rag_sessions = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        
        if rag_sessions.data:
            print(f"\nTesting project: {project['name']}")
            
            test_queries = [
                "How many countries are there?",
                "What is the capital of France?",
                "List 3 countries with their areas"
            ]
            
            for query in test_queries:
                try:
                    result = await rag_service.query_rag(
                        project_id=UUID(project['id']),
                        query=query,
                        azure_credentials=azure_credentials,
                        llm_model='gpt-4o'
                    )
                    
                    print(f"  ✅ '{query}' → {result.answer[:100]}...")
                    
                except Exception as e:
                    print(f"  ❌ '{query}' → Error: {e}")
            
            break  # Test only first project

async def main():
    """Main function"""
    await fix_conditions_mismatch()
    await fix_rag_structured_data_only()
    await test_fixes()

if __name__ == "__main__":
    asyncio.run(main())
