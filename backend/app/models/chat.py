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
    """Model for RAG query request using Azure OpenAI."""
    query: str
    model_deployment: str = "gpt-35-turbo"  # Default to GPT-3.5 Turbo deployment
    azure_credentials: Dict[str, str]  # Must contain 'api_key' and 'endpoint'

class RAGQueryResponse(BaseModel):
    """Model for RAG query response."""
    answer: str
    generation_cost: float
    source_documents: Optional[List[Dict[str, Any]]] = None
