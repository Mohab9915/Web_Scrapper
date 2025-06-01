#!/usr/bin/env python3
"""
Test the RAG option visibility and scraping completeness fixes
"""

import requests
import time
import json

def test_frontend_rag_option():
    """Test if the frontend shows the RAG option"""
    
    print("🔍 TESTING FRONTEND RAG OPTION VISIBILITY")
    print("=" * 60)
    
    frontend_url = "http://localhost:9002"
    
    try:
        # Test if frontend is accessible
        response = requests.get(frontend_url, timeout=10)
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for RAG-related elements in the HTML (updated for new switch design)
            rag_indicators = [
                'rag-enabled-switch',
                'Enable RAG',
                'AI Chat Integration',
                'rag_enabled'
            ]
            
            found_indicators = []
            for indicator in rag_indicators:
                if indicator in html_content:
                    found_indicators.append(indicator)
            
            print(f"✅ Frontend is accessible")
            print(f"RAG indicators found: {len(found_indicators)}/{len(rag_indicators)}")
            
            for indicator in found_indicators:
                print(f"  ✅ Found: {indicator}")
            
            missing_indicators = [ind for ind in rag_indicators if ind not in found_indicators]
            for indicator in missing_indicators:
                print(f"  ❌ Missing: {indicator}")
            
            if len(found_indicators) >= 2:
                print("✅ RAG option should be visible in the UI")
                return True
            else:
                print("⚠️  RAG option may not be fully visible")
                return False
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def test_project_url_creation_with_rag():
    """Test creating a project URL with RAG enabled"""
    
    print("\n🔧 TESTING PROJECT URL CREATION WITH RAG")
    print("=" * 60)
    
    backend_url = "http://localhost:8000"
    
    # Create a test project first
    project_payload = {
        "name": "Test RAG Project",
        "description": "Testing RAG functionality"
    }
    
    try:
        # Create project
        project_response = requests.post(
            f"{backend_url}/api/v1/projects",
            json=project_payload,
            timeout=10
        )
        
        if project_response.status_code == 201:
            project_data = project_response.json()
            project_id = project_data["id"]
            print(f"✅ Test project created: {project_id}")
            
            # Add URL with RAG enabled
            url_payload = {
                "url": "https://scrapethissite.com/pages/simple/",
                "conditions": "country, capital, population, area",
                "display_format": "table",
                "rag_enabled": True
            }
            
            url_response = requests.post(
                f"{backend_url}/api/v1/projects/{project_id}/urls",
                json=url_payload,
                timeout=10
            )
            
            if url_response.status_code == 201:
                url_data = url_response.json()
                print(f"✅ URL added with RAG enabled: {url_data.get('rag_enabled')}")
                
                # Verify the URL was stored correctly
                get_response = requests.get(
                    f"{backend_url}/api/v1/projects/{project_id}/urls",
                    timeout=10
                )
                
                if get_response.status_code == 200:
                    urls = get_response.json()
                    if urls and len(urls) > 0:
                        url_info = urls[0]
                        rag_enabled = url_info.get('rag_enabled', False)
                        print(f"✅ URL retrieved with RAG status: {rag_enabled}")
                        
                        if rag_enabled:
                            print("🎉 RAG option is working correctly!")
                            return True, project_id
                        else:
                            print("❌ RAG option not saved correctly")
                            return False, project_id
                    else:
                        print("❌ No URLs found")
                        return False, project_id
                else:
                    print(f"❌ Failed to retrieve URLs: {get_response.status_code}")
                    return False, project_id
            else:
                print(f"❌ Failed to add URL: {url_response.status_code}")
                try:
                    error_data = url_response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Raw error: {url_response.text}")
                return False, project_id
        else:
            print(f"❌ Failed to create project: {project_response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Project URL test failed: {e}")
        return False, None

def test_scraping_completeness(project_id):
    """Test if scraping captures complete data"""
    
    print(f"\n📊 TESTING SCRAPING COMPLETENESS")
    print("=" * 60)
    
    if not project_id:
        print("❌ No project ID available for testing")
        return False
    
    backend_url = "http://localhost:8000"
    
    # Get the URLs for this project
    try:
        urls_response = requests.get(
            f"{backend_url}/api/v1/projects/{project_id}/urls",
            timeout=10
        )
        
        if urls_response.status_code == 200:
            urls = urls_response.json()
            if urls and len(urls) > 0:
                url_info = urls[0]
                url_id = url_info["id"]
                
                print(f"Testing scraping for URL: {url_info['url']}")
                print(f"RAG enabled: {url_info.get('rag_enabled', False)}")
                
                # Start interactive scraping session
                session_payload = {
                    "initial_url": url_info["url"]
                }

                session_response = requests.post(
                    f"{backend_url}/api/v1/projects/{project_id}/initiate-interactive-scrape",
                    json=session_payload,
                    timeout=30
                )
                
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    session_id = session_data.get("session_id")
                    
                    print(f"✅ Interactive session started: {session_id}")
                    
                    # Execute scraping
                    execute_payload = {
                        "current_page_url": url_info["url"],
                        "session_id": session_id,
                        "api_keys": {},  # Empty to test fallback
                        "display_format": url_info["display_format"],
                        "conditions": url_info["conditions"],
                        "rag_enabled": url_info.get("rag_enabled", False)
                    }
                    
                    execute_response = requests.post(
                        f"{backend_url}/api/v1/projects/{project_id}/execute-scrape",
                        json=execute_payload,
                        timeout=60
                    )
                    
                    if execute_response.status_code == 200:
                        execute_data = execute_response.json()
                        print(f"✅ Scraping executed successfully")
                        print(f"Status: {execute_data.get('status')}")
                        print(f"Message: {execute_data.get('message')}")
                        
                        # Check if we got tabular data
                        tabular_data = execute_data.get('tabular_data', [])
                        fields = execute_data.get('fields', [])
                        
                        print(f"Tabular data entries: {len(tabular_data)}")
                        print(f"Fields extracted: {fields}")
                        
                        if len(tabular_data) > 0:
                            print(f"✅ Data extraction successful!")
                            
                            # Check if we have country data
                            sample_entry = tabular_data[0]
                            print(f"Sample entry: {sample_entry}")
                            
                            # Look for expected fields
                            expected_fields = ['country', 'capital', 'population', 'area']
                            found_fields = [field for field in expected_fields if field in sample_entry]
                            
                            print(f"Expected fields found: {found_fields}")
                            
                            if len(found_fields) >= 2:
                                print("🎉 Scraping completeness looks good!")
                                return True
                            else:
                                print("⚠️  Some expected fields missing")
                                return False
                        else:
                            print("❌ No tabular data extracted")
                            return False
                    else:
                        print(f"❌ Scraping execution failed: {execute_response.status_code}")
                        try:
                            error_data = execute_response.json()
                            print(f"Error details: {error_data}")
                        except:
                            print(f"Raw error: {execute_response.text}")
                        return False
                else:
                    print(f"❌ Failed to start interactive session: {session_response.status_code}")
                    return False
            else:
                print("❌ No URLs found in project")
                return False
        else:
            print(f"❌ Failed to get project URLs: {urls_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Scraping test failed: {e}")
        return False

def cleanup_test_project(project_id):
    """Clean up the test project"""
    
    if not project_id:
        return
    
    print(f"\n🧹 CLEANING UP TEST PROJECT")
    print("=" * 40)
    
    backend_url = "http://localhost:8000"
    
    try:
        response = requests.delete(
            f"{backend_url}/api/v1/projects/{project_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Test project cleaned up: {project_id}")
        else:
            print(f"⚠️  Could not clean up project: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  Cleanup error: {e}")

def main():
    """Run all tests"""
    
    print("🚀 TESTING RAG OPTION AND SCRAPING FIXES")
    print("=" * 80)
    
    # Test 1: Frontend RAG option visibility
    frontend_success = test_frontend_rag_option()
    
    # Test 2: Project URL creation with RAG
    url_success, project_id = test_project_url_creation_with_rag()
    
    # Test 3: Scraping completeness
    scraping_success = False
    if project_id:
        scraping_success = test_scraping_completeness(project_id)
    
    # Cleanup
    cleanup_test_project(project_id)
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    
    if frontend_success:
        print("✅ Frontend RAG option is visible")
    else:
        print("❌ Frontend RAG option needs work")
    
    if url_success:
        print("✅ Project URL creation with RAG is working")
    else:
        print("❌ Project URL creation with RAG needs work")
    
    if scraping_success:
        print("✅ Scraping completeness is good")
    else:
        print("❌ Scraping completeness needs work")
    
    total_success = sum([frontend_success, url_success, scraping_success])
    
    if total_success == 3:
        print("\n🎉 ALL FIXES ARE WORKING!")
        print("✅ RAG option is now visible in the UI")
        print("✅ URLs can be created with RAG enabled")
        print("✅ Scraping captures complete data")
    elif total_success >= 2:
        print("\n✅ Most fixes are working!")
        print("⚠️  Some minor issues may remain")
    else:
        print("\n⚠️  Several issues need attention")
    
    print(f"\n🎯 Success rate: {total_success}/3 tests passed")

if __name__ == "__main__":
    main()
