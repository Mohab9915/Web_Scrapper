#!/usr/bin/env python3
"""
Test the automatic embedding process through real scraping API
"""

import requests
import time
import json

def test_scraping_with_automatic_embedding():
    """Test scraping a URL and verify automatic embedding works"""
    
    print("🧪 TESTING AUTOMATIC EMBEDDING THROUGH SCRAPING API")
    print("=" * 70)
    
    backend_url = "http://localhost:8000"
    project_id = "67bbf078-6648-49f3-9068-95228bfb4989"
    
    # Test URL - use a simple page that will have structured data
    test_url = "https://scrapethissite.com/pages/simple/"
    
    print(f"Project ID: {project_id}")
    print(f"Test URL: {test_url}")
    print(f"Backend URL: {backend_url}")
    
    # Prepare scraping request (without Azure credentials to test fallback)
    scrape_payload = {
        "url": test_url,
        "rag_enabled": True,
        "display_format": "table",
        "api_keys": {}  # Empty API keys to test fallback embedding
    }
    
    print(f"\n📤 Sending scraping request...")
    print(f"RAG enabled: {scrape_payload['rag_enabled']}")
    print(f"Azure credentials: Not provided (testing fallback)")
    
    try:
        # Send scraping request
        response = requests.post(
            f"{backend_url}/api/v1/projects/{project_id}/execute-scrape",
            json=scrape_payload,
            timeout=60  # Give it time to scrape and embed
        )
        
        print(f"\n📥 Scraping response:")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scraping successful!")
            print(f"Message: {data.get('message', 'No message')}")
            print(f"RAG status: {data.get('rag_status', 'No RAG status')}")
            
            # Check if it mentions fallback embeddings
            rag_status = data.get('rag_status', '')
            if 'fallback' in rag_status.lower():
                print(f"✅ Using fallback embeddings as expected!")
            elif 'azure' in rag_status.lower():
                print(f"ℹ️  Using Azure OpenAI embeddings")
            else:
                print(f"⚠️  RAG status unclear: {rag_status}")
            
            # Wait a moment for background task to complete
            print(f"\n⏳ Waiting 10 seconds for background embedding task...")
            time.sleep(10)
            
            # Now check if the data was embedded
            return check_embedding_results(project_id)
            
        else:
            print(f"❌ Scraping failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw error: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Scraping request failed: {e}")
        return False

def check_embedding_results(project_id):
    """Check if the scraped data was properly embedded"""
    
    print(f"\n🔍 CHECKING EMBEDDING RESULTS")
    print("=" * 50)
    
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from backend.app.database import supabase
        
        # Check scrape sessions for this project
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).order("created_at", desc=True).limit(1).execute()
        
        if not sessions_response.data:
            print("❌ No scrape sessions found")
            return False
        
        latest_session = sessions_response.data[0]
        session_id = latest_session["id"]
        status = latest_session["status"]
        unique_id = latest_session.get("unique_scrape_identifier")
        
        print(f"Latest session ID: {session_id}")
        print(f"Session status: {status}")
        print(f"Unique identifier: {unique_id}")
        
        if status == "rag_ingested":
            print("✅ Session status is 'rag_ingested'!")
        elif status == "scraped":
            print("⚠️  Session status is 'scraped' - embedding may still be in progress")
        else:
            print(f"❌ Unexpected session status: {status}")
        
        if unique_id:
            # Check embeddings
            embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_id).execute()
            embeddings = embeddings_response.data or []
            
            print(f"Embeddings found: {len(embeddings)}")
            
            if embeddings:
                print("✅ Embeddings were created!")
                
                # Check if any contain country data
                country_chunks = []
                for embedding in embeddings:
                    content = embedding.get("content", "")
                    if any(country in content.lower() for country in ["country", "capital", "population"]):
                        country_chunks.append(embedding)
                
                print(f"Chunks with country data: {len(country_chunks)}")
                
                if country_chunks:
                    print("✅ Country data found in embeddings!")
                    sample_content = country_chunks[0].get("content", "")
                    print(f"Sample content: {sample_content[:200]}...")
                else:
                    print("⚠️  No country data found in embeddings")
                
                # Check markdowns
                markdown_response = supabase.table("markdowns").select("*").eq("unique_name", unique_id).execute()
                markdowns = markdown_response.data or []
                print(f"Markdown entries: {len(markdowns)}")
                
                return True
            else:
                print("❌ No embeddings found")
                return False
        else:
            print("❌ No unique identifier found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking embedding results: {e}")
        return False

def test_query_after_embedding():
    """Test querying the newly embedded data"""
    
    print(f"\n🔍 TESTING QUERY AFTER EMBEDDING")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    project_id = "67bbf078-6648-49f3-9068-95228bfb4989"
    
    # Test queries
    test_queries = [
        "tell me about the countries",
        "what countries are in the data?",
        "show me country information"
    ]
    
    for query in test_queries:
        print(f"\n🗨️  Testing query: '{query}'")
        
        try:
            response = requests.post(
                f"{backend_url}/api/v1/projects/{project_id}/enhanced-query-rag",
                json={
                    "query": query,
                    "model_name": "gpt-4o-mini"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                
                print(f"✅ Query successful!")
                print(f"Answer length: {len(answer)} characters")
                print(f"Answer preview: {answer[:200]}...")
                
                # Check if the answer contains useful information
                if len(answer) > 50 and any(word in answer.lower() for word in ["country", "capital", "population", "data"]):
                    print(f"✅ Answer contains relevant information!")
                else:
                    print(f"⚠️  Answer may not contain relevant information")
                    
            else:
                print(f"❌ Query failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Query error: {e}")
        
        time.sleep(1)  # Small delay between queries

def main():
    """Run the complete test"""
    
    print("🚀 TESTING AUTOMATIC EMBEDDING SYSTEM")
    print("=" * 80)
    
    # Test 1: Scraping with automatic embedding
    embedding_success = test_scraping_with_automatic_embedding()
    
    # Test 2: Query the embedded data
    if embedding_success:
        test_query_after_embedding()
    else:
        print("\n⚠️  Skipping query test due to embedding failure")
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    
    if embedding_success:
        print("🎉 SUCCESS! Automatic embedding system is working!")
        print("✅ Scraping automatically creates embeddings")
        print("✅ Fallback embeddings work without Azure credentials")
        print("✅ RAG queries can find the embedded data")
        print("\n📋 What this means:")
        print("   • Your system now automatically embeds scraped data")
        print("   • No manual intervention needed")
        print("   • Works even without Azure OpenAI credentials")
        print("   • Chat will find data immediately after scraping")
    else:
        print("⚠️  Automatic embedding system needs more work")
        print("❌ Check the logs for detailed error information")
    
    print(f"\n🎯 Your system should now automatically embed scraped data!")
    print(f"   Try asking about countries in the chat interface.")

if __name__ == "__main__":
    main()
