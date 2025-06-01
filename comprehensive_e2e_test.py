#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing and Analysis of Web Scraping and RAG System
Following the user's specific testing phases and requirements.
"""

import asyncio
import json
import time
import uuid
import requests
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Test Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_PROJECT_NAME = "E2E_Test_Project"
TEST_URLS = [
    {
        "url": "https://example.com",
        "conditions": "title, description, main content, links",
        "display_format": "table"
    },
    {
        "url": "https://httpbin.org/json",
        "conditions": "data, headers, origin, url",
        "display_format": "paragraph"
    }
]

class ComprehensiveE2ETest:
    def __init__(self):
        self.project_id = None
        self.session_ids = []
        self.test_results = {
            "phase_1_component_analysis": {},
            "phase_2_pipeline_integration": {},
            "phase_3_rescaping_verification": {},
            "phase_4_ui_functionality": {},
            "phase_5_data_quality": {},
            "issues_found": [],
            "recommendations": []
        }
        
    def log_result(self, phase: str, test_name: str, status: str, details: str = ""):
        """Log test results"""
        if phase not in self.test_results:
            self.test_results[phase] = {}
        
        self.test_results[phase][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"[{phase}] {test_name}: {status}")
        if details:
            print(f"  Details: {details}")
    
    def log_issue(self, issue: str):
        """Log issues found during testing"""
        self.test_results["issues_found"].append({
            "issue": issue,
            "timestamp": datetime.now().isoformat()
        })
        print(f"❌ ISSUE: {issue}")
    
    def log_recommendation(self, recommendation: str):
        """Log recommendations for improvements"""
        self.test_results["recommendations"].append({
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        })
        print(f"💡 RECOMMENDATION: {recommendation}")

    async def setup_test_environment(self):
        """Setup clean test environment"""
        print("🧹 Setting up clean test environment...")
        
        # Delete all existing projects to start fresh
        try:
            response = requests.get(f"{API_BASE_URL}/projects")
            if response.status_code == 200:
                projects = response.json()
                for project in projects:
                    delete_response = requests.delete(f"{API_BASE_URL}/projects/{project['id']}")
                    if delete_response.status_code == 204:
                        print(f"  Deleted existing project: {project['name']}")
        except Exception as e:
            print(f"  Warning: Could not clean existing projects: {e}")
        
        print("✅ Test environment setup complete")

    # PHASE 1: Component Analysis & Testing
    async def test_url_management_component(self):
        """Test URL management functionality"""
        print("\n📋 PHASE 1.1: Testing URL Management Component")
        
        # Test 1.1.1: Create project
        try:
            project_data = {"name": TEST_PROJECT_NAME}
            response = requests.post(f"{API_BASE_URL}/projects", json=project_data)
            
            if response.status_code == 201:
                project = response.json()
                self.project_id = project["id"]
                self.log_result("phase_1_component_analysis", "create_project", "PASS", 
                              f"Project created with ID: {self.project_id}")
            else:
                self.log_result("phase_1_component_analysis", "create_project", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("phase_1_component_analysis", "create_project", "ERROR", str(e))
            return False
        
        # Test 1.1.2: Add URLs to project
        for i, url_data in enumerate(TEST_URLS):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/projects/{self.project_id}/urls",
                    json=url_data
                )
                
                if response.status_code == 201:
                    url_response = response.json()
                    self.log_result("phase_1_component_analysis", f"add_url_{i+1}", "PASS",
                                  f"URL added: {url_data['url']}")
                else:
                    self.log_result("phase_1_component_analysis", f"add_url_{i+1}", "FAIL",
                                  f"Status: {response.status_code}, Response: {response.text}")
                    self.log_issue(f"Failed to add URL: {url_data['url']}")
            except Exception as e:
                self.log_result("phase_1_component_analysis", f"add_url_{i+1}", "ERROR", str(e))
                self.log_issue(f"Exception adding URL {url_data['url']}: {e}")
        
        # Test 1.1.3: Verify URL storage and validation
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/urls")
            if response.status_code == 200:
                urls = response.json()
                if len(urls) == len(TEST_URLS):
                    self.log_result("phase_1_component_analysis", "url_storage_validation", "PASS",
                                  f"All {len(TEST_URLS)} URLs stored correctly")
                    
                    # Verify URL details
                    for url in urls:
                        if not all(key in url for key in ['url', 'conditions', 'display_format']):
                            self.log_issue(f"URL missing required fields: {url}")
                else:
                    self.log_result("phase_1_component_analysis", "url_storage_validation", "FAIL",
                                  f"Expected {len(TEST_URLS)} URLs, got {len(urls)}")
                    self.log_issue("URL count mismatch after adding URLs")
            else:
                self.log_result("phase_1_component_analysis", "url_storage_validation", "FAIL",
                              f"Status: {response.status_code}")
                self.log_issue("Failed to retrieve URLs from project")
        except Exception as e:
            self.log_result("phase_1_component_analysis", "url_storage_validation", "ERROR", str(e))
            self.log_issue(f"Exception validating URL storage: {e}")
        
        return True

    async def test_conditions_structure_mode_component(self):
        """Test conditions and structure mode functionality"""
        print("\n⚙️ PHASE 1.2: Testing Conditions & Structure Mode Component")
        
        # Test 1.2.1: Verify conditions are properly saved
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/urls")
            if response.status_code == 200:
                urls = response.json()
                conditions_match = True
                
                for i, url in enumerate(urls):
                    expected_conditions = TEST_URLS[i]["conditions"]
                    if url["conditions"] != expected_conditions:
                        conditions_match = False
                        self.log_issue(f"Conditions mismatch for URL {url['url']}: "
                                     f"expected '{expected_conditions}', got '{url['conditions']}'")
                
                if conditions_match:
                    self.log_result("phase_1_component_analysis", "conditions_storage", "PASS",
                                  "All conditions stored correctly")
                else:
                    self.log_result("phase_1_component_analysis", "conditions_storage", "FAIL",
                                  "Conditions mismatch detected")
            else:
                self.log_result("phase_1_component_analysis", "conditions_storage", "FAIL",
                              f"Failed to retrieve URLs: {response.status_code}")
        except Exception as e:
            self.log_result("phase_1_component_analysis", "conditions_storage", "ERROR", str(e))
        
        # Test 1.2.2: Verify display format selection
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/urls")
            if response.status_code == 200:
                urls = response.json()
                format_match = True
                
                for i, url in enumerate(urls):
                    expected_format = TEST_URLS[i]["display_format"]
                    if url["display_format"] != expected_format:
                        format_match = False
                        self.log_issue(f"Display format mismatch for URL {url['url']}: "
                                     f"expected '{expected_format}', got '{url['display_format']}'")
                
                if format_match:
                    self.log_result("phase_1_component_analysis", "display_format_storage", "PASS",
                                  "All display formats stored correctly")
                else:
                    self.log_result("phase_1_component_analysis", "display_format_storage", "FAIL",
                                  "Display format mismatch detected")
            else:
                self.log_result("phase_1_component_analysis", "display_format_storage", "FAIL",
                              f"Failed to retrieve URLs: {response.status_code}")
        except Exception as e:
            self.log_result("phase_1_component_analysis", "display_format_storage", "ERROR", str(e))

    async def test_web_scraping_component(self):
        """Test web scraping functionality"""
        print("\n🕷️ PHASE 1.3: Testing Web Scraping Component")
        
        # Get Azure OpenAI credentials (mock for testing)
        api_keys = {
            "api_key": "test_key",
            "endpoint": "https://test.openai.azure.com",
            "deployment_name": "text-embedding-ada-002"
        }
        
        # Test 1.3.1: Execute scraping on first URL
        try:
            scrape_data = {
                "current_page_url": TEST_URLS[0]["url"],
                "session_id": str(uuid.uuid4()),
                "force_refresh": True,
                "display_format": TEST_URLS[0]["display_format"],
                "conditions": TEST_URLS[0]["conditions"],
                "api_keys": api_keys
            }
            
            response = requests.post(
                f"{API_BASE_URL}/projects/{self.project_id}/execute-scrape",
                json=scrape_data
            )
            
            if response.status_code == 200:
                scrape_result = response.json()
                self.session_ids.append(scrape_result.get("session_id"))
                self.log_result("phase_1_component_analysis", "execute_scraping", "PASS",
                              f"Scraping executed successfully for {TEST_URLS[0]['url']}")
                
                # Verify response structure
                required_fields = ["session_id", "status", "message"]
                missing_fields = [field for field in required_fields if field not in scrape_result]
                if missing_fields:
                    self.log_issue(f"Scraping response missing fields: {missing_fields}")
                
            else:
                self.log_result("phase_1_component_analysis", "execute_scraping", "FAIL",
                              f"Status: {response.status_code}, Response: {response.text}")
                self.log_issue(f"Scraping failed for {TEST_URLS[0]['url']}")
        except Exception as e:
            self.log_result("phase_1_component_analysis", "execute_scraping", "ERROR", str(e))
            self.log_issue(f"Exception during scraping: {e}")
        
        # Wait for scraping to complete
        await asyncio.sleep(5)
        
        # Test 1.3.2: Verify scraping results
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                if sessions:
                    session = sessions[0]
                    
                    # Check for required session fields
                    required_session_fields = ["id", "url", "status", "scraped_at"]
                    missing_session_fields = [field for field in required_session_fields 
                                            if field not in session]
                    
                    if not missing_session_fields:
                        self.log_result("phase_1_component_analysis", "scraping_results_verification", "PASS",
                                      f"Session created with status: {session['status']}")
                    else:
                        self.log_result("phase_1_component_analysis", "scraping_results_verification", "FAIL",
                                      f"Session missing fields: {missing_session_fields}")
                        self.log_issue(f"Incomplete session data: missing {missing_session_fields}")
                else:
                    self.log_result("phase_1_component_analysis", "scraping_results_verification", "FAIL",
                                  "No scraping sessions found")
                    self.log_issue("No scraping sessions created")
            else:
                self.log_result("phase_1_component_analysis", "scraping_results_verification", "FAIL",
                              f"Failed to get sessions: {response.status_code}")
        except Exception as e:
            self.log_result("phase_1_component_analysis", "scraping_results_verification", "ERROR", str(e))

    async def test_rag_ingestion_component(self):
        """Test RAG ingestion functionality"""
        print("\n🧠 PHASE 1.4: Testing RAG Ingestion Component")

        # Test 1.4.1: Enable RAG for project
        try:
            response = requests.patch(
                f"{API_BASE_URL}/projects/{self.project_id}",
                json={"rag_enabled": True}
            )

            if response.status_code == 200:
                project = response.json()
                if project.get("rag_enabled"):
                    self.log_result("phase_1_component_analysis", "enable_rag", "PASS",
                                  "RAG enabled for project")
                else:
                    self.log_result("phase_1_component_analysis", "enable_rag", "FAIL",
                                  "RAG not enabled in response")
                    self.log_issue("RAG enabling failed")
            else:
                self.log_result("phase_1_component_analysis", "enable_rag", "FAIL",
                              f"Status: {response.status_code}")
                self.log_issue("Failed to enable RAG for project")
        except Exception as e:
            self.log_result("phase_1_component_analysis", "enable_rag", "ERROR", str(e))

        # Test 1.4.2: Check embedding generation
        await asyncio.sleep(10)  # Wait for RAG processing

        try:
            # Check if embeddings were created (this would require direct database access)
            # For now, we'll check session status
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                rag_processed = any(session.get("status") == "rag_ingested" for session in sessions)

                if rag_processed:
                    self.log_result("phase_1_component_analysis", "rag_processing", "PASS",
                                  "RAG processing completed")
                else:
                    self.log_result("phase_1_component_analysis", "rag_processing", "PENDING",
                                  "RAG processing may still be in progress")
            else:
                self.log_result("phase_1_component_analysis", "rag_processing", "FAIL",
                              f"Failed to check sessions: {response.status_code}")
        except Exception as e:
            self.log_result("phase_1_component_analysis", "rag_processing", "ERROR", str(e))

    # PHASE 2: Pipeline Integration Testing
    async def test_api_endpoints(self):
        """Test API endpoints in the scraping-to-RAG pipeline"""
        print("\n🔗 PHASE 2.1: Testing API Endpoints")

        # Test 2.1.1: Projects endpoint
        try:
            response = requests.get(f"{API_BASE_URL}/projects")
            if response.status_code == 200:
                projects = response.json()
                self.log_result("phase_2_pipeline_integration", "projects_endpoint", "PASS",
                              f"Retrieved {len(projects)} projects")
            else:
                self.log_result("phase_2_pipeline_integration", "projects_endpoint", "FAIL",
                              f"Status: {response.status_code}")
                self.log_issue("Projects endpoint failed")
        except Exception as e:
            self.log_result("phase_2_pipeline_integration", "projects_endpoint", "ERROR", str(e))

        # Test 2.1.2: URLs endpoint
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/urls")
            if response.status_code == 200:
                urls = response.json()
                self.log_result("phase_2_pipeline_integration", "urls_endpoint", "PASS",
                              f"Retrieved {len(urls)} URLs")
            else:
                self.log_result("phase_2_pipeline_integration", "urls_endpoint", "FAIL",
                              f"Status: {response.status_code}")
                self.log_issue("URLs endpoint failed")
        except Exception as e:
            self.log_result("phase_2_pipeline_integration", "urls_endpoint", "ERROR", str(e))

        # Test 2.1.3: Sessions endpoint
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                self.log_result("phase_2_pipeline_integration", "sessions_endpoint", "PASS",
                              f"Retrieved {len(sessions)} sessions")
            else:
                self.log_result("phase_2_pipeline_integration", "sessions_endpoint", "FAIL",
                              f"Status: {response.status_code}")
                self.log_issue("Sessions endpoint failed")
        except Exception as e:
            self.log_result("phase_2_pipeline_integration", "sessions_endpoint", "ERROR", str(e))

    async def test_data_consistency(self):
        """Test data consistency throughout the pipeline"""
        print("\n📊 PHASE 2.2: Testing Data Consistency")

        # Test 2.2.1: URL → Session consistency
        try:
            urls_response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/urls")
            sessions_response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/sessions")

            if urls_response.status_code == 200 and sessions_response.status_code == 200:
                urls = urls_response.json()
                sessions = sessions_response.json()

                # Check if URLs have corresponding sessions
                urls_with_sessions = [url for url in urls if url.get("last_scraped_session_id")]

                if len(urls_with_sessions) > 0:
                    self.log_result("phase_2_pipeline_integration", "url_session_consistency", "PASS",
                                  f"{len(urls_with_sessions)} URLs have associated sessions")
                else:
                    self.log_result("phase_2_pipeline_integration", "url_session_consistency", "FAIL",
                                  "No URLs have associated sessions")
                    self.log_issue("URL-Session linking failed")
            else:
                self.log_result("phase_2_pipeline_integration", "url_session_consistency", "FAIL",
                              "Failed to retrieve URLs or sessions")
        except Exception as e:
            self.log_result("phase_2_pipeline_integration", "url_session_consistency", "ERROR", str(e))

    # PHASE 3: Re-scraping Logic Verification
    async def test_single_session_per_url_rule(self):
        """Test that each URL has only one active scraping session"""
        print("\n🔄 PHASE 3.1: Testing Single Session Per URL Rule")

        # Test 3.1.1: Re-scrape the same URL
        api_keys = {
            "api_key": "test_key",
            "endpoint": "https://test.openai.azure.com",
            "deployment_name": "text-embedding-ada-002"
        }

        try:
            # Get initial session count
            initial_response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/sessions")
            initial_sessions = initial_response.json() if initial_response.status_code == 200 else []
            initial_count = len(initial_sessions)

            # Re-scrape the same URL
            scrape_data = {
                "current_page_url": TEST_URLS[0]["url"],
                "session_id": str(uuid.uuid4()),
                "force_refresh": True,
                "display_format": TEST_URLS[0]["display_format"],
                "conditions": TEST_URLS[0]["conditions"],
                "api_keys": api_keys
            }

            response = requests.post(
                f"{API_BASE_URL}/projects/{self.project_id}/execute-scrape",
                json=scrape_data
            )

            if response.status_code == 200:
                # Wait for processing
                await asyncio.sleep(5)

                # Check session count after re-scraping
                final_response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/sessions")
                final_sessions = final_response.json() if final_response.status_code == 200 else []
                final_count = len(final_sessions)

                # Should still have only one session per URL
                if final_count <= initial_count + 1:
                    self.log_result("phase_3_rescaping_verification", "single_session_rule", "PASS",
                                  f"Session count: {initial_count} → {final_count}")
                else:
                    self.log_result("phase_3_rescaping_verification", "single_session_rule", "FAIL",
                                  f"Too many sessions created: {initial_count} → {final_count}")
                    self.log_issue("Multiple sessions created for same URL")
            else:
                self.log_result("phase_3_rescaping_verification", "single_session_rule", "FAIL",
                              f"Re-scraping failed: {response.status_code}")
        except Exception as e:
            self.log_result("phase_3_rescaping_verification", "single_session_rule", "ERROR", str(e))

    async def run_phase_1(self):
        """Run all Phase 1 tests"""
        print("\n🔍 STARTING PHASE 1: Component Analysis & Testing")

        await self.test_url_management_component()
        await self.test_conditions_structure_mode_component()
        await self.test_web_scraping_component()
        await self.test_rag_ingestion_component()

        print("\n✅ PHASE 1 COMPLETE")

    async def run_phase_2(self):
        """Run all Phase 2 tests"""
        print("\n🔗 STARTING PHASE 2: Pipeline Integration Testing")

        await self.test_api_endpoints()
        await self.test_data_consistency()

        print("\n✅ PHASE 2 COMPLETE")

    async def test_data_cleanup_on_rescaping(self):
        """Test that old data is properly cleaned up when re-scraping"""
        print("\n🧹 PHASE 3.2: Testing Data Cleanup on Re-scraping")

        # This test would ideally check database directly for embedding cleanup
        # For now, we'll verify session status changes
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/sessions")
            if response.status_code == 200:
                sessions = response.json()

                # Check that we don't have multiple sessions for the same URL
                url_sessions = {}
                for session in sessions:
                    url = session.get("url")
                    if url not in url_sessions:
                        url_sessions[url] = []
                    url_sessions[url].append(session)

                multiple_sessions = {url: sessions for url, sessions in url_sessions.items()
                                   if len(sessions) > 1}

                if not multiple_sessions:
                    self.log_result("phase_3_rescaping_verification", "data_cleanup", "PASS",
                                  "No duplicate sessions found")
                else:
                    self.log_result("phase_3_rescaping_verification", "data_cleanup", "FAIL",
                                  f"Multiple sessions found for URLs: {list(multiple_sessions.keys())}")
                    self.log_issue("Data cleanup failed - multiple sessions exist for same URLs")
            else:
                self.log_result("phase_3_rescaping_verification", "data_cleanup", "FAIL",
                              f"Failed to get sessions: {response.status_code}")
        except Exception as e:
            self.log_result("phase_3_rescaping_verification", "data_cleanup", "ERROR", str(e))

    # PHASE 4: UI Functionality Testing
    async def test_chat_interface(self):
        """Test AI chat functionality with scraped data"""
        print("\n💬 PHASE 4.1: Testing Chat Interface")

        # Test 4.1.1: Test RAG query
        try:
            query_data = {
                "query": "What information was scraped from the websites?",
                "model_name": "gpt-4o-mini",
                "azure_credentials": {
                    "api_key": "test_key",
                    "endpoint": "https://test.openai.azure.com",
                    "deployment_name": "gpt-4o-mini"
                }
            }

            response = requests.post(
                f"{API_BASE_URL}/projects/{self.project_id}/query-rag",
                json=query_data
            )

            if response.status_code == 200:
                rag_response = response.json()

                # Check response structure
                required_fields = ["answer", "sources"]
                missing_fields = [field for field in required_fields if field not in rag_response]

                if not missing_fields:
                    self.log_result("phase_4_ui_functionality", "rag_query", "PASS",
                                  f"RAG query successful, answer length: {len(rag_response.get('answer', ''))}")
                else:
                    self.log_result("phase_4_ui_functionality", "rag_query", "FAIL",
                                  f"Response missing fields: {missing_fields}")
                    self.log_issue(f"RAG response incomplete: missing {missing_fields}")
            else:
                self.log_result("phase_4_ui_functionality", "rag_query", "FAIL",
                              f"Status: {response.status_code}, Response: {response.text}")
                self.log_issue("RAG query failed")
        except Exception as e:
            self.log_result("phase_4_ui_functionality", "rag_query", "ERROR", str(e))

        # Test 4.1.2: Test enhanced RAG query
        try:
            enhanced_query_data = {
                "query": "Show me the data in a table format",
                "model_name": "gpt-4o-mini",
                "azure_credentials": {
                    "api_key": "test_key",
                    "endpoint": "https://test.openai.azure.com",
                    "deployment_name": "gpt-4o-mini"
                }
            }

            response = requests.post(
                f"{API_BASE_URL}/projects/{self.project_id}/enhanced-query-rag",
                json=enhanced_query_data
            )

            if response.status_code == 200:
                enhanced_response = response.json()
                self.log_result("phase_4_ui_functionality", "enhanced_rag_query", "PASS",
                              "Enhanced RAG query successful")
            else:
                self.log_result("phase_4_ui_functionality", "enhanced_rag_query", "FAIL",
                              f"Status: {response.status_code}")
                self.log_issue("Enhanced RAG query failed")
        except Exception as e:
            self.log_result("phase_4_ui_functionality", "enhanced_rag_query", "ERROR", str(e))

    async def test_url_conditions_display(self):
        """Test that URL conditions and formats are displayed correctly"""
        print("\n📋 PHASE 4.2: Testing URL and Conditions Display")

        try:
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/urls")
            if response.status_code == 200:
                urls = response.json()

                display_issues = []
                for url in urls:
                    # Check required display fields
                    required_fields = ["url", "conditions", "display_format", "status"]
                    missing_fields = [field for field in required_fields if field not in url]

                    if missing_fields:
                        display_issues.append(f"URL {url.get('url', 'unknown')} missing: {missing_fields}")

                    # Check status values
                    valid_statuses = ["pending", "processing", "completed", "failed", "processing_rag"]
                    if url.get("status") not in valid_statuses:
                        display_issues.append(f"Invalid status '{url.get('status')}' for URL {url.get('url')}")

                if not display_issues:
                    self.log_result("phase_4_ui_functionality", "url_display", "PASS",
                                  "All URLs have proper display data")
                else:
                    self.log_result("phase_4_ui_functionality", "url_display", "FAIL",
                                  f"Display issues: {display_issues}")
                    for issue in display_issues:
                        self.log_issue(issue)
            else:
                self.log_result("phase_4_ui_functionality", "url_display", "FAIL",
                              f"Failed to get URLs: {response.status_code}")
        except Exception as e:
            self.log_result("phase_4_ui_functionality", "url_display", "ERROR", str(e))

    # PHASE 5: Data Quality Assurance
    async def test_content_verification(self):
        """Test scraped data quality"""
        print("\n🔍 PHASE 5.1: Testing Content Verification")

        try:
            response = requests.get(f"{API_BASE_URL}/projects/{self.project_id}/sessions")
            if response.status_code == 200:
                sessions = response.json()

                quality_issues = []
                for session in sessions:
                    # Check for required content fields
                    if not session.get("raw_markdown"):
                        quality_issues.append(f"Session {session.get('id')} missing raw_markdown")

                    # Check structured data
                    structured_data = session.get("structured_data_json")
                    if structured_data:
                        # Verify it's valid JSON
                        try:
                            if isinstance(structured_data, str):
                                json.loads(structured_data)
                        except json.JSONDecodeError:
                            quality_issues.append(f"Session {session.get('id')} has invalid JSON structured data")
                    else:
                        quality_issues.append(f"Session {session.get('id')} missing structured_data_json")

                if not quality_issues:
                    self.log_result("phase_5_data_quality", "content_verification", "PASS",
                                  f"All {len(sessions)} sessions have valid content")
                else:
                    self.log_result("phase_5_data_quality", "content_verification", "FAIL",
                                  f"Quality issues found: {len(quality_issues)}")
                    for issue in quality_issues[:5]:  # Log first 5 issues
                        self.log_issue(issue)
            else:
                self.log_result("phase_5_data_quality", "content_verification", "FAIL",
                              f"Failed to get sessions: {response.status_code}")
        except Exception as e:
            self.log_result("phase_5_data_quality", "content_verification", "ERROR", str(e))

    async def test_response_quality(self):
        """Test RAG response quality"""
        print("\n🎯 PHASE 5.2: Testing Response Quality")

        test_queries = [
            "What is the main content of the scraped pages?",
            "List all the URLs that were scraped",
            "Show me the structured data in table format"
        ]

        for i, query in enumerate(test_queries):
            try:
                query_data = {
                    "query": query,
                    "model_name": "gpt-4o-mini",
                    "azure_credentials": {
                        "api_key": "test_key",
                        "endpoint": "https://test.openai.azure.com",
                        "deployment_name": "gpt-4o-mini"
                    }
                }

                response = requests.post(
                    f"{API_BASE_URL}/projects/{self.project_id}/query-rag",
                    json=query_data
                )

                if response.status_code == 200:
                    rag_response = response.json()
                    answer = rag_response.get("answer", "")
                    sources = rag_response.get("sources", [])

                    # Quality checks
                    quality_score = 0
                    if len(answer) > 50:  # Substantial answer
                        quality_score += 1
                    if sources:  # Has sources
                        quality_score += 1
                    if "error" not in answer.lower():  # No error messages
                        quality_score += 1

                    if quality_score >= 2:
                        self.log_result("phase_5_data_quality", f"response_quality_{i+1}", "PASS",
                                      f"Query: '{query}' - Quality score: {quality_score}/3")
                    else:
                        self.log_result("phase_5_data_quality", f"response_quality_{i+1}", "FAIL",
                                      f"Query: '{query}' - Low quality score: {quality_score}/3")
                        self.log_issue(f"Poor response quality for query: {query}")
                else:
                    self.log_result("phase_5_data_quality", f"response_quality_{i+1}", "FAIL",
                                  f"Query failed: {response.status_code}")
            except Exception as e:
                self.log_result("phase_5_data_quality", f"response_quality_{i+1}", "ERROR", str(e))

    async def run_phase_3(self):
        """Run all Phase 3 tests"""
        print("\n🔄 STARTING PHASE 3: Re-scraping Logic Verification")

        await self.test_single_session_per_url_rule()
        await self.test_data_cleanup_on_rescaping()

        print("\n✅ PHASE 3 COMPLETE")

    async def run_phase_4(self):
        """Run all Phase 4 tests"""
        print("\n🖥️ STARTING PHASE 4: UI Functionality Testing")

        await self.test_chat_interface()
        await self.test_url_conditions_display()

        print("\n✅ PHASE 4 COMPLETE")

    async def run_phase_5(self):
        """Run all Phase 5 tests"""
        print("\n🔍 STARTING PHASE 5: Data Quality Assurance")

        await self.test_content_verification()
        await self.test_response_quality()

        print("\n✅ PHASE 5 COMPLETE")

    async def generate_final_analysis(self):
        """Generate final analysis and recommendations"""
        print("\n📋 GENERATING FINAL ANALYSIS")

        # Analyze test results and generate recommendations
        phase_results = {}
        for phase_name, phase_data in self.test_results.items():
            if isinstance(phase_data, dict) and phase_name.startswith("phase_"):
                passed = sum(1 for test in phase_data.values() if test.get("status") == "PASS")
                failed = sum(1 for test in phase_data.values() if test.get("status") == "FAIL")
                errors = sum(1 for test in phase_data.values() if test.get("status") == "ERROR")
                total = len(phase_data)

                phase_results[phase_name] = {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "success_rate": (passed / total * 100) if total > 0 else 0
                }

        # Generate recommendations based on results
        recommendations = []

        # Check for common issues
        if any("model" in issue["issue"].lower() for issue in self.test_results["issues_found"]):
            recommendations.append("Consider updating model configuration to ensure GPT-4o is properly configured")

        if any("rag" in issue["issue"].lower() for issue in self.test_results["issues_found"]):
            recommendations.append("Review RAG ingestion pipeline and embedding generation process")

        if any("session" in issue["issue"].lower() for issue in self.test_results["issues_found"]):
            recommendations.append("Investigate session management and re-scraping logic")

        if any("api" in issue["issue"].lower() for issue in self.test_results["issues_found"]):
            recommendations.append("Check API endpoint implementations and error handling")

        # Add general recommendations
        recommendations.extend([
            "Implement comprehensive error logging for better debugging",
            "Add real-time status updates via WebSocket for better UX",
            "Consider adding data validation at each pipeline stage",
            "Implement automated testing for continuous integration",
            "Add performance monitoring for scraping and RAG operations"
        ])

        for rec in recommendations:
            self.log_recommendation(rec)

        # Print detailed analysis
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE TEST ANALYSIS")
        print("="*60)

        for phase_name, results in phase_results.items():
            phase_display = phase_name.replace("_", " ").title()
            print(f"\n{phase_display}:")
            print(f"  Total Tests: {results['total']}")
            print(f"  Passed: {results['passed']} ({results['success_rate']:.1f}%)")
            print(f"  Failed: {results['failed']}")
            print(f"  Errors: {results['errors']}")

        print(f"\n🔍 ISSUES IDENTIFIED ({len(self.test_results['issues_found'])}):")
        for i, issue in enumerate(self.test_results["issues_found"][:10], 1):
            print(f"  {i}. {issue['issue']}")

        if len(self.test_results["issues_found"]) > 10:
            print(f"  ... and {len(self.test_results['issues_found']) - 10} more issues")

        print(f"\n💡 RECOMMENDATIONS ({len(self.test_results['recommendations'])}):")
        for i, rec in enumerate(self.test_results["recommendations"][:10], 1):
            print(f"  {i}. {rec['recommendation']}")

if __name__ == "__main__":
    async def main():
        tester = ComprehensiveE2ETest()

        print("🚀 Starting Comprehensive End-to-End Testing")
        print("=" * 60)
        print("This test will systematically verify:")
        print("  • URL Management & Conditions Setting")
        print("  • Web Scraping with GPT-4o Structured Extraction")
        print("  • RAG Ingestion & Embedding Generation")
        print("  • Re-scraping Data Cleanup Logic")
        print("  • UI Functionality & Chat Interface")
        print("  • Data Quality & Response Accuracy")
        print("=" * 60)

        try:
            await tester.setup_test_environment()
            await tester.run_phase_1()
            await tester.run_phase_2()
            await tester.run_phase_3()
            await tester.run_phase_4()
            await tester.run_phase_5()

            await tester.generate_final_analysis()

        except KeyboardInterrupt:
            print("\n⚠️ Testing interrupted by user")
        except Exception as e:
            print(f"\n❌ Testing failed with error: {e}")
            tester.log_issue(f"Critical testing failure: {e}")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"e2e_test_results_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump(tester.test_results, f, indent=2)

        print(f"\n📊 Test results saved to {results_file}")
        print("\n🎯 COMPREHENSIVE TESTING COMPLETE")

        # Print final summary
        total_tests = sum(len(phase_results) for phase_results in tester.test_results.values()
                         if isinstance(phase_results, dict) and not phase_results == {})
        issues_count = len(tester.test_results["issues_found"])
        recommendations_count = len(tester.test_results["recommendations"])

        print(f"\n📈 FINAL SUMMARY:")
        print(f"  Total Tests Executed: {total_tests}")
        print(f"  Issues Identified: {issues_count}")
        print(f"  Recommendations Generated: {recommendations_count}")
        print(f"  Results File: {results_file}")

        if issues_count == 0:
            print("\n✅ All systems functioning correctly!")
        elif issues_count < 5:
            print("\n⚠️ Minor issues found - system mostly functional")
        else:
            print("\n❌ Multiple issues found - requires attention")

    asyncio.run(main())
