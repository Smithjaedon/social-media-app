from fastapi import WebSocket, APIRouter
import uuid

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: uuid.UUID):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: uuid.UUID):
        self.active_connections[room_id].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(
        self, payload: str, room_id: uuid.UUID, excludes: WebSocket = None
    ):
        for connection in self.active_connections.get(room_id, []):
            if connection != excludes:
                await connection.send_text(payload)


manager = ConnectionManager()
