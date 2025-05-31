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

router = APIRouter(tags=["rag"])

@router.get("/projects/{project_id}/chat", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    project_id: UUID, 
    conversation_id: Optional[UUID] = None,
    rag_service: RAGService = Depends()
):
    """
    Get chat messages for a project.

    Args:
        project_id (UUID): Project ID
        conversation_id (Optional[UUID]): Specific conversation ID

    Returns:
        List[ChatMessageResponse]: List of chat messages
    """
    return await rag_service.get_chat_messages(project_id, conversation_id)

@router.post("/projects/{project_id}/query-rag", response_model=RAGQueryResponse)
async def query_rag(
    project_id: UUID,
    request: RAGQueryRequest,
    rag_service: RAGService = Depends()
):
    """
    Query the RAG system using Azure OpenAI or OpenAI.

    Args:
        project_id (UUID): Project ID
        request (RAGQueryRequest): Request data containing query, model name, and credentials

    Returns:
        RAGQueryResponse: Response with answer and sources

    Raises:
        HTTPException: If credentials are missing
    """
    # Get model name from request or default to environment variable
    model_name = request.model_name or os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini")
    
    # Determine which service to use based on model name or explicit request
    if (request.use_openai or model_name == "gpt-4o"):
        # Use OpenAI directly for gpt-4o
        openai_key = request.openai_key or os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required for gpt-4o model")
        return await rag_service.query_rag_openai(project_id, request.query, openai_key, "gpt-4o")
    else:
        # Use Azure OpenAI for gpt-4o-mini
        # Get Azure credentials from environment if not provided in request
        azure_credentials = request.azure_credentials or {
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
        }

        if not azure_credentials or not azure_credentials.get("api_key") or not azure_credentials.get("endpoint"):
            raise HTTPException(status_code=400, detail="Azure OpenAI credentials (api_key and endpoint) are required")

        return await rag_service.query_rag(project_id, request.query, azure_credentials, model_name)

@router.post("/projects/{project_id}/enhanced-query-rag", response_model=RAGQueryResponse)
async def enhanced_query_rag(
    project_id: UUID,
    request: RAGQueryRequest,
    rag_service: RAGService = Depends()
):
    """
    Query the enhanced RAG system with intelligent formatting and structured data processing.

    Args:
        project_id (UUID): Project ID
        request (RAGQueryRequest): Request data containing query and credentials
        rag_service (RAGService): Enhanced RAG service with conversational capabilities

    Returns:
        RAGQueryResponse: Enhanced formatted response

    Raises:
        HTTPException: If credentials are missing
    """
    # Get Azure credentials from environment if not provided in request
    azure_credentials = request.azure_credentials or {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    }

    if not azure_credentials.get("api_key") or not azure_credentials.get("endpoint"):
        raise HTTPException(status_code=400, detail="Azure OpenAI credentials are required for enhanced RAG")

    # Use our enhanced RAG service with conversational capabilities
    model_name = request.model_name or os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini")

    return await rag_service.query_rag(
        project_id,
        request.query,
        azure_credentials,
        model_name
    )

@router.post("/projects/{project_id}/chat", response_model=ChatMessageResponse)
async def post_chat_message(
    project_id: UUID,
    request: ChatMessageRequest,
    conversation_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
    rag_service: RAGService = Depends()
):
    """
    Post a new chat message.

    Args:
        project_id (UUID): Project ID
        request (ChatMessageRequest): Request data containing content and Azure credentials
        conversation_id (Optional[UUID]): Conversation ID, creates new if None
        session_id (Optional[UUID]): Optional scrape session ID

    Returns:
        ChatMessageResponse: Response with assistant message

    Raises:
        HTTPException: If Azure OpenAI credentials are missing
    """
    # Get Azure credentials from request or environment
    azure_credentials = request.azure_credentials or {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
    }
    
    if not azure_credentials or not azure_credentials.get("api_key") or not azure_credentials.get("endpoint"):
        raise HTTPException(status_code=400, detail="Azure OpenAI credentials (api_key and endpoint) are required")

    return await rag_service.post_chat_message(project_id, request.content, azure_credentials, conversation_id, session_id)

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
