#!/usr/bin/env python3
"""
Fix missing embeddings for sessions marked as rag_ingested but without actual embeddings.
"""
import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import supabase
from backend.app.utils.embedding import generate_embeddings_batch
from backend.app.utils.text_processing import chunk_text
from dotenv import load_dotenv

load_dotenv()

async def fix_missing_embeddings():
    """Fix missing embeddings for current sessions."""
    
    print("🔧 FIXING MISSING EMBEDDINGS")
    print("=" * 60)
    
    # Get Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', ''),
        'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
    }
    
    if not azure_credentials['api_key'] or not azure_credentials['endpoint']:
        print("❌ Azure OpenAI credentials not found!")
        return
    
    print(f"✅ Azure credentials loaded")
    print(f"   Endpoint: {azure_credentials['endpoint'][:50]}...")
    
    # Get all sessions marked as rag_ingested
    sessions_response = supabase.table("scrape_sessions").select("*").eq("status", "rag_ingested").execute()
    
    print(f"\n📊 Found {len(sessions_response.data)} sessions marked as 'rag_ingested'")
    
    for session in sessions_response.data:
        unique_id = session['unique_scrape_identifier']
        
        print(f"\n🔍 Processing session: {session['id'][:8]}...")
        print(f"   Project: {session['project_id']}")
        print(f"   URL: {session['url']}")
        print(f"   Unique ID: {unique_id}")
        
        # Check if embeddings exist
        embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_id).execute()
        
        if embeddings_response.data:
            print(f"   ✅ Already has {len(embeddings_response.data)} embeddings - skipping")
            continue
        
        print(f"   ❌ Missing embeddings - will regenerate")
        
        # Get markdown content
        markdown_response = supabase.table("markdowns").select("*").eq("unique_name", unique_id).execute()
        
        if not markdown_response.data:
            print(f"   ❌ No markdown found - skipping")
            continue
        
        markdown_content = markdown_response.data[0]['markdown']
        print(f"   ✅ Found markdown content ({len(markdown_content)} chars)")
        
        # Create chunks
        chunks = await chunk_text(markdown_content, chunk_size=1000, overlap=100)
        print(f"   📝 Created {len(chunks)} chunks")
        
        try:
            # Generate embeddings
            print(f"   🧠 Generating embeddings...")
            embeddings = await generate_embeddings_batch(chunks, azure_credentials)
            print(f"   ✅ Generated {len(embeddings)} embeddings")
            
            # Verify embedding dimensions
            if embeddings and len(embeddings[0]) == 1536:
                print(f"   ✅ Embeddings have correct dimensions (1536)")
            else:
                print(f"   ⚠️  Warning: Embeddings have {len(embeddings[0]) if embeddings else 0} dimensions")
            
            # Store embeddings
            print(f"   💾 Storing embeddings...")
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                supabase.table("embeddings").insert({
                    "unique_name": unique_id,
                    "chunk_id": i,
                    "content": chunk,
                    "embedding": embedding
                }).execute()
            
            print(f"   ✅ Stored {len(embeddings)} embeddings successfully")
            
        except Exception as e:
            print(f"   ❌ Error generating embeddings: {e}")
            import traceback
            traceback.print_exc()
            
            # Update session status to indicate failure
            supabase.table("scrape_sessions").update({
                "status": "error"
            }).eq("id", session['id']).execute()
            
            print(f"   ⚠️  Updated session status to 'error'")
    
    print(f"\n🎉 Embedding fix process completed!")

async def verify_embeddings():
    """Verify that embeddings were created successfully."""
    
    print(f"\n🔍 VERIFYING EMBEDDINGS")
    print("=" * 60)
    
    # Get all sessions marked as rag_ingested
    sessions_response = supabase.table("scrape_sessions").select("*").eq("status", "rag_ingested").execute()
    
    total_sessions = len(sessions_response.data)
    sessions_with_embeddings = 0
    
    for session in sessions_response.data:
        unique_id = session['unique_scrape_identifier']
        
        # Check embeddings
        embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_id).execute()
        
        if embeddings_response.data:
            sessions_with_embeddings += 1
            print(f"✅ {session['id'][:8]}... has {len(embeddings_response.data)} embeddings")
        else:
            print(f"❌ {session['id'][:8]}... has NO embeddings")
    
    print(f"\n📊 Summary:")
    print(f"   Total rag_ingested sessions: {total_sessions}")
    print(f"   Sessions with embeddings: {sessions_with_embeddings}")
    print(f"   Sessions missing embeddings: {total_sessions - sessions_with_embeddings}")
    
    if sessions_with_embeddings == total_sessions:
        print(f"🎉 All sessions have embeddings!")
    else:
        print(f"⚠️  Some sessions still missing embeddings")

if __name__ == "__main__":
    asyncio.run(fix_missing_embeddings())
    asyncio.run(verify_embeddings())
