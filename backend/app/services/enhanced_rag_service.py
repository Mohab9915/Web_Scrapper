"""
Enhanced RAG Service with intelligent data processing and response formatting.
"""
import json
import re
import httpx
import numpy as np
import os
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import UUID, uuid4
from datetime import datetime
import logging

from fastapi import HTTPException
from ..database import supabase
from ..models.chat import RAGQueryResponse, ChatMessageResponse
# Remove the import since these constants don't exist in config

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    """Enhanced RAG service with structured data processing and intelligent formatting."""
    
    def __init__(self):
        self.response_formatters = {
            'table': self._format_as_table,
            'cards': self._format_as_cards,
            'list': self._format_as_list,
            'summary': self._format_as_summary,
            'json': self._format_as_json,
            'comparison': self._format_as_comparison,
            'stats': self._format_as_stats
        }
    
    async def ingest_structured_content(
        self,
        project_id: UUID,
        session_id: UUID,
        structured_data: Dict[str, Any],
        embedding_api_keys: Dict[str, str],
        project_url_id: Optional[UUID] = None
    ) -> bool:
        """
        Enhanced ingestion that processes only structured/tabular data instead of raw markdown.
        
        Args:
            project_id: Project ID
            session_id: Session ID
            structured_data: The structured data containing tabular_data
            embedding_api_keys: API keys for embedding generation
            project_url_id: Optional project URL ID for status updates
            
        Returns:
            bool: Success status
        """
        try:
            # Extract and process only the structured data
            processed_content = self._extract_structured_content(structured_data)
            
            if not processed_content:
                logger.warning(f"No structured content found for session {session_id}")
                return False
            
            # Get the generated unique_scrape_identifier from the session
            session_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("id", str(session_id)).single().execute()

            if not session_response.data or not session_response.data.get("unique_scrape_identifier"):
                logger.error(f"No unique_scrape_identifier found for session {session_id}")
                return False

            unique_scrape_identifier = session_response.data["unique_scrape_identifier"]

            # Store the processed structured content
            supabase.table("markdowns").insert({
                "unique_name": unique_scrape_identifier,
                "markdown": processed_content,  # Use 'markdown' column, not 'content'
                "url": structured_data.get("source_url", "")
            }).execute()
            
            # Generate embeddings for structured content chunks
            chunks = self._create_smart_chunks(processed_content, structured_data)
            embeddings = await self._generate_embeddings_for_chunks(chunks, embedding_api_keys)
            
            # Store embeddings (match original format)
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                supabase.table("embeddings").insert({
                    "unique_name": unique_scrape_identifier,
                    "chunk_id": i,
                    "content": chunk,
                    "embedding": embedding
                }).execute()
            
            # Update session status (don't update unique_scrape_identifier as it's generated)
            supabase.table("scrape_sessions").update({
                "status": "rag_ingested"
            }).eq("id", str(session_id)).execute()
            
            if project_url_id:
                supabase.table("project_urls").update({
                    "status": "completed"
                }).eq("id", str(project_url_id)).execute()
            
            logger.info(f"Successfully ingested structured content for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting structured content: {e}")
            if project_url_id:
                supabase.table("project_urls").update({
                    "status": "failed"
                }).eq("id", str(project_url_id)).execute()
            return False
    
    def _extract_structured_content(self, structured_data: Dict[str, Any]) -> str:
        """
        Extract and format structured data for RAG ingestion.
        
        Args:
            structured_data: The structured data from scraping
            
        Returns:
            str: Formatted content for RAG
        """
        content_parts = []
        
        # Extract tabular data (main focus)
        tabular_data = structured_data.get("tabular_data", [])
        if tabular_data:
            content_parts.append("=== STRUCTURED DATA ===")
            
            for i, item in enumerate(tabular_data, 1):
                content_parts.append(f"\n--- Item {i} ---")
                for field, value in item.items():
                    if value and str(value).strip():
                        clean_field = field.replace('_', ' ').title()
                        content_parts.append(f"{clean_field}: {value}")
        
        # Add metadata if available
        if "title" in structured_data and structured_data["title"]:
            content_parts.insert(0, f"Page Title: {structured_data['title']}")
        
        # Add any additional structured fields
        for key, value in structured_data.items():
            if key not in ["tabular_data", "title", "raw_markdown"] and value:
                clean_key = key.replace('_', ' ').title()
                content_parts.append(f"{clean_key}: {value}")
        
        return "\n".join(content_parts)
    
    def _create_smart_chunks(self, content: str, structured_data: Dict[str, Any]) -> List[str]:
        """
        Create intelligent chunks based on structured data items.
        
        Args:
            content: The processed content
            structured_data: Original structured data
            
        Returns:
            List[str]: Smart chunks for embedding
        """
        chunks = []
        tabular_data = structured_data.get("tabular_data", [])
        
        # Create one chunk per item in tabular data
        for i, item in enumerate(tabular_data):
            chunk_parts = []
            
            # Add context
            if "title" in structured_data:
                chunk_parts.append(f"Source: {structured_data['title']}")
            
            chunk_parts.append(f"Item {i + 1}:")
            
            # Add all fields for this item
            for field, value in item.items():
                if value and str(value).strip():
                    clean_field = field.replace('_', ' ').title()
                    chunk_parts.append(f"{clean_field}: {value}")
            
            chunks.append("\n".join(chunk_parts))
        
        # If no tabular data, create chunks from the content
        if not chunks:
            # Split content into logical chunks
            lines = content.split('\n')
            current_chunk = []
            
            for line in lines:
                current_chunk.append(line)
                if len('\n'.join(current_chunk)) > 500:  # Chunk size limit
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
        
        return chunks if chunks else [content]

    async def _generate_embeddings_for_chunks(self, chunks: List[str], embedding_api_keys: Dict[str, str]) -> List[List[float]]:
        """Generate embeddings for chunks using Azure OpenAI or fallback method."""
        try:
            # Try Azure OpenAI first
            api_key = embedding_api_keys.get("api_key")
            endpoint = embedding_api_keys.get("endpoint")
            api_version = embedding_api_keys.get("api_version", "2023-05-15")

            if api_key and endpoint:
                logger.info("Using Azure OpenAI for embeddings")
                url = f"{endpoint}/openai/deployments/text-embedding-ada-002/embeddings?api-version={api_version}"

                embeddings = []
                async with httpx.AsyncClient(timeout=30.0) as client:
                    for chunk in chunks:
                        payload = {
                            "input": chunk,
                            "model": "text-embedding-ada-002"
                        }

                        response = await client.post(
                            url,
                            json=payload,
                            headers={
                                "Content-Type": "application/json",
                                "api-key": api_key
                            }
                        )

                        if response.status_code == 200:
                            result = response.json()
                            embedding = result["data"][0]["embedding"]
                            embeddings.append(embedding)
                        else:
                            logger.warning(f"Azure OpenAI embedding failed: {response.status_code}, using fallback")
                            embeddings.append(self._generate_fallback_embedding(chunk))

                return embeddings
            else:
                logger.info("Azure OpenAI credentials not available, using fallback embeddings")
                return [self._generate_fallback_embedding(chunk) for chunk in chunks]

        except Exception as e:
            logger.warning(f"Error with Azure OpenAI embeddings, using fallback: {e}")
            return [self._generate_fallback_embedding(chunk) for chunk in chunks]

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate a deterministic fallback embedding based on text content."""
        import hashlib
        import math

        # Create a deterministic hash-based embedding
        text_bytes = text.encode('utf-8')
        hash_obj = hashlib.sha256(text_bytes)
        hash_hex = hash_obj.hexdigest()

        # Convert hash to embedding vector (1536 dimensions for compatibility)
        embedding = []
        for i in range(0, len(hash_hex), 2):
            # Convert hex pairs to floats between -1 and 1
            hex_pair = hash_hex[i:i+2]
            value = int(hex_pair, 16) / 255.0  # Normalize to 0-1
            value = (value - 0.5) * 2  # Scale to -1 to 1
            embedding.append(value)

        # Extend to 1536 dimensions by repeating and adding text-based features
        while len(embedding) < 1536:
            # Add text-based features
            text_features = [
                len(text) / 1000.0,  # Text length feature
                text.count(' ') / 100.0,  # Word count feature
                text.count('\n') / 10.0,  # Line count feature
                sum(1 for c in text if c.isupper()) / 100.0,  # Uppercase count
                sum(1 for c in text if c.isdigit()) / 100.0,  # Digit count
            ]

            # Repeat existing embedding with slight variations
            for i, val in enumerate(embedding[:min(100, len(embedding))]):
                if len(embedding) >= 1536:
                    break
                # Add slight variation based on text features
                variation = text_features[i % len(text_features)] * 0.1
                embedding.append(val + variation)

        # Ensure exactly 1536 dimensions
        embedding = embedding[:1536]

        # Normalize the vector
        magnitude = math.sqrt(sum(x*x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    async def enhanced_query_rag(
        self,
        project_id: UUID,
        query: str,
        deployment_name: str = None
    ) -> RAGQueryResponse:
        """
        Enhanced RAG query with intelligent response formatting.

        Args:
            project_id: Project ID
            query: User query
            deployment_name: Model deployment name

        Returns:
            RAGQueryResponse: Enhanced formatted response
        """
        # Get Azure OpenAI credentials from environment variables
        azure_credentials = {
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        }

        if not azure_credentials["api_key"] or not azure_credentials["endpoint"]:
            raise HTTPException(status_code=500, detail="Azure OpenAI credentials not configured in environment variables")
        try:
            # Get relevant context
            context_chunks = await self._get_enhanced_context(project_id, query)

            if not context_chunks:
                # Try to get any available data from the project
                logger.warning(f"No enhanced context found for project {project_id}, trying fallback")
                fallback_context = await self._get_fallback_context(project_id)

                if not fallback_context:
                    return RAGQueryResponse(
                        answer="I couldn't find any relevant information in the scraped data for your query. Please make sure you have scraped some data first.",
                        generation_cost=0.0,
                        source_documents=[]
                    )
                else:
                    context_chunks = fallback_context

            # Analyze query intent and determine response format
            query_intent = self._analyze_query_intent(query)
            response_format = self._determine_response_format(query, query_intent)

            # For conversational responses, we don't need scraped data
            if response_format == 'conversational' and not context_chunks:
                # Generate a conversational response without requiring data
                response = await self._generate_conversational_response(
                    query, azure_credentials, deployment_name
                )
            else:
                # Build enhanced context
                context = self._build_enhanced_context(context_chunks, query_intent)

                # Generate response with intelligent formatting
                response = await self._generate_enhanced_response(
                    query, context, query_intent, response_format, azure_credentials, deployment_name
                )

            return response

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error in enhanced RAG query: {str(e)}\nFull traceback: {error_details}")
            return RAGQueryResponse(
                answer=f"I encountered an error while processing your query: {str(e)}",
                generation_cost=0.0,
                source_documents=[]
            )

    async def _get_enhanced_context(self, project_id: UUID, query: str) -> List[Dict[str, Any]]:
        """Get relevant context chunks with enhanced matching."""
        # Check if project has RAG enabled
        project_response = supabase.table("projects").select("rag_enabled").eq("id", str(project_id)).single().execute()
        if not project_response.data or not project_response.data.get("rag_enabled"):
            return []

        # Get sessions with structured data
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", str(project_id)).eq("status", "rag_ingested").execute()

        if not sessions_response.data:
            return []

        unique_names = [session["unique_scrape_identifier"] for session in sessions_response.data]

        # Enhanced keyword matching
        keywords = self._extract_enhanced_keywords(query)

        # Get embeddings-based matches using keyword search
        try:
            # Get all chunks for this project's sessions
            all_chunks = []
            for unique_name in unique_names:
                chunks_response = supabase.table("embeddings").select("*").eq("unique_name", unique_name).execute()
                if chunks_response.data:
                    all_chunks.extend(chunks_response.data)

            # Score chunks based on keyword relevance
            scored_chunks = []
            for chunk in all_chunks:
                score = self._calculate_relevance_score(chunk["content"], keywords, query)
                if score > 0.05:  # Lower threshold for better recall
                    scored_chunks.append((chunk, score))

            # Sort by relevance and return top matches
            scored_chunks.sort(key=lambda x: x[1], reverse=True)
            top_chunks = [chunk for chunk, score in scored_chunks[:8]]

            logger.info(f"Enhanced context found {len(top_chunks)} relevant chunks for query: {query}")
            return top_chunks

        except Exception as e:
            logger.error(f"Error getting enhanced context: {e}")
            return []

    async def _get_fallback_context(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get fallback context when enhanced context is not available."""
        try:
            # Get sessions with RAG data
            sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", str(project_id)).eq("status", "rag_ingested").execute()

            if not sessions_response.data:
                logger.warning(f"No RAG-ingested sessions found for project {project_id}")
                return []

            unique_names = [session["unique_scrape_identifier"] for session in sessions_response.data]

            # Get all chunks from embeddings table as fallback
            all_chunks = []
            for unique_name in unique_names:
                chunks_response = supabase.table("embeddings").select("*").eq("unique_name", unique_name).execute()
                if chunks_response.data:
                    all_chunks.extend(chunks_response.data)

            logger.info(f"Found {len(all_chunks)} fallback context chunks for project {project_id}")
            return all_chunks

        except Exception as e:
            logger.error(f"Error getting fallback context: {e}")
            return []

    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze user query to determine intent and requirements."""
        query_lower = query.lower()

        intent = {
            'type': 'general',
            'wants_data_display': False,
            'wants_comparison': False,
            'wants_statistics': False,
            'wants_summary': False,
            'wants_specific_item': False,
            'wants_list': False,
            'wants_count': False,
            'wants_price_info': False,
            'wants_search': False
        }

        # Data display patterns
        display_patterns = [
            'show', 'display', 'list', 'give me', 'what are', 'tell me about',
            'find', 'get', 'retrieve', 'present', 'output'
        ]

        # Comparison patterns
        comparison_patterns = [
            'compare', 'difference', 'vs', 'versus', 'better', 'best', 'worst',
            'cheaper', 'expensive', 'higher', 'lower', 'more', 'less'
        ]

        # Statistics patterns
        stats_patterns = [
            'how many', 'count', 'total', 'average', 'mean', 'sum', 'statistics',
            'stats', 'number of', 'quantity'
        ]

        # Summary patterns
        summary_patterns = [
            'summary', 'summarize', 'overview', 'brief', 'outline', 'recap'
        ]

        # Specific item patterns
        specific_patterns = [
            'details about', 'information about', 'tell me about', 'what is',
            'describe', 'explain'
        ]

        # Price patterns
        price_patterns = [
            'price', 'cost', 'expensive', 'cheap', 'budget', 'affordable',
            'pricing', 'money', '$', 'dollar'
        ]

        # Analyze patterns
        if any(pattern in query_lower for pattern in display_patterns):
            intent['wants_data_display'] = True
            intent['type'] = 'display'

        if any(pattern in query_lower for pattern in comparison_patterns):
            intent['wants_comparison'] = True
            intent['type'] = 'comparison'

        if any(pattern in query_lower for pattern in stats_patterns):
            intent['wants_statistics'] = True
            intent['wants_count'] = True
            intent['type'] = 'statistics'

        if any(pattern in query_lower for pattern in summary_patterns):
            intent['wants_summary'] = True
            intent['type'] = 'summary'

        if any(pattern in query_lower for pattern in specific_patterns):
            intent['wants_specific_item'] = True
            intent['type'] = 'specific'

        if any(pattern in query_lower for pattern in price_patterns):
            intent['wants_price_info'] = True

        # List indicators
        if any(word in query_lower for word in ['all', 'every', 'each', 'list']):
            intent['wants_list'] = True

        return intent

    def _determine_response_format(self, query: str, intent: Dict[str, Any]) -> str:
        """Determine the best response format based on query intent."""
        query_lower = query.lower()

        # Chart format requests - only when explicitly requested
        explicit_chart_keywords = [
            'chart', 'graph', 'plot', 'visualize', 'visualization',
            'bar chart', 'pie chart', 'line chart', 'create a chart',
            'show me a chart', 'make a chart', 'generate a chart',
            'draw a chart', 'display a chart'
        ]
        if any(keyword in query_lower for keyword in explicit_chart_keywords):
            return 'chart'

        # Explicit format requests
        if 'table' in query_lower or 'tabular' in query_lower:
            return 'table'
        elif 'json' in query_lower:
            return 'json'
        elif 'summary' in query_lower or intent['wants_summary']:
            return 'summary'
        elif 'compare' in query_lower or intent['wants_comparison']:
            return 'comparison'
        elif 'statistics' in query_lower or intent['wants_statistics']:
            return 'stats'
        elif intent['wants_list'] or 'list' in query_lower:
            return 'list'
        elif intent['wants_specific_item']:
            return 'cards'
        else:
            # Default to conversational response for general queries
            return 'conversational'

    def _extract_enhanced_keywords(self, query: str) -> List[str]:
        """Extract enhanced keywords from query."""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'what', 'how', 'when', 'where', 'why', 'who', 'tell', 'me', 'about'}

        # Extract words and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        # Add phrase extraction for better matching
        phrases = []
        if 'price' in query.lower():
            phrases.extend(['price', 'cost', 'pricing'])
        if 'product' in query.lower():
            phrases.extend(['product', 'item'])
        if 'description' in query.lower():
            phrases.extend(['description', 'details'])

        # Add country-specific terms
        if any(word in query.lower() for word in ['country', 'countries', 'nation', 'capital', 'population', 'area']):
            phrases.extend(['capital', 'population', 'area', 'country'])

        # Preserve important proper nouns (country names, etc.)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', query)
        keywords.extend([noun.lower() for noun in proper_nouns])

        return list(set(keywords + phrases))

    def _calculate_relevance_score(self, content: str, keywords: List[str], query: str) -> float:
        """Calculate relevance score for content."""
        content_lower = content.lower()
        query_lower = query.lower()

        score = 0.0

        # Keyword matching with higher weight for important terms
        for keyword in keywords:
            if keyword in content_lower:
                # Give higher weight to country names and specific terms
                if keyword in ['russia', 'china', 'usa', 'india', 'brazil', 'canada', 'australia', 'germany', 'france', 'japan']:
                    score += 5.0  # High weight for country names
                elif keyword in ['capital', 'population', 'area', 'country']:
                    score += 2.0  # Medium weight for country attributes
                else:
                    score += 1.0  # Normal weight

        # Phrase matching (higher weight)
        if len(keywords) > 1:
            for i in range(len(keywords) - 1):
                phrase = f"{keywords[i]} {keywords[i+1]}"
                if phrase in content_lower:
                    score += 3.0

        # Exact query matching (highest weight)
        if query_lower in content_lower:
            score += 10.0

        # Country section matching (look for ### CountryName pattern)
        import re
        country_pattern = r'###\s*([^#\n]+)'
        matches = re.findall(country_pattern, content, re.IGNORECASE)
        for match in matches:
            if any(keyword in match.lower() for keyword in keywords):
                score += 8.0  # Very high weight for country section headers

        # Normalize by content length (but don't make it too small)
        content_length = max(len(content.split()), 10)
        return score / (content_length / 100)

    def _build_enhanced_context(self, chunks: List[Dict[str, Any]], intent: Dict[str, Any]) -> str:
        """Build enhanced context based on query intent."""
        if not chunks:
            return ""

        context_parts = []

        # Add structured data header
        context_parts.append("=== AVAILABLE DATA ===")

        for i, chunk in enumerate(chunks, 1):
            content = chunk.get("content", "")
            context_parts.append(f"\n--- Data Source {i} ---")
            context_parts.append(content)

        return "\n".join(context_parts)

    async def _generate_enhanced_response(
        self,
        query: str,
        context: str,
        intent: Dict[str, Any],
        response_format: str,
        azure_credentials: Dict[str, str],
        deployment_name: str = None
    ) -> RAGQueryResponse:
        """Generate enhanced response with intelligent formatting."""

        # Build enhanced system prompt based on intent and format
        system_prompt = self._build_system_prompt(intent, response_format)

        # Build user prompt with formatting instructions
        user_prompt = self._build_user_prompt(query, context, response_format)

        try:
            # Use Azure OpenAI
            api_key = azure_credentials.get("api_key")
            endpoint = azure_credentials.get("endpoint")
            api_version = azure_credentials.get("api_version", "2024-12-01-preview")
            deployment = deployment_name or "gpt-4o"

            url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            payload = {
                "messages": messages,
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 2048
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "api-key": api_key
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"]

                    # Apply post-processing formatting
                    formatted_answer = self._apply_post_formatting(answer, response_format)

                    # Calculate cost (approximate)
                    usage = result.get("usage", {})
                    total_tokens = usage.get("total_tokens", 0)
                    cost = (total_tokens / 1000) * 0.002  # Approximate cost

                    return RAGQueryResponse(
                        answer=formatted_answer,
                        generation_cost=cost,
                        source_documents=[]  # Will be populated by caller
                    )
                else:
                    error_msg = f"Azure OpenAI API error: {response.status_code}"
                    return RAGQueryResponse(
                        answer=error_msg,
                        generation_cost=0.0,
                        source_documents=[]
                    )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error generating enhanced response: {str(e)}\nFull traceback: {error_details}")
            return RAGQueryResponse(
                answer=f"I encountered an error while generating the response: {str(e)}",
                generation_cost=0.0,
                source_documents=[]
            )

    async def _generate_conversational_response(
        self,
        query: str,
        azure_credentials: Dict[str, str],
        deployment_name: str = None
    ) -> RAGQueryResponse:
        """Generate a conversational response without requiring scraped data."""

        system_prompt = """You are a helpful AI assistant. Respond to the user in a natural, conversational manner. Be friendly and helpful. If the user asks about data or products that you don't have access to, let them know you can help analyze their scraped data if they have specific questions about it."""

        user_prompt = f"User message: {query}\n\nPlease respond naturally and conversationally."

        try:
            # Use Azure OpenAI
            api_key = azure_credentials.get("api_key")
            endpoint = azure_credentials.get("endpoint")
            api_version = azure_credentials.get("api_version", "2024-12-01-preview")
            deployment = deployment_name or "gpt-4o"

            url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            payload = {
                "messages": messages,
                "temperature": 0.7,  # Higher temperature for more natural conversation
                "top_p": 0.9,
                "max_tokens": 1024
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "api-key": api_key
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"]

                    # Calculate cost (approximate)
                    usage = result.get("usage", {})
                    total_tokens = usage.get("total_tokens", 0)
                    cost = (total_tokens / 1000) * 0.002  # Approximate cost

                    return RAGQueryResponse(
                        answer=answer,
                        generation_cost=cost,
                        source_documents=[]
                    )
                else:
                    error_msg = f"Azure OpenAI API error: {response.status_code}"
                    return RAGQueryResponse(
                        answer=error_msg,
                        generation_cost=0.0,
                        source_documents=[]
                    )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error generating conversational response: {str(e)}\nFull traceback: {error_details}")
            return RAGQueryResponse(
                answer="Hello! I'm here to help you with your questions. Feel free to ask me anything!",
                generation_cost=0.0,
                source_documents=[]
            )

    def _build_system_prompt(self, intent: Dict[str, Any], response_format: str) -> str:
        """Build system prompt based on intent and format."""
        base_prompt = """You are a helpful AI assistant with access to scraped e-commerce data. You can have normal conversations and also help analyze product data when needed.

For general conversations (greetings, questions not about data), respond naturally and conversationally.
For data-related questions, use the available product information to provide helpful answers.
When asked to create charts, graphs, or visualizations, you MUST respond with ONLY the JSON chart data in the specified format - no additional text or explanations."""

        format_instructions = {
            'table': "Format your response as a clean, readable table using markdown syntax with proper headers and alignment.",
            'cards': "Format your response as individual product cards with clear sections for each item, using headers and bullet points for easy reading.",
            'list': "Format your response as a numbered or bulleted list with clear, concise information for each item.",
            'summary': "Provide a concise summary with key insights and highlights from the data.",
            'json': "Structure your response in a JSON-like format that's easy to read and parse.",
            'comparison': "Create a detailed comparison highlighting differences, similarities, and recommendations.",
            'stats': "Provide statistical analysis with numbers, counts, averages, and key metrics.",
            'conversational': "Respond in a natural, conversational manner. Be helpful and friendly. Only use the scraped data if it's relevant to the user's question. For general greetings or questions not related to the data, respond conversationally without forcing data into the response.",
            'chart': """IMPORTANT: You MUST respond with ONLY a JSON code block containing chart data. Do not include any other text.

Format your response as chart data in JSON format. Use this exact structure:
```json
{
  "chart_type": "bar|pie|line|table|stats",
  "title": "Chart Title",
  "description": "Brief description of the data",
  "data": {
    "labels": ["Label1", "Label2", "Label3"],
    "values": [10, 20, 30],
    "datasets": [{"label": "Dataset Name", "data": [10, 20, 30], "backgroundColor": ["#8B5CF6", "#A78BFA", "#C4B5FD"]}]
  }
}
```

CHART TYPE SELECTION:
- Use "bar" for comparing different categories or items
- Use "pie" for showing proportions or percentages of a whole
- Use "line" for showing trends over time or sequences
- Use "table" for detailed data display with multiple columns
- Use "stats" for key metrics, counts, averages, or summary statistics

IMPORTANT: Your response must start with ```json and end with ``` - no other text allowed."""
        }

        intent_instructions = ""
        if intent['wants_price_info']:
            intent_instructions += " Focus on pricing information, costs, and value comparisons."
        if intent['wants_statistics']:
            intent_instructions += " Include relevant statistics, counts, and numerical analysis."
        if intent['wants_comparison']:
            intent_instructions += " Highlight comparisons and differences between items."

        return f"{base_prompt}\n\n{format_instructions.get(response_format, '')}{intent_instructions}\n\nAlways base your response only on the provided data and be helpful and informative."

    def _build_user_prompt(self, query: str, context: str, response_format: str) -> str:
        """Build user prompt with context and formatting instructions."""
        return f"""Based on the following scraped data, please answer the user's question in {response_format} format:

SCRAPED DATA:
{context}

USER QUESTION: {query}

Please provide a well-formatted, helpful response based only on the available data."""

    def _apply_post_formatting(self, answer: str, response_format: str) -> str:
        """Apply post-processing formatting to the response."""
        if response_format == 'table':
            return self._enhance_table_formatting(answer)
        elif response_format == 'cards':
            return self._enhance_card_formatting(answer)
        elif response_format == 'list':
            return self._enhance_list_formatting(answer)
        elif response_format == 'json':
            return self._enhance_json_formatting(answer)
        elif response_format == 'chart':
            return self._enhance_chart_formatting(answer)
        else:
            return answer

    def _enhance_table_formatting(self, answer: str) -> str:
        """Enhance table formatting."""
        # Add table styling and ensure proper markdown
        if '|' in answer and not answer.startswith('```'):
            return f"```\n{answer}\n```"
        return answer

    def _enhance_card_formatting(self, answer: str) -> str:
        """Enhance card formatting."""
        # Add visual separators and improve readability
        lines = answer.split('\n')
        enhanced_lines = []

        for line in lines:
            if line.strip().startswith('#'):
                enhanced_lines.append(f"\n{line}")
            elif line.strip() and not line.startswith(' '):
                enhanced_lines.append(f"**{line}**" if not line.startswith('**') else line)
            else:
                enhanced_lines.append(line)

        return '\n'.join(enhanced_lines)

    def _enhance_list_formatting(self, answer: str) -> str:
        """Enhance list formatting."""
        # Ensure proper list formatting
        lines = answer.split('\n')
        enhanced_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(('-', '*', '1.', '2.', '3.', '4.', '5.')):
                if stripped.startswith('#'):
                    enhanced_lines.append(line)
                else:
                    enhanced_lines.append(f"• {stripped}")
            else:
                enhanced_lines.append(line)

        return '\n'.join(enhanced_lines)

    def _enhance_json_formatting(self, answer: str) -> str:
        """Enhance JSON formatting."""
        # Wrap in code block if not already
        if not answer.strip().startswith('```'):
            return f"```json\n{answer}\n```"
        return answer

    def _enhance_chart_formatting(self, answer: str) -> str:
        """Enhance chart formatting and validate JSON structure."""
        import json
        import re

        try:
            # Extract JSON from the response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', answer, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                chart_data = json.loads(json_str)

                # Validate required fields
                required_fields = ['chart_type', 'title', 'data']
                if all(field in chart_data for field in required_fields):
                    # Ensure proper structure
                    if 'labels' not in chart_data['data'] and 'values' in chart_data['data']:
                        # Generate labels if missing
                        values = chart_data['data']['values']
                        chart_data['data']['labels'] = [f"Item {i+1}" for i in range(len(values))]

                    # Return the enhanced JSON
                    return f"```json\n{json.dumps(chart_data, indent=2)}\n```"

            # If no valid JSON found, return original
            return answer

        except (json.JSONDecodeError, KeyError, TypeError):
            # If JSON parsing fails, return original answer
            return answer

    # Formatter methods (placeholders for the response_formatters dict)
    def _format_as_table(self, data: List[Dict[str, Any]]) -> str:
        """Format data as a table."""
        # Implementation for direct data formatting
        pass

    def _format_as_cards(self, data: List[Dict[str, Any]]) -> str:
        """Format data as cards."""
        # Implementation for direct data formatting
        pass

    def _format_as_list(self, data: List[Dict[str, Any]]) -> str:
        """Format data as a list."""
        # Implementation for direct data formatting
        pass

    def _format_as_summary(self, data: List[Dict[str, Any]]) -> str:
        """Format data as a summary."""
        # Implementation for direct data formatting
        pass

    def _format_as_json(self, data: List[Dict[str, Any]]) -> str:
        """Format data as JSON."""
        # Implementation for direct data formatting
        pass

    def _format_as_comparison(self, data: List[Dict[str, Any]]) -> str:
        """Format data as a comparison."""
        # Implementation for direct data formatting
        pass

    def _format_as_stats(self, data: List[Dict[str, Any]]) -> str:
        """Format data as statistics."""
        # Implementation for direct data formatting
        pass
