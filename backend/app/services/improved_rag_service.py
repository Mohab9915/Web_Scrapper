"""
Improved RAG Service with better handling of obvious questions and context selection.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import re
import logging
import json
import httpx
import numpy as np
from datetime import datetime
from ..utils.embedding import generate_embeddings
from ..database import supabase
from ..models.chat import RAGQueryResponse, ChatMessageResponse
from ..scraper_modules.assets import AZURE_CHAT_MODEL # Corrected path
from .chat_history_service import ChatHistoryService # Corrected relative import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedRAGService:
    """Improved RAG functionality."""

    def __init__(self):
        self.chat_history_service = ChatHistoryService()

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
        # Look for sessions with 'rag_ingested' status first, but also accept 'scraped' sessions if project has RAG enabled
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", str(project_id)).eq("status", "rag_ingested").execute()

        # If no rag_ingested sessions found, check if project has RAG enabled and look for scraped sessions
        if not sessions_response.data:
            # Check if project has RAG enabled
            project_response = supabase.table("projects").select("rag_enabled").eq("id", str(project_id)).single().execute()
            project_rag_enabled = project_response.data.get("rag_enabled", False) if project_response.data else False

            if project_rag_enabled:
                # If RAG is enabled, also accept 'scraped' sessions as they contain the data needed for RAG
                sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", str(project_id)).eq("status", "scraped").execute()

        # Check if the found sessions actually have embeddings
        # Only use current sessions - do NOT fall back to old embeddings when re-scraping
        if sessions_response.data:
            # Check if any of the found sessions have embeddings
            session_unique_names = [s["unique_scrape_identifier"] for s in sessions_response.data]
            embeddings_check = supabase.table("embeddings").select("unique_name").in_("unique_name", session_unique_names).execute()

            if not embeddings_check.data:
                # No embeddings for current sessions - this is expected after re-scraping
                # We will use the markdown content directly instead of falling back to old embeddings
                pass

        # If no current sessions found, return error - do NOT use old embeddings
        # This ensures RAG forgets all previous sessions and only uses latest scraped data

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
            raise Exception("RAG is not enabled for this project") # This could also return a RAGQueryResponse
        # Look for sessions with 'rag_ingested' status first, but also accept 'scraped' sessions if project has RAG enabled
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", str(project_id)).eq("status", "rag_ingested").execute()

        # If no rag_ingested sessions found, check if project has RAG enabled and look for scraped sessions
        if not sessions_response.data:
            # Project RAG setting was already checked above, so we know it's enabled
            # If RAG is enabled, also accept 'scraped' sessions as they contain the data needed for RAG
            sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", str(project_id)).eq("status", "scraped").execute()
            logger.info(f"DEBUG: RAG enabled project, found {len(sessions_response.data)} scraped sessions")

        # Check if the found sessions actually have embeddings
        # Only use current sessions - do NOT fall back to old embeddings when re-scraping
        if sessions_response.data:
            # Check if any of the found sessions have embeddings
            session_unique_names = [s["unique_scrape_identifier"] for s in sessions_response.data]
            embeddings_check = supabase.table("embeddings").select("unique_name").in_("unique_name", session_unique_names).execute()

            if not embeddings_check.data:
                logger.info(f"DEBUG: Found sessions but no embeddings for them. RAG will use markdown content directly.")
                # No embeddings for current sessions - this is expected after re-scraping
                # We will use the markdown content directly instead of falling back to old embeddings
                unique_names = [session["unique_scrape_identifier"] for session in sessions_response.data]
                return await self._query_with_markdown_content(project_id, query, azure_credentials, unique_names)
            else:
                logger.info(f"DEBUG: Found {len(embeddings_check.data)} embeddings for current sessions")

        # If no current sessions found, return error - do NOT use old embeddings
        # This ensures RAG forgets all previous sessions and only uses latest scraped data

        if not sessions_response.data:
            logger.warning(f"No RAG-processed data available for project {project_id} when querying.")
            return RAGQueryResponse(
                answer="No RAG-processed data is currently available for this project. Please ensure content has been scraped and RAG ingestion is complete.",
                generation_cost=0.0,
                source_documents=[]
            )
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

    async def get_chat_messages(self, project_id: UUID, conversation_id: Optional[UUID] = None) -> List[ChatMessageResponse]:
        """
        Get chat messages for a project.

        Args:
            project_id (UUID): Project ID
            conversation_id (Optional[UUID]): Specific conversation ID

        Returns:
            List[ChatMessageResponse]: List of chat messages
        """
        if conversation_id:
            return await self.chat_history_service.get_conversation_messages(project_id, conversation_id)
        else:
            # Get the most recent conversation
            conversations = await self.chat_history_service.get_project_conversations(project_id, limit=1)
            if conversations:
                return await self.chat_history_service.get_conversation_messages(
                    project_id, UUID(conversations[0]["conversation_id"])
                )
            return []

    async def post_chat_message(
        self, 
        project_id: UUID, 
        content: str, 
        azure_credentials: Dict[str, str],
        conversation_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> ChatMessageResponse:
        """
        Post a new chat message and get a response using Azure OpenAI.

        Args:
            project_id (UUID): Project ID
            content (str): Message content
            azure_credentials (Dict[str, str]): Dictionary containing 'api_key', 'endpoint', and optional 'deployment_name'
            conversation_id (Optional[UUID]): Conversation ID, creates new if None
            session_id (Optional[UUID]): Optional scrape session ID

        Returns:
            ChatMessageResponse: Response with assistant message

        Raises:
            HTTPException: If Azure OpenAI credentials are missing
        """
        from fastapi import HTTPException
        
        # Check if Azure OpenAI credentials are provided
        if not azure_credentials or 'api_key' not in azure_credentials or 'endpoint' not in azure_credentials:
            raise HTTPException(status_code=400, detail="Azure OpenAI credentials (api_key and endpoint) are required")

        # Create or use existing conversation
        if not conversation_id:
            conversation_id = await self.chat_history_service.create_conversation(project_id, session_id)

        # Save user message
        user_message_id = await self.chat_history_service.save_message(
            project_id=project_id,
            conversation_id=conversation_id,
            session_id=session_id,
            role="user",
            content=content,
            metadata={"timestamp": datetime.now().isoformat()}
        )

        # Create user message
        user_message = ChatMessageResponse(
            id=str(user_message_id),
            role="user",
            content=content,
            timestamp=datetime.now()
        )

        # Always use the correct chat model
        deployment_name = AZURE_CHAT_MODEL

        # Query RAG using Azure OpenAI
        rag_response = await self.query_rag(
            project_id,
            content,
            azure_credentials,
            deployment_name
        )

        # Save assistant message
        assistant_message_id = await self.chat_history_service.save_message(
            project_id=project_id,
            conversation_id=conversation_id,
            session_id=session_id,
            role="assistant",
            content=rag_response.answer,
            metadata={
                "cost": rag_response.generation_cost,
                "sources": [doc["metadata"]["url"] for doc in rag_response.source_documents] if rag_response.source_documents else [],
                "model": deployment_name,
                "timestamp": datetime.now().isoformat()
            }
        )

        # Create assistant message
        assistant_message = ChatMessageResponse(
            id=str(assistant_message_id),
            role="assistant",
            content=rag_response.answer,
            timestamp=datetime.now(),
            cost=rag_response.generation_cost,
            sources=[doc["metadata"]["url"] for doc in rag_response.source_documents] if rag_response.source_documents else None
        )

        return assistant_message

    async def _query_with_markdown_content(
        self,
        project_id: UUID,
        query: str,
        azure_credentials: Dict[str, str],
        unique_names: List[str]
    ) -> RAGQueryResponse:
        """
        Query using markdown content directly when no embeddings are available.
        This is used after re-scraping when embeddings haven't been generated yet.
        """
        logger.info(f"DEBUG: Using markdown content directly for {len(unique_names)} sessions")

        # Get markdown content for all current sessions
        markdown_contents = []
        source_documents = []

        for unique_name in unique_names:
            markdown_response = supabase.table("markdowns").select("markdown, url").eq("unique_name", unique_name).execute()
            if markdown_response.data:
                markdown_data = markdown_response.data[0]
                markdown_content = markdown_data.get("markdown", "")
                url = markdown_data.get("url", "")

                if markdown_content:
                    # Truncate very long content to avoid token limits
                    max_chars = 8000  # Roughly 2000 tokens
                    if len(markdown_content) > max_chars:
                        markdown_content = markdown_content[:max_chars] + "... [content truncated]"

                    markdown_contents.append(markdown_content)
                    source_documents.append({
                        "content": markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content,
                        "metadata": {
                            "url": url,
                            "similarity": 1.0  # Direct match since we're using all content
                        }
                    })

        if not markdown_contents:
            return RAGQueryResponse(
                answer="No content available in the latest scraped data.",
                generation_cost=0.0,
                source_documents=[]
            )

        # Combine all markdown content as context
        context = "\n\n".join(markdown_contents)

        # Use Azure OpenAI to generate response
        try:
            import httpx
            api_key = azure_credentials['api_key']
            endpoint = azure_credentials['endpoint']
            deployment_name = AZURE_CHAT_MODEL

            # Handle practicehub endpoint format
            if "practicehub3994533910" in endpoint:
                url = f"https://practicehub3994533910.services.ai.azure.com/openai/deployments/{deployment_name}/chat/completions?api-version=2024-05-01-preview"
            elif "services.ai.azure.com" in endpoint:
                base_endpoint = endpoint.replace("/models", "")
                url = f"{base_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2023-05-15"
            else:
                url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2023-05-15"

            system_message = (
                "You are an AI assistant answering questions based on the latest scraped content. "
                "Provide helpful and accurate answers based only on the provided context. "
                "If the context doesn't contain relevant information, say so clearly."
            )

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {query}"}
            ]

            payload = {
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.8,
                "max_tokens": 1024,
                "model": deployment_name
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

                    # Calculate cost
                    input_chars = len(context) + len(query) + 100
                    output_chars = len(answer)
                    total_tokens = (input_chars + output_chars) / 4
                    generation_cost = (total_tokens / 1000) * 0.002

        except Exception as e:
            logger.error(f"Error calling Azure OpenAI API: {e}")
            answer = f"Sorry, I encountered an error while generating a response: {str(e)}"
            generation_cost = 0.0

        return RAGQueryResponse(
            answer=answer,
            generation_cost=generation_cost,
            source_documents=source_documents
        )
