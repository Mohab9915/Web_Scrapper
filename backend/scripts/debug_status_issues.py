#!/usr/bin/env python3
"""
Debug script to investigate URL status and RAG data issues.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import supabase

def debug_project_urls(project_id=None):
    """Debug project URLs and their statuses."""
    print("=== PROJECT URLS DEBUG ===")
    
    if project_id:
        print(f"Checking project {project_id}...")
        response = supabase.table("project_urls").select("*").eq("project_id", project_id).execute()
    else:
        print("Checking all projects...")
        response = supabase.table("project_urls").select("*").execute()
    
    if not response.data:
        print("No project URLs found.")
        return
    
    for url_data in response.data:
        print(f"\nURL: {url_data['url']}")
        print(f"  Project ID: {url_data['project_id']}")
        print(f"  Status: {url_data.get('status', 'NO STATUS')}")
        print(f"  Conditions: {url_data.get('conditions', 'NO CONDITIONS')}")
        print(f"  RAG Enabled: {url_data.get('rag_enabled', 'NO RAG SETTING')}")
        print(f"  Last Session ID: {url_data.get('last_scraped_session_id', 'NO SESSION')}")

def debug_scrape_sessions(project_id=None):
    """Debug scrape sessions and their statuses."""
    print("\n=== SCRAPE SESSIONS DEBUG ===")
    
    if project_id:
        print(f"Checking sessions for project {project_id}...")
        response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
    else:
        print("Checking all sessions...")
        response = supabase.table("scrape_sessions").select("*").execute()
    
    if not response.data:
        print("No scrape sessions found.")
        return
    
    status_counts = {}
    for session in response.data:
        status = session.get('status', 'NO STATUS')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\nSession: {session['id']}")
        print(f"  Project ID: {session['project_id']}")
        print(f"  URL: {session['url']}")
        print(f"  Status: {status}")
        print(f"  Scraped At: {session.get('scraped_at', 'NO TIMESTAMP')}")
        print(f"  Unique Identifier: {session.get('unique_scrape_identifier', 'NO IDENTIFIER')}")
        print(f"  Has Raw Markdown: {'Yes' if session.get('raw_markdown') else 'No'}")
        print(f"  Has Structured Data: {'Yes' if session.get('structured_data_json') else 'No'}")
    
    print(f"\nStatus Summary:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")

def debug_rag_data(project_id=None):
    """Debug RAG-related data (markdowns and embeddings)."""
    print("\n=== RAG DATA DEBUG ===")
    
    # Check markdowns table
    print("Checking markdowns table...")
    markdowns_response = supabase.table("markdowns").select("unique_name, url").execute()
    print(f"Found {len(markdowns_response.data)} markdown entries")
    
    # Check embeddings table
    print("Checking embeddings table...")
    embeddings_response = supabase.table("embeddings").select("unique_name").execute()
    unique_names_with_embeddings = set(e['unique_name'] for e in embeddings_response.data)
    print(f"Found embeddings for {len(unique_names_with_embeddings)} unique names")
    
    # Cross-reference with sessions
    if project_id:
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier, status, url").eq("project_id", project_id).execute()
        print(f"\nFor project {project_id}:")
        for session in sessions_response.data:
            unique_id = session.get('unique_scrape_identifier')
            if unique_id:
                has_markdown = any(m['unique_name'] == unique_id for m in markdowns_response.data)
                has_embeddings = unique_id in unique_names_with_embeddings
                print(f"  {session['url']}: status={session['status']}, markdown={has_markdown}, embeddings={has_embeddings}")
            else:
                print(f"  {session['url']}: NO UNIQUE IDENTIFIER")

def debug_projects():
    """Debug projects and their RAG settings."""
    print("\n=== PROJECTS DEBUG ===")
    
    response = supabase.table("projects").select("*").execute()
    
    if not response.data:
        print("No projects found.")
        return
    
    for project in response.data:
        print(f"\nProject: {project['name']} ({project['id']})")
        print(f"  RAG Enabled: {project.get('rag_enabled', 'NO RAG SETTING')}")
        print(f"  Created At: {project.get('created_at', 'NO TIMESTAMP')}")

def main():
    """Main debug function."""
    print("Starting debug analysis...")
    
    # Get all projects first
    projects_response = supabase.table("projects").select("id, name").execute()
    
    if not projects_response.data:
        print("No projects found in database.")
        return
    
    print(f"Found {len(projects_response.data)} projects:")
    for i, project in enumerate(projects_response.data):
        print(f"  {i+1}. {project['name']} ({project['id']})")
    
    # Debug all projects
    debug_projects()
    
    # Debug each project individually
    for project in projects_response.data:
        project_id = project['id']
        print(f"\n{'='*60}")
        print(f"DEBUGGING PROJECT: {project['name']} ({project_id})")
        print(f"{'='*60}")
        
        debug_project_urls(project_id)
        debug_scrape_sessions(project_id)
        debug_rag_data(project_id)

if __name__ == "__main__":
    main()
