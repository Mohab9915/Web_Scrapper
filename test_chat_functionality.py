#!/usr/bin/env python3
"""
Test the chat functionality end-to-end to ensure the RAG system works properly.
"""
import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.enhanced_rag_service import EnhancedRAGService
from uuid import UUID
from dotenv import load_dotenv

load_dotenv()

async def test_chat_functionality():
    """Test the enhanced RAG service with actual chat queries."""
    
    print("🧪 TESTING CHAT FUNCTIONALITY")
    print("=" * 60)
    
    # Test with project that has scraped data
    test_project_id = "0ba79db8-54af-481b-91f9-889220e3c41b"  # test1 project
    
    # Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', ''),
        'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
    }
    
    if not azure_credentials['api_key'] or not azure_credentials['endpoint']:
        print("❌ Azure OpenAI credentials not found!")
        return
    
    print(f"✅ Azure credentials loaded")
    
    # Initialize enhanced RAG service
    enhanced_rag = EnhancedRAGService()
    
    # Test queries
    test_queries = [
        "What countries are in the dataset?",
        "Tell me about Andorra",
        "How many countries have a population over 1 million?",
        "What is the capital of France?",
        "List some European countries",
        "Hello, how are you?"  # Conversational query
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test Query {i}: '{query}'")
        print("-" * 50)
        
        try:
            # Test the enhanced RAG query
            response = await enhanced_rag.enhanced_query_rag(
                project_id=UUID(test_project_id),
                query=query,
                azure_credentials=azure_credentials,
                deployment_name="gpt-4o"
            )
            
            print(f"✅ Response received:")
            print(f"   Answer: {response.answer[:200]}{'...' if len(response.answer) > 200 else ''}")
            print(f"   Generation cost: {response.generation_cost}")
            print(f"   Source documents: {len(response.source_documents) if response.source_documents else 0}")
            
            if response.chart_data:
                print(f"   Chart data: {response.chart_data.get('type', 'Unknown')}")
            
            if response.conversation_title:
                print(f"   Conversation title: {response.conversation_title}")
            
            # Check if this is the problematic message
            if "couldn't find any relevant information" in response.answer.lower():
                print(f"   ❌ Still getting the 'no relevant information' message!")
            else:
                print(f"   ✅ Got a proper response!")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()

async def test_regular_rag_service():
    """Test the regular RAG service as well."""
    
    print(f"\n🧪 TESTING REGULAR RAG SERVICE")
    print("=" * 60)
    
    from backend.app.services.rag_service import RAGService
    
    # Test with project that has scraped data
    test_project_id = "0ba79db8-54af-481b-91f9-889220e3c41b"  # test1 project
    test_query = "What countries are in the dataset?"
    
    # Azure credentials
    azure_credentials = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY', ''),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', ''),
        'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
    }
    
    # Initialize regular RAG service
    rag_service = RAGService()
    
    try:
        print(f"🔍 Query: '{test_query}'")
        
        # Test the regular RAG query
        response = await rag_service.query_rag(
            project_id=UUID(test_project_id),
            query=test_query,
            azure_credentials=azure_credentials,
            llm_model="gpt-4o"
        )
        
        print(f"✅ Response received:")
        print(f"   Answer: {response.answer[:200]}{'...' if len(response.answer) > 200 else ''}")
        print(f"   Generation cost: {response.generation_cost}")
        print(f"   Source documents: {len(response.source_documents) if response.source_documents else 0}")
        
        # Check if this is the problematic message
        if "couldn't find any relevant information" in response.answer.lower():
            print(f"   ❌ Still getting the 'no relevant information' message!")
        else:
            print(f"   ✅ Got a proper response!")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_functionality())
    asyncio.run(test_regular_rag_service())
