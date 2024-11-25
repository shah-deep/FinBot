import time
from websocket import WebSocketApp

# WebSocket server URL
SERVER_URL = "ws://127.0.0.1:8000/ws"
RECONNECT_INTERVAL = 3  # Time in seconds to wait before reconnecting

# Global WebSocket instance
ws_app = None

def on_open(ws):
    print("Connected to server")

def on_message(ws, message):
    print(f"Message received: {message}")

def on_close(ws, close_status_code, close_msg):
    print("Disconnected from server. Attempting to reconnect...")
    reconnect()

def on_error(ws, error):
    print(f"WebSocket error: {error}")
    ws.close()  # Close the connection to trigger reconnection

def reconnect():
    time.sleep(RECONNECT_INTERVAL)  # Wait before reconnecting
    connect_websocket()  # Reconnect to the server

def send_message(message):
    global ws_app
    if ws_app and ws_app.sock and ws_app.sock.connected:
        try:
            ws_app.send(message)
            print(f"Message sent: {message}")
        except Exception as e:
            print(f"Error sending message: {e}")
    else:
        print("WebSocket is not connected. Unable to send message.")

def connect_websocket():
    global ws_app
    ws_app = WebSocketApp(
        SERVER_URL,
        on_open=on_open,
        on_message=on_message,
        on_close=on_close,
        on_error=on_error,
    )
    try:
        ws_app.run_forever()  # Start the WebSocket connection
    except KeyboardInterrupt:
        print("Client terminated by user.")

if __name__ == "__main__":
    connect_websocket()

    # Example: Sending messages manually from the console
    while True:
        user_input = input("Enter a message to send (or 'exit' to quit): ")
        if user_input.lower() == "exit":
            print("Exiting client...")
            break
        send_message(user_input)
