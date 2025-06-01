"""
Chat models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class ChatMessageBase(BaseModel):
    """Base model for chat message data."""
    content: str

class ChatMessageCreate(ChatMessageBase):
    """Model for creating a new chat message."""
    pass

class ChatMessageRequest(BaseModel):
    """Model for chat message request including Azure credentials."""
    content: str
    azure_credentials: Optional[Dict[str, str]] = None  # Must contain 'api_key' and 'endpoint' for Azure

class ChatMessageResponse(ChatMessageBase):
    """Model for chat message response."""
    id: str
    role: str  # 'user' or 'assistant'
    timestamp: datetime
    cost: Optional[float] = None
    sources: Optional[List[str]] = None

    class Config:
        from_attributes = True

class RAGQueryRequest(BaseModel):
    """Model for RAG query request using Azure OpenAI or regular OpenAI."""
    query: str
    model_name: Optional[str] = None  # Optional model name for Azure deployments or OpenAI models
    azure_credentials: Optional[Dict[str, str]] = None  # Must contain 'api_key' and 'endpoint' for Azure
    openai_key: Optional[str] = None  # OpenAI API key for using OpenAI models
    use_openai: Optional[bool] = False  # Whether to use OpenAI instead of Azure

class RAGQueryResponse(BaseModel):
    """Model for RAG query response."""
    answer: str
    generation_cost: float
    source_documents: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[Dict[str, Any]]] = None  # Alias for source_documents for compatibility
    chart_data: Optional[Dict[str, Any]] = None  # Chart configuration and data
    conversation_title: Optional[str] = None  # AI-generated conversation title
