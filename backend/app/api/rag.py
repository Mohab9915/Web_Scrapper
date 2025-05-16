"""
API endpoints for RAG functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
from uuid import UUID

from app.models.chat import ChatMessageResponse, ChatMessageCreate, RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import RAGService

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
    Query the RAG system using Azure OpenAI.

    Args:
        project_id (UUID): Project ID
        request (RAGQueryRequest): Request data containing query, model name, and Azure OpenAI credentials

    Returns:
        RAGQueryResponse: Response with answer and sources

    Raises:
        HTTPException: If Azure OpenAI credentials are missing
    """
    # Validate Azure credentials
    if not request.azure_credentials or 'api_key' not in request.azure_credentials or 'endpoint' not in request.azure_credentials:
        raise HTTPException(status_code=400, detail="Azure OpenAI credentials (api_key and endpoint) are required")

    return await rag_service.query_rag(project_id, request.query, request.model_deployment, request.azure_credentials)

@router.post("/projects/{project_id}/chat", response_model=ChatMessageResponse)
async def post_chat_message(
    project_id: UUID,
    message: ChatMessageCreate,
    azure_credentials: Dict[str, str],
    rag_service: RAGService = Depends()
):
    """
    Post a new chat message.

    Args:
        project_id (UUID): Project ID
        message (ChatMessageCreate): Message data
        azure_credentials (Dict[str, str]): Dictionary containing 'api_key', 'endpoint', and optional 'deployment_name'

    Returns:
        ChatMessageResponse: Response with assistant message

    Raises:
        HTTPException: If Azure OpenAI credentials are missing
    """
    if not azure_credentials or 'api_key' not in azure_credentials or 'endpoint' not in azure_credentials:
        raise HTTPException(status_code=400, detail="Azure OpenAI credentials (api_key and endpoint) are required")

    return await rag_service.post_chat_message(project_id, message.content, azure_credentials)
