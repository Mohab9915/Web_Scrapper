"""
WebSocket endpoints for real-time updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Any
from uuid import UUID

from ..utils.websocket_manager import manager

router = APIRouter(tags=["websockets"])

@router.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for real-time updates.
    
    Args:
        websocket (WebSocket): The WebSocket connection
        project_id (str): Project ID
    """
    await manager.connect(websocket, project_id)
    try:
        while True:
            # Keep the connection alive
            data = await websocket.receive_text()
            # Echo back to confirm connection is active
            await websocket.send_json({"type": "ping", "data": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
