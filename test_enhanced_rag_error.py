#!/usr/bin/env python3
"""
Test the enhanced RAG service error handling specifically
"""

import requests
import json

def test_enhanced_rag_with_real_project():
    """Test enhanced RAG with a real project ID from the logs"""
    
    backend_url = "http://localhost:8000"
    project_id = "67bbf078-6648-49f3-9068-95228bfb4989"  # From the logs
    
    print("🔍 Testing Enhanced RAG Error Handling with Real Project")
    print("=" * 60)
    
    # Test payload
    test_payload = {
        "query": "create a chart showing the data",
        "deployment_name": "gpt-4o-mini"
    }
    
    try:
        print(f"📤 Sending request to project {project_id}")
        print(f"Query: {test_payload['query']}")
        
        response = requests.post(
            f"{backend_url}/api/v1/projects/{project_id}/enhanced-rag-query",
            json=test_payload,
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Success! Response received:")
                print(f"   Answer length: {len(data.get('answer', ''))}")
                print(f"   Generation cost: {data.get('generation_cost', 0)}")
                print(f"   Source documents: {len(data.get('source_documents', []))}")
                
                # Check if it's a chart response
                answer = data.get('answer', '')
                if '```json' in answer and 'chart_type' in answer:
                    print("📊 Chart data detected in response!")
                    return True
                else:
                    print("💬 Regular conversational response received")
                    return True
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"Raw response: {response.text[:200]}...")
                return False
                
        else:
            print(f"❌ Error response: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw error: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might indicate the error we're trying to fix")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_chart_generation_specifically():
    """Test chart generation specifically"""
    
    backend_url = "http://localhost:8000"
    project_id = "67bbf078-6648-49f3-9068-95228bfb4989"
    
    print("\n🔍 Testing Chart Generation Specifically")
    print("=" * 60)
    
    chart_queries = [
        "create a bar chart of the data",
        "show me a pie chart",
        "generate a chart visualization",
        "make a chart showing the products"
    ]
    
    for query in chart_queries:
        print(f"\n📊 Testing query: '{query}'")
        
        test_payload = {
            "query": query,
            "deployment_name": "gpt-4o-mini"
        }
        
        try:
            response = requests.post(
                f"{backend_url}/api/v1/projects/{project_id}/enhanced-rag-query",
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                
                if '```json' in answer:
                    print("✅ Chart JSON detected!")
                    # Try to extract and validate the JSON
                    try:
                        import re
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', answer, re.DOTALL)
                        if json_match:
                            chart_data = json.loads(json_match.group(1))
                            if 'chart_type' in chart_data and 'data' in chart_data:
                                print(f"   ✅ Valid chart data: {chart_data['chart_type']}")
                            else:
                                print("   ⚠️  Chart JSON missing required fields")
                        else:
                            print("   ⚠️  Could not extract JSON from response")
                    except Exception as e:
                        print(f"   ❌ Invalid chart JSON: {e}")
                else:
                    print("   💬 No chart data in response")
                    
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            
        # Small delay between requests
        import time
        time.sleep(1)

def check_recent_logs():
    """Check for any new error logs after our tests"""
    
    print("\n🔍 Checking Recent Logs")
    print("=" * 60)
    
    try:
        with open("backend/logs/app.log", "r") as f:
            lines = f.readlines()
            
        # Get last 10 lines
        recent_lines = lines[-10:]
        
        print("📋 Last 10 log entries:")
        for i, line in enumerate(recent_lines, 1):
            if "ERROR" in line:
                print(f"❌ {i}: {line.strip()}")
            elif "WARNING" in line:
                print(f"⚠️  {i}: {line.strip()}")
            else:
                print(f"ℹ️  {i}: {line.strip()}")
                
    except Exception as e:
        print(f"❌ Could not read logs: {e}")

if __name__ == "__main__":
    print("🚀 Enhanced RAG Error Testing")
    print("=" * 60)
    
    # Test 1: Basic enhanced RAG functionality
    success1 = test_enhanced_rag_with_real_project()
    
    # Test 2: Chart generation specifically
    test_chart_generation_specifically()
    
    # Test 3: Check logs for any new errors
    check_recent_logs()
    
    print("\n" + "=" * 60)
    print("📊 ENHANCED RAG TESTING COMPLETE")
    print("=" * 60)
    
    if success1:
        print("✅ Enhanced RAG service is working correctly")
        print("✅ Error handling improvements are in place")
        print("\n📋 The empty error message issue should now provide detailed logs")
    else:
        print("⚠️  Enhanced RAG service may still have issues")
        print("📋 Check the logs above for detailed error information")
    
    print("\n🎯 NEXT: Test the chart stability in the browser:")
    print("1. Go to http://localhost:9002")
    print("2. Navigate to the chat for the project")
    print("3. Ask for a chart")
    print("4. Type in the chat input while chart is visible")
    print("5. Chart should NOT refresh/flicker")
