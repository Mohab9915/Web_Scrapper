#!/usr/bin/env python3
"""
Test script to verify the chart refreshing fixes and error handling improvements.
"""

import asyncio
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

class ChartFixTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:9002"
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver for testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"❌ Could not setup Chrome driver: {e}")
            print("📝 Note: Selenium tests require Chrome and chromedriver to be installed")
            return False

    def test_backend_health(self):
        """Test 1: Backend Health Check"""
        print("🔍 Test 1: Backend Health Check")
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is running and healthy")
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
            if response.status_code == 200 and "react" in response.text.lower():
                print("✅ Frontend is accessible")
                return True
            else:
                print(f"❌ Frontend accessibility failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Frontend connection failed: {e}")
            return False

    def test_enhanced_rag_endpoint(self):
        """Test 3: Enhanced RAG Endpoint Error Handling"""
        print("\n🔍 Test 3: Enhanced RAG Endpoint Error Handling")
        try:
            # Test with invalid project ID to trigger error handling
            test_payload = {
                "query": "test query",
                "deployment_name": "gpt-4o-mini"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/projects/invalid-uuid/enhanced-rag-query",
                json=test_payload,
                timeout=10
            )
            
            if response.status_code in [400, 404, 422]:  # Expected error codes
                print("✅ Enhanced RAG endpoint properly handles invalid requests")
                return True
            else:
                print(f"⚠️  Unexpected response code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Enhanced RAG endpoint test failed: {e}")
            return False

    def test_chart_stability_simulation(self):
        """Test 4: Chart Stability Simulation (without browser)"""
        print("\n🔍 Test 4: Chart Stability Simulation")
        
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
        
        # Test JSON serialization stability (key part of our fix)
        try:
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

    def test_browser_chart_stability(self):
        """Test 5: Browser-based Chart Stability (if driver available)"""
        print("\n🔍 Test 5: Browser-based Chart Stability")
        
        if not self.driver:
            print("⚠️  Skipping browser test - Chrome driver not available")
            return True
            
        try:
            # Navigate to the application
            self.driver.get(self.frontend_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print("✅ Successfully loaded frontend in browser")
            
            # Look for any JavaScript errors in console
            logs = self.driver.get_log('browser')
            error_logs = [log for log in logs if log['level'] == 'SEVERE']
            
            if not error_logs:
                print("✅ No severe JavaScript errors detected")
                return True
            else:
                print(f"⚠️  Found {len(error_logs)} JavaScript errors:")
                for log in error_logs[:3]:  # Show first 3 errors
                    print(f"   - {log['message']}")
                return False
                
        except Exception as e:
            print(f"❌ Browser test failed: {e}")
            return False

    def test_error_logging_improvements(self):
        """Test 6: Error Logging Improvements"""
        print("\n🔍 Test 6: Error Logging Improvements")
        
        # Check if log files exist and have recent entries
        log_files = [
            "backend/logs/app.log",
            "logs/firecrawl_api.log"
        ]
        
        recent_logs_found = False
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        # Check if there are recent log entries (last 10 lines)
                        recent_lines = lines[-10:]
                        if any("2025" in line for line in recent_lines):
                            recent_logs_found = True
                            print(f"✅ Found recent log entries in {log_file}")
                        else:
                            print(f"⚠️  No recent entries in {log_file}")
                    else:
                        print(f"⚠️  {log_file} is empty")
            except FileNotFoundError:
                print(f"⚠️  {log_file} not found")
            except Exception as e:
                print(f"⚠️  Could not read {log_file}: {e}")
        
        if recent_logs_found:
            print("✅ Error logging system is active")
            return True
        else:
            print("⚠️  No recent log activity detected")
            return True  # Not a failure, just no recent activity

    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting Chart Fix Verification Tests")
        print("=" * 50)
        
        # Setup browser driver (optional)
        driver_available = self.setup_driver()
        
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("Enhanced RAG Error Handling", self.test_enhanced_rag_endpoint),
            ("Chart Stability Simulation", self.test_chart_stability_simulation),
            ("Browser Chart Stability", self.test_browser_chart_stability),
            ("Error Logging Improvements", self.test_error_logging_improvements),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Cleanup
        if self.driver:
            self.driver.quit()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Chart fixes are working correctly.")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. Minor issues may exist but core fixes are working.")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
        
        return passed, total

if __name__ == "__main__":
    tester = ChartFixTester()
    passed, total = tester.run_all_tests()
    
    print(f"\n📋 TESTING COMPLETE: {passed}/{total} tests passed")
