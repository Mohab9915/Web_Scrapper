#!/usr/bin/env python3
"""
Test re-scraping with the fixed LLM system to verify user-focused field extraction
"""

import sys
import os
import json
import requests
import time

# Add backend to path
sys.path.append('backend')

def test_rescrap_with_llm():
    """Test re-scraping to see if LLM gives name column"""
    
    try:
        print("🧪 Testing Re-scraping with Fixed LLM System")
        print("=" * 60)
        
        # Find the countries project
        backend_url = "http://localhost:8000"
        api_url = f"{backend_url}/api/v1"
        
        # Get projects to find the countries project
        projects_response = requests.get(f"{api_url}/projects", timeout=10)
        if projects_response.status_code != 200:
            print(f"❌ Failed to get projects: {projects_response.status_code}")
            return
            
        projects = projects_response.json()
        countries_project = None
        
        for project in projects:
            if 'countries' in project['name'].lower():
                countries_project = project
                break
                
        if not countries_project:
            print("❌ Countries project not found")
            return
            
        project_id = countries_project['id']
        print(f"✅ Found project: {countries_project['name']} (ID: {project_id})")
        
        # Prepare scraping request with user conditions
        scrape_data = {
            "current_page_url": "https://www.scrapethissite.com/pages/simple/",
            "session_id": f"test_rescrap_{int(time.time())}",
            "force_refresh": True,
            "display_format": "table",
            "conditions": "name, area",  # User-specified conditions
            "api_keys": {
                "api_key": "test_key",
                "endpoint": "test_endpoint",
                "deployment_name": "gpt-4o"
            }
        }
        
        print(f"🚀 Starting re-scrape with conditions: '{scrape_data['conditions']}'")
        print(f"🌐 URL: {scrape_data['current_page_url']}")
        print(f"🔄 Force refresh: {scrape_data['force_refresh']}")
        
        # Execute scraping
        response = requests.post(
            f"{api_url}/projects/{project_id}/execute-scrape",
            json=scrape_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Scraping completed successfully")
            print(f"📊 Status: {result.get('status', 'Unknown')}")
            print(f"📝 Message: {result.get('message', 'No message')}")
            
            session_id = result.get('session_id')
            if session_id:
                print(f"🔑 Session ID: {session_id}")
                
                # Wait a moment for processing
                time.sleep(2)
                
                # Get the session details to check the extracted data
                session_response = requests.get(f"{api_url}/sessions/{session_id}", timeout=10)
                
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    
                    print(f"\n📊 Session Analysis:")
                    print(f"   Status: {session_data.get('status', 'Unknown')}")
                    
                    # Check structured data
                    structured_data = session_data.get('structured_data', {})
                    if structured_data:
                        extraction_method = structured_data.get('extraction_method', 'Not specified')
                        print(f"   Extraction Method: {extraction_method}")
                        
                        if 'llm' in extraction_method.lower() or 'azure' in extraction_method.lower():
                            print("✅ LLM extraction was used!")
                        elif 'fallback' in extraction_method.lower():
                            print("⚠️  Fallback extraction was used (content too large or no API keys)")
                        else:
                            print(f"🔍 Unknown extraction method: {extraction_method}")
                        
                        # Check the actual data structure
                        listings = structured_data.get('listings', [])
                        if listings and len(listings) > 0:
                            first_item = listings[0]
                            print(f"\n🔍 First Item Analysis:")
                            print(f"   Available Fields: {list(first_item.keys())}")
                            
                            # Check for user-requested fields
                            if 'name' in first_item:
                                name_value = first_item['name']
                                if name_value and name_value.strip():
                                    print(f"✅ 'name' field found with value: '{name_value}' (SUCCESS!)")
                                else:
                                    print(f"❌ 'name' field found but empty: '{name_value}'")
                            else:
                                print(f"❌ 'name' field NOT found in extracted data")
                                
                            if 'area' in first_item:
                                area_value = first_item['area']
                                if area_value and area_value.strip():
                                    print(f"✅ 'area' field found with value: '{area_value}' (SUCCESS!)")
                                else:
                                    print(f"❌ 'area' field found but empty: '{area_value}'")
                            else:
                                print(f"❌ 'area' field NOT found in extracted data")
                                
                            # Check for unwanted extra fields
                            requested_fields = ['name', 'area']
                            extra_fields = [f for f in first_item.keys() if f not in requested_fields]
                            if extra_fields:
                                print(f"⚠️  Extra fields found (not requested): {extra_fields}")
                            else:
                                print(f"✅ No extra fields - only requested fields present")
                                
                            print(f"\n📋 Sample Data:")
                            for key, value in first_item.items():
                                print(f"   {key}: '{value}'")
                                
                        else:
                            print(f"❌ No listings found in structured data")
                    else:
                        print(f"❌ No structured data found in session")
                        
                else:
                    print(f"❌ Failed to get session details: {session_response.status_code}")
                    
            else:
                print(f"❌ No session ID returned from scraping")
                
        else:
            print(f"❌ Scraping failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during re-scraping test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rescrap_with_llm()
