import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from PIL import Image

from layouts import create_app_layout
from callbacks import register_callbacks


# Define app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


app.title = "FinBot"

# Set up app layout
app.layout = create_app_layout()

# Register callbacks
register_callbacks(app)





if __name__ == "__main__":
    app.run_server(debug=True)