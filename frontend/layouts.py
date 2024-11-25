import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket
from PIL import Image

def create_app_layout():

    conversation = html.Div(
        html.Div(id="display-conversation"),
        style={
            "overflow-y": "auto",
            "display": "flex",
            "height": "calc(90vh - 132px)",
            "flex-direction": "column-reverse",
        },
    )

    controls = dbc.InputGroup(
        children=[
            dbc.Input(id="user-input", placeholder="Request a Financial Analysis...", type="text", autocomplete="off"),
            dbc.Button("Send", id="submit", color="secondary"),
        ]
    )

    container = dbc.Container(
        fluid=False,
        children=[
            WebSocket(id='ws', url='ws://127.0.0.1:8000/ws'),
            dcc.Store(id="store-conversation", data=""),
            conversation,
            controls,
        ],
    )

    return container