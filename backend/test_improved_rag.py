#!/usr/bin/env python3
"""
Test the improved RAG system with conversational capabilities.
"""
import sys
import os
import asyncio
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.database import get_supabase_client
from app.services.rag_service import RAGService

async def test_improved_rag():
    """Test the improved RAG system with different types of queries."""
    project_id = '67df8224-feba-4dd0-8648-abb9100cbb38'
    deployment_name = 'gpt-4o-mini'

    # Get real Azure credentials from environment
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT')
    }

    print(f"Using Azure endpoint: {azure_credentials['endpoint']}")
    print(f"API key present: {'Yes' if azure_credentials['api_key'] else 'No'}")
    
    rag_service = RAGService()
    
    # Test queries
    test_queries = [
        "hi",
        "hello there",
        "what products are available?",
        "show me the product list",
        "how are you?",
        "what can you help me with?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print(f"{'='*50}")
        
        try:
            result = await rag_service.query_rag(project_id, query, azure_credentials, deployment_name)
            print(f"Answer: {result.answer}")
            print(f"Source documents: {len(result.source_documents)}")
            if result.source_documents:
                for doc in result.source_documents:
                    print(f"  - {doc['content'][:100]}...")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_rag())
