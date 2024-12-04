from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

def create_app_layout():
    conversation = html.Div(
        html.Div(id="display-conversation"),
        style={
            "overflowY": "auto",
            "display": "flex",
            "height": "calc(98vh - 45px)",
            "flexDirection": "column-reverse",
        },
    )

    controls = dbc.InputGroup(
        children=[
            dbc.Input(
                id="user-input", 
                placeholder="Request Financial Analysis... (Eg: Return on Equity, Return on Assets)", 
                type="text", 
                autocomplete="off", 
                disabled=True
            ),
            dbc.Button("Send", id="submit", color="secondary", disabled=True),
        ]
    )

    container = dbc.Container(
            id="main_container",
            fluid=False,
            children=[
                dcc.Location(id="redirect_home", refresh=True),
                dcc.Location(id='url', refresh=False),
                html.Div(id="ws-msg-holder", style={'display': 'none'}, children=""),
                html.Div(id="userinput-holder", style={'display': 'none'}, children=""),
                html.Div(id="connection-id", style={'display': 'none'}, children=""),
                dcc.Store(id="store-conversation", data=""),
                conversation,
                controls,
            ],
            style={
                "height": "100vh",
                "width": "98vw",
                "position": "relative",
                "max-width": "unset",
            }
        )

    return html.Div(container)