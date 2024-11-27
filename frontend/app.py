from flask import Flask, render_template, redirect, url_for, request
from chat_app import make_chat_app

server = Flask(__name__)
app = make_chat_app(server)

@server.route("/")
def home():
    return render_template("index.html")

@server.route("/redirect", methods=["POST"])
def handle_redirect():
    ticker = request.form.get("ticker")
    if not ticker:
        return redirect(url_for("home"))
    return redirect(f"/c/?t={ticker}")


server.run(host="127.0.0.1", port=8050, debug=True)