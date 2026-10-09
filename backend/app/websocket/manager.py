import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("textile_machine.websocket")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining clients: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any] = None):
        if not self.active_connections:
            return

        payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data or {}
        }
        
        # Flatten payload fields for convenience if desired by frontend
        if data:
            for k, v in data.items():
                if k not in payload:
                    payload[k] = v

        message_str = json.dumps(payload)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.warning(f"Error sending message to client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


ws_manager = ConnectionManager()
