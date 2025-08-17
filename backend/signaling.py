from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Connected: {client_id}")

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        print(f"Disconnected: {client_id}")

    async def send_to(self, target_id: str, message: str):
        if target_id in self.active_connections:
            await self.active_connections[target_id].send_text(message)
        else:
            print(f"Target {target_id} not connected.")

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def signaling(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                # Expects message format: {"to": "receiver_id", "data": {"type": "offer/answer/ice", "data": actualData}}
                import json
                msg = json.loads(data)
                to = msg["to"]
                await manager.send_to(to, json.dumps(msg["data"]))
            except Exception as e:
                print("Invalid message or error:", e)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
