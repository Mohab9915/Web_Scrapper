#!/usr/bin/env python3
"""
Debug the frontend data flow to understand why country names are not showing.
"""
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import get_supabase_client

def debug_data_flow():
    """Debug the complete data flow from database to frontend"""
    print("🔍 DEBUGGING FRONTEND DATA FLOW")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Get test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    
    if not project_response.data:
        print("❌ test1 project not found")
        return
    
    project = project_response.data[0]
    project_id = project['id']
    
    print(f"📋 Project: {project['name']} (ID: {project_id})")
    
    # Step 1: Check project_urls table
    print("\n1️⃣ CHECKING PROJECT_URLS TABLE")
    print("-" * 40)
    
    project_urls_response = supabase.table("project_urls").select("*").eq("project_id", project_id).execute()
    
    if not project_urls_response.data:
        print("❌ No project URLs found")
        return
    
    for url_entry in project_urls_response.data:
        print(f"URL: {url_entry['url']}")
        print(f"Conditions: {url_entry.get('conditions', 'N/A')}")
        print(f"Display Format: {url_entry.get('display_format', 'N/A')}")
        print(f"Last Scraped Session ID: {url_entry.get('last_scraped_session_id', 'N/A')}")
        print(f"Status: {url_entry.get('status', 'N/A')}")
        
        # Step 2: Check the linked scrape session
        if url_entry.get('last_scraped_session_id'):
            print(f"\n2️⃣ CHECKING LINKED SCRAPE SESSION")
            print("-" * 40)
            
            session_response = supabase.table("scrape_sessions").select("*").eq("id", url_entry['last_scraped_session_id']).execute()
            
            if session_response.data:
                session = session_response.data[0]
                print(f"Session ID: {session['id']}")
                print(f"Status: {session['status']}")
                print(f"URL: {session['url']}")
                print(f"Scraped At: {session['scraped_at']}")
                
                # Check structured_data_json
                if session.get('structured_data_json'):
                    print(f"\n3️⃣ ANALYZING STRUCTURED DATA")
                    print("-" * 40)
                    
                    try:
                        if isinstance(session['structured_data_json'], str):
                            structured_data = json.loads(session['structured_data_json'])
                        else:
                            structured_data = session['structured_data_json']
                        
                        print(f"Structured data keys: {list(structured_data.keys())}")
                        
                        if 'listings' in structured_data:
                            listings = structured_data['listings']
                            print(f"Listings count: {len(listings)}")
                            
                            if listings:
                                print(f"First listing: {listings[0]}")
                                print(f"First listing keys: {list(listings[0].keys())}")
                                
                                # Check if country field exists and has value
                                if 'country' in listings[0]:
                                    print(f"✅ Country field exists: '{listings[0]['country']}'")
                                else:
                                    print("❌ Country field missing!")
                                
                                # Show first 3 entries
                                print("\nFirst 3 entries:")
                                for i, item in enumerate(listings[:3]):
                                    print(f"  {i+1}. {item}")
                        
                        # Step 4: Simulate backend API response
                        print(f"\n4️⃣ SIMULATING BACKEND API RESPONSE")
                        print("-" * 40)
                        
                        # This simulates what get_sessions_by_project returns
                        session_data_for_model = {}
                        
                        # Parse structured_data_json
                        if session.get('structured_data_json'):
                            session_data_for_model["structured_data"] = structured_data
                            
                            # Extract tabular_data (this is what frontend uses)
                            current_tabular_data = []
                            if isinstance(structured_data.get("listings"), list):
                                current_tabular_data = structured_data["listings"]
                            elif isinstance(structured_data, list):
                                current_tabular_data = structured_data
                            elif isinstance(structured_data, dict):
                                current_tabular_data = [structured_data]
                            
                            session_data_for_model["tabular_data"] = current_tabular_data
                            
                            # Extract fields
                            if current_tabular_data and isinstance(current_tabular_data[0], dict):
                                session_data_for_model["fields"] = list(current_tabular_data[0].keys())
                            else:
                                session_data_for_model["fields"] = []
                        
                        print(f"Tabular data count: {len(session_data_for_model.get('tabular_data', []))}")
                        print(f"Fields: {session_data_for_model.get('fields', [])}")
                        
                        if session_data_for_model.get('tabular_data'):
                            print(f"Sample tabular data: {session_data_for_model['tabular_data'][0]}")
                        
                        # Step 5: Simulate frontend processing
                        print(f"\n5️⃣ SIMULATING FRONTEND PROCESSING")
                        print("-" * 40)
                        
                        # This simulates Dashboard.js logic
                        tabular_data = session_data_for_model.get('tabular_data', [])
                        fields = session_data_for_model.get('fields', [])
                        
                        print(f"Frontend receives tabular_data: {len(tabular_data)} items")
                        print(f"Frontend receives fields: {fields}")
                        
                        if tabular_data:
                            print(f"Frontend sample item: {tabular_data[0]}")
                            
                            # Check what would be displayed in table
                            print("\nTable display simulation:")
                            print("Headers:", fields)
                            
                            for i, row in enumerate(tabular_data[:3]):
                                row_values = []
                                for field in fields:
                                    value = row.get(field, '')
                                    row_values.append(value)
                                print(f"Row {i+1}: {row_values}")
                        
                    except Exception as e:
                        print(f"❌ Error parsing structured data: {e}")
                else:
                    print("❌ No structured_data_json found")
            else:
                print("❌ Session not found")
        else:
            print("❌ No last_scraped_session_id")

def check_api_endpoint_simulation():
    """Simulate the actual API endpoint that frontend calls"""
    print(f"\n6️⃣ SIMULATING API ENDPOINT /projects/{{project_id}}/sessions")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Get test1 project
    project_response = supabase.table("projects").select("*").eq("name", "test1").execute()
    project = project_response.data[0]
    project_id = project['id']
    
    # Simulate the exact logic from scraping_service.py get_sessions_by_project
    project_urls_response = supabase.table("project_urls").select(
        "id, project_id, url, conditions, display_format, created_at, status, rag_enabled, last_scraped_session_id"
    ).eq("project_id", str(project_id)).order("created_at", desc=True).execute()
    
    results = []
    for pu_entry in project_urls_response.data:
        print(f"\nProcessing URL: {pu_entry['url']}")
        
        session_data_for_model = {}
        raw_session_data = None
        
        # Get the session data
        if pu_entry.get("last_scraped_session_id"):
            session_response = supabase.table("scrape_sessions").select(
                "id, project_id, url, scraped_at, status, raw_markdown, structured_data_json, display_format, formatted_tabular_data"
            ).eq("id", pu_entry["last_scraped_session_id"]).single().execute()
            
            if session_response.data:
                raw_session_data = session_response.data
                print(f"Found session: {raw_session_data['id']}")
                
                # Parse structured_data_json (exact logic from backend)
                if "structured_data_json" in raw_session_data and raw_session_data["structured_data_json"]:
                    try:
                        structured_data = json.loads(raw_session_data["structured_data_json"])
                        session_data_for_model["structured_data"] = structured_data
                        
                        current_tabular_data = []
                        if isinstance(structured_data.get("listings"), list):
                            current_tabular_data = structured_data["listings"]
                        elif isinstance(structured_data, list):
                            current_tabular_data = structured_data
                        elif isinstance(structured_data, dict):
                            current_tabular_data = [structured_data]
                        
                        session_data_for_model["tabular_data"] = current_tabular_data
                        
                        # Extract fields
                        if current_tabular_data and isinstance(current_tabular_data[0], dict):
                            session_data_for_model["fields"] = list(current_tabular_data[0].keys())
                        
                        print(f"✅ Parsed structured data successfully")
                        print(f"   Tabular data: {len(current_tabular_data)} items")
                        print(f"   Fields: {session_data_for_model.get('fields', [])}")
                        print(f"   Sample: {current_tabular_data[0] if current_tabular_data else 'None'}")
                        
                    except Exception as e:
                        print(f"❌ Error parsing structured_data_json: {e}")
        
        # Create the response object (as it would be sent to frontend)
        result_entry = {
            "id": pu_entry["id"],
            "project_id": pu_entry["project_id"],
            "url": pu_entry["url"],
            "conditions": pu_entry.get("conditions"),
            "display_format": pu_entry.get("display_format", "table"),
            "created_at": pu_entry.get("created_at"),
            "status": pu_entry.get("status", "pending"),
            "rag_enabled": pu_entry.get("rag_enabled", False),
            "last_scraped_session_id": pu_entry.get("last_scraped_session_id"),
            "latest_scrape_data": session_data_for_model if session_data_for_model else None
        }
        
        results.append(result_entry)
        
        print(f"API Response for this URL:")
        print(f"  latest_scrape_data exists: {bool(result_entry['latest_scrape_data'])}")
        if result_entry['latest_scrape_data']:
            print(f"  tabular_data: {len(result_entry['latest_scrape_data'].get('tabular_data', []))} items")
            print(f"  fields: {result_entry['latest_scrape_data'].get('fields', [])}")
    
    print(f"\n📊 FINAL API RESPONSE SUMMARY:")
    print(f"Total URLs: {len(results)}")
    for i, result in enumerate(results):
        print(f"URL {i+1}: {result['url']}")
        if result['latest_scrape_data']:
            tabular_data = result['latest_scrape_data'].get('tabular_data', [])
            fields = result['latest_scrape_data'].get('fields', [])
            print(f"  ✅ Has data: {len(tabular_data)} items, fields: {fields}")
        else:
            print(f"  ❌ No data")

if __name__ == "__main__":
    debug_data_flow()
    check_api_endpoint_simulation()
