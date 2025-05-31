#!/usr/bin/env python3
"""
Quick script to fix the project URL status issue.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_supabase_client

def fix_url_status():
    """Fix the project URL status for the specific URL that's stuck on processing_rag."""
    supabase = get_supabase_client()
    
    # The specific project and URL from the logs
    project_id = '67df8224-feba-4dd0-8648-abb9100cbb38'
    session_id = '208ffe51-c0e4-4c8e-9003-cae52c3d493e'
    url = 'https://webscraper.io/test-sites/e-commerce/allinone'
    
    print(f"Fixing status for project {project_id}, URL: {url}")
    
    # Check current session status
    session_response = supabase.table('scrape_sessions').select('*').eq('id', session_id).execute()
    if session_response.data:
        session = session_response.data[0]
        print(f"Session status: {session['status']}")
        
        # Check current project URL status
        project_url_response = supabase.table('project_urls').select('*').eq('project_id', project_id).eq('url', url).execute()
        if project_url_response.data:
            project_url = project_url_response.data[0]
            print(f"Current project URL status: {project_url['status']}")
            
            # If session is rag_ingested but project URL is not completed, fix it
            if session['status'] == 'rag_ingested' and project_url['status'] != 'completed':
                print("Updating project URL status to 'completed'")
                update_response = supabase.table('project_urls').update({
                    'status': 'completed',
                    'last_scraped_session_id': session_id
                }).eq('id', project_url['id']).execute()
                
                if update_response.data:
                    print("✅ Successfully updated project URL status to 'completed'")
                else:
                    print("❌ Failed to update project URL status")
            else:
                print("✅ Project URL status is already correct")
        else:
            print("❌ Project URL not found")
    else:
        print("❌ Session not found")

if __name__ == "__main__":
    fix_url_status()
