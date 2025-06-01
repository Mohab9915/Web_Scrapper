#!/usr/bin/env python3
"""
Check if there's raw data stored and manually trigger RAG ingestion
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import supabase

def check_raw_data():
    """Check if there's raw data stored for the countries project"""
    
    project_id = "67bbf078-6648-49f3-9068-95228bfb4989"
    
    print("🔍 CHECKING RAW DATA STORAGE")
    print("=" * 60)
    
    # 1. Check scrape_sessions for raw_markdown
    print("📝 Checking scrape_sessions for raw_markdown:")
    try:
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        for session in sessions:
            session_id = session.get('id')
            raw_markdown = session.get('raw_markdown', '')
            structured_data = session.get('structured_data', '')
            
            print(f"\n   Session ID: {session_id}")
            print(f"   Raw markdown length: {len(raw_markdown)} characters")
            print(f"   Structured data length: {len(structured_data)} characters")
            
            if raw_markdown:
                print(f"   Raw markdown preview: {raw_markdown[:200]}...")
                
                # Check if it contains country data
                if 'russia' in raw_markdown.lower():
                    print("   ✅ Contains 'Russia' in raw markdown!")
                else:
                    print("   ❌ No 'Russia' found in raw markdown")
                    
            if structured_data:
                print(f"   Structured data preview: {structured_data[:200]}...")
                
                # Check if it contains country data
                if 'russia' in structured_data.lower():
                    print("   ✅ Contains 'Russia' in structured data!")
                else:
                    print("   ❌ No 'Russia' found in structured data")
                    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 2. Check raw_data table (if it exists)
    print("🗃️  Checking raw_data table:")
    try:
        # Get unique_scrape_identifier from sessions
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        for session in sessions:
            unique_id = session.get('unique_scrape_identifier')
            if unique_id:
                print(f"\n   Checking unique_id: {unique_id}")
                
                # Try to find raw data
                raw_data_response = supabase.table("raw_data").select("*").eq("unique_name", unique_id).execute()
                raw_data_entries = raw_data_response.data or []
                
                print(f"   Raw data entries: {len(raw_data_entries)}")
                
                for entry in raw_data_entries:
                    raw_data = entry.get('raw_data', '')
                    url = entry.get('url', '')
                    
                    print(f"     URL: {url}")
                    print(f"     Raw data length: {len(raw_data)} characters")
                    
                    if raw_data:
                        print(f"     Preview: {raw_data[:200]}...")
                        
                        # Check for country data
                        if 'russia' in raw_data.lower():
                            print("     ✅ Contains 'Russia'!")
                        else:
                            print("     ❌ No 'Russia' found")
                            
    except Exception as e:
        print(f"   ❌ Error checking raw_data table: {e}")
    
    print()
    
    # 3. Check formatted_data table
    print("📊 Checking formatted_data table:")
    try:
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        for session in sessions:
            unique_id = session.get('unique_scrape_identifier')
            if unique_id:
                print(f"\n   Checking unique_id: {unique_id}")
                
                formatted_data_response = supabase.table("formatted_data").select("*").eq("unique_name", unique_id).execute()
                formatted_entries = formatted_data_response.data or []
                
                print(f"   Formatted data entries: {len(formatted_entries)}")
                
                for entry in formatted_entries:
                    formatted_data = entry.get('formatted_data', '')
                    
                    print(f"     Formatted data length: {len(formatted_data)} characters")
                    
                    if formatted_data:
                        print(f"     Preview: {formatted_data[:300]}...")
                        
                        # Check for country data
                        if 'russia' in formatted_data.lower():
                            print("     ✅ Contains 'Russia'!")
                            
                            # Try to parse as JSON to see structure
                            try:
                                import json
                                data = json.loads(formatted_data)
                                if isinstance(data, dict) and 'listings' in data:
                                    listings = data['listings']
                                    print(f"     📋 Found {len(listings)} listings")
                                    
                                    # Look for Russia specifically
                                    russia_entries = [item for item in listings if 'russia' in str(item).lower()]
                                    if russia_entries:
                                        print(f"     🇷🇺 Found {len(russia_entries)} Russia entries:")
                                        for entry in russia_entries[:2]:  # Show first 2
                                            print(f"       {entry}")
                                else:
                                    print(f"     📋 Data structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                            except json.JSONDecodeError:
                                print("     ⚠️  Not valid JSON format")
                        else:
                            print("     ❌ No 'Russia' found")
                            
    except Exception as e:
        print(f"   ❌ Error checking formatted_data table: {e}")

def trigger_rag_ingestion():
    """Manually trigger RAG ingestion for the countries project"""
    
    print("\n" + "=" * 60)
    print("🚀 TRIGGERING RAG INGESTION")
    print("=" * 60)
    
    project_id = "67bbf078-6648-49f3-9068-95228bfb4989"
    
    try:
        # Get sessions that need RAG ingestion
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).eq("status", "scraped").execute()
        sessions = sessions_response.data or []
        
        print(f"Found {len(sessions)} sessions needing RAG ingestion")
        
        for session in sessions:
            session_id = session.get('id')
            unique_id = session.get('unique_scrape_identifier')
            raw_markdown = session.get('raw_markdown', '')
            structured_data = session.get('structured_data', '')
            
            print(f"\nProcessing session: {session_id}")
            print(f"Unique ID: {unique_id}")
            
            # Check if we have data to process
            if not raw_markdown and not structured_data:
                print("   ❌ No raw_markdown or structured_data found")
                continue
            
            # Use the data we have
            content_to_process = structured_data if structured_data else raw_markdown
            
            print(f"   📝 Content length: {len(content_to_process)} characters")
            
            # Store in markdowns table
            try:
                # Check if already exists
                existing_markdown = supabase.table("markdowns").select("*").eq("unique_name", unique_id).execute()
                
                if not existing_markdown.data:
                    # Insert new markdown entry
                    supabase.table("markdowns").insert({
                        "unique_name": unique_id,
                        "markdown": content_to_process,
                        "url": session.get('url', ''),
                        "content": content_to_process  # Also store in content field if it exists
                    }).execute()
                    print("   ✅ Stored in markdowns table")
                else:
                    print("   ℹ️  Already exists in markdowns table")
                    
            except Exception as e:
                print(f"   ❌ Error storing markdown: {e}")
            
            # Create simple embeddings (without Azure OpenAI for now)
            try:
                # Check if embeddings already exist
                existing_embeddings = supabase.table("embeddings").select("*").eq("unique_name", unique_id).execute()
                
                if not existing_embeddings.data:
                    # Create simple chunks
                    chunks = []
                    chunk_size = 1000
                    
                    for i in range(0, len(content_to_process), chunk_size):
                        chunk = content_to_process[i:i + chunk_size]
                        if chunk.strip():
                            chunks.append(chunk)
                    
                    print(f"   📊 Created {len(chunks)} chunks")
                    
                    # Store chunks with dummy embeddings
                    for i, chunk in enumerate(chunks):
                        # Create a simple hash-based "embedding" for testing
                        import hashlib
                        hash_obj = hashlib.md5(chunk.encode())
                        # Convert hash to a list of floats (dummy embedding)
                        dummy_embedding = [float(int(hash_obj.hexdigest()[j:j+2], 16)) / 255.0 for j in range(0, 32, 2)]
                        # Pad to 1536 dimensions
                        while len(dummy_embedding) < 1536:
                            dummy_embedding.extend(dummy_embedding[:min(16, 1536 - len(dummy_embedding))])
                        dummy_embedding = dummy_embedding[:1536]
                        
                        supabase.table("embeddings").insert({
                            "unique_name": unique_id,
                            "chunk_id": i,
                            "content": chunk,
                            "embedding": dummy_embedding
                        }).execute()
                    
                    print("   ✅ Created embeddings with dummy vectors")
                else:
                    print("   ℹ️  Embeddings already exist")
                    
            except Exception as e:
                print(f"   ❌ Error creating embeddings: {e}")
            
            # Update session status
            try:
                supabase.table("scrape_sessions").update({
                    "status": "rag_ingested"
                }).eq("id", session_id).execute()
                print("   ✅ Updated session status to 'rag_ingested'")
            except Exception as e:
                print(f"   ❌ Error updating session status: {e}")
        
        print(f"\n🎉 RAG ingestion completed for {len(sessions)} sessions!")
        
    except Exception as e:
        print(f"❌ Error in RAG ingestion: {e}")

if __name__ == "__main__":
    check_raw_data()
    trigger_rag_ingestion()
