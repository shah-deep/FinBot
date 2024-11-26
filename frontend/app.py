import dash
import dash_bootstrap_components as dbc
from PIL import Image

from layouts import create_app_layout
from callbacks import register_callbacks


# Define app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.title = "FinBot"

# Set up app layout
app.layout = create_app_layout()

# Register callbacks
register_callbacks(app)


if __name__ == "__main__":
    app.run_server(host="127.0.0.1", port=8050, debug=True)