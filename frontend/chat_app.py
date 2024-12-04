import dash
import dash_bootstrap_components as dbc
from layouts import create_app_layout
from callbacks import CallbacksHandler

def make_chat_app(server):
    app = dash.Dash(
        __name__, 
        server=server, 
        external_stylesheets=[dbc.themes.BOOTSTRAP], # Use Bootstrap for styling
        url_base_pathname="/c/") # Define base path for app

    app.title = "FinBot"

    # Set up app layout
    app.layout = create_app_layout()

    # Register callbacks
    callbacks = CallbacksHandler(app)
    callbacks.register_callbacks()

    return app