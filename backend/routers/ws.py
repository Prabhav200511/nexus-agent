"""
WebSocket Router — Real-time agent update streaming.

Responsibilities:
  - Accept WebSocket connections scoped to a task_id
  - Manage active connections (connect / disconnect)
  - Receive messages from agent via broadcast()
  - Forward agent step updates to the correct frontend client

NOT allowed here:
  - Agent logic
  - Tool calls
  - LLM calls
  - Any direct LangGraph imports
"""

from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """
    Manages active WebSocket connections keyed by task_id.
    One task can have multiple connected clients (e.g. multiple browser tabs).
    """

    def __init__(self) -> None:
        # task_id (str) → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(task_id, []).append(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(task_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self._connections.pop(task_id, None)

    async def broadcast(self, task_id: str, message: dict) -> None:
        """Send a message to all clients watching this task."""
        for websocket in self._connections.get(task_id, []):
            try:
                await websocket.send_json(message)
            except Exception:
                # Stale connection — will be cleaned up on next disconnect
                pass

    def has_listeners(self, task_id: str) -> bool:
        return bool(self._connections.get(task_id))


# Singleton — imported by agent/executor.py to push live updates
manager = ConnectionManager()


@router.websocket("/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str) -> None:
    """
    Client connects here to stream live step updates for a specific task.
    URL: ws://localhost:8000/ws/{task_id}
    """
    await manager.connect(task_id, websocket)
    try:
        # Send current task state immediately on connect
        await websocket.send_json({
            "event": "connected",
            "task_id": task_id,
            "message": "Subscribed to task updates",
        })

        # Keep connection alive — agent pushes updates via manager.broadcast()
        while True:
            # We only listen for a "ping" to keep the connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)