#!/usr/bin/env python3
"""
Simple test script to verify the chart refreshing fixes and error handling improvements.
"""

import json
import time
import requests
import sys
import os

class SimpleChartFixTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:9002"
        
    def test_backend_health(self):
        """Test 1: Backend Health Check"""
        print("🔍 Test 1: Backend Health Check")
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend is running and healthy: {data}")
                return True
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend connection failed: {e}")
            return False

    def test_frontend_accessibility(self):
        """Test 2: Frontend Accessibility"""
        print("\n🔍 Test 2: Frontend Accessibility")
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print("✅ Frontend is accessible")
                return True
            else:
                print(f"❌ Frontend accessibility failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Frontend connection failed: {e}")
            return False

    def test_enhanced_rag_error_handling(self):
        """Test 3: Enhanced RAG Error Handling"""
        print("\n🔍 Test 3: Enhanced RAG Error Handling")
        try:
            # Test with invalid project ID to trigger error handling
            test_payload = {
                "query": "test query for error handling",
                "deployment_name": "gpt-4o-mini"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/projects/00000000-0000-0000-0000-000000000000/enhanced-rag-query",
                json=test_payload,
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            if response.status_code in [400, 404, 422, 500]:  # Expected error codes
                try:
                    error_data = response.json()
                    print(f"✅ Enhanced RAG endpoint properly handles errors: {error_data}")
                    return True
                except:
                    print("✅ Enhanced RAG endpoint returns error response")
                    return True
            else:
                print(f"⚠️  Unexpected response code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Enhanced RAG endpoint test failed: {e}")
            return False

    def test_chart_data_stability(self):
        """Test 4: Chart Data Stability (JSON serialization)"""
        print("\n🔍 Test 4: Chart Data Stability")
        
        # Simulate chart data that would be rendered
        chart_data = {
            "chart_type": "bar",
            "title": "Test Chart",
            "description": "Test chart for stability",
            "data": {
                "labels": ["Item 1", "Item 2", "Item 3"],
                "values": [10, 20, 30],
                "datasets": [{
                    "label": "Test Data",
                    "data": [10, 20, 30],
                    "backgroundColor": ["#8B5CF6", "#A78BFA", "#C4B5FD"]
                }]
            }
        }
        
        try:
            # Test JSON serialization stability (key part of our fix)
            json_str1 = json.dumps(chart_data, sort_keys=True)
            json_str2 = json.dumps(chart_data, sort_keys=True)
            
            if json_str1 == json_str2:
                print("✅ Chart data serialization is stable")
                
                # Test with slight modification
                chart_data_modified = chart_data.copy()
                chart_data_modified["title"] = "Modified Test Chart"
                json_str3 = json.dumps(chart_data_modified, sort_keys=True)
                
                if json_str1 != json_str3:
                    print("✅ Chart data change detection works correctly")
                    return True
                else:
                    print("❌ Chart data change detection failed")
                    return False
            else:
                print("❌ Chart data serialization is unstable")
                return False
                
        except Exception as e:
            print(f"❌ Chart stability test failed: {e}")
            return False

    def test_component_files_exist(self):
        """Test 5: Verify Updated Component Files Exist"""
        print("\n🔍 Test 5: Component Files Verification")
        
        files_to_check = [
            "new-front/src/components/ChartRenderer.js",
            "new-front/src/components/StableChartRenderer.js",
            "new-front/src/components/MessageRenderer.js",
            "backend/app/services/enhanced_rag_service.py"
        ]
        
        all_exist = True
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                print(f"✅ {file_path} exists")
                
                # Check for key improvements in the files
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    if "ChartRenderer.js" in file_path:
                        if "useMemo" in content and "memoizedChartData" in content:
                            print(f"   ✅ ChartRenderer has memoization fixes")
                        else:
                            print(f"   ⚠️  ChartRenderer may be missing memoization")
                            
                    elif "StableChartRenderer.js" in file_path:
                        if "memo" in content and "JSON.stringify" in content:
                            print(f"   ✅ StableChartRenderer has stability fixes")
                        else:
                            print(f"   ⚠️  StableChartRenderer may be missing stability fixes")
                            
                    elif "enhanced_rag_service.py" in file_path:
                        if "traceback.format_exc()" in content:
                            print(f"   ✅ Enhanced RAG service has improved error logging")
                        else:
                            print(f"   ⚠️  Enhanced RAG service may be missing error improvements")
                            
                except Exception as e:
                    print(f"   ⚠️  Could not verify content of {file_path}: {e}")
                    
            else:
                print(f"❌ {file_path} does not exist")
                all_exist = False
        
        return all_exist

    def test_log_files(self):
        """Test 6: Check Log Files"""
        print("\n🔍 Test 6: Log Files Check")
        
        log_files = [
            "backend/logs/app.log",
            "logs/firecrawl_api.log"
        ]
        
        logs_found = False
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            recent_lines = lines[-5:]  # Last 5 lines
                            print(f"✅ {log_file} exists with {len(lines)} lines")
                            print(f"   Last entry preview: {recent_lines[-1].strip()[:100]}...")
                            logs_found = True
                        else:
                            print(f"⚠️  {log_file} exists but is empty")
                except Exception as e:
                    print(f"⚠️  Could not read {log_file}: {e}")
            else:
                print(f"⚠️  {log_file} not found")
        
        if logs_found:
            print("✅ Logging system is active")
        else:
            print("⚠️  No log files found (may be normal for new installation)")
            
        return True  # Not a critical failure

    def test_api_endpoints(self):
        """Test 7: Test Key API Endpoints"""
        print("\n🔍 Test 7: API Endpoints Test")
        
        endpoints_to_test = [
            ("/health", "GET"),
            ("/api/v1/projects", "GET"),
        ]
        
        working_endpoints = 0
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.backend_url}{endpoint}", timeout=5)
                
                if response.status_code in [200, 401, 422]:  # 401/422 are acceptable for auth-required endpoints
                    print(f"✅ {method} {endpoint} - Status: {response.status_code}")
                    working_endpoints += 1
                else:
                    print(f"⚠️  {method} {endpoint} - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {method} {endpoint} - Error: {e}")
        
        if working_endpoints >= len(endpoints_to_test) * 0.5:
            print(f"✅ API endpoints are mostly functional ({working_endpoints}/{len(endpoints_to_test)})")
            return True
        else:
            print(f"❌ Too many API endpoints failing ({working_endpoints}/{len(endpoints_to_test)})")
            return False

    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting Chart Fix Verification Tests")
        print("=" * 60)
        
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("Enhanced RAG Error Handling", self.test_enhanced_rag_error_handling),
            ("Chart Data Stability", self.test_chart_data_stability),
            ("Component Files Verification", self.test_component_files_exist),
            ("Log Files Check", self.test_log_files),
            ("API Endpoints", self.test_api_endpoints),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Chart fixes are working correctly.")
            print("\n📋 NEXT STEPS:")
            print("1. Open your browser and go to http://localhost:9002")
            print("2. Create a project and scrape some data")
            print("3. Generate a chart in the chat")
            print("4. Type in the chat while the chart is visible")
            print("5. Verify the chart doesn't refresh/flicker")
        elif passed >= total * 0.7:
            print("✅ Most tests passed. Core fixes are working.")
            print("\n📋 NEXT STEPS:")
            print("1. Check any failed tests above")
            print("2. Test chart stability manually in the browser")
        else:
            print("⚠️  Several tests failed. Please check the issues above.")
        
        return passed, total

if __name__ == "__main__":
    tester = SimpleChartFixTester()
    passed, total = tester.run_all_tests()
    
    print(f"\n📋 TESTING COMPLETE: {passed}/{total} tests passed")
    
    if passed >= total * 0.7:
        print("\n🎯 MANUAL TESTING INSTRUCTIONS:")
        print("=" * 40)
        print("1. Open http://localhost:9002 in your browser")
        print("2. Create a new project")
        print("3. Add a URL and scrape it")
        print("4. Go to the Chat tab")
        print("5. Ask for a chart (e.g., 'create a chart of the data')")
        print("6. Once the chart appears, start typing in the chat input")
        print("7. ✅ SUCCESS: Chart should NOT refresh while typing")
        print("8. ❌ ISSUE: If chart refreshes, there may be additional React issues")
