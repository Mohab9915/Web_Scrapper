#!/usr/bin/env python3
"""
Debug script to test RAG functionality and identify the issue with "couldn't find relevant information" message.
"""
import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import supabase
from backend.app.services.enhanced_rag_service import EnhancedRAGService
from uuid import UUID

async def test_enhanced_rag():
    """Test the enhanced RAG service with a project that has scraped data."""
    
    # Test with project that has scraped data
    test_project_id = "0ba79db8-54af-481b-91f9-889220e3c41b"  # test1 project
    test_query = "What countries are in the dataset?"
    
    print(f"🧪 Testing Enhanced RAG Service")
    print(f"Project ID: {test_project_id}")
    print(f"Query: {test_query}")
    print("=" * 60)
    
    # Check project exists and has RAG enabled
    project_response = supabase.table("projects").select("*").eq("id", test_project_id).single().execute()
    if not project_response.data:
        print("❌ Project not found!")
        return
    
    project = project_response.data
    print(f"✅ Project found: {project['name']}")
    print(f"   RAG Enabled: {project.get('rag_enabled', False)}")
    
    # Check scrape sessions
    sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", test_project_id).execute()
    print(f"✅ Found {len(sessions_response.data)} scrape sessions")
    
    for session in sessions_response.data:
        print(f"   Session {session['id'][:8]}...")
        print(f"     Status: {session['status']}")
        print(f"     URL: {session['url']}")
        print(f"     Unique ID: {session['unique_scrape_identifier']}")
        
        # Check markdowns
        markdown_response = supabase.table("markdowns").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
        print(f"     Markdowns: {len(markdown_response.data)} entries")
        
        # Check embeddings
        embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
        print(f"     Embeddings: {len(embeddings_response.data)} entries")
        
        if embeddings_response.data:
            print(f"     Sample embedding content: {embeddings_response.data[0]['content'][:100]}...")
    
    print("\n" + "=" * 60)
    print("🚀 Testing Enhanced RAG Query")
    
    # Test the enhanced RAG service
    enhanced_rag = EnhancedRAGService()
    
    # Mock Azure credentials (we'll test without actual API calls first)
    mock_credentials = {
        "api_key": "test_key",
        "endpoint": "https://test.openai.azure.com/",
        "api_version": "2024-12-01-preview"
    }
    
    try:
        # Test getting enhanced context first
        print("📋 Testing context retrieval...")
        context_chunks = await enhanced_rag._get_enhanced_context(UUID(test_project_id), test_query)
        print(f"   Context chunks found: {len(context_chunks) if context_chunks else 0}")
        
        if context_chunks:
            for i, chunk in enumerate(context_chunks[:3]):  # Show first 3 chunks
                print(f"   Chunk {i+1}: {chunk['content'][:100]}...")
        else:
            print("   No context chunks found, testing fallback...")
            fallback_context = await enhanced_rag._get_fallback_context(UUID(test_project_id))
            print(f"   Fallback context chunks: {len(fallback_context) if fallback_context else 0}")
            
            if fallback_context:
                for i, chunk in enumerate(fallback_context[:3]):
                    print(f"   Fallback Chunk {i+1}: {chunk['content'][:100]}...")
    
    except Exception as e:
        print(f"❌ Error testing context retrieval: {e}")
        import traceback
        traceback.print_exc()

async def test_keyword_search():
    """Test keyword search functionality."""
    
    test_project_id = "0ba79db8-54af-481b-91f9-889220e3c41b"
    test_query = "countries"
    
    print(f"\n🔍 Testing Keyword Search")
    print(f"Project ID: {test_project_id}")
    print(f"Query: {test_query}")
    print("=" * 60)
    
    # Get sessions for this project
    sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", test_project_id).execute()
    unique_names = [session["unique_scrape_identifier"] for session in sessions_response.data]
    
    print(f"✅ Found {len(unique_names)} unique session identifiers")
    
    # Test direct embeddings query
    for unique_name in unique_names:
        print(f"\n📊 Testing embeddings for: {unique_name}")
        
        embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_name).execute()
        print(f"   Found {len(embeddings_response.data)} embedding chunks")
        
        if embeddings_response.data:
            # Test keyword matching
            matching_chunks = []
            for chunk in embeddings_response.data:
                content = chunk["content"].lower()
                if test_query.lower() in content:
                    matching_chunks.append(chunk)
            
            print(f"   Keyword matches: {len(matching_chunks)}")
            if matching_chunks:
                print(f"   Sample match: {matching_chunks[0]['content'][:200]}...")

if __name__ == "__main__":
    asyncio.run(test_enhanced_rag())
    asyncio.run(test_keyword_search())
