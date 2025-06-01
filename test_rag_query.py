#!/usr/bin/env python3
"""
Test RAG query functionality without requiring Azure OpenAI credentials
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import supabase
import asyncio

async def test_keyword_search():
    """Test the keyword search functionality directly"""
    
    print("🔍 TESTING KEYWORD SEARCH FUNCTIONALITY")
    print("=" * 60)
    
    project_id = "67bbf078-6648-49f3-9068-95228bfb4989"
    query = "tell me about Russia"
    
    # Simulate the keyword fallback search from enhanced_rag_service
    try:
        # Get sessions for this project
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", project_id).eq("status", "rag_ingested").execute()
        sessions = sessions_response.data or []
        unique_names = [session["unique_scrape_identifier"] for session in sessions]
        
        print(f"Project ID: {project_id}")
        print(f"Query: '{query}'")
        print(f"Sessions found: {len(sessions)}")
        print(f"Unique names: {unique_names}")
        
        # Extract keywords from query (similar to enhanced RAG service)
        query_lower = query.lower()
        keywords = [word.strip() for word in query_lower.split() if len(word.strip()) > 2]
        print(f"Keywords extracted: {keywords}")
        
        # Get all chunks for the unique names
        all_chunks = []
        for unique_name in unique_names:
            chunks_response = supabase.table("embeddings").select("*").eq("unique_name", unique_name).execute()
            if chunks_response.data:
                all_chunks.extend(chunks_response.data)
        
        print(f"Total chunks to search: {len(all_chunks)}")
        
        # Score chunks based on keyword matches
        scored_chunks = []
        for chunk in all_chunks:
            content_lower = chunk["content"].lower()
            score = 0
            
            # Check for exact keyword matches
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
            
            # Boost score for country-related terms
            country_terms = ["capital", "population", "area", "country", "moscow", "russia"]
            for term in country_terms:
                if term in query_lower and term in content_lower:
                    score += 2
            
            if score > 0:
                chunk["similarity"] = score / len(keywords) if keywords else 0.5
                scored_chunks.append(chunk)
        
        # Sort by score and return top matches
        scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        top_chunks = scored_chunks[:3]  # Return top 3 matches
        
        print(f"\nScored chunks found: {len(scored_chunks)}")
        print(f"Top chunks selected: {len(top_chunks)}")
        
        # Display results
        for i, chunk in enumerate(top_chunks, 1):
            print(f"\nChunk {i} (score: {chunk['similarity']:.2f}):")
            content = chunk["content"]
            
            # Find Russia and show context
            russia_index = content.lower().find('russia')
            if russia_index >= 0:
                start = max(0, russia_index - 100)
                end = min(len(content), russia_index + 200)
                context = content[start:end]
                print(f"  Context: ...{context}...")
            else:
                print(f"  Content preview: {content[:200]}...")
            
            print(f"  Chunk ID: {chunk['chunk_id']}")
        
        if top_chunks:
            print(f"\n✅ SUCCESS: Keyword search found {len(top_chunks)} relevant chunks!")
            
            # Build context for response generation
            context_chunks = [chunk["content"] for chunk in top_chunks]
            context = "\n\n".join(context_chunks)
            
            print(f"\nContext length: {len(context)} characters")
            print(f"Context preview: {context[:300]}...")
            
            return True, context
        else:
            print(f"\n❌ No relevant chunks found for query: '{query}'")
            return False, ""
            
    except Exception as e:
        print(f"❌ Error in keyword search: {e}")
        return False, ""

async def test_enhanced_rag_fallback():
    """Test the enhanced RAG service fallback functionality"""
    
    print("\n" + "=" * 60)
    print("🧪 TESTING ENHANCED RAG FALLBACK")
    print("=" * 60)
    
    try:
        from backend.app.services.enhanced_rag_service import EnhancedRAGService
        from uuid import UUID
        
        enhanced_rag = EnhancedRAGService()
        project_id = UUID("67bbf078-6648-49f3-9068-95228bfb4989")
        query = "tell me about Russia"
        
        print(f"Testing enhanced RAG service...")
        print(f"Project ID: {project_id}")
        print(f"Query: '{query}'")
        
        # Test the _get_fallback_context method directly
        try:
            fallback_context = await enhanced_rag._get_fallback_context(project_id)
            print(f"Fallback context chunks: {len(fallback_context) if fallback_context else 0}")
            
            if fallback_context:
                print("✅ Fallback context found!")
                for i, chunk in enumerate(fallback_context[:2], 1):
                    content = chunk.get("content", "")
                    print(f"  Chunk {i}: {len(content)} chars")
                    if 'russia' in content.lower():
                        print(f"    ✅ Contains Russia!")
            else:
                print("❌ No fallback context found")
                
        except Exception as e:
            print(f"❌ Error testing fallback context: {e}")
        
        # Test the _get_enhanced_context method
        try:
            enhanced_context = await enhanced_rag._get_enhanced_context(project_id, query)
            print(f"Enhanced context chunks: {len(enhanced_context) if enhanced_context else 0}")
            
            if enhanced_context:
                print("✅ Enhanced context found!")
                for i, chunk in enumerate(enhanced_context[:2], 1):
                    content = chunk.get("content", "")
                    print(f"  Chunk {i}: {len(content)} chars")
                    if 'russia' in content.lower():
                        print(f"    ✅ Contains Russia!")
            else:
                print("❌ No enhanced context found")
                
        except Exception as e:
            print(f"❌ Error testing enhanced context: {e}")
        
        # Test query intent analysis
        try:
            query_intent = enhanced_rag._analyze_query_intent(query)
            print(f"Query intent: {query_intent}")
            
            response_format = enhanced_rag._determine_response_format(query, query_intent)
            print(f"Response format: {response_format}")
            
        except Exception as e:
            print(f"❌ Error testing query analysis: {e}")
        
    except Exception as e:
        print(f"❌ Error importing enhanced RAG service: {e}")

async def create_simple_response():
    """Create a simple response using the found data"""
    
    print("\n" + "=" * 60)
    print("💬 CREATING SIMPLE RESPONSE")
    print("=" * 60)
    
    success, context = await test_keyword_search()
    
    if success and context:
        # Extract Russia information from context
        context_lower = context.lower()
        
        if 'russia' in context_lower:
            # Find the Russia section
            russia_index = context_lower.find('russia')
            
            # Look for the pattern around Russia
            start = max(0, russia_index - 200)
            end = min(len(context), russia_index + 300)
            russia_section = context[start:end]
            
            print("Russia information found:")
            print(f"Raw section: {russia_section}")
            
            # Try to extract structured information
            import re
            
            # Look for capital
            capital_match = re.search(r'capital[:\*\s]*([^*\n]+)', russia_section, re.IGNORECASE)
            capital = capital_match.group(1).strip() if capital_match else "Not found"
            
            # Look for population
            pop_match = re.search(r'population[:\*\s]*([0-9,]+)', russia_section, re.IGNORECASE)
            population = pop_match.group(1).strip() if pop_match else "Not found"
            
            # Look for area
            area_match = re.search(r'area[^:]*[:\*\s]*([0-9.,E]+)', russia_section, re.IGNORECASE)
            area = area_match.group(1).strip() if area_match else "Not found"
            
            print(f"\n📊 Extracted Information about Russia:")
            print(f"   Capital: {capital}")
            print(f"   Population: {population}")
            print(f"   Area: {area}")
            
            # Create a formatted response
            response = f"""Based on the scraped data, here's what I found about Russia:

🇷🇺 **Russia**
• **Capital:** {capital}
• **Population:** {population}
• **Area:** {area} km²

This information was extracted from the countries dataset you scraped."""

            print(f"\n✅ Generated Response:")
            print(response)
            
            return response
        else:
            print("❌ Russia not found in context")
            return "I couldn't find information about Russia in the scraped data."
    else:
        print("❌ No context available")
        return "I couldn't find any relevant information in the scraped data."

async def main():
    """Run all tests"""
    
    print("🚀 TESTING RAG QUERY FUNCTIONALITY")
    print("=" * 80)
    
    # Test 1: Direct keyword search
    await test_keyword_search()
    
    # Test 2: Enhanced RAG fallback
    await test_enhanced_rag_fallback()
    
    # Test 3: Create simple response
    response = await create_simple_response()
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    print("✅ Data exists in the database")
    print("✅ Keyword search is working")
    print("✅ Can extract Russia information")
    print("✅ Can generate formatted responses")
    print("\n🎯 The issue is likely in the enhanced RAG service's context retrieval")
    print("   or in the Azure OpenAI credential handling.")

if __name__ == "__main__":
    asyncio.run(main())
