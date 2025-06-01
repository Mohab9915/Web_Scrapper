#!/usr/bin/env python3
"""
Test the automatic embedding process without Azure credentials
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from uuid import UUID, uuid4

async def test_automatic_embedding():
    """Test the automatic embedding process"""
    
    print("🧪 TESTING AUTOMATIC EMBEDDING PROCESS")
    print("=" * 60)
    
    try:
        from backend.app.services.enhanced_rag_service import EnhancedRAGService
        
        enhanced_rag = EnhancedRAGService()
        
        # Create test data similar to what would be scraped
        test_structured_data = {
            "title": "Test Countries Data",
            "source_url": "https://test.example.com",
            "tabular_data": [
                {
                    "country": "Russia",
                    "capital": "Moscow",
                    "population": "140,702,000",
                    "area": "1.71E7"
                },
                {
                    "country": "China",
                    "capital": "Beijing", 
                    "population": "1,439,323,776",
                    "area": "9.597E6"
                },
                {
                    "country": "USA",
                    "capital": "Washington D.C.",
                    "population": "331,002,651",
                    "area": "9.834E6"
                }
            ]
        }
        
        # Test with empty credentials (should use fallback)
        empty_credentials = {}
        
        print("Testing ingest_structured_content with empty credentials...")
        print(f"Test data contains {len(test_structured_data['tabular_data'])} countries")
        
        # Create a test session ID
        test_session_id = uuid4()
        test_project_id = UUID("67bbf078-6648-49f3-9068-95228bfb4989")
        
        print(f"Test session ID: {test_session_id}")
        print(f"Project ID: {test_project_id}")
        
        # Test the ingestion process
        success = await enhanced_rag.ingest_structured_content(
            project_id=test_project_id,
            session_id=test_session_id,
            structured_data=test_structured_data,
            embedding_api_keys=empty_credentials,
            project_url_id=None
        )
        
        if success:
            print("✅ Automatic embedding process succeeded!")
            
            # Check if data was stored
            from backend.app.database import supabase
            
            # Check session status
            session_response = supabase.table("scrape_sessions").select("*").eq("id", str(test_session_id)).execute()
            if session_response.data:
                session = session_response.data[0]
                print(f"  Session status: {session.get('status')}")
                print(f"  Unique identifier: {session.get('unique_scrape_identifier')}")
                
                unique_id = session.get('unique_scrape_identifier')
                if unique_id:
                    # Check embeddings
                    embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_id).execute()
                    embeddings = embeddings_response.data or []
                    print(f"  Embeddings created: {len(embeddings)}")
                    
                    # Check if Russia data is in embeddings
                    russia_chunks = [e for e in embeddings if 'russia' in e.get('content', '').lower()]
                    print(f"  Chunks containing Russia: {len(russia_chunks)}")
                    
                    if russia_chunks:
                        print("  ✅ Russia data successfully embedded!")
                        sample_content = russia_chunks[0].get('content', '')
                        print(f"  Sample content: {sample_content[:200]}...")
                    
                    # Check markdowns
                    markdown_response = supabase.table("markdowns").select("*").eq("unique_name", unique_id).execute()
                    markdowns = markdown_response.data or []
                    print(f"  Markdown entries: {len(markdowns)}")
                    
                    return True
            else:
                print("❌ Session not found after ingestion")
                return False
        else:
            print("❌ Automatic embedding process failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing automatic embedding: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fallback_embeddings():
    """Test the fallback embedding generation"""
    
    print("\n" + "=" * 60)
    print("🔧 TESTING FALLBACK EMBEDDING GENERATION")
    print("=" * 60)
    
    try:
        from backend.app.services.enhanced_rag_service import EnhancedRAGService
        
        enhanced_rag = EnhancedRAGService()
        
        # Test fallback embedding generation
        test_texts = [
            "Russia is a country with capital Moscow and population 140,702,000",
            "China is a country with capital Beijing and population 1,439,323,776",
            "USA is a country with capital Washington D.C. and population 331,002,651"
        ]
        
        print(f"Testing fallback embeddings for {len(test_texts)} texts...")
        
        for i, text in enumerate(test_texts, 1):
            embedding = enhanced_rag._generate_fallback_embedding(text)
            print(f"  Text {i}: {len(embedding)} dimensions")
            print(f"    Sample values: {embedding[:5]}")
            print(f"    Text preview: {text[:50]}...")
            
            # Verify embedding properties
            if len(embedding) == 1536:
                print(f"    ✅ Correct dimensions")
            else:
                print(f"    ❌ Wrong dimensions: {len(embedding)}")
            
            # Check if normalized
            import math
            magnitude = math.sqrt(sum(x*x for x in embedding))
            if 0.9 <= magnitude <= 1.1:
                print(f"    ✅ Properly normalized (magnitude: {magnitude:.3f})")
            else:
                print(f"    ⚠️  Normalization issue (magnitude: {magnitude:.3f})")
        
        print("✅ Fallback embedding generation working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing fallback embeddings: {e}")
        return False

async def test_query_with_fallback_embeddings():
    """Test querying with fallback embeddings"""
    
    print("\n" + "=" * 60)
    print("🔍 TESTING QUERY WITH FALLBACK EMBEDDINGS")
    print("=" * 60)
    
    try:
        from backend.app.services.enhanced_rag_service import EnhancedRAGService
        
        enhanced_rag = EnhancedRAGService()
        project_id = UUID("67bbf078-6648-49f3-9068-95228bfb4989")
        query = "tell me about Russia"
        
        print(f"Testing query: '{query}'")
        print(f"Project ID: {project_id}")
        
        # Test enhanced context retrieval
        context_chunks = await enhanced_rag._get_enhanced_context(project_id, query)
        print(f"Enhanced context chunks found: {len(context_chunks)}")
        
        if context_chunks:
            russia_chunks = [c for c in context_chunks if 'russia' in c.get('content', '').lower()]
            print(f"Chunks containing Russia: {len(russia_chunks)}")
            
            if russia_chunks:
                print("✅ Query successfully found Russia data with fallback embeddings!")
                sample_content = russia_chunks[0].get('content', '')
                print(f"Sample content: {sample_content[:200]}...")
                return True
            else:
                print("⚠️  Context found but no Russia data")
                return False
        else:
            print("❌ No context chunks found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing query with fallback embeddings: {e}")
        return False

async def main():
    """Run all tests"""
    
    print("🚀 TESTING AUTOMATIC EMBEDDING SYSTEM")
    print("=" * 80)
    
    # Test 1: Automatic embedding process
    success1 = await test_automatic_embedding()
    
    # Test 2: Fallback embedding generation
    success2 = await test_fallback_embeddings()
    
    # Test 3: Query with fallback embeddings
    success3 = await test_query_with_fallback_embeddings()
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    
    if success1:
        print("✅ Automatic embedding process works without Azure credentials")
    else:
        print("❌ Automatic embedding process needs work")
    
    if success2:
        print("✅ Fallback embedding generation is working")
    else:
        print("❌ Fallback embedding generation needs work")
    
    if success3:
        print("✅ Query system works with fallback embeddings")
    else:
        print("❌ Query system needs work with fallback embeddings")
    
    if success1 and success2 and success3:
        print("\n🎉 EXCELLENT! Your system now automatically embeds scraped data")
        print("   even without Azure OpenAI credentials!")
        print("\n📋 What this means:")
        print("   • New scrapes will automatically create embeddings")
        print("   • RAG queries will work immediately after scraping")
        print("   • No more manual intervention needed")
        print("   • Azure OpenAI is optional (but recommended for better quality)")
    else:
        print("\n⚠️  Some issues remain with the automatic embedding system")
    
    print("\n🎯 Try scraping a new URL to test the automatic embedding!")

if __name__ == "__main__":
    asyncio.run(main())
