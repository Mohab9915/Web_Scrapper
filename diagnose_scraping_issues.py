#!/usr/bin/env python3
"""
Diagnose scraping and RAG system issues by examining the database directly.
"""
import json
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import get_supabase_client

def main():
    """Main diagnosis function"""
    print("🔍 SCRAPING AND RAG SYSTEM DIAGNOSIS")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Get recent projects
    print("\n📋 RECENT PROJECTS:")
    projects_response = supabase.table("projects").select("*").order("created_at", desc=True).limit(5).execute()
    
    for project in projects_response.data:
        print(f"\n  Project: {project['name']} (ID: {project['id']})")
        print(f"  RAG Enabled: {project['rag_enabled']}")
        print(f"  Created: {project['created_at']}")
        
        # Get URLs for this project
        urls_response = supabase.table("project_urls").select("*").eq("project_id", project['id']).execute()
        print(f"  URLs: {len(urls_response.data)}")
        
        for url in urls_response.data:
            print(f"    - {url['url']} (Status: {url.get('status', 'unknown')})")
        
        # Get scrape sessions for this project
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project['id']).order("scraped_at", desc=True).execute()
        print(f"  Scrape Sessions: {len(sessions_response.data)}")
        
        for session in sessions_response.data:
            print(f"\n    Session ID: {session['id']}")
            print(f"    URL: {session['url']}")
            print(f"    Status: {session['status']}")
            print(f"    Scraped At: {session['scraped_at']}")
            
            # Check structured data
            structured_data = session.get('structured_data_json')
            if structured_data:
                try:
                    if isinstance(structured_data, str):
                        data = json.loads(structured_data)
                    else:
                        data = structured_data
                    
                    print(f"    Structured Data Keys: {list(data.keys())}")
                    
                    # Check for tabular data
                    tabular_data = data.get('tabular_data', [])
                    listings = data.get('listings', [])
                    
                    if tabular_data:
                        print(f"    Tabular Data Items: {len(tabular_data)}")
                        if tabular_data:
                            print(f"    Sample Item Keys: {list(tabular_data[0].keys())}")
                            print(f"    Sample Item: {tabular_data[0]}")
                    
                    if listings:
                        print(f"    Listings Items: {len(listings)}")
                        if listings:
                            print(f"    Sample Listing Keys: {list(listings[0].keys())}")
                            print(f"    Sample Listing: {listings[0]}")
                    
                    if not tabular_data and not listings:
                        print(f"    ⚠️  No tabular data or listings found!")
                        print(f"    Raw structured data: {json.dumps(data, indent=2)[:500]}...")
                        
                except Exception as e:
                    print(f"    ❌ Error parsing structured data: {e}")
                    print(f"    Raw data type: {type(structured_data)}")
                    print(f"    Raw data preview: {str(structured_data)[:200]}...")
            else:
                print(f"    ❌ No structured data found!")
            
            # Check RAG ingestion
            if session['status'] == 'rag_ingested':
                # Check embeddings
                embeddings_response = supabase.table("embeddings").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
                embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
                print(f"    Embeddings Count: {embeddings_count}")
                
                # Check markdowns
                markdowns_response = supabase.table("markdowns").select("*").eq("unique_name", session['unique_scrape_identifier']).execute()
                markdowns_count = len(markdowns_response.data) if markdowns_response.data else 0
                print(f"    Markdowns Count: {markdowns_count}")
            
            print("    " + "-" * 40)
    
    print("\n🔍 CHECKING FOR COMMON ISSUES:")
    
    # Check for sessions with status issues
    print("\n1. Sessions with status inconsistencies:")
    all_sessions = supabase.table("scrape_sessions").select("*").execute()
    
    for session in all_sessions.data:
        issues = []
        
        # Check if rag_ingested but no embeddings
        if session['status'] == 'rag_ingested':
            embeddings_response = supabase.table("embeddings").select("count").eq("unique_name", session['unique_scrape_identifier']).execute()
            embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
            if embeddings_count == 0:
                issues.append("Status is 'rag_ingested' but no embeddings found")
        
        # Check if structured data is missing or malformed
        if not session.get('structured_data_json'):
            issues.append("No structured data")
        else:
            try:
                data = json.loads(session['structured_data_json']) if isinstance(session['structured_data_json'], str) else session['structured_data_json']
                if not data.get('tabular_data') and not data.get('listings'):
                    issues.append("Structured data exists but no tabular_data or listings")
            except:
                issues.append("Structured data is malformed")
        
        if issues:
            print(f"  Session {session['id'][:8]}... ({session['url'][:50]}...): {', '.join(issues)}")
    
    print("\n2. RAG system status:")
    
    # Check projects with RAG enabled but no rag_ingested sessions
    rag_projects = supabase.table("projects").select("*").eq("rag_enabled", True).execute()
    
    for project in rag_projects.data:
        rag_sessions = supabase.table("scrape_sessions").select("count").eq("project_id", project['id']).eq("status", "rag_ingested").execute()
        rag_count = len(rag_sessions.data) if rag_sessions.data else 0
        
        scraped_sessions = supabase.table("scrape_sessions").select("count").eq("project_id", project['id']).eq("status", "scraped").execute()
        scraped_count = len(scraped_sessions.data) if scraped_sessions.data else 0
        
        if rag_count == 0 and scraped_count > 0:
            print(f"  Project '{project['name']}' has RAG enabled but {scraped_count} scraped sessions are not RAG-ingested")
    
    print("\n✅ Diagnosis complete!")

if __name__ == "__main__":
    main()
