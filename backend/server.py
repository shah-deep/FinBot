import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from .agentsystem.utils import create_agent, HelperAgent
from typing import Dict

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, HelperAgent] = {}
        self.agent_responses: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str, ticker: str):
        """
        Accepts a WebSocket connection and initializes an agent for the client.
        """
        await websocket.accept()
        self.connections[client_id] = websocket
        self.agents[client_id] = create_agent(ticker)
        self.agent_responses[client_id] = ""

    def disconnect(self, client_id: str):
        """
        Removes a client's connection and agent from the manager.
        """
        self.connections.pop(client_id, None)
        self.agents.pop(client_id, None)
        self.agent_responses.pop(client_id, None)
        print(f"Client {client_id} disconnected.")

    async def handle_message_exchange(self, websocket: WebSocket):
        """
        Handles incoming and outgoing messages for a specific client.
        """
        client_id = None
        try:
            message = await websocket.receive_text()
            data = json.loads(message)
            client_id = data["client_id"]
            user_input = data["user_input"]
            print(client_id, user_input)

            await self.agent_communication(client_id, user_input)
            print(client_id, self.agent_responses[client_id])
            await self.connections[client_id].send_text(self.agent_responses[client_id])
            return True

        except WebSocketDisconnect:
            self.disconnect(client_id)
            return False

        except Exception as e:
            self.disconnect(client_id)
            print(f"Error for client {client_id}:   {e}")
            return False
    
    async def agent_communication(self, client_id: str, user_input: str):   
        """
        Facilitates communication with the agent and formats the response.
        """ 
        response = self.agents[client_id].send_message(user_input)
        self.agent_responses[client_id] = json.dumps(response)


manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, tkr: str = Query(None)):
    """
    WebSocket endpoint for managing client-agent communication.
    """
    await manager.connect(websocket, client_id, tkr)
    connected = True
    while connected:
        connected = await manager.handle_message_exchange(websocket)
    
    

# To Run:
# uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000 
