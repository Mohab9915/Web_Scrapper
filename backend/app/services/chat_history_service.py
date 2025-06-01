"""
Service for managing chat history and conversation persistence.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import HTTPException

from ..database import supabase
from ..models.chat import ChatMessageResponse


class ChatHistoryService:
    """Service for managing chat history and conversations."""

    async def create_conversation(self, project_id: UUID, session_id: Optional[UUID] = None) -> UUID:
        """
        Create a new conversation thread.

        Args:
            project_id (UUID): Project ID
            session_id (Optional[UUID]): Optional scrape session ID

        Returns:
            UUID: New conversation ID
        """
        conversation_id = uuid4()
        
        # Create initial system message for the conversation
        await self.save_message(
            project_id=project_id,
            conversation_id=conversation_id,
            session_id=session_id,
            role="system",
            content="Conversation started",
            metadata={"conversation_started": datetime.now().isoformat()}
        )
        
        return conversation_id

    async def save_message(
        self,
        project_id: UUID,
        conversation_id: UUID,
        role: str,
        content: str,
        session_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Save a chat message to the database.

        Args:
            project_id (UUID): Project ID
            conversation_id (UUID): Conversation ID
            role (str): Message role (user, assistant, system)
            content (str): Message content
            session_id (Optional[UUID]): Optional scrape session ID
            metadata (Optional[Dict[str, Any]]): Additional metadata

        Returns:
            UUID: Message ID

        Raises:
            HTTPException: If save operation fails
        """
        try:
            message_data = {
                "project_id": str(project_id),
                "conversation_id": str(conversation_id),
                "message_role": role,
                "message_content": content,
                "metadata": metadata or {}
            }
            
            if session_id:
                message_data["session_id"] = str(session_id)

            response = supabase.table("chat_history").insert(message_data).execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to save chat message")
            
            return UUID(response.data[0]["id"])
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving chat message: {str(e)}")

    async def get_conversation_messages(
        self,
        project_id: UUID,
        conversation_id: UUID,
        limit: Optional[int] = 100
    ) -> List[ChatMessageResponse]:
        """
        Get messages for a specific conversation.

        Args:
            project_id (UUID): Project ID
            conversation_id (UUID): Conversation ID
            limit (Optional[int]): Maximum number of messages to return

        Returns:
            List[ChatMessageResponse]: List of chat messages

        Raises:
            HTTPException: If retrieval fails
        """
        try:
            query = supabase.table("chat_history")\
                .select("*")\
                .eq("project_id", str(project_id))\
                .eq("conversation_id", str(conversation_id))\
                .order("created_at", desc=False)
            
            if limit:
                query = query.limit(limit)
                
            response = query.execute()
            
            messages = []
            for row in response.data:
                # Skip system messages when returning to UI
                if row["message_role"] == "system":
                    continue
                    
                message = ChatMessageResponse(
                    id=row["id"],
                    role=row["message_role"],
                    content=row["message_content"],
                    timestamp=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                    cost=row["metadata"].get("cost"),
                    sources=row["metadata"].get("sources")
                )
                messages.append(message)
            
            return messages
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving conversation messages: {str(e)}")

    async def get_project_conversations(
        self,
        project_id: UUID,
        limit: Optional[int] = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation summaries for a project.

        Args:
            project_id (UUID): Project ID
            limit (Optional[int]): Maximum number of conversations to return

        Returns:
            List[Dict[str, Any]]: List of conversation summaries

        Raises:
            HTTPException: If retrieval fails
        """
        try:
            # Get conversations with their latest message
            response = supabase.rpc(
                "get_project_conversations_summary",
                {
                    "p_project_id": str(project_id),
                    "p_limit": limit or 50
                }
            ).execute()
            
            # If the RPC doesn't exist, fall back to a simpler query
            if not response.data:
                response = supabase.table("chat_history")\
                    .select("conversation_id, created_at, message_content")\
                    .eq("project_id", str(project_id))\
                    .eq("message_role", "user")\
                    .order("created_at", desc=True)\
                    .limit(limit or 50)\
                    .execute()
                
                conversations = []
                seen_conversations = set()
                
                for row in response.data:
                    conv_id = row["conversation_id"]
                    if conv_id not in seen_conversations:
                        conversations.append({
                            "conversation_id": conv_id,
                            "last_message_at": row["created_at"],
                            "preview": row["message_content"][:100] + "..." if len(row["message_content"]) > 100 else row["message_content"]
                        })
                        seen_conversations.add(conv_id)
                
                return conversations
            
            return response.data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving project conversations: {str(e)}")

    async def delete_conversation(
        self,
        project_id: UUID,
        conversation_id: UUID
    ) -> bool:
        """
        Delete an entire conversation.

        Args:
            project_id (UUID): Project ID
            conversation_id (UUID): Conversation ID

        Returns:
            bool: True if successful

        Raises:
            HTTPException: If deletion fails
        """
        try:
            response = supabase.table("chat_history")\
                .delete()\
                .eq("project_id", str(project_id))\
                .eq("conversation_id", str(conversation_id))\
                .execute()
            
            return True
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

    async def update_message_metadata(
        self,
        message_id: UUID,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for a specific message.

        Args:
            message_id (UUID): Message ID
            metadata (Dict[str, Any]): Metadata to update

        Returns:
            bool: True if successful

        Raises:
            HTTPException: If update fails
        """
        try:
            response = supabase.table("chat_history")\
                .update({"metadata": metadata})\
                .eq("id", str(message_id))\
                .execute()

            return bool(response.data)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating message metadata: {str(e)}")

    async def update_conversation_title(
        self,
        project_id: UUID,
        conversation_id: UUID,
        title: str
    ) -> bool:
        """
        Update the conversation title by storing it in the system message metadata.

        Args:
            project_id (UUID): Project ID
            conversation_id (UUID): Conversation ID
            title (str): Generated conversation title

        Returns:
            bool: True if successful

        Raises:
            HTTPException: If update fails
        """
        try:
            # First, try to find an existing system message for this conversation
            existing_response = supabase.table("chat_history")\
                .select("id, metadata")\
                .eq("project_id", str(project_id))\
                .eq("conversation_id", str(conversation_id))\
                .eq("message_role", "system")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            if existing_response.data:
                # Update existing system message with title
                existing_metadata = existing_response.data[0]["metadata"] or {}
                existing_metadata["conversation_title"] = title

                response = supabase.table("chat_history")\
                    .update({"metadata": existing_metadata})\
                    .eq("id", existing_response.data[0]["id"])\
                    .execute()

                return bool(response.data)
            else:
                # Create a new system message with the title
                await self.save_message(
                    project_id=project_id,
                    conversation_id=conversation_id,
                    role="system",
                    content="Conversation title set",
                    metadata={"conversation_title": title, "title_set_at": datetime.now().isoformat()}
                )
                return True

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating conversation title: {str(e)}")

    async def get_conversation_title(
        self,
        project_id: UUID,
        conversation_id: UUID
    ) -> Optional[str]:
        """
        Get the conversation title from system message metadata.

        Args:
            project_id (UUID): Project ID
            conversation_id (UUID): Conversation ID

        Returns:
            Optional[str]: Conversation title if exists
        """
        try:
            response = supabase.table("chat_history")\
                .select("metadata")\
                .eq("project_id", str(project_id))\
                .eq("conversation_id", str(conversation_id))\
                .eq("message_role", "system")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            if response.data and response.data[0]["metadata"]:
                return response.data[0]["metadata"].get("conversation_title")

            return None

        except Exception:
            # Don't raise an exception for title retrieval failures
            return None

    async def is_first_user_message(
        self,
        project_id: UUID,
        conversation_id: UUID
    ) -> bool:
        """
        Check if this is the first user message in the conversation.

        Args:
            project_id (UUID): Project ID
            conversation_id (UUID): Conversation ID

        Returns:
            bool: True if this is the first user message
        """
        try:
            response = supabase.table("chat_history")\
                .select("id")\
                .eq("project_id", str(project_id))\
                .eq("conversation_id", str(conversation_id))\
                .eq("message_role", "user")\
                .limit(1)\
                .execute()

            # If no user messages exist, this will be the first
            return len(response.data) == 0

        except Exception:
            # If we can't determine, assume it's not the first
            return False
