#!/usr/bin/env python3
"""
Test the enhanced RAG endpoint to make sure it's using our improved service.
"""
import sys
import os
import asyncio
import httpx
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

async def test_enhanced_endpoint():
    """Test the enhanced RAG endpoint."""
    project_id = '67df8224-feba-4dd0-8648-abb9100cbb38'
    
    # Get real Azure credentials from environment
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT')
    }
    
    print(f"Using Azure endpoint: {azure_credentials['endpoint']}")
    print(f"API key present: {'Yes' if azure_credentials['api_key'] else 'No'}")
    
    # Test queries
    test_queries = [
        "hi",
        "what products are available?",
        "show me the product list"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print(f"{'='*50}")
        
        try:
            payload = {
                "query": query,
                "model_name": "gpt-4o-mini",
                "azure_credentials": azure_credentials
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/projects/67df8224-feba-4dd0-8648-abb9100cbb38/enhanced-query-rag",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Answer: {result['answer']}")
                    print(f"Source documents: {len(result.get('source_documents', []))}")
                    if result.get('source_documents'):
                        for doc in result['source_documents']:
                            print(f"  - {doc['content'][:100]}...")
                else:
                    print(f"Error {response.status_code}: {response.text}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_endpoint())
