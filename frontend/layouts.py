import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket


conversation = html.Div(
    html.Div(id="display-conversation"),
    style={
        "overflowY": "auto",
        "display": "flex",
        "height": "calc(90vh - 132px)",
        "flexDirection": "column-reverse",
    },
)

controls = dbc.InputGroup(
    children=[
        dbc.Input(id="user-input", placeholder="Request a Financial Analysis...", type="text", autocomplete="off", disabled=False),
        dbc.Button("Send", id="submit", color="secondary"),
    ]
)


def create_app_layout():

    container = dbc.Container(
        id="main_container",
        fluid=False,
        children=[
            html.Div(id="ws_msg_holder", style={'display': 'none'}, children=""),
            dcc.Store(id="store-conversation", data=""),
            conversation,
            controls,
        ],
    )

    return container