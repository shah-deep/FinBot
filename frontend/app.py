from flask import Flask
from chat_app import make_chat_app

server = Flask(__name__)

@server.route('/c/')
def index():
    app = make_chat_app(server)
    return app.index() 

server.run(host="127.0.0.1", port=8050, debug=True)