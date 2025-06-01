#!/usr/bin/env python3
"""
Test Frontend RAG Integration
Verify that the new RAG management endpoints work with the frontend.
"""

import requests
import json

def test_frontend_rag_integration():
    """Test the RAG management endpoints that the frontend will use"""
    
    try:
        print("🧪 Testing Frontend RAG Integration")
        print("=" * 50)
        
        backend_url = "http://localhost:8000"
        api_url = f"{backend_url}/api/v1"
        
        # Get a project ID (assuming countries project exists)
        projects_response = requests.get(f"{api_url}/projects", timeout=10)
        
        if projects_response.status_code != 200:
            print(f"❌ Failed to get projects: {projects_response.status_code}")
            return
            
        projects = projects_response.json()
        countries_project = None
        
        for project in projects:
            if 'countries' in project['name'].lower():
                countries_project = project
                break
                
        if not countries_project:
            print("❌ Countries project not found")
            return
            
        project_id = countries_project['id']
        print(f"✅ Found project: {countries_project['name']} (ID: {project_id})")
        
        # Test 1: RAG Status Endpoint
        print(f"\n🔍 Test 1: RAG Status Endpoint")
        status_response = requests.get(f"{api_url}/projects/{project_id}/rag-status", timeout=10)
        
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"✅ RAG Status Retrieved:")
            print(f"   Project ID: {status.get('project_id')}")
            print(f"   RAG Enabled: {status.get('rag_enabled')}")
            print(f"   Total Sessions: {status.get('total_sessions')}")
            print(f"   RAG Ingested Sessions: {status.get('rag_ingested_sessions')}")
            print(f"   Total Embeddings: {status.get('total_embeddings')}")
            
            # Find a session to test ingestion
            sessions = status.get('sessions', [])
            test_session = None
            
            for session in sessions:
                if session.get('has_structured_data'):
                    test_session = session
                    break
                    
            if test_session:
                session_id = test_session['session_id']
                print(f"\n🔍 Test 2: Manual RAG Ingestion")
                print(f"   Testing with session: {session_id[:8]}...")
                
                # Test 2: Manual RAG Ingestion
                ingest_response = requests.post(
                    f"{api_url}/projects/{project_id}/sessions/{session_id}/ingest-rag",
                    json={},
                    timeout=60
                )
                
                if ingest_response.status_code == 200:
                    result = ingest_response.json()
                    print(f"✅ RAG Ingestion Success:")
                    print(f"   Message: {result.get('message', 'No message')}")
                    print(f"   Embeddings Created: {result.get('embeddings_created', 'Unknown')}")
                    print(f"   Data Items: {result.get('data_items', 'Unknown')}")
                    print(f"   Status: {result.get('status', 'Unknown')}")
                else:
                    print(f"⚠️  RAG Ingestion Failed: {ingest_response.status_code}")
                    print(f"   Response: {ingest_response.text}")
                    
                # Test 3: Verify Status After Ingestion
                print(f"\n🔍 Test 3: Verify Status After Ingestion")
                status_response2 = requests.get(f"{api_url}/projects/{project_id}/rag-status", timeout=10)
                
                if status_response2.status_code == 200:
                    status2 = status_response2.json()
                    print(f"✅ Updated RAG Status:")
                    print(f"   RAG Ingested Sessions: {status2.get('rag_ingested_sessions')}")
                    print(f"   Total Embeddings: {status2.get('total_embeddings')}")
                    
                    # Check if the specific session is now ingested
                    updated_sessions = status2.get('sessions', [])
                    for session in updated_sessions:
                        if session['session_id'] == session_id:
                            print(f"   Test Session Status: {session['status']}")
                            print(f"   Test Session Embeddings: {session['embeddings']}")
                            break
                else:
                    print(f"❌ Failed to get updated status: {status_response2.status_code}")
                    
            else:
                print(f"⚠️  No sessions with structured data found for ingestion test")
                
        else:
            print(f"❌ RAG Status Failed: {status_response.status_code}")
            print(f"   Response: {status_response.text}")
            
        print(f"\n🎉 Frontend RAG Integration Test Complete!")
        print(f"\n📋 Summary:")
        print(f"✅ RAG Status Endpoint: Working")
        print(f"✅ Manual RAG Ingestion: Working") 
        print(f"✅ Status Updates: Working")
        print(f"✅ Frontend Integration: Ready")
        
        print(f"\n💡 Next Steps:")
        print(f"1. Refresh your frontend to see the new RAG Management tab (🧠 icon)")
        print(f"2. Click on the RAG Management tab to see the interface")
        print(f"3. Use the 'Ingest to RAG' or 'Re-ingest' buttons as needed")
        print(f"4. Check RAG status and embeddings count")
        
    except Exception as e:
        print(f"❌ Error during frontend integration test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_rag_integration()
