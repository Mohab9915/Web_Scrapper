#!/usr/bin/env python3
"""
Script to check and fix database schema issues.
"""
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import supabase

def check_table_structure():
    """Check the structure of both tables."""
    print("=== CHECKING TABLE STRUCTURES ===")
    
    # Check project_urls table
    print("\n--- PROJECT_URLS TABLE ---")
    try:
        response = supabase.table("project_urls").select("*").limit(1).execute()
        if response.data:
            print("Available fields:")
            for key in response.data[0].keys():
                print(f"  - {key}")
        else:
            print("No data in project_urls table")
    except Exception as e:
        print(f"Error checking project_urls: {e}")
    
    # Check scrape_sessions table
    print("\n--- SCRAPE_SESSIONS TABLE ---")
    try:
        response = supabase.table("scrape_sessions").select("*").limit(1).execute()
        if response.data:
            print("Available fields:")
            for key in response.data[0].keys():
                print(f"  - {key}")
        else:
            print("No data in scrape_sessions table")
    except Exception as e:
        print(f"Error checking scrape_sessions: {e}")

def check_missing_scraped_at():
    """Check if scraped_at field exists and add it if missing."""
    print("\n=== CHECKING SCRAPED_AT FIELD ===")
    
    try:
        # Try to select scraped_at field
        response = supabase.table("scrape_sessions").select("scraped_at").limit(1).execute()
        print("scraped_at field exists")
        return True
    except Exception as e:
        print(f"scraped_at field missing or error: {e}")
        
        # Check if created_at exists instead
        try:
            response = supabase.table("scrape_sessions").select("created_at").limit(1).execute()
            print("created_at field exists - we can use this as scraped_at")
            return False
        except Exception as e2:
            print(f"Neither scraped_at nor created_at exists: {e2}")
            return False

def fix_scraped_at_field():
    """Add scraped_at field or update existing records."""
    print("\n=== FIXING SCRAPED_AT FIELD ===")
    
    # First, let's see what timestamp fields exist
    try:
        response = supabase.table("scrape_sessions").select("*").limit(1).execute()
        if response.data:
            session = response.data[0]
            timestamp_fields = [k for k in session.keys() if 'at' in k.lower() or 'time' in k.lower() or 'date' in k.lower()]
            print(f"Available timestamp fields: {timestamp_fields}")
            
            # If created_at exists but scraped_at doesn't, we need to add scraped_at
            if 'created_at' in session and 'scraped_at' not in session:
                print("Need to add scraped_at column to scrape_sessions table")
                print("This requires a database migration. Let me create the SQL for you:")
                
                sql = """
-- Add scraped_at column to scrape_sessions table
ALTER TABLE scrape_sessions 
ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMPTZ DEFAULT NOW();

-- Update existing records to use created_at as scraped_at
UPDATE scrape_sessions 
SET scraped_at = created_at 
WHERE scraped_at IS NULL AND created_at IS NOT NULL;
"""
                print("SQL to run:")
                print(sql)
                return sql
                
    except Exception as e:
        print(f"Error checking fields: {e}")
        return None

def test_session_retrieval():
    """Test if we can retrieve session data properly."""
    print("\n=== TESTING SESSION RETRIEVAL ===")
    
    # Get a project with URLs
    projects_response = supabase.table("projects").select("id, name").execute()
    if not projects_response.data:
        print("No projects found")
        return
    
    project_id = projects_response.data[0]["id"]
    print(f"Testing with project: {projects_response.data[0]['name']} ({project_id})")
    
    # Get project URLs
    urls_response = supabase.table("project_urls").select("*").eq("project_id", project_id).execute()
    if not urls_response.data:
        print("No URLs found for this project")
        return
    
    for url_data in urls_response.data:
        print(f"\nURL: {url_data['url']}")
        print(f"  Status: {url_data.get('status', 'NO STATUS')}")
        print(f"  Last Session ID: {url_data.get('last_scraped_session_id', 'NO SESSION')}")
        
        if url_data.get('last_scraped_session_id'):
            # Try to get the session
            try:
                session_response = supabase.table("scrape_sessions").select("*").eq("id", url_data['last_scraped_session_id']).single().execute()
                if session_response.data:
                    session = session_response.data
                    print(f"  ✓ Session found: {session['id']}")
                    print(f"    Status: {session.get('status', 'NO STATUS')}")
                    print(f"    Has raw_markdown: {'Yes' if session.get('raw_markdown') else 'No'}")
                    print(f"    Has structured_data_json: {'Yes' if session.get('structured_data_json') else 'No'}")
                    print(f"    Created at: {session.get('created_at', 'NO TIMESTAMP')}")
                    print(f"    Scraped at: {session.get('scraped_at', 'NO TIMESTAMP')}")
                else:
                    print(f"  ✗ Session not found")
            except Exception as e:
                print(f"  ✗ Error retrieving session: {e}")

def main():
    """Main function."""
    print("Checking and fixing database schema issues...")
    
    check_table_structure()
    
    scraped_at_exists = check_missing_scraped_at()
    
    if not scraped_at_exists:
        sql = fix_scraped_at_field()
        if sql:
            print("\n" + "="*60)
            print("MANUAL ACTION REQUIRED:")
            print("Please run the following SQL in your Supabase SQL editor:")
            print("="*60)
            print(sql)
            print("="*60)
    
    test_session_retrieval()
    
    print("\nDatabase check completed!")

if __name__ == "__main__":
    main()
