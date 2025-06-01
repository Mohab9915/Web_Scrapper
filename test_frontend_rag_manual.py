#!/usr/bin/env python3
"""
Manual test for frontend RAG option visibility
"""

import time
import requests

def test_api_fixes():
    """Test the API fixes we made"""
    
    print("🧪 TESTING API FIXES")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    
    # Create a test project
    project_payload = {
        "name": "RAG Test Project",
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
            
            # Test URL creation with RAG enabled
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
                print(f"✅ URL created with RAG enabled: {url_data.get('rag_enabled')}")
                
                # Test interactive scraping initiation
                session_payload = {
                    "initial_url": "https://scrapethissite.com/pages/simple/"
                }
                
                session_response = requests.post(
                    f"{backend_url}/api/v1/projects/{project_id}/initiate-interactive-scrape",
                    json=session_payload,
                    timeout=10
                )
                
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    print(f"✅ Interactive scraping session initiated: {session_data.get('session_id')}")
                    
                    # Clean up
                    requests.delete(f"{backend_url}/api/v1/projects/{project_id}", timeout=10)
                    print(f"✅ Test project cleaned up")
                    
                    return True
                else:
                    print(f"❌ Interactive scraping failed: {session_response.status_code}")
                    print(f"Error: {session_response.text}")
                    return False
            else:
                print(f"❌ URL creation failed: {url_response.status_code}")
                print(f"Error: {url_response.text}")
                return False
        else:
            print(f"❌ Project creation failed: {project_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def check_frontend_status():
    """Check if frontend is running and accessible"""
    
    print("\n🌐 CHECKING FRONTEND STATUS")
    print("=" * 50)
    
    frontend_url = "http://localhost:9002"
    
    try:
        response = requests.get(frontend_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Frontend is accessible at {frontend_url}")
            
            # Check if it's a React app
            html_content = response.text
            if 'react' in html_content.lower() or 'root' in html_content:
                print(f"✅ React app detected")
                return True
            else:
                print(f"⚠️  May not be a React app")
                return False
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend check failed: {e}")
        return False

def main():
    """Run manual tests and provide instructions"""
    
    print("🚀 MANUAL TESTING FOR RAG OPTION AND SCRAPING FIXES")
    print("=" * 80)
    
    # Test API fixes
    api_success = test_api_fixes()
    
    # Check frontend status
    frontend_success = check_frontend_status()
    
    print("\n" + "=" * 80)
    print("📋 MANUAL TESTING INSTRUCTIONS")
    print("=" * 80)
    
    if api_success:
        print("✅ Backend API fixes are working correctly!")
        print("   • Project URL creation with RAG enabled: ✅")
        print("   • Interactive scraping session initiation: ✅")
    else:
        print("❌ Backend API fixes need attention")
    
    if frontend_success:
        print("✅ Frontend is accessible!")
    else:
        print("❌ Frontend accessibility issues")
    
    print(f"\n🎯 MANUAL TESTING STEPS:")
    print(f"1. Open your browser and go to: http://localhost:9002")
    print(f"2. Create a new project or select an existing one")
    print(f"3. Go to the 'URLs' tab")
    print(f"4. Click 'Add New URL'")
    print(f"5. Look for the RAG checkbox with text: '🧠 Enable RAG (AI Chat Integration)'")
    print(f"6. Fill in the form:")
    print(f"   • URL: https://scrapethissite.com/pages/simple/")
    print(f"   • Conditions: country, capital, population, area")
    print(f"   • Display Format: Table View")
    print(f"   • ✅ Check the RAG checkbox")
    print(f"7. Click 'Add URL'")
    print(f"8. Verify the URL appears with a '🧠 RAG' badge")
    print(f"9. Click 'Start Scraping' on the URL")
    print(f"10. Complete the scraping process")
    print(f"11. Go to the 'Chat' tab")
    print(f"12. Ask: 'tell me about Russia'")
    print(f"13. Verify the chat responds with Russia's information")
    
    print(f"\n✅ EXPECTED RESULTS:")
    print(f"   • RAG checkbox should be visible in the URL form")
    print(f"   • URLs with RAG enabled should show a '🧠 RAG' badge")
    print(f"   • Scraping should complete successfully")
    print(f"   • Chat should find and display country information")
    
    if api_success and frontend_success:
        print(f"\n🎉 ALL SYSTEMS READY FOR MANUAL TESTING!")
    else:
        print(f"\n⚠️  Some issues detected - check the logs above")
    
    print(f"\n📝 If the RAG checkbox is not visible:")
    print(f"   • Try refreshing the browser (Ctrl+F5)")
    print(f"   • Check browser console for JavaScript errors")
    print(f"   • Verify the frontend compiled successfully")

if __name__ == "__main__":
    main()
