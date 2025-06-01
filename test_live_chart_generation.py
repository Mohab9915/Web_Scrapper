#!/usr/bin/env python3
"""
Test live chart generation with real Azure OpenAI credentials
"""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_live_chart_generation():
    """Test chart generation with real Azure OpenAI credentials."""
    print("🎯 Testing Live Chart Generation with Real Credentials\n")
    
    # Use existing project ID from logs
    project_id = "67df8224-feba-4dd0-8648-abb9100cbb38"
    backend_url = "http://localhost:8000"
    
    # Get credentials from .env file
    azure_credentials = {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    }
    
    print(f"Using Azure OpenAI:")
    print(f"  Endpoint: {azure_credentials['endpoint']}")
    print(f"  API Version: {azure_credentials['api_version']}")
    print(f"  API Key: {'*' * 20}...{azure_credentials['api_key'][-10:] if azure_credentials['api_key'] else 'None'}")
    print()
    
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
            "query": "show me statistics about the products",
            "expected_chart_type": "stats"
        }
    ]
    
    success_count = 0
    
    try:
        async with httpx.AsyncClient() as client:
            for i, test_case in enumerate(chart_queries, 1):
                print(f"🧪 Test {i}: {test_case['query']}")
                
                # Test enhanced RAG query with credentials from .env
                rag_data = {
                    "query": test_case["query"],
                    "azure_credentials": azure_credentials
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
                        
                        print(f"  ✅ Response received ({len(answer)} chars)")
                        
                        # Check for chart data
                        if "```json" in answer and "chart_type" in answer:
                            print(f"  📊 Chart JSON detected!")
                            
                            # Try to extract and validate chart data
                            try:
                                import re
                                json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', answer)
                                if json_match:
                                    chart_data = json.loads(json_match.group(1))
                                    chart_type = chart_data.get("chart_type")
                                    title = chart_data.get("title", "No title")
                                    data = chart_data.get("data", {})
                                    
                                    print(f"  🎨 Chart type: {chart_type}")
                                    print(f"  📋 Title: {title}")
                                    print(f"  📊 Data keys: {list(data.keys())}")
                                    
                                    # Validate structure
                                    if chart_type and title and data:
                                        print(f"  ✅ Valid chart structure!")
                                        success_count += 1
                                        
                                        # Pretty print the chart data
                                        print(f"  📄 Chart JSON:")
                                        print(f"     {json.dumps(chart_data, indent=6)}")
                                    else:
                                        print(f"  ❌ Invalid chart structure")
                                else:
                                    print(f"  ❌ Could not extract JSON from response")
                            except json.JSONDecodeError as e:
                                print(f"  ❌ JSON parsing error: {e}")
                        else:
                            print(f"  ⚠️  No chart JSON in response")
                            print(f"  📄 Response preview: {answer[:300]}...")
                            
                            # Check if it's a text response saying it will create a chart
                            if "chart" in answer.lower() and "create" in answer.lower():
                                print(f"  💡 AI acknowledged chart request but didn't generate JSON")
                    else:
                        print(f"  ❌ Request failed with status {response.status_code}")
                        error_text = await response.text()
                        print(f"  📄 Error: {error_text[:200]}...")
                        
                except Exception as e:
                    print(f"  ❌ Request error: {e}")
                
                print()
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    # Summary
    print(f"📊 Live Chart Generation Test Results:")
    print(f"  ✅ Successful chart generations: {success_count}/{len(chart_queries)}")
    
    if success_count > 0:
        print(f"🎉 Chart generation is working! {success_count} out of {len(chart_queries)} tests passed.")
        print(f"\n📖 To test in the frontend:")
        print(f"1. Visit: http://localhost:9002")
        print(f"2. Login and select project: {project_id}")
        print(f"3. Go to Chat tab and try these queries:")
        for query in chart_queries:
            print(f"   - {query['query']}")
        print(f"4. Charts should appear automatically in the chat!")
    else:
        print(f"⚠️  Chart generation needs attention.")
        print(f"💡 Possible issues:")
        print(f"   - Azure OpenAI credentials might be invalid")
        print(f"   - AI model might not be following instructions")
        print(f"   - Project might not have scraped data")
    
    return success_count > 0

async def main():
    await test_live_chart_generation()

if __name__ == "__main__":
    asyncio.run(main())
