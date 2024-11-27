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


def create_app_layout(ticker: str):

    container = dbc.Container(
        fluid=False,
        children=[
            # WebSocket(id='ws', url=f'ws://127.0.0.1:8000/ws?tkr={ticker}'),
            dcc.Store(id="store-conversation", data=""),
            conversation,
            controls,
        ],
    )

    return container