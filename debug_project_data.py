#!/usr/bin/env python3
"""
Debug script to check what data is available in the project
"""

import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

async def debug_project_data():
    """Debug what data is available in the project."""
    print("🔍 Debugging Project Data\n")
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Use existing project ID from logs
    project_id = "67df8224-feba-4dd0-8648-abb9100cbb38"
    
    print(f"📊 Checking project: {project_id}\n")
    
    # Check project details
    try:
        project_response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        if project_response.data:
            project = project_response.data
            print(f"✅ Project found:")
            print(f"   Name: {project.get('name', 'N/A')}")
            print(f"   RAG Enabled: {project.get('rag_enabled', False)}")
            print(f"   Created: {project.get('created_at', 'N/A')}")
        else:
            print(f"❌ Project not found")
            return
    except Exception as e:
        print(f"❌ Error fetching project: {e}")
        return
    
    print()
    
    # Check scrape sessions
    try:
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        print(f"📋 Found {len(sessions)} scrape sessions:")
        for i, session in enumerate(sessions, 1):
            print(f"   Session {i}:")
            print(f"     ID: {session.get('id', 'N/A')}")
            print(f"     Status: {session.get('status', 'N/A')}")
            print(f"     Unique Name: {session.get('unique_scrape_identifier', 'N/A')}")
            print(f"     Created: {session.get('created_at', 'N/A')}")
            
            # Check structured data
            structured_data = session.get('structured_data')
            if structured_data:
                if isinstance(structured_data, dict):
                    tabular_data = structured_data.get('tabular_data', [])
                    print(f"     Tabular Data: {len(tabular_data)} items")
                    if tabular_data:
                        # Show first item as example
                        first_item = tabular_data[0]
                        print(f"     Sample Item: {list(first_item.keys())[:5]}...")
                else:
                    print(f"     Structured Data: {type(structured_data)}")
            else:
                print(f"     Structured Data: None")
            print()
            
    except Exception as e:
        print(f"❌ Error fetching sessions: {e}")
    
    # Check embeddings
    try:
        embeddings_response = supabase.table("embeddings").select("unique_name, content").eq("project_id", project_id).execute()
        embeddings = embeddings_response.data or []
        
        print(f"🧠 Found {len(embeddings)} embedding chunks:")
        unique_names = set()
        for embedding in embeddings:
            unique_names.add(embedding.get('unique_name', 'Unknown'))
        
        for unique_name in unique_names:
            chunks = [e for e in embeddings if e.get('unique_name') == unique_name]
            print(f"   {unique_name}: {len(chunks)} chunks")
            if chunks:
                sample_content = chunks[0].get('content', '')[:100]
                print(f"     Sample: {sample_content}...")
        print()
            
    except Exception as e:
        print(f"❌ Error fetching embeddings: {e}")
    
    # Test the enhanced RAG context methods
    print("🧪 Testing Enhanced RAG Context Methods:")
    
    try:
        # Import the enhanced RAG service
        import sys
        sys.path.append('backend')
        from app.services.enhanced_rag_service import EnhancedRAGService
        
        enhanced_rag = EnhancedRAGService()
        
        # Test enhanced context
        enhanced_context = await enhanced_rag._get_enhanced_context(project_id, "show me products")
        print(f"   Enhanced context chunks: {len(enhanced_context)}")
        
        # Test fallback context
        fallback_context = await enhanced_rag._get_fallback_context(project_id)
        print(f"   Fallback context chunks: {len(fallback_context)}")
        
        if fallback_context:
            print(f"   Sample fallback content: {fallback_context[0]['content'][:200]}...")
        
    except Exception as e:
        print(f"❌ Error testing RAG context: {e}")
    
    print("\n✅ Debug complete!")

async def main():
    await debug_project_data()

if __name__ == "__main__":
    asyncio.run(main())
