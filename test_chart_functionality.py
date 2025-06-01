#!/usr/bin/env python3
"""
Simple Chart Functionality Test
Tests chart generation with existing project data
"""

import asyncio
import httpx
import json

async def test_chart_functionality():
    """Test chart functionality with existing project."""
    print("🎯 Testing Chart Functionality with Real Data\n")
    
    # Use existing project ID from logs
    project_id = "67df8224-feba-4dd0-8648-abb9100cbb38"
    backend_url = "http://localhost:8000"
    
    # Test chart queries
    chart_queries = [
        {
            "query": "show me a bar chart of product prices",
            "expected_chart_type": "bar"
        },
        {
            "query": "create a pie chart showing product categories",
            "expected_chart_type": "pie"
        },
        {
            "query": "visualize the data as a line graph",
            "expected_chart_type": "line"
        },
        {
            "query": "show me statistics about the products",
            "expected_chart_type": "stats"
        }
    ]
    
    success_count = 0
    
    try:
        async with httpx.AsyncClient() as client:
            for i, test_case in enumerate(chart_queries, 1):
                print(f"Test {i}: {test_case['query']}")
                
                # Test enhanced RAG query
                rag_data = {
                    "query": test_case["query"],
                    "azure_credentials": {
                        "api_key": "test-key",
                        "endpoint": "test-endpoint"
                    }
                }
                
                try:
                    response = await client.post(
                        f"{backend_url}/api/v1/projects/{project_id}/enhanced-query-rag",
                        json=rag_data,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        answer = result.get("answer", "")
                        
                        print(f"  ✅ Response received")
                        print(f"  📝 Answer length: {len(answer)} characters")
                        
                        # Check for chart data
                        if "```json" in answer and "chart_type" in answer:
                            print(f"  📊 Chart data detected!")
                            
                            # Try to extract and validate chart data
                            try:
                                import re
                                json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', answer)
                                if json_match:
                                    chart_data = json.loads(json_match.group(1))
                                    chart_type = chart_data.get("chart_type")
                                    title = chart_data.get("title", "No title")
                                    
                                    print(f"  🎨 Chart type: {chart_type}")
                                    print(f"  📋 Title: {title}")
                                    
                                    if chart_type:
                                        print(f"  ✅ Valid chart data structure")
                                        success_count += 1
                                    else:
                                        print(f"  ❌ Invalid chart data structure")
                                else:
                                    print(f"  ❌ Could not extract JSON from response")
                            except json.JSONDecodeError as e:
                                print(f"  ❌ JSON parsing error: {e}")
                        else:
                            print(f"  ⚠️  No chart data in response")
                            print(f"  📄 Response preview: {answer[:200]}...")
                    else:
                        print(f"  ❌ Request failed with status {response.status_code}")
                        if response.status_code == 500:
                            print(f"  💡 This might be due to missing Azure OpenAI credentials")
                        
                except Exception as e:
                    print(f"  ❌ Request error: {e}")
                
                print()
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    # Summary
    print(f"📊 Chart Functionality Test Results:")
    print(f"  ✅ Successful chart responses: {success_count}/{len(chart_queries)}")
    
    if success_count > 0:
        print(f"🎉 Chart functionality is working! {success_count} out of {len(chart_queries)} tests passed.")
        print(f"\n📖 How to test in the frontend:")
        print(f"1. Visit: http://localhost:9002")
        print(f"2. Login and select project: {project_id}")
        print(f"3. Go to Chat tab and try these queries:")
        for query in chart_queries:
            print(f"   - {query['query']}")
        print(f"4. Or visit: http://localhost:9002?test=charts for chart examples")
    else:
        print(f"⚠️  Chart functionality needs attention. Check Azure OpenAI credentials.")
    
    return success_count > 0

async def main():
    await test_chart_functionality()

if __name__ == "__main__":
    asyncio.run(main())
