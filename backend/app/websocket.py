from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # Format: {contest_id: [WebSocket]}
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, contest_id: int):
        await websocket.accept()
        if contest_id not in self.active_connections:
            self.active_connections[contest_id] = []
        self.active_connections[contest_id].append(websocket)

    def disconnect(self, websocket: WebSocket, contest_id: int):
        if contest_id in self.active_connections:
            if websocket in self.active_connections[contest_id]:
                self.active_connections[contest_id].remove(websocket)
            if not self.active_connections[contest_id]:
                del self.active_connections[contest_id]

    async def broadcast_leaderboard(self, contest_id: int, leaderboard: List[dict]):
        if contest_id in self.active_connections:
            message = json.dumps({
                "type": "leaderboard_update",
                "contest_id": contest_id,
                "data": leaderboard
            })
            for connection in self.active_connections[contest_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Connection might be closed, we will clean it up on disconnect
                    pass

manager = ConnectionManager()
