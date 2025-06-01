#!/usr/bin/env python3
"""
Comprehensive test script for chart integration with RAG system.
Tests chart generation, data visualization, and RAG responses.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, List
import httpx

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from app.services.enhanced_rag_service import EnhancedRAGService

class ChartIntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_project_id = "test-project-123"
        self.enhanced_rag = EnhancedRAGService()
        
    async def test_chart_detection(self):
        """Test chart keyword detection in queries."""
        print("🔍 Testing Chart Detection...")
        
        chart_queries = [
            "show me a bar chart of product prices",
            "create a pie chart of categories",
            "visualize the data as a line graph",
            "plot the sales data",
            "generate a chart showing price distribution"
        ]
        
        for query in chart_queries:
            intent = self.enhanced_rag._analyze_query_intent(query)
            response_format = self.enhanced_rag._determine_response_format(query, intent)
            
            print(f"  Query: '{query}'")
            print(f"  Format: {response_format}")
            print(f"  Intent: {intent}")
            
            if response_format == 'chart':
                print("  ✅ Chart format detected correctly")
            else:
                print("  ❌ Chart format not detected")
            print()
    
    async def test_chart_data_generation(self):
        """Test chart data generation from sample data."""
        print("📊 Testing Chart Data Generation...")
        
        # Sample scraped data
        sample_context = """
        === AVAILABLE DATA ===
        
        --- Data Source 1 ---
        Product: iPhone 15 Pro, Price: $999, Category: Smartphones
        Product: Samsung Galaxy S24, Price: $899, Category: Smartphones  
        Product: Google Pixel 8, Price: $699, Category: Smartphones
        Product: iPad Pro, Price: $1099, Category: Tablets
        Product: Surface Pro, Price: $1299, Category: Tablets
        """
        
        test_cases = [
            {
                "query": "show me a bar chart of product prices",
                "expected_type": "bar"
            },
            {
                "query": "create a pie chart of product categories", 
                "expected_type": "pie"
            },
            {
                "query": "show statistics about the products",
                "expected_type": "stats"
            }
        ]
        
        for test_case in test_cases:
            print(f"  Testing: {test_case['query']}")
            
            intent = self.enhanced_rag._analyze_query_intent(test_case['query'])
            response_format = self.enhanced_rag._determine_response_format(test_case['query'], intent)
            
            # Build system prompt for chart generation
            system_prompt = self.enhanced_rag._build_system_prompt(intent, response_format)
            user_prompt = self.enhanced_rag._build_user_prompt(test_case['query'], sample_context, response_format)
            
            print(f"    Response format: {response_format}")
            print(f"    Expected chart type: {test_case['expected_type']}")
            
            if response_format == 'chart':
                print("    ✅ Chart format selected")
                print(f"    System prompt includes chart instructions: {'chart' in system_prompt.lower()}")
            else:
                print("    ❌ Chart format not selected")
            print()
    
    async def test_chart_json_parsing(self):
        """Test chart JSON parsing and validation."""
        print("🔧 Testing Chart JSON Parsing...")
        
        # Sample chart responses
        test_responses = [
            {
                "name": "Valid Bar Chart",
                "response": '''```json
{
  "chart_type": "bar",
  "title": "Product Prices",
  "description": "Comparison of product prices",
  "data": {
    "labels": ["iPhone 15 Pro", "Samsung Galaxy S24", "Google Pixel 8"],
    "values": [999, 899, 699]
  }
}
```''',
                "should_parse": True
            },
            {
                "name": "Valid Pie Chart",
                "response": '''```json
{
  "chart_type": "pie", 
  "title": "Product Categories",
  "data": {
    "labels": ["Smartphones", "Tablets"],
    "values": [3, 2]
  }
}
```''',
                "should_parse": True
            },
            {
                "name": "Invalid JSON",
                "response": "This is just regular text without chart data",
                "should_parse": False
            }
        ]
        
        for test in test_responses:
            print(f"  Testing: {test['name']}")
            
            # Test chart formatting
            formatted = self.enhanced_rag._enhance_chart_formatting(test['response'])
            
            # Try to extract chart data (simulate MessageRenderer logic)
            try:
                import re
                json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', formatted)
                if json_match:
                    chart_data = json.loads(json_match.group(1))
                    has_required_fields = all(field in chart_data for field in ['chart_type', 'title', 'data'])
                    
                    if test['should_parse']:
                        if has_required_fields:
                            print(f"    ✅ Successfully parsed chart data")
                            print(f"    Chart type: {chart_data.get('chart_type')}")
                            print(f"    Title: {chart_data.get('title')}")
                        else:
                            print(f"    ❌ Missing required fields")
                    else:
                        print(f"    ❌ Unexpectedly parsed invalid data")
                else:
                    if not test['should_parse']:
                        print(f"    ✅ Correctly rejected non-chart data")
                    else:
                        print(f"    ❌ Failed to parse valid chart data")
                        
            except json.JSONDecodeError:
                if not test['should_parse']:
                    print(f"    ✅ Correctly rejected invalid JSON")
                else:
                    print(f"    ❌ Failed to parse valid JSON")
            print()
    
    async def test_frontend_integration(self):
        """Test frontend API integration."""
        print("🌐 Testing Frontend Integration...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test if backend is running
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                if response.status_code == 200:
                    print("  ✅ Backend is running")
                else:
                    print("  ❌ Backend health check failed")
                    return
                    
        except Exception as e:
            print(f"  ❌ Cannot connect to backend: {e}")
            print("  💡 Make sure to start the backend with: cd backend && python -m uvicorn app.main:app --reload")
            return
        
        # Test enhanced RAG endpoint
        test_payload = {
            "query": "show me a bar chart of product prices",
            "azure_credentials": {
                "api_key": "test-key",
                "endpoint": "test-endpoint"
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/projects/{self.test_project_id}/enhanced-query-rag",
                    json=test_payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print("  ✅ Enhanced RAG endpoint accessible")
                else:
                    print(f"  ⚠️  Enhanced RAG endpoint returned {response.status_code}")
                    
        except Exception as e:
            print(f"  ⚠️  Enhanced RAG endpoint test failed: {e}")
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Chart Integration Tests\n")
        
        await self.test_chart_detection()
        await self.test_chart_data_generation()
        await self.test_chart_json_parsing()
        await self.test_frontend_integration()
        
        print("✨ Chart Integration Tests Complete!")

async def main():
    tester = ChartIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
