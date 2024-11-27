import dash
import dash_bootstrap_components as dbc
from flask import request
from layouts import create_app_layout
from callbacks import register_callbacks

def make_chat_app(server):
    app = dash.Dash(
        __name__, 
        server=server, 
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        url_base_pathname="/c/")

    app.title = "FinBot"

    # Set up app layout
    app.layout = create_app_layout()

    # Register callbacks
    register_callbacks(app)

    return app