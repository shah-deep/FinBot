import websocket
import time
import asyncio
import json
import uuid
import threading

class ConnectionHandler:
    def __init__(self):
        self.curr_response = ''
        self.ws = None
        self.ticker = None
        self.is_connected = threading.Event()

    def on_message(self, ws, message):
        self.curr_response = message
        # print("Got message: ", self.curr_response)

    def get_message(self):
        # print("Waiting to get message")
        while not self.curr_response:
            time.sleep(0.1)  
        temp = self.curr_response
        self.curr_response = ''
        # print("Sending message")
        return temp

    def on_error(self, ws, error):
        self.curr_response = "Error"
        self.is_connected.clear()

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection Closed")
        self.curr_response = "Error"
        self.is_connected.clear()

    def on_open(self, ws):
        self.is_connected.set()
        # print("Connection established.")

    def create_connection(self, ticker, cid):
        ws = websocket.WebSocketApp(
            f"ws://127.0.0.1:8000/ws/{cid}?tkr={ticker}",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        return ws

    async def connect_server(self, ticker):
        self.ticker = ticker
        self.conn_id = ticker + str(uuid.uuid4()).replace("-", "")
        self.ws = self.create_connection(ticker, self.conn_id)

        def run_ws():
            try:
                self.ws.run_forever()
            except Exception as e:
                print(f"Connection error occurred: {e}")
                # time.sleep(5)

        ws_thread = threading.Thread(target=run_ws)
        ws_thread.start()


    def send_message(self, user_input: str):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            message = {
                "client_id": self.conn_id,
                "user_input": user_input,
            }
            self.ws.send(json.dumps(message))

        
