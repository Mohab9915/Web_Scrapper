"""
Improved RAG Service with better handling of obvious questions and context selection.
"""
from typing import List, Dict, Any
import re
import logging
import json
import httpx
import numpy as np
from app.utils.embedding import generate_embeddings
from app.database import supabase
from app.models.chat import RAGQueryResponse
from app.utils.firecrawl_api import AZURE_CHAT_MODEL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedRAGService:
    """Improved RAG functionality."""

    def _is_obvious_question(self, query: str) -> bool:
        obvious_patterns = [
            r'what is\s+.*\?', r'what are\s+.*\?', r'who is\s+.*\?',
            r'where is\s+.*\?', r'when is\s+.*\?', r'how to\s+.*\?',
            r'can you\s+.*\?', r'could you\s+.*\?', r'please\s+.*\?'
        ]
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in obvious_patterns)

    def _extract_keywords(self, query: str) -> List[str]:
        query = re.sub(r'^(what|who|where|when|why|how|can|could|please)\s+', '', query.lower())
        query = re.sub(r'[?.,!]', '', query)
        common_words = {'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
        words = query.split()
        return [word for word in words if word not in common_words]
    
    def _parse_country_population(self, text: str) -> List[Dict[str, Any]]:
        """Parse country-population pairs from text."""
        facts = []
        # Look for patterns like "Country: 12,345,678" or "Country has a population of 12,345,678"
        patterns = [
            r'([A-Za-z\s]+)\s*:\s*([0-9,]+)\s*(?:people|population)?',
            r'([A-Za-z\s]+)\s+has\s+a\s+population\s+of\s+([0-9,]+)',
            r'population\s+of\s+([A-Za-z\s]+)\s+is\s+([0-9,]+)'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                country = match[0].strip()
                # Remove commas from population string and convert to int
                try:
                    population = int(match[1].replace(',', ''))
                    facts.append({"country": country, "population": population})
                except ValueError:
                    pass  # Skip if population can't be converted to int
        return facts
    def _is_aggregation_question(self, query: str) -> bool:
        agg_patterns = [
            r"most population", r"highest population", r"largest population", r"biggest population",
            r"least population", r"smallest population", r"lowest population",
            r"most populous", r"least populous", r"highest", r"lowest", r"largest", r"smallest"
        ]
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in agg_patterns)

    async def _get_context_chunks(self, project_id, query) -> List[Dict]:
        """Get context chunks for a query."""
        project_response = supabase.table("projects").select("rag_enabled").eq("id", str(project_id)).single().execute()
        if not project_response.data:
            raise Exception("Project not found")
        if not project_response.data["rag_enabled"]:
            raise Exception("RAG is not enabled for this project")
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", str(project_id)).eq("status", "rag_ingested").execute()
        if not sessions_response.data:
            raise Exception("No RAG-processed data available for this project")
        unique_names = [session["unique_scrape_identifier"] for session in sessions_response.data]
        
        # For OpenAI, we need to generate a mock embedding
        # This is a temporary solution - in production we'd want to use OpenAI embeddings
        query_embedding = list(np.random.rand(1536))  # Use random embedding for demo
        
        is_obvious = self._is_obvious_question(query)
        logger.info(f"Question type: {'obvious' if is_obvious else 'complex'}")
        keywords = self._extract_keywords(query)
        logger.info(f"Extracted keywords: {keywords}")
        match_count = 8 if is_obvious else 5
        
        rpc_response = supabase.rpc(
            "match_embeddings_filtered",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
                "p_unique_names": unique_names
            }
        ).execute()
        
        if not rpc_response.data:
            return []
            
        scored_chunks = []
        for chunk in rpc_response.data:
            score = chunk["similarity"]
            content = chunk["content"].lower()
            for keyword in keywords:
                if keyword in content:
                    score *= 1.2
            scored_chunks.append((chunk, score))
        
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:match_count]
    
    async def query_rag_openai(self, project_id, query, api_key: str, model_name: str = None) -> RAGQueryResponse:
        """Query the RAG system using OpenAI."""
        # Always use gpt-4o for OpenAI direct API calls, regardless of what was passed
        model_name = "gpt-4o" if not model_name or model_name == "gpt-4o-mini" else model_name
        logger.info(f"Processing RAG query with OpenAI model {model_name}: {query}")
        
        try:
            # Get context chunks using the method extracted from query_rag
            top_chunks = await self._get_context_chunks(project_id, query)
            
            if not top_chunks:
                return RAGQueryResponse(
                    answer="I couldn't find any relevant information in the scraped data.",
                    generation_cost=0.0,
                    source_documents=[]
                )
            
            # Prepare context
            context_chunks = [chunk["content"] for chunk, _ in top_chunks]
            context = "\n\n".join(context_chunks)
            is_obvious = self._is_obvious_question(query)
            
            # Check for aggregation questions
            if self._is_aggregation_question(query):
                facts = []
                for chunk in context_chunks:
                    facts.extend(self._parse_country_population(chunk))
                if facts:
                    if any(word in query.lower() for word in ["most", "highest", "largest", "biggest", "most populous"]):
                        top = max(facts, key=lambda x: x["population"])
                        answer = f"{top['country']} has the highest population: {int(top['population']):,}"
                    elif any(word in query.lower() for word in ["least", "smallest", "lowest"]):
                        top = min(facts, key=lambda x: x["population"])
                        answer = f"{top['country']} has the lowest population: {int(top['population']):,}"
                    else:
                        answer = "I found population data but could not determine the aggregation you want."
                    return RAGQueryResponse(
                        answer=answer,
                        generation_cost=0.0,
                        source_documents=[{"content": json.dumps(facts), "metadata": {}}]
                    )
            
            # Use OpenAI API
            url = "https://api.openai.com/v1/chat/completions"
            
            system_message = (
                "You are an AI assistant answering questions based on provided context. "
                "For obvious questions, provide direct and concise answers. "
                "For complex questions, provide detailed and well-structured responses. "
                "Always base your answer only on the provided context. "
                "If the context doesn't contain relevant information, say so."
            )
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {query}"}
            ]
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.2 if is_obvious else 0.7,
                "top_p": 0.8,
                "max_tokens": 1024
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Error from OpenAI API: {response.text}")
                    answer = "Sorry, I encountered an error while generating a response."
                    generation_cost = 0.0
                else:
                    response_data = response.json()
                    answer = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    # Calculate approximate cost
                    input_chars = len(context) + len(query) + 100
                    output_chars = len(answer)
                    total_tokens = (input_chars + output_chars) / 4
                    generation_cost = (total_tokens / 1000) * 0.005  # Approximate cost for GPT-4o
            
            # Prepare source documents
            source_documents = []
            for chunk, score in top_chunks:
                markdown_response = supabase.table("markdowns").select("url").eq("unique_name", chunk["unique_name"]).single().execute()
                if markdown_response.data:
                    source_documents.append({
                        "content": chunk["content"],
                        "metadata": {
                            "url": markdown_response.data["url"],
                            "similarity": score
                        }
                    })
            
            return RAGQueryResponse(
                answer=answer,
                generation_cost=generation_cost,
                source_documents=source_documents
            )
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            answer = f"Sorry, I encountered an error while generating a response: {str(e)}"
            return RAGQueryResponse(
                answer=answer,
                generation_cost=0.0,
                source_documents=[]
            )
    
    async def query_rag(self, project_id, query, azure_credentials: Dict[str, str], model_name: str = None) -> RAGQueryResponse:
        logger.info(f"Processing RAG query: {query}")
        if not azure_credentials or 'api_key' not in azure_credentials or 'endpoint' not in azure_credentials:
            raise Exception("Azure OpenAI credentials (api_key and endpoint) are required")
        project_response = supabase.table("projects").select("rag_enabled").eq("id", str(project_id)).single().execute()
        if not project_response.data:
            raise Exception("Project not found")
        if not project_response.data["rag_enabled"]:
            raise Exception("RAG is not enabled for this project")
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", str(project_id)).eq("status", "rag_ingested").execute()
        if not sessions_response.data:
            raise Exception("No RAG-processed data available for this project")
        unique_names = [session["unique_scrape_identifier"] for session in sessions_response.data]
        query_embedding = await generate_embeddings(query, azure_credentials)
        is_obvious = self._is_obvious_question(query)
        logger.info(f"Question type: {'obvious' if is_obvious else 'complex'}")
        keywords = self._extract_keywords(query)
        logger.info(f"Extracted keywords: {keywords}")
        match_count = 8 if is_obvious else 5
        rpc_response = supabase.rpc(
            "match_embeddings_filtered",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
                "p_unique_names": unique_names
            }
        ).execute()
        if not rpc_response.data:
            return RAGQueryResponse(
                answer="I couldn't find any relevant information in the scraped data.",
                generation_cost=0.0,
                source_documents=[]
            )
        scored_chunks = []
        for chunk in rpc_response.data:
            score = chunk["similarity"]
            content = chunk["content"].lower()
            for keyword in keywords:
                if keyword in content:
                    score *= 1.2
            scored_chunks.append((chunk, score))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = scored_chunks[:match_count]
        context_chunks = [chunk["content"] for chunk, _ in top_chunks]
        context = "\n\n".join(context_chunks)

# --- Aggregation logic for structured data ---
        if self._is_aggregation_question(query):
            # Try to parse all context for country-population pairs
            facts = []
            for chunk in context_chunks:
                facts.extend(self._parse_country_population(chunk))
            if facts:
                # Find max/min depending on question
                if any(word in query.lower() for word in ["most", "highest", "largest", "biggest", "most populous"]):
                    top = max(facts, key=lambda x: x["population"])
                    answer = f"{top['country']} has the highest population: {int(top['population']):,}"
                elif any(word in query.lower() for word in ["least", "smallest", "lowest"]):
                    top = min(facts, key=lambda x: x["population"])
                    answer = f"{top['country']} has the lowest population: {int(top['population']):,}"
                else:
                    answer = "I found population data but could not determine the aggregation you want."
                return RAGQueryResponse(
                    answer=answer,
                    generation_cost=0.0,
                    source_documents=[{"content": json.dumps(facts), "metadata": {}}]
                )
                logger.info(f"Selected {len(context_chunks)} chunks for context")
        logger.debug(f"Context length: {len(context)} characters")
        try:
            import httpx
            api_key = azure_credentials['api_key']
            endpoint = azure_credentials['endpoint']
            deployment_name = model_name if model_name else AZURE_CHAT_MODEL
            
            # Handle practicehub endpoint format
            if "practicehub3994533910" in endpoint:
                # For practicehub, use the direct endpoint
                url = f"https://practicehub3994533910.services.ai.azure.com/openai/deployments/{deployment_name}/chat/completions?api-version=2024-05-01-preview"
            elif "services.ai.azure.com" in endpoint:
                base_endpoint = endpoint.replace("/models", "")
                url = f"{base_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2023-05-15"
            else:
                url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2023-05-15"
            
            system_message = (
                "You are an AI assistant answering questions based on provided context. "
                "For obvious questions, provide direct and concise answers. "
                "For complex questions, provide detailed and well-structured responses. "
                "Always base your answer only on the provided context. "
                "If the context doesn't contain relevant information, say so."
            )
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {query}"}
            ]
            payload = {
                "messages": messages,
                "temperature": 0.2 if is_obvious else 0.7,
                "top_p": 0.8,
                "max_tokens": 1024,
                "model": deployment_name  # Add model name to payload
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "api-key": api_key
                    }
                )
                if response.status_code != 200:
                    logger.error(f"Error from Azure OpenAI API: {response.text}")
                    answer = "Sorry, I encountered an error while generating a response."
                    generation_cost = 0.0
                else:
                    response_data = response.json()
                    answer = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    input_chars = len(context) + len(query) + 100
                    output_chars = len(answer)
                    total_tokens = (input_chars + output_chars) / 4
                    generation_cost = (total_tokens / 1000) * 0.002
        except Exception as e:
            logger.error(f"Error calling Azure OpenAI API: {e}")
            answer = f"Sorry, I encountered an error while generating a response: {str(e)}"
            generation_cost = 0.0
        source_documents = []
        for chunk, score in top_chunks:
            markdown_response = supabase.table("markdowns").select("url").eq("unique_name", chunk["unique_name"]).single().execute()
            if markdown_response.data:
                source_documents.append({
                    "content": chunk["content"],
                    "metadata": {
                        "url": markdown_response.data["url"],
                        "similarity": score
                    }
                })
        return RAGQueryResponse(
            answer=answer,
            generation_cost=generation_cost,
            source_documents=source_documents
        )
