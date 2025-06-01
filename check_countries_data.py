#!/usr/bin/env python3
"""
Check what data is stored for the countries project and test search functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import supabase

def check_countries_project_data():
    """Check what data is stored for the countries project"""
    
    project_id = "67bbf078-6648-49f3-9068-95228bfb4989"
    
    print("🔍 CHECKING COUNTRIES PROJECT DATA")
    print("=" * 60)
    print(f"Project ID: {project_id}")
    print()
    
    # 1. Check project details
    print("📊 Project Details:")
    try:
        project_response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        if project_response.data:
            project = project_response.data
            print(f"   Name: {project.get('name', 'Unknown')}")
            print(f"   RAG Enabled: {project.get('rag_enabled', False)}")
            print(f"   Created: {project.get('created_at', 'Unknown')}")
        else:
            print("   ❌ Project not found")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    print()
    
    # 2. Check scrape sessions
    print("🕷️  Scrape Sessions:")
    try:
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        print(f"   Found {len(sessions)} sessions")
        
        for i, session in enumerate(sessions, 1):
            print(f"\n   Session {i}:")
            print(f"     ID: {session.get('id')}")
            print(f"     URL: {session.get('url')}")
            print(f"     Status: {session.get('status')}")
            print(f"     Unique ID: {session.get('unique_scrape_identifier')}")
            print(f"     Created: {session.get('scraped_at')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 3. Check markdown content
    print("📝 Markdown Content:")
    try:
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        for session in sessions:
            unique_id = session.get('unique_scrape_identifier')
            if unique_id:
                markdown_response = supabase.table("markdowns").select("*").eq("unique_name", unique_id).execute()
                markdowns = markdown_response.data or []
                
                print(f"\n   Unique ID: {unique_id}")
                print(f"   Markdown entries: {len(markdowns)}")
                
                for markdown in markdowns:
                    content = markdown.get('content', '')
                    print(f"     URL: {markdown.get('url')}")
                    print(f"     Content length: {len(content)} characters")
                    
                    # Check if content contains country information
                    if content:
                        content_lower = content.lower()
                        countries = ['russia', 'china', 'usa', 'india', 'brazil', 'canada', 'australia']
                        found_countries = [country for country in countries if country in content_lower]
                        
                        if found_countries:
                            print(f"     Contains countries: {', '.join(found_countries)}")
                            
                            # Show a sample of content containing Russia
                            if 'russia' in content_lower:
                                russia_index = content_lower.find('russia')
                                start = max(0, russia_index - 100)
                                end = min(len(content), russia_index + 200)
                                sample = content[start:end]
                                print(f"     Russia sample: ...{sample}...")
                        else:
                            print(f"     No common countries found")
                            print(f"     Content preview: {content[:200]}...")
                    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 4. Check embeddings
    print("🧠 Embeddings:")
    try:
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        total_embeddings = 0
        
        for session in sessions:
            unique_id = session.get('unique_scrape_identifier')
            if unique_id:
                embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_id).execute()
                embeddings = embeddings_response.data or []
                
                print(f"\n   Unique ID: {unique_id}")
                print(f"   Embedding chunks: {len(embeddings)}")
                total_embeddings += len(embeddings)
                
                # Check content of embeddings for countries
                for i, embedding in enumerate(embeddings[:3]):  # Show first 3
                    content = embedding.get('content', '')
                    print(f"     Chunk {i+1}: {len(content)} chars")
                    
                    if content:
                        content_lower = content.lower()
                        if 'russia' in content_lower:
                            print(f"       ✅ Contains 'Russia'")
                            # Show context around Russia
                            russia_index = content_lower.find('russia')
                            start = max(0, russia_index - 50)
                            end = min(len(content), russia_index + 100)
                            sample = content[start:end]
                            print(f"       Context: ...{sample}...")
                        else:
                            print(f"       Preview: {content[:100]}...")
        
        print(f"\n   Total embeddings: {total_embeddings}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 5. Test keyword search manually
    print("🔍 Manual Keyword Search Test:")
    try:
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        search_terms = ['russia', 'Russian', 'area', 'population', 'country']
        
        for term in search_terms:
            print(f"\n   Searching for '{term}':")
            found_chunks = []
            
            for session in sessions:
                unique_id = session.get('unique_scrape_identifier')
                if unique_id:
                    # Search in embeddings
                    embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_id).execute()
                    embeddings = embeddings_response.data or []
                    
                    for embedding in embeddings:
                        content = embedding.get('content', '')
                        if term.lower() in content.lower():
                            found_chunks.append({
                                'unique_id': unique_id,
                                'chunk_id': embedding.get('chunk_id'),
                                'content': content
                            })
            
            print(f"     Found in {len(found_chunks)} chunks")
            
            # Show first match
            if found_chunks:
                first_match = found_chunks[0]
                content = first_match['content']
                term_index = content.lower().find(term.lower())
                start = max(0, term_index - 50)
                end = min(len(content), term_index + 100)
                sample = content[start:end]
                print(f"     Sample: ...{sample}...")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_simple_keyword_search():
    """Test a simple keyword search without embeddings"""
    
    print("\n" + "=" * 60)
    print("🧪 TESTING SIMPLE KEYWORD SEARCH")
    print("=" * 60)
    
    project_id = "67bbf078-6648-49f3-9068-95228bfb4989"
    query = "Russia"
    
    try:
        # Get sessions for this project
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        print(f"Query: '{query}'")
        print(f"Sessions to search: {len(sessions)}")
        
        # Search through all chunks
        matching_chunks = []
        
        for session in sessions:
            unique_id = session.get('unique_scrape_identifier')
            if unique_id:
                # Get all chunks for this session
                embeddings_response = supabase.table("embeddings").select("*").eq("unique_name", unique_id).execute()
                embeddings = embeddings_response.data or []
                
                for embedding in embeddings:
                    content = embedding.get('content', '')
                    if query.lower() in content.lower():
                        # Calculate a simple relevance score
                        score = content.lower().count(query.lower())
                        matching_chunks.append({
                            'content': content,
                            'score': score,
                            'unique_id': unique_id,
                            'chunk_id': embedding.get('chunk_id')
                        })
        
        # Sort by relevance
        matching_chunks.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\nFound {len(matching_chunks)} matching chunks")
        
        # Show top 3 matches
        for i, chunk in enumerate(matching_chunks[:3], 1):
            print(f"\nMatch {i} (score: {chunk['score']}):")
            content = chunk['content']
            
            # Find the query term and show context
            query_index = content.lower().find(query.lower())
            start = max(0, query_index - 100)
            end = min(len(content), query_index + 200)
            sample = content[start:end]
            
            print(f"  Context: ...{sample}...")
            print(f"  Chunk ID: {chunk['chunk_id']}")
        
        if matching_chunks:
            print(f"\n✅ SUCCESS: Found data about '{query}' in the scraped content!")
            print("The issue is likely in the RAG query processing, not the data storage.")
        else:
            print(f"\n❌ No data found about '{query}' in the scraped content.")
            print("The data might not contain information about this country.")
        
    except Exception as e:
        print(f"❌ Error in keyword search: {e}")

if __name__ == "__main__":
    check_countries_project_data()
    test_simple_keyword_search()
