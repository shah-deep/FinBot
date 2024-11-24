
import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

def register_callbacks(app):
    def textbox(text, box="AI"):
        style = {
            "max-width": "60%",
            "width": "max-content",
            "padding": "2px 6px",
            "margin-bottom": 20,
        }

        if box == "user":
            style["margin-left"] = "auto"
            style["margin-right"] = 0
            return dbc.Card(text, style=style, body=True, color="secondary", inverse=True)

        elif box == "AI":
            style["margin-left"] = 0
            style["margin-right"] = "auto"
            textbox = dbc.Card(text, style=style, body=True, color="light", inverse=False)
            return html.Div(textbox)

        else:
            raise ValueError("Incorrect option for `box`.")
        
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
        Output("store-conversation", "data"),
        [Input("submit", "n_clicks"), Input("user-input", "n_submit")],
        [State("user-input", "value"), State("store-conversation", "data")],
    )
    def run_chatbot(n_clicks, n_submit, user_input, chat_history):
        if n_clicks == 0 and n_submit is None:
            return ""

        if user_input is None or user_input == "":
            return chat_history


        # First add the user input to the chat history
        chat_history += f"{user_input}<split>"

        
        model_output = "AI Response"

        chat_history += f"{model_output}<split>"

        return chat_history