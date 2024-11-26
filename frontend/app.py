from flask import Flask
from chat_app import make_chat_app

server = Flask(__name__)

make_chat_app(server)

server.run(host="127.0.0.1", port=8050, debug=True)