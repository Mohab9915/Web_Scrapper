#!/usr/bin/env python3
"""
Check markdown data in the database to understand why RAG ingestion is failing.
"""
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import get_supabase_client

def main():
    """Check markdown data"""
    print("🔍 CHECKING MARKDOWN DATA")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Get the test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if not project_response.data:
        print("❌ No 'test1' project found")
        return
    
    project = project_response.data[0]
    project_id = project['id']
    
    print(f"📋 Project: {project['name']} (ID: {project_id})")
    print(f"RAG Enabled: {project['rag_enabled']}")
    
    # Get scrape sessions
    sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
    
    print(f"\n📊 Found {len(sessions_response.data)} scrape sessions")
    
    for session in sessions_response.data:
        print(f"\n🔍 Session: {session['id']}")
        print(f"   URL: {session['url']}")
        print(f"   Status: {session['status']}")
        print(f"   Unique ID: {session['unique_scrape_identifier']}")
        print(f"   Scraped At: {session['scraped_at']}")
        
        # Check raw markdown
        raw_markdown = session.get('raw_markdown')
        if raw_markdown:
            print(f"   Raw Markdown: {len(raw_markdown)} characters")
            print(f"   Preview: {raw_markdown[:200]}...")
        else:
            print("   ❌ No raw markdown found")
        
        # Check structured data
        structured_data = session.get('structured_data_json')
        if structured_data:
            try:
                if isinstance(structured_data, str):
                    data = json.loads(structured_data)
                else:
                    data = structured_data
                
                print(f"   Structured Data Keys: {list(data.keys())}")
                
                # Check for tabular data
                tabular_data = data.get('tabular_data', [])
                listings = data.get('listings', [])
                
                if tabular_data:
                    print(f"   Tabular Data: {len(tabular_data)} items")
                    if tabular_data:
                        print(f"   Sample Item: {tabular_data[0]}")
                
                if listings:
                    print(f"   Listings: {len(listings)} items")
                    if listings:
                        print(f"   Sample Listing: {listings[0]}")
                        
            except Exception as e:
                print(f"   ❌ Error parsing structured data: {e}")
        else:
            print("   ❌ No structured data found")
        
        # Check if markdown exists in markdowns table
        markdown_response = supabase.table("markdowns").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
        
        if markdown_response.data:
            markdown_entry = markdown_response.data[0]
            print(f"   ✅ Markdown entry exists in markdowns table")
            print(f"   Markdown length: {len(markdown_entry['markdown'])} characters")
            print(f"   Markdown preview: {markdown_entry['markdown'][:200]}...")
        else:
            print("   ❌ No markdown entry in markdowns table")
        
        # Check embeddings
        embeddings_response = supabase.table("embeddings").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
        embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
        print(f"   Embeddings: {embeddings_count} chunks")
        
        print("   " + "-" * 50)
    
    # Check if we can manually create markdown content from structured data
    print("\n🔧 ATTEMPTING TO CREATE MARKDOWN FROM STRUCTURED DATA")
    
    for session in sessions_response.data:
        if session.get('structured_data_json') and not session.get('raw_markdown'):
            print(f"\n📝 Creating markdown for session {session['id'][:8]}...")
            
            try:
                if isinstance(session['structured_data_json'], str):
                    data = json.loads(session['structured_data_json'])
                else:
                    data = session['structured_data_json']
                
                # Convert structured data to markdown
                markdown_content = ""
                
                if 'tabular_data' in data and data['tabular_data']:
                    markdown_content += "# Countries Data\n\n"
                    
                    for i, item in enumerate(data['tabular_data']):
                        markdown_content += f"## Country {i+1}\n\n"
                        for key, value in item.items():
                            markdown_content += f"**{key.title()}:** {value}\n\n"
                        markdown_content += "---\n\n"
                
                elif 'listings' in data and data['listings']:
                    markdown_content += "# Listings Data\n\n"
                    
                    for i, item in enumerate(data['listings']):
                        markdown_content += f"## Item {i+1}\n\n"
                        for key, value in item.items():
                            markdown_content += f"**{key.title()}:** {value}\n\n"
                        markdown_content += "---\n\n"
                
                if markdown_content:
                    print(f"   ✅ Generated {len(markdown_content)} characters of markdown")
                    print(f"   Preview: {markdown_content[:300]}...")
                    
                    # Save to markdowns table
                    try:
                        supabase.table("markdowns").upsert({
                            "unique_name": session['unique_scrape_identifier'],
                            "url": session['url'],
                            "markdown": markdown_content
                        }, on_conflict="unique_name").execute()
                        
                        print("   ✅ Saved markdown to database")
                        
                    except Exception as e:
                        print(f"   ❌ Error saving markdown: {e}")
                else:
                    print("   ❌ Could not generate markdown from structured data")
                    
            except Exception as e:
                print(f"   ❌ Error processing structured data: {e}")

if __name__ == "__main__":
    main()
