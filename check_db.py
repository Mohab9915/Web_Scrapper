import os
import sys
import json
from supabase import create_client, Client

# Supabase credentials
url = "https://xyzcompany.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh5emNvbXBhbnkiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYyMDY2Mjk0Niwic3ViIjoiYW5vbiIsImV4cCI6MTkzNjIzODk0Nn0.xyz"

# Initialize Supabase client
supabase: Client = create_client(url, key)

try:
    # Check if scrape_sessions table exists
    print("Checking for scrape_sessions table...")
    sessions = supabase.table('scrape_sessions').select('*').execute()
    print(f"Number of scraping sessions: {len(sessions.data)}")
    
    if sessions.data:
        print("\nScraping Sessions:")
        for i, session in enumerate(sessions.data, 1):
            print(f"\nSession {i}:")
            print(f"  ID: {session.get('id')}")
            print(f"  Project ID: {session.get('project_id')}")
            print(f"  URL: {session.get('url')}")
            print(f"  Status: {session.get('status')}")
    else:
        print("\nNo scraping sessions found in the database.")
    
    # Check if web_cache table exists
    print("\nChecking for web_cache table...")
    cache = supabase.table('web_cache').select('*').execute()
    print(f"Number of cached web pages: {len(cache.data)}")
    
    if cache.data:
        print("\nCached Web Pages:")
        for i, entry in enumerate(cache.data, 1):
            print(f"\nCache Entry {i}:")
            print(f"  URL: {entry.get('url')}")
            print(f"  Created at: {entry.get('created_at')}")
            print(f"  Expires at: {entry.get('expires_at')}")
    else:
        print("\nNo cached web pages found in the database.")
    
    # Check if projects table exists
    print("\nChecking for projects table...")
    projects = supabase.table('projects').select('*').execute()
    print(f"Number of projects: {len(projects.data)}")
    
    if projects.data:
        print("\nProjects:")
        for i, project in enumerate(projects.data, 1):
            print(f"\nProject {i}:")
            print(f"  ID: {project.get('id')}")
            print(f"  Name: {project.get('name')}")
            print(f"  RAG Enabled: {project.get('rag_enabled')}")
            print(f"  Caching Enabled: {project.get('caching_enabled')}")
    else:
        print("\nNo projects found in the database.")

except Exception as e:
    print(f"Error: {e}")
