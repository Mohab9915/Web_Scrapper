"""
Service for RAG functionality.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import Depends, HTTPException
import uuid
import time
from datetime import datetime

from app.database import supabase
from app.models.chat import ChatMessageResponse, RAGQueryResponse
from app.utils.text_processing import chunk_text
from app.utils.embedding import generate_embeddings, calculate_embedding_cost, process_chunks_with_batching
from app.utils.firecrawl_api import AZURE_EMBEDDING_MODEL, AZURE_CHAT_MODEL
from app.utils.websocket_manager import manager

class RAGService:
    """Service for RAG functionality."""

    async def get_chat_messages(self, project_id: UUID) -> List[ChatMessageResponse]:
        """
        Get chat messages for a project.

        Args:
            project_id (UUID): Project ID

        Returns:
            List[ChatMessageResponse]: List of chat messages
        """
        # In a real implementation, this would retrieve messages from a database
        # For now, we'll return an empty list
        return []

    async def query_rag(
        self,
        project_id: UUID,
        query: str,
        llm_model: str,
        azure_credentials: Dict[str, str]
    ) -> RAGQueryResponse:
        """
        Query the RAG system using Azure OpenAI Service.

        Args:
            project_id (UUID): Project ID
            query (str): Query text
            llm_model (str): Azure OpenAI deployment name (e.g., "gpt-35-turbo")
            azure_credentials (Dict[str, str]): Dictionary containing 'api_key', 'endpoint', and optional 'deployment_name'

        Returns:
            RAGQueryResponse: Response with answer and sources

        Raises:
            HTTPException: If project not found, RAG not enabled, no data available, or missing credentials
        """
        # Check if Azure OpenAI credentials are provided
        if not azure_credentials or 'api_key' not in azure_credentials or 'endpoint' not in azure_credentials:
            raise HTTPException(status_code=400, detail="Azure OpenAI credentials (api_key and endpoint) are required")

        # Check if project exists and has RAG enabled
        project_response = supabase.table("projects").select("rag_enabled").eq("id", str(project_id)).single().execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        if not project_response.data["rag_enabled"]:
            raise HTTPException(status_code=400, detail="RAG is not enabled for this project")

        # Get all unique scrape identifiers for this project
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier").eq("project_id", str(project_id)).eq("status", "rag_ingested").execute()
        if not sessions_response.data:
            raise HTTPException(status_code=400, detail="No RAG-processed data available for this project")

        unique_names = [session["unique_scrape_identifier"] for session in sessions_response.data]

        # Generate embedding for the query using Azure OpenAI
        query_embedding = await generate_embeddings(query, azure_credentials)

        # Search for similar content
        rpc_response = supabase.rpc(
            "match_embeddings_filtered",
            {
                "query_embedding": query_embedding,
                "match_count": 5,
                "p_unique_names": unique_names
            }
        ).execute()

        if not rpc_response.data:
            return RAGQueryResponse(
                answer="I couldn't find any relevant information in the scraped data.",
                generation_cost=0.0,
                source_documents=[]
            )

        # Build context from matched chunks
        context_chunks = [chunk["content"] for chunk in rpc_response.data]
        context = "\n\n".join(context_chunks)

        # Call Azure OpenAI API to generate a response
        try:
            import httpx

            # Get Azure OpenAI credentials
            api_key = azure_credentials['api_key']
            endpoint = azure_credentials['endpoint']

            # Determine which deployment to use
            # Always use the correct chat model
            deployment_name = AZURE_CHAT_MODEL

            # Determine the correct API endpoint format based on the endpoint URL
            if "services.ai.azure.com" in endpoint:
                # Azure AI Studio format - use the standard Azure OpenAI format
                # Remove "/models" if it's in the endpoint
                base_endpoint = endpoint.replace("/models", "")
                url = f"{base_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2023-05-15"
                print(f"Using Azure AI Studio chat API URL: {url}")
            else:
                # Traditional Azure OpenAI format
                url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2023-05-15"
                print(f"Using Azure OpenAI chat API URL: {url}")

            # Construct the system and user messages
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant answering questions based on provided context. Answer the question based only on the provided context. If the context doesn't contain relevant information, say so."
                },
                {
                    "role": "user",
                    "content": f"CONTEXT:\n{context}\n\nQUESTION: {query}"
                }
            ]

            # Request payload - use the same format for all Azure endpoints
            payload = {
                "messages": messages,
                "temperature": 0.2,
                "top_p": 0.8,
                "max_tokens": 1024
            }

            # Make the API request
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
                    print(f"Error from Azure OpenAI API: {response.text}")
                    answer = "Sorry, I encountered an error while generating a response."
                    generation_cost = 0.0
                else:
                    # Extract answer from response
                    response_data = response.json()
                    answer = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    # Calculate approximate cost
                    # Azure OpenAI GPT-3.5 Turbo costs approximately $0.002 per 1K tokens (input + output)
                    # A simple approximation: 1 token ≈ 4 characters
                    input_chars = len(context) + len(query) + 100  # Adding 100 for system message
                    output_chars = len(answer)
                    total_tokens = (input_chars + output_chars) / 4
                    generation_cost = (total_tokens / 1000) * 0.002

        except Exception as e:
            print(f"Error calling Azure OpenAI API: {e}")
            answer = f"Sorry, I encountered an error while generating a response: {str(e)}"
            generation_cost = 0.0

        # Get source documents
        source_documents = []
        for chunk in rpc_response.data:
            # Get the URL for this chunk
            markdown_response = supabase.table("markdowns").select("url").eq("unique_name", chunk["unique_name"]).single().execute()
            if markdown_response.data:
                source_documents.append({
                    "content": chunk["content"],
                    "metadata": {
                        "url": markdown_response.data["url"],
                        "similarity": chunk["similarity"]
                    }
                })

        return RAGQueryResponse(
            answer=answer,
            generation_cost=generation_cost,
            source_documents=source_documents
        )

    async def post_chat_message(self, project_id: UUID, content: str, azure_credentials: Dict[str, str]) -> ChatMessageResponse:
        """
        Post a new chat message and get a response using Azure OpenAI.

        Args:
            project_id (UUID): Project ID
            content (str): Message content
            azure_credentials (Dict[str, str]): Dictionary containing 'api_key', 'endpoint', and optional 'deployment_name'

        Returns:
            ChatMessageResponse: Response with assistant message

        Raises:
            HTTPException: If Azure OpenAI credentials are missing
        """
        # Check if Azure OpenAI credentials are provided
        if not azure_credentials or 'api_key' not in azure_credentials or 'endpoint' not in azure_credentials:
            raise HTTPException(status_code=400, detail="Azure OpenAI credentials (api_key and endpoint) are required")

        # Create user message
        user_message = ChatMessageResponse(
            id=f"msg_{uuid.uuid4()}",
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
            deployment_name,
            azure_credentials
        )

        # Create assistant message
        assistant_message = ChatMessageResponse(
            id=f"msg_{uuid.uuid4()}",
            role="assistant",
            content=rag_response.answer,
            timestamp=datetime.now(),
            cost=rag_response.generation_cost,
            sources=[doc["metadata"]["url"] for doc in rag_response.source_documents] if rag_response.source_documents else None
        )

        return assistant_message

    async def ingest_scraped_content(
        self,
        project_id: UUID,
        session_id: UUID,
        markdown_content: str,
        azure_credentials: Optional[Dict[str, str]]
    ) -> bool:
        """
        Ingest scraped content into the RAG system using Azure OpenAI for embeddings.

        Args:
            project_id (UUID): Project ID
            session_id (UUID): Session ID
            markdown_content (str): Markdown content
            azure_credentials (Optional[Dict[str, str]]): Dictionary containing 'api_key', 'endpoint', and optional 'deployment_name'

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ValueError: If Azure OpenAI credentials are missing
        """
        try:
            # Check if Azure OpenAI credentials are provided
            if not azure_credentials or 'api_key' not in azure_credentials or 'endpoint' not in azure_credentials:
                print("Error: Azure OpenAI credentials (api_key and endpoint) are required for ingestion")
                await manager.update_progress(
                    str(project_id),
                    str(session_id),
                    {
                        "status": "error",
                        "message": "Azure OpenAI credentials are missing or incomplete",
                        "error": "Missing credentials"
                    }
                )
                return False

            # Get session data
            session_response = supabase.table("scrape_sessions").select("*").eq("id", str(session_id)).single().execute()
            if not session_response.data:
                await manager.update_progress(
                    str(project_id),
                    str(session_id),
                    {
                        "status": "error",
                        "message": "Session not found",
                        "error": "Session not found"
                    }
                )
                return False

            session = session_response.data
            unique_scrape_identifier = session["unique_scrape_identifier"]
            url = session["url"]

            # Insert into markdowns table
            markdown_response = supabase.table("markdowns").insert({
                "unique_name": unique_scrape_identifier,
                "url": url,
                "markdown": markdown_content
            }).execute()

            if not markdown_response.data:
                await manager.update_progress(
                    str(project_id),
                    str(session_id),
                    {
                        "status": "error",
                        "message": "Failed to insert markdown content",
                        "error": "Database error"
                    }
                )
                return False

            # Chunk the markdown content
            chunks = await chunk_text(markdown_content)
            total_chunks = len(chunks)

            # Send initial progress update
            await manager.update_progress(
                str(project_id),
                str(session_id),
                {
                    "status": "processing",
                    "message": "Starting RAG ingestion...",
                    "current_chunk": 0,
                    "total_chunks": total_chunks,
                    "percent_complete": 0
                }
            )

            # Generate embeddings for chunks using batched processing
            start_time = time.time()

            # Update progress to indicate batch processing has started
            await manager.update_progress(
                str(project_id),
                str(session_id),
                {
                    "status": "processing",
                    "message": f"Processing {total_chunks} chunks in batches...",
                    "current_chunk": 0,
                    "total_chunks": total_chunks,
                    "percent_complete": 5
                }
            )

            # Process chunks with batching
            embeddings = await process_chunks_with_batching(chunks, azure_credentials)

            # Calculate processing time and performance metrics
            processing_time = time.time() - start_time
            chunks_per_second = total_chunks / processing_time if processing_time > 0 else 0

            # Update progress to indicate batch processing is complete
            await manager.update_progress(
                str(project_id),
                str(session_id),
                {
                    "status": "processing",
                    "message": f"Batch processing complete. Processed {total_chunks} chunks in {processing_time:.2f} seconds ({chunks_per_second:.2f} chunks/sec)",
                    "current_chunk": total_chunks,
                    "total_chunks": total_chunks,
                    "percent_complete": 80
                }
            )

            # Insert embeddings into database
            await manager.update_progress(
                str(project_id),
                str(session_id),
                {
                    "status": "processing",
                    "message": "Storing embeddings in database...",
                    "current_chunk": total_chunks,
                    "total_chunks": total_chunks,
                    "percent_complete": 90
                }
            )

            # Insert all embeddings into the database
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Insert into embeddings table
                supabase.table("embeddings").insert({
                    "unique_name": unique_scrape_identifier,
                    "chunk_id": i,
                    "content": chunk,
                    "embedding": embedding
                }).execute()

            # Update session status
            supabase.table("scrape_sessions").update({
                "status": "rag_ingested"
            }).eq("id", str(session_id)).execute()

            # Send final progress update
            await manager.update_progress(
                str(project_id),
                str(session_id),
                {
                    "status": "completed",
                    "message": "RAG ingestion completed successfully!",
                    "current_chunk": total_chunks,
                    "total_chunks": total_chunks,
                    "percent_complete": 100
                }
            )

            return True
        except Exception as e:
            # Send error progress update
            await manager.update_progress(
                str(project_id),
                str(session_id),
                {
                    "status": "error",
                    "message": f"Error during RAG ingestion: {str(e)}",
                    "error": str(e)
                }
            )

            # Re-raise the exception
            raise
