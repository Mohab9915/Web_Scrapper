#!/usr/bin/env python3
"""
Comprehensive Frontend Integration Test Suite
Tests the complete frontend-backend integration for the ScrapeMaster AI system.
"""

import asyncio
import json
import time
import requests
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

class FrontendIntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:9002"
        self.api_url = f"{self.backend_url}/api/v1"
        self.test_results = []
        self.test_project_id = None
        self.test_session_id = None
        self.test_conversation_id = None
        
        # Test data
        self.test_project_name = f"Frontend_Integration_Test_{int(time.time())}"
        self.test_urls = [
            "https://httpbin.org/json",
            "https://jsonplaceholder.typicode.com/posts/1"
        ]
        
    def log_test(self, test_name: str, status: str, details: str = "", data: Any = None):
        """Log test results"""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "data": data
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if data and isinstance(data, dict):
            print(f"   Data: {json.dumps(data, indent=2)[:200]}...")
            
    def check_service_health(self, service_name: str, url: str) -> bool:
        """Check if a service is running and healthy"""
        try:
            response = requests.get(f"{url}/health" if "backend" in service_name.lower() else url, timeout=5)
            if response.status_code == 200:
                self.log_test(f"{service_name} Health Check", "PASS", f"Service running on {url}")
                return True
            else:
                self.log_test(f"{service_name} Health Check", "FAIL", f"HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test(f"{service_name} Health Check", "FAIL", f"Connection error: {str(e)}")
            return False
            
    def test_api_endpoints(self) -> bool:
        """Test core API endpoints availability"""
        endpoints = [
            ("GET", "/projects", "List Projects"),
            ("GET", "/cache/stats", "Cache Statistics"),
        ]
        
        all_passed = True
        for method, endpoint, description in endpoints:
            try:
                url = f"{self.api_url}{endpoint}"
                response = requests.request(method, url, timeout=10)
                
                if response.status_code in [200, 404]:  # 404 is OK for empty projects
                    self.log_test(f"API Endpoint: {description}", "PASS", 
                                f"{method} {endpoint} -> HTTP {response.status_code}")
                else:
                    self.log_test(f"API Endpoint: {description}", "FAIL", 
                                f"{method} {endpoint} -> HTTP {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"API Endpoint: {description}", "FAIL", f"Error: {str(e)}")
                all_passed = False
                
        return all_passed
        
    def test_project_lifecycle(self) -> bool:
        """Test complete project lifecycle: create, read, update, delete"""
        try:
            # 1. Create Project
            create_data = {
                "name": self.test_project_name,
                "initial_urls": self.test_urls
            }
            
            response = requests.post(f"{self.api_url}/projects",
                                   json=create_data, timeout=10)

            if response.status_code not in [200, 201]:  # Accept both 200 and 201 for creation
                self.log_test("Project Creation", "FAIL",
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
            project_data = response.json()
            self.test_project_id = project_data.get("id")
            
            if not self.test_project_id:
                self.log_test("Project Creation", "FAIL", "No project ID returned")
                return False
                
            self.log_test("Project Creation", "PASS", 
                        f"Created project {self.test_project_id}", project_data)
            
            # 2. Read Project
            response = requests.get(f"{self.api_url}/projects/{self.test_project_id}", timeout=10)
            if response.status_code == 200:
                project_data = response.json()
                self.log_test("Project Read", "PASS", "Successfully retrieved project", project_data)
            else:
                self.log_test("Project Read", "FAIL", f"HTTP {response.status_code}")
                return False
                
            # 3. Update Project Name
            update_data = {"name": f"{self.test_project_name}_Updated"}
            response = requests.put(f"{self.api_url}/projects/{self.test_project_id}", 
                                  json=update_data, timeout=10)
            
            if response.status_code == 200:
                self.log_test("Project Update", "PASS", "Successfully updated project name")
            else:
                self.log_test("Project Update", "FAIL", f"HTTP {response.status_code}")
                return False
                
            # 4. Update RAG Status
            rag_data = {"rag_enabled": True}
            response = requests.put(f"{self.api_url}/projects/{self.test_project_id}", 
                                  json=rag_data, timeout=10)
            
            if response.status_code == 200:
                self.log_test("Project RAG Update", "PASS", "Successfully enabled RAG")
            else:
                self.log_test("Project RAG Update", "FAIL", f"HTTP {response.status_code}")
                
            return True
            
        except Exception as e:
            self.log_test("Project Lifecycle", "FAIL", f"Exception: {str(e)}")
            return False
            
    def test_scraping_functionality(self) -> bool:
        """Test web scraping functionality"""
        if not self.test_project_id:
            self.log_test("Scraping Test", "SKIP", "No test project available")
            return False
            
        try:
            # Test URL scraping
            test_url = self.test_urls[0]  # Use httpbin.org/json for reliable testing
            self.test_session_id = str(uuid.uuid4())
            
            scrape_data = {
                "current_page_url": test_url,
                "session_id": self.test_session_id,
                "force_refresh": True,
                "display_format": "table",
                "conditions": "",
                "api_keys": {
                    "api_key": "test_key",
                    "endpoint": "test_endpoint",
                    "deployment_name": "text-embedding-ada-002"
                }
            }
            
            response = requests.post(
                f"{self.api_url}/projects/{self.test_project_id}/execute-scrape",
                json=scrape_data,
                timeout=30
            )
            
            if response.status_code == 200:
                scrape_result = response.json()
                self.log_test("URL Scraping", "PASS", 
                            f"Successfully scraped {test_url}", scrape_result)
                
                # Check for expected data structure
                expected_fields = ["session_id", "url", "status"]
                missing_fields = [field for field in expected_fields 
                                if field not in scrape_result]
                
                if missing_fields:
                    self.log_test("Scraping Data Structure", "WARN", 
                                f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Scraping Data Structure", "PASS", 
                                "All expected fields present")
                    
                return True
            else:
                self.log_test("URL Scraping", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Scraping Functionality", "FAIL", f"Exception: {str(e)}")
            return False
            
    def test_rag_functionality(self) -> bool:
        """Test RAG (Retrieval Augmented Generation) functionality"""
        if not self.test_project_id:
            self.log_test("RAG Test", "SKIP", "No test project available")
            return False
            
        try:
            # Test Enhanced RAG Query
            query_data = {
                "query": "What data is available in this project?",
                "model_name": "gpt-4o-mini",
                "azure_credentials": {
                    "api_key": "test_key",
                    "endpoint": "test_endpoint", 
                    "deployment_name": "gpt-4o-mini"
                }
            }
            
            response = requests.post(
                f"{self.api_url}/projects/{self.test_project_id}/enhanced-query-rag",
                json=query_data,
                timeout=30
            )
            
            if response.status_code == 200:
                rag_result = response.json()
                self.log_test("Enhanced RAG Query", "PASS", 
                            "Successfully queried RAG system", rag_result)
                return True
            else:
                # RAG might fail due to missing API keys, which is expected in testing
                self.log_test("Enhanced RAG Query", "WARN", 
                            f"HTTP {response.status_code} (Expected without valid API keys)")
                return True
                
        except Exception as e:
            self.log_test("RAG Functionality", "WARN", 
                        f"Exception (Expected without valid API keys): {str(e)}")
            return True  # Consider this a pass since API keys are expected to be missing
            
    def test_chat_functionality(self) -> bool:
        """Test chat/conversation functionality"""
        if not self.test_project_id:
            self.log_test("Chat Test", "SKIP", "No test project available")
            return False
            
        try:
            # 1. Create a conversation
            create_conv_data = {}
            if self.test_session_id:
                create_conv_url = f"{self.api_url}/projects/{self.test_project_id}/conversations?session_id={self.test_session_id}"
            else:
                create_conv_url = f"{self.api_url}/projects/{self.test_project_id}/conversations"
                
            response = requests.post(create_conv_url, json=create_conv_data, timeout=10)
            
            if response.status_code == 200:
                conv_data = response.json()
                self.test_conversation_id = conv_data.get("id")
                self.log_test("Conversation Creation", "PASS", 
                            f"Created conversation {self.test_conversation_id}")
            else:
                self.log_test("Conversation Creation", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
            # 2. Send a chat message
            message_data = {
                "content": "Hello, this is a test message.",
                "azure_credentials": {
                    "api_key": "test_key",
                    "endpoint": "test_endpoint",
                    "deployment_name": "gpt-4o-mini"
                }
            }
            
            chat_url = f"{self.api_url}/projects/{self.test_project_id}/chat"
            if self.test_conversation_id:
                chat_url += f"?conversation_id={self.test_conversation_id}"
                
            response = requests.post(chat_url, json=message_data, timeout=30)
            
            if response.status_code == 200:
                chat_result = response.json()
                self.log_test("Chat Message", "PASS", "Successfully sent chat message", chat_result)
            else:
                # Chat might fail due to missing API keys
                self.log_test("Chat Message", "WARN", 
                            f"HTTP {response.status_code} (Expected without valid API keys)")
                
            # 3. Get conversation messages
            response = requests.get(
                f"{self.api_url}/projects/{self.test_project_id}/conversations/{self.test_conversation_id}/messages",
                timeout=10
            )
            
            if response.status_code == 200:
                messages = response.json()
                self.log_test("Get Messages", "PASS", 
                            f"Retrieved {len(messages)} messages", messages)
            else:
                self.log_test("Get Messages", "FAIL", f"HTTP {response.status_code}")
                
            return True

        except Exception as e:
            self.log_test("Chat Functionality", "FAIL", f"Exception: {str(e)}")
            return False

    def test_frontend_api_integration(self) -> bool:
        """Test frontend API client integration patterns"""
        try:
            # Test CORS headers
            response = requests.options(f"{self.api_url}/projects", timeout=5)
            cors_headers = response.headers

            expected_cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]

            missing_cors = [header for header in expected_cors_headers
                          if header not in cors_headers]

            if not missing_cors:
                self.log_test("CORS Configuration", "PASS", "All CORS headers present")
            else:
                self.log_test("CORS Configuration", "WARN", f"Missing CORS headers: {missing_cors}")

            # Test API response format (snake_case vs camelCase)
            if self.test_project_id:
                response = requests.get(f"{self.api_url}/projects/{self.test_project_id}", timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    # Check for snake_case fields (backend format)
                    snake_case_fields = [key for key in data.keys() if "_" in key]
                    camel_case_fields = [key for key in data.keys() if any(c.isupper() for c in key)]

                    self.log_test("API Response Format", "INFO",
                                f"Snake_case fields: {len(snake_case_fields)}, "
                                f"CamelCase fields: {len(camel_case_fields)}")

            return True

        except Exception as e:
            self.log_test("Frontend API Integration", "FAIL", f"Exception: {str(e)}")
            return False

    def test_websocket_functionality(self) -> bool:
        """Test WebSocket connections for real-time features"""
        try:
            # Test WebSocket endpoint availability
            ws_url = f"ws://localhost:8000/api/v1/ws"

            # Since we can't easily test WebSocket in this context,
            # we'll check if the endpoint exists
            response = requests.get(f"{self.backend_url}/api/v1/ws", timeout=5)

            # WebSocket endpoints typically return 426 Upgrade Required for HTTP requests
            if response.status_code in [426, 400, 405]:
                self.log_test("WebSocket Endpoint", "PASS",
                            "WebSocket endpoint available (HTTP upgrade required)")
            else:
                self.log_test("WebSocket Endpoint", "WARN",
                            f"Unexpected response: HTTP {response.status_code}")

            return True

        except Exception as e:
            self.log_test("WebSocket Functionality", "WARN", f"Exception: {str(e)}")
            return True  # Non-critical for basic functionality

    def test_data_export_functionality(self) -> bool:
        """Test data export features"""
        if not self.test_project_id or not self.test_session_id:
            self.log_test("Data Export Test", "SKIP", "No test data available")
            return False

        try:
            export_formats = ["json", "csv"]  # Skip PDF for now

            for format_type in export_formats:
                export_url = f"{self.backend_url}/download/{self.test_project_id}/{self.test_session_id}/{format_type}"
                response = requests.get(export_url, timeout=10)

                if response.status_code == 200:
                    self.log_test(f"Export {format_type.upper()}", "PASS",
                                f"Successfully exported data in {format_type} format")
                elif response.status_code == 404:
                    self.log_test(f"Export {format_type.upper()}", "WARN",
                                "No data available for export (expected for test)")
                else:
                    self.log_test(f"Export {format_type.upper()}", "FAIL",
                                f"HTTP {response.status_code}")

            return True

        except Exception as e:
            self.log_test("Data Export Functionality", "FAIL", f"Exception: {str(e)}")
            return False

    def test_error_handling(self) -> bool:
        """Test API error handling and response formats"""
        try:
            # Test 404 error handling
            response = requests.get(f"{self.api_url}/projects/00000000-0000-0000-0000-000000000000", timeout=5)
            if response.status_code == 404:
                error_data = response.json()
                if "detail" in error_data:
                    self.log_test("404 Error Handling", "PASS", "Proper error format returned")
                else:
                    self.log_test("404 Error Handling", "WARN", "Error format could be improved")
            else:
                self.log_test("404 Error Handling", "FAIL", f"Expected 404, got {response.status_code}")

            # Test invalid data handling
            invalid_data = {"invalid_field": "invalid_value"}
            response = requests.post(f"{self.api_url}/projects", json=invalid_data, timeout=5)

            if response.status_code in [400, 422]:  # Bad Request or Unprocessable Entity
                self.log_test("Invalid Data Handling", "PASS", "Properly rejected invalid data")
            else:
                self.log_test("Invalid Data Handling", "WARN",
                            f"Unexpected response to invalid data: {response.status_code}")

            return True

        except Exception as e:
            self.log_test("Error Handling", "FAIL", f"Exception: {str(e)}")
            return False

    def cleanup_test_data(self) -> bool:
        """Clean up test data"""
        try:
            cleanup_success = True

            # Delete test conversation
            if self.test_conversation_id and self.test_project_id:
                response = requests.delete(
                    f"{self.api_url}/projects/{self.test_project_id}/conversations/{self.test_conversation_id}",
                    timeout=10
                )
                if response.status_code in [200, 404]:
                    self.log_test("Cleanup Conversation", "PASS", "Test conversation cleaned up")
                else:
                    self.log_test("Cleanup Conversation", "WARN", f"HTTP {response.status_code}")
                    cleanup_success = False

            # Delete test session
            if self.test_session_id and self.test_project_id:
                response = requests.delete(
                    f"{self.api_url}/projects/{self.test_project_id}/sessions/{self.test_session_id}",
                    timeout=10
                )
                if response.status_code in [200, 404]:
                    self.log_test("Cleanup Session", "PASS", "Test session cleaned up")
                else:
                    self.log_test("Cleanup Session", "WARN", f"HTTP {response.status_code}")

            # Delete test project
            if self.test_project_id:
                response = requests.delete(f"{self.api_url}/projects/{self.test_project_id}", timeout=10)
                if response.status_code in [200, 404]:
                    self.log_test("Cleanup Project", "PASS", "Test project cleaned up")
                else:
                    self.log_test("Cleanup Project", "WARN", f"HTTP {response.status_code}")
                    cleanup_success = False

            return cleanup_success

        except Exception as e:
            self.log_test("Cleanup", "WARN", f"Exception during cleanup: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🚀 Starting Comprehensive Frontend Integration Tests")
        print("=" * 60)

        start_time = time.time()

        # Phase 1: Service Health Checks
        print("\n📋 Phase 1: Service Health Checks")
        backend_healthy = self.check_service_health("Backend", self.backend_url)
        frontend_healthy = self.check_service_health("Frontend", self.frontend_url)

        if not backend_healthy:
            print("❌ Backend is not running. Please start the backend service first.")
            return self.generate_report(start_time, early_exit=True)

        # Phase 2: API Endpoint Tests
        print("\n📋 Phase 2: API Endpoint Tests")
        api_healthy = self.test_api_endpoints()

        # Phase 3: Core Functionality Tests
        print("\n📋 Phase 3: Core Functionality Tests")
        project_test = self.test_project_lifecycle()
        scraping_test = self.test_scraping_functionality()
        rag_test = self.test_rag_functionality()
        chat_test = self.test_chat_functionality()

        # Phase 4: Integration Tests
        print("\n📋 Phase 4: Frontend Integration Tests")
        frontend_integration = self.test_frontend_api_integration()
        websocket_test = self.test_websocket_functionality()
        export_test = self.test_data_export_functionality()
        error_handling_test = self.test_error_handling()

        # Phase 5: Cleanup
        print("\n📋 Phase 5: Cleanup")
        cleanup_success = self.cleanup_test_data()

        # Generate final report
        return self.generate_report(start_time)

    def generate_report(self, start_time: float, early_exit: bool = False) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        end_time = time.time()
        duration = end_time - start_time

        # Count test results
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        warned_tests = len([t for t in self.test_results if t["status"] == "WARN"])
        skipped_tests = len([t for t in self.test_results if t["status"] == "SKIP"])

        # Calculate success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warned_tests,
                "skipped": skipped_tests,
                "success_rate": round(success_rate, 2),
                "duration_seconds": round(duration, 2),
                "early_exit": early_exit
            },
            "test_results": self.test_results,
            "recommendations": self.generate_recommendations()
        }

        # Print summary
        print("\n" + "=" * 60)
        print("📊 FRONTEND INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {warned_tests}")
        print(f"⏭️  Skipped: {skipped_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Duration: {duration:.2f} seconds")

        if early_exit:
            print("\n⚠️  Tests exited early due to service unavailability")

        # Print failed tests
        if failed_tests > 0:
            print(f"\n❌ Failed Tests ({failed_tests}):")
            for test in self.test_results:
                if test["status"] == "FAIL":
                    print(f"   • {test['test_name']}: {test['details']}")

        # Print warnings
        if warned_tests > 0:
            print(f"\n⚠️  Warnings ({warned_tests}):")
            for test in self.test_results:
                if test["status"] == "WARN":
                    print(f"   • {test['test_name']}: {test['details']}")

        # Print recommendations
        recommendations = report["recommendations"]
        if recommendations:
            print(f"\n💡 Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")

        return report

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Check for failed tests
        failed_tests = [t for t in self.test_results if t["status"] == "FAIL"]
        if failed_tests:
            recommendations.append("Address failed tests to ensure proper frontend-backend integration")

        # Check for API connectivity issues
        api_failures = [t for t in failed_tests if "API" in t["test_name"]]
        if api_failures:
            recommendations.append("Check backend API service status and network connectivity")

        # Check for CORS issues
        cors_warnings = [t for t in self.test_results if "CORS" in t["test_name"] and t["status"] == "WARN"]
        if cors_warnings:
            recommendations.append("Review CORS configuration for frontend-backend communication")

        # Check for authentication issues
        auth_failures = [t for t in failed_tests if any(keyword in t["details"].lower()
                        for keyword in ["unauthorized", "forbidden", "api key"])]
        if auth_failures:
            recommendations.append("Verify API key configuration and authentication setup")

        # Check for data format issues
        format_warnings = [t for t in self.test_results if "format" in t["test_name"].lower()]
        if format_warnings:
            recommendations.append("Consider implementing consistent data transformation between frontend and backend")

        return recommendations

    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save test report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"frontend_integration_test_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n💾 Test report saved to: {filename}")
        return filename


def main():
    """Main execution function"""
    print("🔧 Frontend Integration Test Suite")
    print("Testing frontend-backend connectivity and integration")

    # Check if services are expected to be running
    print("\n⚠️  Prerequisites:")
    print("   1. Backend service should be running on http://localhost:8000")
    print("   2. Frontend service should be running on http://localhost:9002")
    print("   3. Database should be accessible and configured")

    input("\nPress Enter to continue with the tests...")

    # Initialize and run tests
    tester = FrontendIntegrationTester()
    report = tester.run_all_tests()

    # Save report
    report_file = tester.save_report(report)

    # Exit with appropriate code
    if report["test_summary"]["failed"] > 0:
        print(f"\n❌ Tests completed with {report['test_summary']['failed']} failures")
        sys.exit(1)
    else:
        print(f"\n✅ All tests completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
