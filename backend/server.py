import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from .agentsystem.utils import create_agent, HelperAgent

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, tkr: str = Query(None)):
    """
    WebSocket endpoint for managing client-agent communication.
    """
    await websocket.accept()
    agent = create_agent(tkr)
    try:
        while True:
            user_input = await websocket.receive_text()
            agent_response = await agent_communication(user_input, agent)
            await websocket.send_text(agent_response)

    except WebSocketDisconnect:
        print("Connection closed.")


async def agent_communication(user_input: str, agent: HelperAgent) -> str:   
    """
    Facilitates communication with the agent and formats the response.
    """ 
    response = agent.send_message(user_input)
    res_json = json.dumps(response)
    return res_json


# To Run:
# uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000 
