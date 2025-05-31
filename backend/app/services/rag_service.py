"""
Service for RAG functionality.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import Depends, HTTPException
import uuid
import time
from datetime import datetime

from ..database import supabase
from ..models.chat import ChatMessageResponse, ChatMessageCreate, ChatMessageRequest, RAGQueryRequest, RAGQueryResponse
from ..utils.text_processing import chunk_text
from ..utils.embedding import generate_embeddings, calculate_embedding_cost, process_chunks_with_batching
from ..scraper_modules.assets import AZURE_EMBEDDING_MODEL, AZURE_CHAT_MODEL # Corrected path
from ..utils.websocket_manager import manager
from .chat_history_service import ChatHistoryService # Corrected relative import

class RAGService:
    """Service for RAG functionality."""
    
    def __init__(self):
        self.chat_history_service = ChatHistoryService()

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

    async def query_rag(
        self,
        project_id: UUID,
        query: str,
        llm_model: str,
        azure_credentials: Dict[str, str],
        conversation_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
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
        # Look for sessions with 'rag_ingested' status first, but also accept 'scraped' sessions if project has RAG enabled
        sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier, status, url").eq("project_id", str(project_id)).eq("status", "rag_ingested").execute()

        # If no rag_ingested sessions found, check if project has RAG enabled and look for scraped sessions
        if not sessions_response.data:
            # Check if project has RAG enabled
            project_response = supabase.table("projects").select("rag_enabled").eq("id", str(project_id)).single().execute()
            project_rag_enabled = project_response.data.get("rag_enabled", False) if project_response.data else False

            if project_rag_enabled:
                # If RAG is enabled, also accept 'scraped' sessions as they contain the data needed for RAG
                sessions_response = supabase.table("scrape_sessions").select("unique_scrape_identifier, status, url").eq("project_id", str(project_id)).eq("status", "scraped").execute()
                print(f"DEBUG: RAG enabled project, found {len(sessions_response.data)} scraped sessions")

        # Debug: Check all sessions for this project
        all_sessions_response = supabase.table("scrape_sessions").select("id, status, url, unique_scrape_identifier").eq("project_id", str(project_id)).execute()
        print(f"DEBUG: All sessions for project {project_id}:")
        for session in all_sessions_response.data:
            print(f"  Session {session['id']}: status={session['status']}, url={session['url']}, unique_id={session.get('unique_scrape_identifier', 'None')}")

        if not sessions_response.data:
            # Check if there are any sessions at all
            if not all_sessions_response.data:
                error_msg = "No scraped data found for this project. Please scrape some URLs first."
            else:
                scraped_count = len([s for s in all_sessions_response.data if s['status'] == 'scraped'])
                rag_ingested_count = len([s for s in all_sessions_response.data if s['status'] == 'rag_ingested'])
                error_msg = f"No RAG-processed data available for this project. Found {len(all_sessions_response.data)} total sessions ({scraped_count} scraped, {rag_ingested_count} rag-ingested). Please ensure RAG is enabled and Azure OpenAI credentials are configured."
            raise HTTPException(status_code=400, detail=error_msg)

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
            deployment_name,
            azure_credentials,
            conversation_id,
            session_id
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

    async def ingest_scraped_content(
        self,
        project_id: UUID,
        session_id: UUID,
        markdown_content: str,
        azure_credentials: Optional[Dict[str, str]],
        structured_data: Optional[Dict[str, Any]] = None,
        project_url_id: Optional[UUID] = None  # Added project_url_id
    ) -> bool:
        """
        Ingest scraped content into the RAG system using Azure OpenAI for embeddings.
        If structured_data is provided, it will be used instead of the full markdown content.

        Args:
            project_id (UUID): Project ID
            session_id (UUID): Session ID
            markdown_content (str): Markdown content (used as fallback)
            azure_credentials (Optional[Dict[str, str]]): Dictionary containing 'api_key', 'endpoint', and optional 'deployment_name'
            structured_data (Optional[Dict[str, Any]]): Structured data containing tabular_data to ingest instead of full markdown
            project_url_id (Optional[UUID]): ID of the project_urls entry to update status

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
                    str(project_id), str(session_id),
                    {"status": "error", "message": "Azure OpenAI credentials are missing or incomplete", "error": "Missing credentials"}
                )
                if project_url_id:
                    supabase.table("project_urls").update({"status": "failed"}).eq("id", str(project_url_id)).execute()
                return False

            session_response = supabase.table("scrape_sessions").select("*").eq("id", str(session_id)).single().execute()
            if not session_response.data:
                await manager.update_progress(
                    str(project_id), str(session_id),
                    {"status": "error", "message": "Session not found", "error": "Session not found"}
                )
                if project_url_id:
                    supabase.table("project_urls").update({"status": "failed"}).eq("id", str(project_url_id)).execute()
                return False

            session = session_response.data
            unique_scrape_identifier = session.get("unique_scrape_identifier") # Use .get for safety
            if not unique_scrape_identifier: # Ensure unique_scrape_identifier exists
                # This should ideally be generated by a DB trigger if not present.
                # For now, let's log an error and fail if it's missing.
                # Or, generate one here if that's the desired behavior.
                # For this change, we assume it's present from the scrape_sessions table.
                # If it's not, RAG cannot proceed correctly.
                print(f"Error: unique_scrape_identifier missing for session {session_id}")
                await manager.update_progress(
                    str(project_id), str(session_id),
                    {"status": "error", "message": "unique_scrape_identifier missing", "error": "Missing identifier"}
                )
                if project_url_id:
                    supabase.table("project_urls").update({"status": "failed"}).eq("id", str(project_url_id)).execute()
                return False

            url = session["url"]

            content_to_ingest = markdown_content
            if structured_data and "tabular_data" in structured_data:
                content_to_ingest = self._convert_structured_data_to_text(structured_data)
                await manager.update_progress(
                    str(project_id), str(session_id),
                    {"status": "processing", "message": "Using structured data for RAG ingestion", "current_chunk": 0, "total_chunks": 0, "percent_complete": 0}
                )
            else:
                await manager.update_progress(
                    str(project_id), str(session_id),
                    {"status": "processing", "message": "Using full markdown content for RAG ingestion", "current_chunk": 0, "total_chunks": 0, "percent_complete": 0}
                )

            markdown_response = supabase.table("markdowns").insert({
                "unique_name": unique_scrape_identifier, "url": url, "markdown": content_to_ingest
            }).execute()

            if not markdown_response.data:
                await manager.update_progress(
                    str(project_id), str(session_id),
                    {"status": "error", "message": "Failed to insert content for RAG processing", "error": "Database error"}
                )
                if project_url_id:
                    supabase.table("project_urls").update({"status": "failed"}).eq("id", str(project_url_id)).execute()
                return False

            chunks = await chunk_text(content_to_ingest)
            total_chunks = len(chunks)

            await manager.update_progress(
                str(project_id), str(session_id),
                {"status": "processing", "message": "Starting RAG ingestion...", "current_chunk": 0, "total_chunks": total_chunks, "percent_complete": 0}
            )
            
            start_time = time.time()
            await manager.update_progress(
                str(project_id), str(session_id),
                {"status": "processing", "message": f"Processing {total_chunks} chunks in batches...", "current_chunk": 0, "total_chunks": total_chunks, "percent_complete": 5}
            )

            embeddings = await process_chunks_with_batching(chunks, azure_credentials)
            processing_time = time.time() - start_time
            chunks_per_second = total_chunks / processing_time if processing_time > 0 else 0

            await manager.update_progress(
                str(project_id), str(session_id),
                {"status": "processing", "message": f"Batch processing complete. Processed {total_chunks} chunks in {processing_time:.2f} seconds ({chunks_per_second:.2f} chunks/sec)", "current_chunk": total_chunks, "total_chunks": total_chunks, "percent_complete": 80}
            )
            await manager.update_progress(
                str(project_id), str(session_id),
                {"status": "processing", "message": "Storing embeddings in database...", "current_chunk": total_chunks, "total_chunks": total_chunks, "percent_complete": 90}
            )

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                supabase.table("embeddings").insert({
                    "unique_name": unique_scrape_identifier, "chunk_id": i, "content": chunk, "embedding": embedding
                }).execute()

            supabase.table("scrape_sessions").update({"status": "rag_ingested"}).eq("id", str(session_id)).execute()
            
            if project_url_id: # Update project_urls status to completed
                supabase.table("project_urls").update({"status": "completed"}).eq("id", str(project_url_id)).execute()

            await manager.update_progress(
                str(project_id), str(session_id),
                {"status": "completed", "message": "RAG ingestion completed successfully!", "current_chunk": total_chunks, "total_chunks": total_chunks, "percent_complete": 100}
            )
            return True

        except Exception as e:
            await manager.update_progress(
                str(project_id), str(session_id),
                {"status": "error", "message": f"Error during RAG ingestion: {str(e)}", "error": str(e)}
            )
            if project_url_id: # Update project_urls status to failed on exception
                supabase.table("project_urls").update({"status": "failed"}).eq("id", str(project_url_id)).execute()
            raise

    def _convert_structured_data_to_text(self, structured_data: Dict[str, Any]) -> str:
        """
        Convert structured data to a text format suitable for RAG ingestion.
        
        Args:
            structured_data (Dict[str, Any]): Structured data containing tabular_data
            
        Returns:
            str: Text representation of the structured data
        """
        text_content = []
        
        # Add title if available
        if "title" in structured_data:
            text_content.append(f"# {structured_data['title']}")
            text_content.append("")
        
        # Process tabular data - this is the main content we want for RAG
        tabular_data = structured_data.get("tabular_data", [])
        
        if tabular_data:
            text_content.append("## Extracted Data")
            text_content.append("")
            
            # Convert each row of tabular data to readable text
            for i, row in enumerate(tabular_data, 1):
                text_content.append(f"### Item {i}")
                for field, value in row.items():
                    if value:  # Only include non-empty values
                        # Clean up field names for better readability
                        field_name = field.replace('_', ' ').title()
                        text_content.append(f"**{field_name}:** {value}")
                text_content.append("")
        
        # Add any additional sections if available
        if "sections" in structured_data:
            for section in structured_data["sections"]:
                if "heading" in section and "content" in section:
                    text_content.append(f"## {section['heading']}")
                    text_content.append(section["content"])
                    text_content.append("")
        
        # Add bullet points if available
        if "bullet_points" in structured_data:
            text_content.append("## Additional Information")
            for point in structured_data["bullet_points"]:
                text_content.append(f"- {point}")
            text_content.append("")
        
        # Join all content with newlines
        final_text = "\n".join(text_content)
        
        # If no meaningful content was created, fall back to a basic representation
        if len(final_text.strip()) == 0 or final_text.strip() == "#":
            final_text = f"Structured data containing {len(tabular_data)} items with the following information:\n\n"
            if tabular_data:
                # Create a summary of all available fields and their values
                all_fields = set()
                for row in tabular_data:
                    all_fields.update(row.keys())
                
                for field in all_fields:
                    values = [str(row.get(field, "")) for row in tabular_data if row.get(field)]
                    if values:
                        final_text += f"**{field.replace('_', ' ').title()}:** {', '.join(values[:3])}{'...' if len(values) > 3 else ''}\n"
        
        return final_text
