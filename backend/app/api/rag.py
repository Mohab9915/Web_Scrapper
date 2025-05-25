"""
API endpoints for RAG functionality.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional
from uuid import UUID

from app.models.chat import ChatMessageResponse, ChatMessageCreate, RAGQueryRequest, RAGQueryResponse
from app.services.improved_rag_service import ImprovedRAGService as RAGService

router = APIRouter(tags=["rag"])

@router.get("/projects/{project_id}/chat", response_model=List[ChatMessageResponse])
async def get_chat_messages(project_id: UUID, rag_service: RAGService = Depends()):
    """
    Get chat messages for a project.

    Args:
        project_id (UUID): Project ID

    Returns:
        List[ChatMessageResponse]: List of chat messages
    """
    return await rag_service.get_chat_messages(project_id)

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

@router.post("/projects/{project_id}/chat", response_model=ChatMessageResponse)
async def post_chat_message(
    project_id: UUID,
    message: ChatMessageCreate,
    azure_credentials: Optional[Dict[str, str]] = None,
    rag_service: RAGService = Depends()
):
    """
    Post a new chat message.

    Args:
        project_id (UUID): Project ID
        message (ChatMessageCreate): Message data
        azure_credentials (Optional[Dict[str, str]]): Dictionary containing 'api_key', 'endpoint', and optional 'deployment_name'

    Returns:
        ChatMessageResponse: Response with assistant message

    Raises:
        HTTPException: If Azure OpenAI credentials are missing
    """
    # Get Azure credentials from environment if not provided
    if not azure_credentials:
        azure_credentials = {
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
        }
    
    if not azure_credentials or not azure_credentials.get("api_key") or not azure_credentials.get("endpoint"):
        raise HTTPException(status_code=400, detail="Azure OpenAI credentials (api_key and endpoint) are required")

    return await rag_service.post_chat_message(project_id, message.content, azure_credentials)
