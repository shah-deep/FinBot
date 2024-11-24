import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
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
            dbc.Input(id="user-input", placeholder="Request a Financial Analysis...", type="text", autocomplete=False),
            dbc.Button("Send", id="submit", color="secondary"),
        ]
    )

    container = dbc.Container(
        fluid=False,
        children=[
            dcc.Store(id="store-conversation", data=""),
            conversation,
            controls,
        ],
    )

    return container