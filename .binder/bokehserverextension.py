from subprocess import Popen

def load_jupyter_server_extension(nbapp):
    """serve the bokeh-app directory with bokeh server"""
    Popen(["panel", "serve", "poseidon_viz/Thalassa.ipynb", "--allow-websocket-origin=*"])
