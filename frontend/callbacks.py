from dash import html
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket
from dash.dependencies import Input, Output, State
import os
import json
from PIL import Image

image_source_path = os.path.join('./', 'data', 'img')

def textbox(chat_msg, box="AI"):
    style = {
        "maxWidth": "60%",
        "width": "max-content",
        "padding": "2px 6px",
        "marginBottom": 20,
    }

    if box == "user":
        style["marginLeft"] = "auto"
        style["marginRight"] = 0
        return dbc.Card(chat_msg, style=style, body=True, color="secondary", inverse=True)

    elif box == "AI":
        style["marginLeft"] = 0
        style["marginRight"] = "auto"
        if(chat_msg[-4:]==".png" or chat_msg[-4:]==".jpg"):
            image_style = {"width": "100%", "height": "auto", "object-fit": "contain"}
            curr_img_source = os.path.join(image_source_path, chat_msg)
            chat_msg = html.Img(src=Image.open(curr_img_source), style=image_style)

        return dbc.Card(chat_msg, style=style, body=True, color="light", inverse=False)

    else:
        raise ValueError("Incorrect option for textbox.")

def register_callbacks(app):
    @app.callback(
        Output("display-conversation", "children"), [Input("store-conversation", "data")]
    )
    def update_display(chat_history):
        return [
            textbox(x, box="user") if i % 2 == 0 else textbox(x, box="AI")
            for i, x in enumerate(chat_history.split("<split>")[:-1])
        ]
    
    @app.callback(
        Output("user-input", "value"),
        [Input("submit", "n_clicks"), Input("user-input", "n_submit")],
    )
    def clear_input(n_clicks, n_submit):
        return ""


    @app.callback(
        [Output('ws', 'send'), Output("store-conversation", "data", allow_duplicate=True), Output("user-input", "disabled", allow_duplicate=True)],
        [Input("submit", "n_clicks"), Input("user-input", "n_submit")],
        [State("user-input", "value"), State("store-conversation", "data")],
        prevent_initial_call=True
    )
    def send_server_message(n_clicks, n_submit, user_input, chat_history):
        if n_clicks == 0 and n_submit is None:
            return "", "", False

        if user_input is None or user_input == "":
            return "", chat_history, False
        
        chat_history += f"{user_input}<split>"
        
        return user_input, chat_history, True
    

    @app.callback(
        [Output("store-conversation", "data"), Output('user-input', 'disabled')],
        Input('ws', 'message'),
        State("store-conversation", "data"),
        prevent_initial_call=True
    )
    def get_server_message(ws_message, chat_history):

        if not ws_message:
            return chat_history, False
        
        error_response = "Apologies, I am unable to fulfill this request. Please try again and ensure that you provide a company ticker and limit your questions to financial analysis."
        
        try:
            server_response = ws_message["data"]

            server_response = json.loads(server_response)
            if(server_response["sender"]=="ratios_agent"):
                model_output = server_response["response"]

            elif(server_response["sender"]=="techplot_agent"):
                model_output = server_response["response"]

            elif(server_response["response"]=="Error"):
                model_output = error_response
            
            else:
                raise TypeError(f"Incorrect server response format. Got response: {server_response}")

        except Exception as e:
            model_output = error_response
            print(f"Error retriving server response: {e}")

        finally:
            chat_history += f"{model_output}<split>"
            return chat_history, False
    