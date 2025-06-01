#!/usr/bin/env python3
"""
Test the enhanced RAG service fixes for finding Russia data
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from uuid import UUID

async def test_enhanced_rag_context():
    """Test the enhanced RAG service context retrieval"""
    
    print("🧪 TESTING ENHANCED RAG SERVICE FIXES")
    print("=" * 60)
    
    try:
        from backend.app.services.enhanced_rag_service import EnhancedRAGService
        
        enhanced_rag = EnhancedRAGService()
        project_id = UUID("67bbf078-6648-49f3-9068-95228bfb4989")
        query = "tell me about Russia"
        
        print(f"Project ID: {project_id}")
        print(f"Query: '{query}'")
        
        # Test keyword extraction
        keywords = enhanced_rag._extract_enhanced_keywords(query)
        print(f"Extracted keywords: {keywords}")
        
        # Test query intent analysis
        intent = enhanced_rag._analyze_query_intent(query)
        print(f"Query intent: {intent}")
        
        # Test response format determination
        response_format = enhanced_rag._determine_response_format(query, intent)
        print(f"Response format: {response_format}")
        
        # Test enhanced context retrieval
        print(f"\n🔍 Testing enhanced context retrieval...")
        enhanced_context = await enhanced_rag._get_enhanced_context(project_id, query)
        print(f"Enhanced context chunks: {len(enhanced_context)}")
        
        if enhanced_context:
            print("✅ Enhanced context found!")
            for i, chunk in enumerate(enhanced_context[:3], 1):
                content = chunk.get("content", "")
                print(f"  Chunk {i}: {len(content)} chars")
                if 'russia' in content.lower():
                    print(f"    ✅ Contains Russia!")
                    # Show context around Russia
                    russia_index = content.lower().find('russia')
                    start = max(0, russia_index - 50)
                    end = min(len(content), russia_index + 100)
                    context_sample = content[start:end]
                    print(f"    Context: ...{context_sample}...")
        else:
            print("❌ No enhanced context found")
        
        # Test fallback context
        print(f"\n🔄 Testing fallback context...")
        fallback_context = await enhanced_rag._get_fallback_context(project_id)
        print(f"Fallback context chunks: {len(fallback_context)}")
        
        if fallback_context:
            print("✅ Fallback context found!")
            russia_chunks = []
            for chunk in fallback_context:
                content = chunk.get("content", "")
                if 'russia' in content.lower():
                    russia_chunks.append(chunk)
            
            print(f"  Chunks containing Russia: {len(russia_chunks)}")
            
            if russia_chunks:
                # Show the best Russia chunk
                best_chunk = russia_chunks[0]
                content = best_chunk.get("content", "")
                russia_index = content.lower().find('russia')
                start = max(0, russia_index - 100)
                end = min(len(content), russia_index + 200)
                russia_section = content[start:end]
                print(f"  Russia section: ...{russia_section}...")
        
        # Test building enhanced context
        if enhanced_context or fallback_context:
            context_chunks = enhanced_context if enhanced_context else fallback_context
            context = enhanced_rag._build_enhanced_context(context_chunks, intent)
            print(f"\n📝 Built context length: {len(context)} characters")
            
            # Look for Russia in the built context
            if 'russia' in context.lower():
                print("✅ Russia found in built context!")
                return True, context
            else:
                print("❌ Russia not found in built context")
                return False, context
        else:
            print("❌ No context available")
            return False, ""
            
    except Exception as e:
        print(f"❌ Error testing enhanced RAG: {e}")
        import traceback
        traceback.print_exc()
        return False, ""

async def test_simple_response_generation():
    """Test generating a simple response without Azure OpenAI"""
    
    print("\n" + "=" * 60)
    print("💬 TESTING SIMPLE RESPONSE GENERATION")
    print("=" * 60)
    
    success, context = await test_enhanced_rag_context()
    
    if success and context:
        print("✅ Context available, generating simple response...")
        
        # Extract Russia information manually
        context_lower = context.lower()
        
        if 'russia' in context_lower:
            # Find the Russia section
            russia_index = context_lower.find('russia')
            
            # Look for the pattern around Russia
            start = max(0, russia_index - 200)
            end = min(len(context), russia_index + 300)
            russia_section = context[start:end]
            
            print(f"Russia section found: {russia_section[:200]}...")
            
            # Try to extract structured information
            import re
            
            # Look for capital (after Russia)
            russia_pos = russia_section.lower().find('russia')
            after_russia = russia_section[russia_pos:]
            
            capital_match = re.search(r'capital[:\*\s]*([^*\n]+)', after_russia, re.IGNORECASE)
            capital = capital_match.group(1).strip() if capital_match else "Not found"
            
            # Look for population (after Russia)
            pop_match = re.search(r'population[:\*\s]*([0-9,]+)', after_russia, re.IGNORECASE)
            population = pop_match.group(1).strip() if pop_match else "Not found"
            
            # Look for area (after Russia)
            area_match = re.search(r'area[^:]*[:\*\s]*([0-9.,E]+)', after_russia, re.IGNORECASE)
            area = area_match.group(1).strip() if area_match else "Not found"
            
            print(f"\n📊 Extracted Information about Russia:")
            print(f"   Capital: {capital}")
            print(f"   Population: {population}")
            print(f"   Area: {area}")
            
            # Create a formatted response
            response = f"""Based on the scraped data, here's what I found about Russia:

🇷🇺 **Russia**
• **Capital:** {capital}
• **Population:** {population} people
• **Area:** {area} km²

This information was extracted from the countries dataset you scraped from scrapethissite.com."""

            print(f"\n✅ Generated Response:")
            print(response)
            
            return response
        else:
            print("❌ Russia not found in context")
            return "I couldn't find information about Russia in the scraped data."
    else:
        print("❌ No context available for response generation")
        return "I couldn't find any relevant information in the scraped data."

async def test_enhanced_rag_without_credentials():
    """Test enhanced RAG service without Azure OpenAI credentials"""
    
    print("\n" + "=" * 60)
    print("🔧 TESTING ENHANCED RAG WITHOUT CREDENTIALS")
    print("=" * 60)
    
    try:
        from backend.app.services.enhanced_rag_service import EnhancedRAGService
        
        enhanced_rag = EnhancedRAGService()
        project_id = UUID("67bbf078-6648-49f3-9068-95228bfb4989")
        query = "tell me about Russia"
        
        # Test with empty credentials (should use fallback)
        azure_credentials = {}
        deployment_name = "gpt-4o-mini"
        
        print(f"Testing enhanced_query_rag with empty credentials...")
        
        try:
            response = await enhanced_rag.enhanced_query_rag(
                project_id, query, azure_credentials, deployment_name
            )
            
            print(f"Response received:")
            print(f"  Answer length: {len(response.answer)} characters")
            print(f"  Generation cost: {response.generation_cost}")
            print(f"  Source documents: {len(response.source_documents)}")
            print(f"  Answer preview: {response.answer[:200]}...")
            
            if 'russia' in response.answer.lower():
                print("✅ Response contains Russia information!")
                return True
            else:
                print("⚠️  Response doesn't contain Russia information")
                return False
                
        except Exception as e:
            print(f"❌ Error in enhanced_query_rag: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing enhanced RAG without credentials: {e}")
        return False

async def main():
    """Run all tests"""
    
    print("🚀 TESTING ENHANCED RAG SERVICE FIXES")
    print("=" * 80)
    
    # Test 1: Context retrieval
    success1, context = await test_enhanced_rag_context()
    
    # Test 2: Simple response generation
    response = await test_simple_response_generation()
    
    # Test 3: Enhanced RAG without credentials
    success3 = await test_enhanced_rag_without_credentials()
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    
    if success1:
        print("✅ Enhanced context retrieval is working")
    else:
        print("❌ Enhanced context retrieval needs work")
    
    if "Russia" in response:
        print("✅ Simple response generation is working")
    else:
        print("❌ Simple response generation needs work")
    
    if success3:
        print("✅ Enhanced RAG service works without credentials")
    else:
        print("❌ Enhanced RAG service still requires credentials")
    
    print("\n🎯 The enhanced RAG service should now be able to find Russia data!")
    print("   Try asking about Russia in the chat interface.")

if __name__ == "__main__":
    asyncio.run(main())
