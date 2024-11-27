from flask import Flask, request, redirect, url_for
from dash import Dash, html, dcc

# Initialize Flask
server = Flask(__name__)

# Initialize Dash
dash_app = Dash(__name__, server=server, url_base_pathname='/dash/')

# Define the Dash layout
dash_app.layout = html.Div([
    html.H1("Dash App Embedded in Flask"),
    html.Div(id='query-output', children="Query parameters will appear here."),
    dcc.Input(id='input', type='text', placeholder='Enter something'),
    html.Button('Submit', id='button'),
])

# Flask route
@server.route('/')
def home():
    # Flask route that accepts query parameters
    name = request.args.get('name', 'Guest')
    return f"Hello, {name}! Visit the Dash app at /dash/"

# Flask route to dynamically redirect to Dash with a query string
@server.route('/go-to-dash')
def go_to_dash():
    user = request.args.get('user', 'anonymous')
    # Redirect to the Dash app with a query parameter
    return redirect(url_for('dash', user=user))

# Dash callback to capture and display query parameters
@dash_app.server.route('/dash/')
def dash():
    # Retrieve query parameters
    user = request.args.get('user', 'No user provided')
    return f"Hello from Dash! User: {user}"

# Run the Flask server
if __name__ == '__main__':
    server.run(debug=True)
