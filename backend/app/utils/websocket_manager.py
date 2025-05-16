"""
WebSocket connection manager for real-time updates.
"""
from typing import Dict, List, Any
from fastapi import WebSocket
import json
import asyncio
from uuid import UUID

class ConnectionManager:
    """
    WebSocket connection manager for handling real-time updates.
    """
    def __init__(self):
        # Store active connections by project_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store progress information by project_id and session_id
        self.progress_info: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        """
        Connect a WebSocket client for a specific project.
        
        Args:
            websocket (WebSocket): The WebSocket connection
            project_id (str): Project ID
        """
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        
        self.active_connections[project_id].append(websocket)
        
        # Send initial progress info if available
        if project_id in self.progress_info:
            for session_id, progress in self.progress_info[project_id].items():
                await websocket.send_json({
                    "type": "progress_update",
                    "project_id": project_id,
                    "session_id": session_id,
                    "data": progress
                })

    def disconnect(self, websocket: WebSocket, project_id: str):
        """
        Disconnect a WebSocket client.
        
        Args:
            websocket (WebSocket): The WebSocket connection
            project_id (str): Project ID
        """
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            
            # Clean up if no connections left for this project
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def update_progress(self, project_id: str, session_id: str, progress_data: Dict[str, Any]):
        """
        Update progress information and broadcast to connected clients.
        
        Args:
            project_id (str): Project ID
            session_id (str): Session ID
            progress_data (Dict[str, Any]): Progress data to broadcast
        """
        # Store progress information
        if project_id not in self.progress_info:
            self.progress_info[project_id] = {}
        
        self.progress_info[project_id][session_id] = progress_data
        
        # Broadcast to all connected clients for this project
        if project_id in self.active_connections:
            message = {
                "type": "progress_update",
                "project_id": project_id,
                "session_id": session_id,
                "data": progress_data
            }
            
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be closed, we'll handle it on the next ping
                    pass

    def clear_progress(self, project_id: str, session_id: str):
        """
        Clear progress information for a session.
        
        Args:
            project_id (str): Project ID
            session_id (str): Session ID
        """
        if project_id in self.progress_info and session_id in self.progress_info[project_id]:
            del self.progress_info[project_id][session_id]
            
            # Clean up if no sessions left for this project
            if not self.progress_info[project_id]:
                del self.progress_info[project_id]

# Create a global connection manager instance
manager = ConnectionManager()
