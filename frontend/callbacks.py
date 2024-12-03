from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import os
import json
import time
from PIL import Image
import urllib.parse
from connection import ConnectionHandler
import asyncio
import yfinance as yf


class CallbacksHandler:
    def __init__(self, app):
        self.app = app
        self.image_source_path = os.path.join('./', 'data', 'img')
        self.conn = None

    def textbox(self, chat_msg, box="AI"):
        style = {
            "maxWidth": "60%",
            "width": "max-content",
            "padding": "2px 6px",
            "marginBottom": 20,
            "whiteSpace": "pre-line",
        }

        if box == "user":
            style["marginLeft"] = "auto"
            style["marginRight"] = 0
            return dbc.Card(chat_msg, style=style, body=True, color="secondary", inverse=True)

        elif box == "AI":
            style["marginLeft"] = 0
            style["marginRight"] = "auto"
            if(chat_msg[-4:]==".png" or chat_msg[-4:]==".jpg"):
                image_style = {"width": "100%", "height": "auto", "object-fit": "contain", "max-width": "600px"}
                curr_img_source = os.path.join(self.image_source_path, chat_msg)
                chat_msg = html.Img(src=Image.open(curr_img_source), style=image_style)

            return dbc.Card(chat_msg, style=style, body=True, color="light", inverse=False)

        else:
            raise ValueError("Incorrect option for textbox.")

    def register_callbacks(self):
        
        @self.app.callback(
            Output("display-conversation", "children"), 
            Input("store-conversation", "data")
        )
        def update_display(chat_history):
            """
            Update the displayed conversation history. 
            Textbox are created alternatively for user message and AI message.
            """
            return [
                self.textbox(x, box="user") if i % 2 == 0 else self.textbox(x, box="AI")
                for i, x in enumerate(chat_history.split("<split>")[:-1])
            ]
        
        @self.app.callback(
            Output("user-input", "value"),
            [Input("submit", "n_clicks"), Input("user-input", "n_submit")],
        )
        def clear_input(n_clicks, n_submit):
            return ""
        

        @self.app.callback(
            [Output("redirect_home", "href"), 
             Output("user-input", "disabled", allow_duplicate=True), 
             Output("submit", "disabled", allow_duplicate=True)],
            Input('url', 'search'),
            prevent_initial_call='initial_duplicate'
        )
        def update_query_param(query_string):
            global conn
            params = urllib.parse.parse_qs(query_string.lstrip('?'))
            ticker = params.get('t', [''])[0]
            ticker = str(ticker).upper()
            try:
                info = yf.Ticker(ticker).history(period='5d', interval='1d')
                if(len(info) == 0):
                    return "/?res=Error", True, True
            except:
                # print("Got fin error")
                return "/?res=Error", True, True

            self.ticker = ticker
            conn = ConnectionHandler()
            asyncio.run(conn.connect_server(ticker))
            while not conn.is_connected.is_set():
                time.sleep(0.1)
            return None, False, False


        # def register_socket_callbacks(app):
        @self.app.callback(
            [Output("userinput-holder", "children"), 
             Output("store-conversation", "data"), 
             Output("user-input", "disabled", allow_duplicate=True), 
             Output("submit", "disabled", allow_duplicate=True)],
            [Input("submit", "n_clicks"), Input("user-input", "n_submit")],
            [State("user-input", "value"), State("store-conversation", "data")],
            prevent_initial_call=True
        )
        def send_server_message(n_clicks, n_submit, user_input, chat_history):
            if n_clicks == 0 and n_submit is None:
                return "", "", False, False

            if user_input is None or user_input == "":
                return "", chat_history, False, False
            
            chat_history += f"{user_input}<split>"
            return user_input, chat_history, True, True
        

        @self.app.callback(
            Output("ws-msg-holder", "children"),
            Input("userinput-holder", "children"),
            prevent_initial_call=True
        )
        def send_server_message(user_input):
            global conn
            conn.send_message(user_input)
            response = conn.get_message()
            return response
        

        @self.app.callback(
            [Output("store-conversation", "data", allow_duplicate=True), 
             Output("user-input", "disabled"), 
             Output("submit", "disabled")],
            Input("ws-msg-holder", "children"),
            State("store-conversation", "data"),
            prevent_initial_call=True
        )
        def get_server_message(server_response, chat_history):

            if not server_response:
                return chat_history, False, False
            
            error_response = "Apologies, I cannot fulfill this request. Please try again and focus your questions on financial analysis."
            
            try:
                server_response = json.loads(server_response)
                if(server_response["sender"] in ["ratios_agent", "techplot_agent", "compinfo_agent"]):
                    model_output = server_response["response"]

                else:
                    raise ValueError(f"Incorrect server sender. Got response: {server_response}")
                
                if(server_response["response"]=="Error"):
                    model_output = error_response

            except Exception as e:
                model_output = error_response
                print(f"Error retriving server response: {e}")

            finally:
                chat_history += f"{model_output}<split>"
                return chat_history, False, False
    