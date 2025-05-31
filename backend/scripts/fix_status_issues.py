#!/usr/bin/env python3
"""
Script to fix status issues in the database.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import supabase

def fix_missing_status_columns():
    """Fix any missing status values in project_urls table."""
    print("=== FIXING MISSING STATUS VALUES ===")
    
    # Get all project URLs
    response = supabase.table("project_urls").select("*").execute()
    
    if not response.data:
        print("No project URLs found.")
        return
    
    fixed_count = 0
    for url_data in response.data:
        if not url_data.get('status'):
            print(f"Fixing missing status for URL: {url_data['url']}")
            
            # Check if there are any completed scrape sessions for this URL
            sessions_response = supabase.table("scrape_sessions").select("status").eq("project_id", url_data['project_id']).eq("url", url_data['url']).order("scraped_at", desc=True).limit(1).execute()
            
            if sessions_response.data:
                session_status = sessions_response.data[0]['status']
                if session_status == 'rag_ingested':
                    new_status = 'completed'
                elif session_status == 'scraped':
                    new_status = 'completed'  # If scraped but not RAG processed, still mark as completed
                else:
                    new_status = 'pending'
            else:
                new_status = 'pending'
            
            # Update the status
            supabase.table("project_urls").update({"status": new_status}).eq("id", url_data['id']).execute()
            print(f"  Set status to: {new_status}")
            fixed_count += 1
    
    print(f"Fixed {fixed_count} URLs with missing status.")

def fix_missing_unique_identifiers():
    """Fix any missing unique_scrape_identifier values in scrape_sessions table."""
    print("\n=== FIXING MISSING UNIQUE IDENTIFIERS ===")
    
    # Get all scrape sessions
    response = supabase.table("scrape_sessions").select("*").execute()
    
    if not response.data:
        print("No scrape sessions found.")
        return
    
    fixed_count = 0
    for session in response.data:
        if not session.get('unique_scrape_identifier'):
            print(f"Fixing missing unique identifier for session: {session['id']}")
            
            # Generate a unique identifier based on project_id and session_id
            unique_identifier = f"{session['project_id']}_{session['id']}"
            
            # Update the unique identifier
            supabase.table("scrape_sessions").update({"unique_scrape_identifier": unique_identifier}).eq("id", session['id']).execute()
            print(f"  Set unique identifier to: {unique_identifier}")
            fixed_count += 1
    
    print(f"Fixed {fixed_count} sessions with missing unique identifiers.")

def sync_project_url_status():
    """Sync project_urls status with the latest scrape session status."""
    print("\n=== SYNCING PROJECT URL STATUS ===")
    
    # Get all project URLs
    response = supabase.table("project_urls").select("*").execute()
    
    if not response.data:
        print("No project URLs found.")
        return
    
    updated_count = 0
    for url_data in response.data:
        # Get the latest scrape session for this URL
        sessions_response = supabase.table("scrape_sessions").select("status, id").eq("project_id", url_data['project_id']).eq("url", url_data['url']).order("scraped_at", desc=True).limit(1).execute()
        
        if sessions_response.data:
            session = sessions_response.data[0]
            session_status = session['status']
            session_id = session['id']
            
            # Determine the appropriate project URL status
            if session_status == 'rag_ingested':
                new_status = 'completed'
            elif session_status == 'scraped':
                # Check if RAG is enabled for this URL
                if url_data.get('rag_enabled', False):
                    new_status = 'processing_rag'  # Should be processing RAG
                else:
                    new_status = 'completed'  # RAG not enabled, so completed
            elif session_status == 'error':
                new_status = 'failed'
            else:
                new_status = 'pending'
            
            # Update if status has changed
            current_status = url_data.get('status', 'pending')
            if current_status != new_status:
                print(f"Updating status for {url_data['url']}: {current_status} -> {new_status}")
                
                update_data = {
                    "status": new_status,
                    "last_scraped_session_id": session_id
                }
                
                supabase.table("project_urls").update(update_data).eq("id", url_data['id']).execute()
                updated_count += 1
        else:
            # No sessions found, ensure status is pending
            if url_data.get('status') != 'pending':
                print(f"No sessions found for {url_data['url']}, setting status to pending")
                supabase.table("project_urls").update({"status": "pending"}).eq("id", url_data['id']).execute()
                updated_count += 1
    
    print(f"Updated {updated_count} project URL statuses.")

def main():
    """Main fix function."""
    print("Starting database fixes...")
    
    fix_missing_status_columns()
    fix_missing_unique_identifiers()
    sync_project_url_status()
    
    print("\nDatabase fixes completed!")

if __name__ == "__main__":
    main()
