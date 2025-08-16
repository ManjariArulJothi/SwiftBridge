from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket

    def disconnect(self, websocket: WebSocket, username: str):
        self.active_connections.pop(username, None)

    async def send_personal_message(self, message: str, username: str):
        websocket = self.active_connections.get(username)
        if websocket:
            await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/chat/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_text()
            recipient, message = data.split(":", 1)
            await manager.send_personal_message(message, recipient)
    except WebSocketDisconnect:
        manager.disconnect(websocket, username)

@app.get("/")
async def get():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <input id="usernameInput" type="text" placeholder="Username" autocomplete="off"/>
        <input id="messageInput" type="text" placeholder="Message" autocomplete="off"/>
        <input id="recipientInput" type="text" placeholder="Recipient Username" autocomplete="off"/>
        <button onclick="sendMessage()">Send</button>
        <ul id="messages"></ul>
        <script>
            var ws;
            function initWebSocket() {
                var username = document.getElementById("usernameInput").value;
                // Replace 'alice' with the actual username
                ws = new WebSocket("ws://" + location.host + "/ws/chat/" + username);
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages');
                    var message = document.createElement('li');
                    message.textContent = event.data;
                    messages.appendChild(message);
                };
            }
            function sendMessage() {
                var input = document.getElementById("messageInput");
                var recipient = document.getElementById("recipientInput").value;
                ws.send(recipient + ":" + input.value);
                input.value = '';
            }
            document.getElementById("usernameInput").addEventListener("change", initWebSocket);
            // To send "Hello" to user "bob"
            ws.send("bob:Hello");
        </script>
    </body>
    </html>
    """)