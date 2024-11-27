import websocket
import time
import asyncio
import threading

class ConnectionHandler:
    def __init__(self):
        self.curr_response = ''
        self.ws = None
        self.ticker = None

    def on_message(self, ws, message):
        self.curr_response = message
        print("Got message: ", self.curr_response)

    def get_message(self):
        print("Waiting to get message")
        while not self.curr_response:
            time.sleep(0.1)  
        temp = self.curr_response
        self.curr_response = ''
        print("Sending message")
        return temp

    def on_error(self, ws, error):
        self.curr_response = "Error"

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed. Reconnecting...")
        asyncio.run(self.connect_server(self.ticker))  # Use asyncio.run to schedule the async task

    def on_open(self, ws):
        print("Connection established.")
        # ws.send("Hello, server!")  # You can send an initial message if needed.
        pass

    def create_connection(self, ticker):
        ws = websocket.WebSocketApp(
            f"ws://127.0.0.1:8000/ws?tkr={ticker}",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        return ws

    async def connect_server(self, ticker):
        print("in conn_server")
        self.ticker = ticker
        self.ws = self.create_connection(ticker)
        print("got conn")
        def run_ws():
            try:
                print("running forever")
                self.ws.run_forever()
            except Exception as e:
                print(f"Error occurred: {e}, retrying in 5 seconds...")
                time.sleep(5)

        ws_thread = threading.Thread(target=run_ws)
        ws_thread.start()

        # while True:
        #     await asyncio.sleep(1) 

    def send_message(self, message):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(message)

        
