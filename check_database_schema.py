#!/usr/bin/env python3
"""
Check the actual database schema to understand available columns
"""

import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

async def check_database_schema():
    """Check the actual database schema."""
    print("🔍 Checking Database Schema\n")
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Check scrape_sessions table structure
    print("📋 Checking scrape_sessions table:")
    try:
        sessions_response = supabase.table("scrape_sessions").select("*").limit(1).execute()
        if sessions_response.data:
            session = sessions_response.data[0]
            print(f"   Available columns: {list(session.keys())}")
            print(f"   Sample data:")
            for key, value in session.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"     {key}: {value[:100]}...")
                else:
                    print(f"     {key}: {value}")
        else:
            print("   No sessions found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Check embeddings table structure
    print("🧠 Checking embeddings table:")
    try:
        embeddings_response = supabase.table("embeddings").select("*").limit(1).execute()
        if embeddings_response.data:
            embedding = embeddings_response.data[0]
            print(f"   Available columns: {list(embedding.keys())}")
            print(f"   Sample data:")
            for key, value in embedding.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"     {key}: {value[:100]}...")
                elif isinstance(value, list) and len(value) > 10:
                    print(f"     {key}: [list with {len(value)} items]")
                else:
                    print(f"     {key}: {value}")
        else:
            print("   No embeddings found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Check projects table structure
    print("📊 Checking projects table:")
    try:
        projects_response = supabase.table("projects").select("*").limit(1).execute()
        if projects_response.data:
            project = projects_response.data[0]
            print(f"   Available columns: {list(project.keys())}")
        else:
            print("   No projects found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Check if there are any other relevant tables
    print("🔍 Looking for data in existing project:")
    project_id = "67df8224-feba-4dd0-8648-abb9100cbb38"
    
    try:
        # Check all sessions for this project
        sessions_response = supabase.table("scrape_sessions").select("*").eq("project_id", project_id).execute()
        sessions = sessions_response.data or []
        
        print(f"📋 Found {len(sessions)} sessions for project {project_id}:")
        for session in sessions:
            print(f"   Session ID: {session.get('id')}")
            print(f"   Status: {session.get('status')}")
            print(f"   Available fields: {list(session.keys())}")
            
            # Look for any field that might contain scraped data
            for key, value in session.items():
                if key in ['data', 'content', 'scraped_data', 'results', 'output']:
                    if value:
                        print(f"   Found data in '{key}': {type(value)}")
                        if isinstance(value, str):
                            print(f"     Content preview: {value[:200]}...")
                        elif isinstance(value, dict):
                            print(f"     Dict keys: {list(value.keys())}")
                        elif isinstance(value, list):
                            print(f"     List length: {len(value)}")
            print()
            
    except Exception as e:
        print(f"❌ Error checking sessions: {e}")
    
    print("✅ Schema check complete!")

async def main():
    await check_database_schema()

if __name__ == "__main__":
    asyncio.run(main())
