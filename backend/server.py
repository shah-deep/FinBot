import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .agentsystem.utils import create_agent, HelperAgent

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    agent = create_agent()
    try:
        while True:
            user_input = await websocket.receive_text()
            agent_response = await agent_communication(user_input, agent)
            await websocket.send_text(agent_response)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def agent_communication(user_input: str, agent: HelperAgent) -> str:    
    response = agent.send_message(user_input)
    res_json = json.dumps(response)
    return res_json

# To Run:
# uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000
