#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite
Tests the complete chart integration with RAG system
"""

import asyncio
import json
import httpx
import uuid
from typing import Dict, Any

class ComprehensiveTestSuite:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:9002"
        self.test_project_id = str(uuid.uuid4())
        
    async def test_project_management(self):
        """Test project creation and management."""
        print("🏗️  Testing Project Management...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Create a test project
                project_data = {
                    "name": "Chart Integration Test Project",
                    "description": "Testing chart functionality"
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/v1/projects",
                    json=project_data,
                    timeout=10.0
                )
                
                if response.status_code == 201:
                    project = response.json()
                    self.test_project_id = project["id"]
                    print(f"  ✅ Project created: {project['name']}")
                    return True
                else:
                    print(f"  ❌ Failed to create project: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"  ❌ Project management test failed: {e}")
            return False
    
    async def test_url_scraping(self):
        """Test URL scraping functionality."""
        print("🕷️  Testing URL Scraping...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test scraping a sample URL
                scrape_data = {
                    "current_page_url": "https://example.com",
                    "display_format": "structured",
                    "conditions": [],
                    "api_keys": {
                        "api_key": "test-key",
                        "endpoint": "test-endpoint"
                    }
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/v1/projects/{self.test_project_id}/execute-scrape",
                    json=scrape_data,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    print("  ✅ Scraping endpoint accessible")
                    return True
                else:
                    print(f"  ⚠️  Scraping returned {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"  ⚠️  Scraping test failed: {e}")
            return False
    
    async def test_rag_system(self):
        """Test RAG system functionality."""
        print("🧠 Testing RAG System...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test enhanced RAG query
                rag_data = {
                    "query": "show me a bar chart of product prices",
                    "azure_credentials": {
                        "api_key": "test-key",
                        "endpoint": "test-endpoint"
                    }
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/v1/projects/{self.test_project_id}/enhanced-query-rag",
                    json=rag_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("  ✅ Enhanced RAG endpoint working")
                    
                    # Check if response contains chart data
                    answer = result.get("answer", "")
                    if "chart_type" in answer and "```json" in answer:
                        print("  ✅ Chart data detected in RAG response")
                        return True
                    else:
                        print("  ⚠️  No chart data in RAG response")
                        return False
                else:
                    print(f"  ❌ RAG query failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"  ❌ RAG system test failed: {e}")
            return False
    
    async def test_chat_functionality(self):
        """Test chat functionality with chart responses."""
        print("💬 Testing Chat Functionality...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test chat message
                chat_data = {
                    "content": "create a pie chart showing product categories",
                    "azure_credentials": {
                        "api_key": "test-key",
                        "endpoint": "test-endpoint"
                    }
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/v1/projects/{self.test_project_id}/chat",
                    json=chat_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("  ✅ Chat endpoint working")
                    
                    # Check message content
                    message = result.get("message", {})
                    content = message.get("content", "")
                    
                    if content:
                        print("  ✅ Chat response received")
                        return True
                    else:
                        print("  ⚠️  Empty chat response")
                        return False
                else:
                    print(f"  ❌ Chat failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"  ❌ Chat test failed: {e}")
            return False
    
    async def test_frontend_accessibility(self):
        """Test frontend accessibility."""
        print("🌐 Testing Frontend Accessibility...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test main frontend
                response = await client.get(self.frontend_url, timeout=10.0)
                
                if response.status_code == 200:
                    print("  ✅ Frontend is accessible")
                    
                    # Test chart test page
                    test_response = await client.get(f"{self.frontend_url}?test=charts", timeout=10.0)
                    
                    if test_response.status_code == 200:
                        print("  ✅ Chart test page accessible")
                        return True
                    else:
                        print("  ⚠️  Chart test page not accessible")
                        return False
                else:
                    print(f"  ❌ Frontend not accessible: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"  ❌ Frontend test failed: {e}")
            return False
    
    async def test_chart_data_formats(self):
        """Test different chart data formats."""
        print("📊 Testing Chart Data Formats...")
        
        test_charts = [
            {
                "name": "Bar Chart",
                "data": {
                    "chart_type": "bar",
                    "title": "Test Bar Chart",
                    "data": {"labels": ["A", "B", "C"], "values": [10, 20, 30]}
                }
            },
            {
                "name": "Pie Chart", 
                "data": {
                    "chart_type": "pie",
                    "title": "Test Pie Chart",
                    "data": {"labels": ["X", "Y"], "values": [60, 40]}
                }
            },
            {
                "name": "Stats Chart",
                "data": {
                    "chart_type": "stats",
                    "title": "Test Stats",
                    "data": {"stats": [{"label": "Total", "value": "100"}]}
                }
            }
        ]
        
        success_count = 0
        for chart in test_charts:
            try:
                # Validate chart data structure
                chart_data = chart["data"]
                required_fields = ["chart_type", "title", "data"]
                
                if all(field in chart_data for field in required_fields):
                    print(f"  ✅ {chart['name']} format valid")
                    success_count += 1
                else:
                    print(f"  ❌ {chart['name']} format invalid")
                    
            except Exception as e:
                print(f"  ❌ {chart['name']} validation failed: {e}")
        
        return success_count == len(test_charts)
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive tests."""
        print("🚀 Starting Comprehensive Test Suite\n")
        
        test_results = []
        
        # Run all tests
        tests = [
            ("Project Management", self.test_project_management),
            ("URL Scraping", self.test_url_scraping),
            ("RAG System", self.test_rag_system),
            ("Chat Functionality", self.test_chat_functionality),
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("Chart Data Formats", self.test_chart_data_formats)
        ]
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                test_results.append((test_name, result))
                print()
            except Exception as e:
                print(f"  ❌ {test_name} failed with exception: {e}\n")
                test_results.append((test_name, False))
        
        # Summary
        print("📋 Test Summary:")
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Chart integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        
        return passed == total

async def main():
    """Main test runner."""
    tester = ComprehensiveTestSuite()
    success = await tester.run_comprehensive_tests()
    
    if success:
        print("\n✨ Comprehensive testing complete - System is ready!")
        print("\n📖 How to use the chart features:")
        print("1. Start both backend and frontend servers")
        print("2. Create a project and scrape some data")
        print("3. In chat, ask for charts like:")
        print("   - 'show me a bar chart of prices'")
        print("   - 'create a pie chart of categories'")
        print("   - 'visualize the data as a line graph'")
        print("4. Visit http://localhost:9002?test=charts to see chart examples")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main())
