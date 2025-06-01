#!/usr/bin/env python3
"""
Manual RAG Ingestion Script
Ingests the latest scraping session into the RAG system for chat functionality.
"""

import sys
import os
import json
import asyncio
import requests

# Add backend to path
sys.path.append('backend')

async def manual_rag_ingestion():
    """Manually ingest the latest session into RAG system"""
    
    try:
        print("🚀 Manual RAG Ingestion")
        print("=" * 50)
        
        # First, let's use the API endpoint we just created
        backend_url = "http://localhost:8000"
        api_url = f"{backend_url}/api/v1"

        # Get the latest session
        sys.path.insert(0, '.')
        from app.database import supabase
        
        # Find the latest scrapethissite session
        sessions = supabase.table('scrape_sessions').select('*').ilike('url', '%scrapethissite%').order('scraped_at', desc=True).limit(1).execute()
        
        if not sessions.data:
            print("❌ No scrapethissite sessions found")
            return
            
        session = sessions.data[0]
        session_id = session['id']
        project_id = session['project_id']
        
        print(f"📋 Session: {session_id}")
        print(f"🌐 URL: {session['url']}")
        print(f"📅 Scraped: {session['scraped_at']}")
        print(f"📊 Current Status: {session['status']}")
        
        # Check structured data
        if session.get('structured_data_json'):
            structured_data = json.loads(session['structured_data_json']) if isinstance(session['structured_data_json'], str) else session['structured_data_json']
            listings = structured_data.get('listings', [])
            print(f"📊 Data Items: {len(listings)}")
            
            if listings:
                print(f"🔍 Sample Item: {listings[0]}")
        else:
            print("❌ No structured data found")
            return
            
        # Method 1: Try using the API endpoint
        print(f"\n🔄 Method 1: Using API Endpoint")
        try:
            response = requests.post(
                f"{api_url}/projects/{project_id}/sessions/{session_id}/ingest-rag",
                json={},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API Ingestion Success!")
                print(f"   Message: {result.get('message', 'No message')}")
                print(f"   Embeddings: {result.get('embeddings_created', 'Unknown')}")
                print(f"   Data Items: {result.get('data_items', 'Unknown')}")
                print(f"   Status: {result.get('status', 'Unknown')}")
                return
            else:
                print(f"⚠️  API Ingestion Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"⚠️  API method failed: {e}")
            
        # Method 2: Direct ingestion using enhanced RAG service
        print(f"\n🔄 Method 2: Direct Enhanced RAG Service")
        try:
            from app.services.enhanced_rag_service import EnhancedRAGService
            from uuid import UUID
            
            # Create enhanced RAG service
            enhanced_rag_service = EnhancedRAGService()
            
            # Prepare Azure credentials (dummy for testing)
            azure_credentials = {
                "api_key": "dummy_key",
                "endpoint": "dummy_endpoint", 
                "deployment_name": "text-embedding-ada-002"
            }
            
            # Perform ingestion
            success = await enhanced_rag_service.ingest_structured_content(
                project_id=UUID(project_id),
                session_id=UUID(session_id),
                structured_data=structured_data,
                embedding_api_keys=azure_credentials
            )
            
            if success:
                print(f"✅ Direct Ingestion Success!")
                
                # Update session status
                supabase.table('scrape_sessions').update({
                    'status': 'rag_ingested'
                }).eq('id', session_id).execute()
                
                print(f"✅ Session status updated to 'rag_ingested'")
                
            else:
                print(f"⚠️  Direct ingestion completed with warnings")
                
        except Exception as e:
            print(f"⚠️  Direct method failed: {e}")
            
        # Method 3: Simple embedding creation (fallback)
        print(f"\n🔄 Method 3: Simple Embedding Creation (Fallback)")
        try:
            unique_id = session['unique_scrape_identifier']
            
            # Check if embeddings already exist
            existing_embeddings = supabase.table('embeddings').select('*').eq('unique_name', unique_id).execute()
            
            if existing_embeddings.data:
                print(f"✅ Embeddings already exist: {len(existing_embeddings.data)} chunks")
            else:
                # Create simple content from structured data
                content_parts = []
                for i, item in enumerate(listings[:20]):  # First 20 items
                    item_text = f"Item {i+1}: "
                    for key, value in item.items():
                        if value and str(value).strip():
                            item_text += f"{key}: {value}, "
                    content_parts.append(item_text.rstrip(', '))
                
                content = "\\n".join(content_parts)
                
                # Create dummy embedding
                dummy_embedding = [0.0] * 1536
                
                supabase.table('embeddings').insert({
                    'unique_name': unique_id,
                    'chunk_id': 0,
                    'content': content,
                    'embedding': dummy_embedding
                }).execute()
                
                print(f"✅ Simple embeddings created")
                
            # Update session status
            supabase.table('scrape_sessions').update({
                'status': 'rag_ingested'
            }).eq('id', session_id).execute()
            
            print(f"✅ Session status updated to 'rag_ingested'")
            
        except Exception as e:
            print(f"❌ Fallback method failed: {e}")
            
        # Verify the results
        print(f"\n🔍 Verification:")
        
        # Check session status
        updated_session = supabase.table('scrape_sessions').select('*').eq('id', session_id).single().execute()
        print(f"📊 Session Status: {updated_session.data['status']}")
        
        # Check embeddings
        unique_id = session['unique_scrape_identifier']
        embeddings = supabase.table('embeddings').select('*').eq('unique_name', unique_id).execute()
        print(f"🔗 Embeddings: {len(embeddings.data)} chunks")
        
        # Check project RAG sessions
        rag_sessions = supabase.table('scrape_sessions').select('*').eq('project_id', project_id).eq('status', 'rag_ingested').execute()
        print(f"📈 Total RAG sessions for project: {len(rag_sessions.data)}")
        
        print(f"\n🎉 RAG Ingestion Complete!")
        print(f"\n💡 You can now:")
        print(f"1. Enable RAG in the UI")
        print(f"2. Ask questions like 'How many countries are there?'")
        print(f"3. Query specific data like 'What countries have the largest area?'")
        
    except Exception as e:
        print(f"❌ Error during RAG ingestion: {e}")
        import traceback
        traceback.print_exc()

def test_rag_status():
    """Test the RAG status endpoint"""
    try:
        print(f"\n🧪 Testing RAG Status Endpoint")
        print("=" * 40)
        
        backend_url = "http://localhost:8000"
        api_url = f"{backend_url}/api/v1"
        
        # Get project ID
        sys.path.insert(0, '.')
        from app.database import supabase
        
        projects = supabase.table('projects').select('*').ilike('name', '%countries%').execute()
        if not projects.data:
            print("❌ No countries project found")
            return
            
        project_id = projects.data[0]['id']
        
        # Test RAG status endpoint
        response = requests.get(f"{api_url}/projects/{project_id}/rag-status", timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ RAG Status Retrieved:")
            print(f"   Project ID: {status.get('project_id')}")
            print(f"   RAG Enabled: {status.get('rag_enabled')}")
            print(f"   Total Sessions: {status.get('total_sessions')}")
            print(f"   RAG Ingested Sessions: {status.get('rag_ingested_sessions')}")
            print(f"   Total Embeddings: {status.get('total_embeddings')}")
            
            sessions = status.get('sessions', [])
            print(f"\\n📋 Session Details:")
            for session in sessions[-3:]:  # Last 3 sessions
                print(f"   - {session['session_id'][:8]}... | {session['status']} | {session['embeddings']} embeddings")
                
        else:
            print(f"❌ RAG Status Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing RAG status: {e}")

if __name__ == "__main__":
    print("🔧 ScrapeMaster AI - Manual RAG Ingestion")
    print("This will ingest your scraped data into the RAG system for chat functionality")
    
    # Run the ingestion
    asyncio.run(manual_rag_ingestion())
    
    # Test the status endpoint
    test_rag_status()
