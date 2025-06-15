"""
API endpoints for RAG functionality.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional
from uuid import UUID

from ..models.chat import ChatMessageResponse, ChatMessageCreate, ChatMessageRequest, RAGQueryRequest, RAGQueryResponse
from ..services.rag_service import RAGService
from ..services.chat_history_service import ChatHistoryService
from ..services.enhanced_rag_service import EnhancedRAGService
from ..dependencies.auth import get_current_user, get_current_user_id
from ..models.auth import UserResponse
from ..config import settings
from ..database import supabase

router = APIRouter(tags=["rag"])

# Create a dependency that provides RAGService with settings
def get_rag_service():
    return RAGService(settings=settings)

@router.get("/projects/{project_id}/chat", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    project_id: UUID,
    conversation_id: Optional[UUID] = None,
    current_user_id: UUID = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get chat messages for a project for the authenticated user.

    Args:
        project_id (UUID): Project ID
        conversation_id (Optional[UUID]): Specific conversation ID
        current_user_id (UUID): ID of the authenticated user

    Returns:
        List[ChatMessageResponse]: List of chat messages
    """
    return await rag_service.get_chat_messages(project_id, conversation_id, current_user_id)

@router.post("/projects/{project_id}/query-rag", response_model=RAGQueryResponse)
async def query_rag(
    project_id: UUID,
    request: RAGQueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Query the RAG system using Azure OpenAI.

    Args:
        project_id (UUID): Project ID
        request (RAGQueryRequest): Request data containing query and model name

    Returns:
        RAGQueryResponse: Response with answer and sources
    """
    # Get model name from request or default to environment variable
    model_name = request.model_name or os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

    # Use Azure OpenAI for all queries
    return await rag_service.query_rag(project_id, request.query, model_name)

@router.post("/projects/{project_id}/enhanced-query-rag", response_model=RAGQueryResponse)
async def enhanced_query_rag(
    project_id: UUID,
    request: RAGQueryRequest
):
    """
    Query the enhanced RAG system with intelligent formatting and structured data processing.

    Args:
        project_id (UUID): Project ID
        request (RAGQueryRequest): Request data containing query

    Returns:
        RAGQueryResponse: Enhanced formatted response
    """
    # Use the enhanced RAG service directly
    from app.services.enhanced_rag_service import EnhancedRAGService
    enhanced_rag_service = EnhancedRAGService()

    model_name = request.model_name or os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

    return await enhanced_rag_service.enhanced_query_rag(
        project_id,
        request.query,
        model_name
    )

@router.post("/projects/{project_id}/chat", response_model=ChatMessageResponse)
async def post_chat_message(
    project_id: UUID,
    request: ChatMessageRequest,
    conversation_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
    current_user_id: UUID = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Post a new chat message.

    Args:
        project_id (UUID): Project ID
        request (ChatMessageRequest): Request data containing content and Azure credentials
        conversation_id (Optional[UUID]): Conversation ID, creates new if None
        session_id (Optional[UUID]): Optional scrape session ID
        current_user_id (UUID): ID of the authenticated user

    Returns:
        ChatMessageResponse: Response with assistant message

    """
    # Use Azure OpenAI from environment variables
    return await rag_service.post_chat_message(project_id, request.content, conversation_id, session_id)

@router.get("/projects/{project_id}/conversations")
async def get_project_conversations(
    project_id: UUID,
    limit: Optional[int] = 50,
    chat_service: ChatHistoryService = Depends()
):
    """
    Get conversation summaries for a project.

    Args:
        project_id (UUID): Project ID
        limit (Optional[int]): Maximum number of conversations to return

    Returns:
        List[Dict]: List of conversation summaries
    """
    return await chat_service.get_project_conversations(project_id, limit)

@router.post("/projects/{project_id}/conversations")
async def create_conversation(
    project_id: UUID,
    session_id: Optional[UUID] = None,
    chat_service: ChatHistoryService = Depends()
):
    """
    Create a new conversation thread.

    Args:
        project_id (UUID): Project ID
        session_id (Optional[UUID]): Optional scrape session ID

    Returns:
        Dict: New conversation details
    """
    conversation_id = await chat_service.create_conversation(project_id, session_id)
    return {"conversation_id": conversation_id}

@router.delete("/projects/{project_id}/conversations/{conversation_id}")
async def delete_conversation(
    project_id: UUID,
    conversation_id: UUID,
    chat_service: ChatHistoryService = Depends()
):
    """
    Delete a conversation and all its messages.

    Args:
        project_id (UUID): Project ID
        conversation_id (UUID): Conversation ID

    Returns:
        Dict: Success status
    """
    success = await chat_service.delete_conversation(project_id, conversation_id)
    return {"success": success}

@router.get("/projects/{project_id}/conversations/{conversation_id}/messages", response_model=List[ChatMessageResponse])
async def get_conversation_messages(
    project_id: UUID,
    conversation_id: UUID,
    limit: Optional[int] = 100,
    chat_service: ChatHistoryService = Depends()
):
    """
    Get messages for a specific conversation.

    Args:
        project_id (UUID): Project ID
        conversation_id (UUID): Conversation ID
        limit (Optional[int]): Maximum number of messages to return

    Returns:
        List[ChatMessageResponse]: List of chat messages
    """
    return await chat_service.get_conversation_messages(project_id, conversation_id, limit)

@router.post("/projects/{project_id}/sessions/{session_id}/ingest-rag")
async def ingest_session_to_rag(
    project_id: UUID,
    session_id: UUID,
    azure_credentials: Optional[Dict] = None
):
    """
    Manually ingest a scraping session into the RAG system.

    This endpoint allows users to trigger RAG ingestion for any scraped session,
    useful when re-scraping or when initial ingestion failed.

    Args:
        project_id (UUID): Project ID
        session_id (UUID): Session ID to ingest
        azure_credentials (Optional[Dict]): Azure OpenAI credentials for embeddings

    Returns:
        Dict: Ingestion status and details

    Raises:
        HTTPException: If session not found or ingestion fails
    """
    try:
        # Import database and get session
        from app.database import supabase
        import json

        # Get the session
        session_response = supabase.table('scrape_sessions').select('*').eq('id', str(session_id)).eq('project_id', str(project_id)).single().execute()

        if not session_response.data:
            raise HTTPException(status_code=404, detail="Session not found")

        session_data = session_response.data

        # Check if session has structured data
        if not session_data.get('structured_data_json'):
            raise HTTPException(status_code=400, detail="Session has no structured data to ingest")

        # Parse structured data
        structured_data = json.loads(session_data['structured_data_json']) if isinstance(session_data['structured_data_json'], str) else session_data['structured_data_json']

        # Get Azure credentials from environment if not provided
        if not azure_credentials:
            azure_credentials = {
                "api_key": os.getenv("AZURE_OPENAI_API_KEY", "dummy_key"),
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "dummy_endpoint"),
                "deployment_name": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
            }

        # Use enhanced RAG service for ingestion
        enhanced_rag_service = EnhancedRAGService()

        # Perform ingestion
        success = await enhanced_rag_service.ingest_structured_content(
            project_id=project_id,
            session_id=session_id,
            structured_data=structured_data,
            embedding_api_keys=azure_credentials
        )

        if success:
            # Update session status to rag_ingested
            supabase.table('scrape_sessions').update({
                'status': 'rag_ingested'
            }).eq('id', str(session_id)).execute()

            # Check how many embeddings were created
            unique_id = session_data['unique_scrape_identifier']
            embeddings = supabase.table('embeddings').select('*').eq('unique_name', unique_id).execute()
            embedding_count = len(embeddings.data) if embeddings.data else 0

            return {
                "success": True,
                "message": "Session successfully ingested into RAG system",
                "session_id": str(session_id),
                "project_id": str(project_id),
                "embeddings_created": embedding_count,
                "data_items": structured_data.get('total_items', len(structured_data.get('listings', []))),
                "status": "rag_ingested"
            }
        else:
            return {
                "success": False,
                "message": "RAG ingestion completed with warnings",
                "session_id": str(session_id),
                "project_id": str(project_id)
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG ingestion failed: {str(e)}")

@router.get("/projects/{project_id}/rag-status")
async def get_project_rag_status(project_id: UUID):
    """
    Get RAG status for a project including ingested sessions and embedding counts.

    Args:
        project_id (UUID): Project ID

    Returns:
        Dict: RAG status information
    """
    try:

        # Get project RAG enabled status
        project_response = supabase.table('projects').select('rag_enabled').eq('id', str(project_id)).single().execute()

        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        rag_enabled = project_response.data['rag_enabled']

        # Get all sessions for this project
        sessions_response = supabase.table('scrape_sessions').select('*').eq('project_id', str(project_id)).execute()
        sessions = sessions_response.data or []

        # Count RAG-ingested sessions
        rag_sessions = [s for s in sessions if s['status'] == 'rag_ingested']

        # Count total embeddings for this project
        total_embeddings = 0
        session_details = []

        for session in sessions:
            unique_id = session['unique_scrape_identifier']
            embeddings = supabase.table('embeddings').select('*').eq('unique_name', unique_id).execute()
            embedding_count = len(embeddings.data) if embeddings.data else 0
            total_embeddings += embedding_count

            session_details.append({
                "session_id": session['id'],
                "url": session['url'],
                "status": session['status'],
                "scraped_at": session['scraped_at'],
                "embeddings": embedding_count,
                "has_structured_data": bool(session.get('structured_data_json'))
            })

        return {
            "project_id": str(project_id),
            "rag_enabled": rag_enabled,
            "total_sessions": len(sessions),
            "rag_ingested_sessions": len(rag_sessions),
            "total_embeddings": total_embeddings,
            "sessions": session_details
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RAG status: {str(e)}")
