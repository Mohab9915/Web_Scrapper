#!/usr/bin/env python3
"""
Test conversational behavior vs chart generation
"""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_conversational_behavior():
    """Test that the chatbot behaves conversationally for general queries and only creates charts when requested."""
    print("🤖 Testing Conversational Behavior vs Chart Generation\n")
    
    # Use existing project ID from logs
    project_id = "67df8224-feba-4dd0-8648-abb9100cbb38"
    backend_url = "http://localhost:8000"
    
    # Get credentials from .env file
    azure_credentials = {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    }
    
    # Test different types of queries
    test_queries = [
        {
            "query": "hi",
            "expected_behavior": "conversational",
            "description": "Simple greeting"
        },
        {
            "query": "hello, how are you?",
            "expected_behavior": "conversational", 
            "description": "Friendly greeting"
        },
        {
            "query": "what can you help me with?",
            "expected_behavior": "conversational",
            "description": "General question about capabilities"
        },
        {
            "query": "tell me about the products",
            "expected_behavior": "data_response",
            "description": "Data-related question"
        },
        {
            "query": "show me a bar chart of product prices",
            "expected_behavior": "chart",
            "description": "Explicit chart request"
        },
        {
            "query": "create a pie chart of categories",
            "expected_behavior": "chart",
            "description": "Another explicit chart request"
        },
        {
            "query": "what's the weather like?",
            "expected_behavior": "conversational",
            "description": "Non-data related question"
        }
    ]
    
    success_count = 0
    total_tests = len(test_queries)
    
    try:
        async with httpx.AsyncClient() as client:
            for i, test_case in enumerate(test_queries, 1):
                print(f"🧪 Test {i}: {test_case['description']}")
                print(f"   Query: '{test_case['query']}'")
                print(f"   Expected: {test_case['expected_behavior']}")
                
                # Test enhanced RAG query
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
                        
                        print(f"   ✅ Response received ({len(answer)} chars)")
                        
                        # Analyze the response
                        is_chart = "```json" in answer and "chart_type" in answer
                        is_conversational = not is_chart and len(answer) < 500 and not ("Item 1:" in answer or "Product:" in answer)
                        is_data_response = not is_chart and not is_conversational
                        
                        actual_behavior = "chart" if is_chart else ("conversational" if is_conversational else "data_response")
                        
                        print(f"   📝 Actual behavior: {actual_behavior}")
                        print(f"   📄 Response preview: {answer[:150]}...")
                        
                        # Check if behavior matches expectation
                        if actual_behavior == test_case["expected_behavior"]:
                            print(f"   ✅ PASS - Behavior matches expectation")
                            success_count += 1
                        else:
                            print(f"   ❌ FAIL - Expected {test_case['expected_behavior']}, got {actual_behavior}")
                        
                    else:
                        print(f"   ❌ Request failed with status {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Request error: {e}")
                
                print()
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    # Summary
    print(f"📊 Conversational Behavior Test Results:")
    print(f"  ✅ Correct behaviors: {success_count}/{total_tests}")
    
    if success_count >= total_tests * 0.8:  # 80% success rate
        print(f"🎉 Great! The chatbot is behaving correctly!")
        print(f"   ✅ Conversational for general queries")
        print(f"   ✅ Creates charts only when explicitly requested")
        print(f"   ✅ Uses data appropriately for data-related questions")
    else:
        print(f"⚠️  Some behaviors need adjustment.")
        print(f"💡 The chatbot should:")
        print(f"   - Respond conversationally to greetings and general questions")
        print(f"   - Only create charts when explicitly asked (with words like 'chart', 'graph', etc.)")
        print(f"   - Use scraped data only when relevant to the question")
    
    return success_count >= total_tests * 0.8

async def main():
    await test_conversational_behavior()

if __name__ == "__main__":
    asyncio.run(main())
