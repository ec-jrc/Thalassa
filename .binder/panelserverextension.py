from subprocess import Popen

def load_jupyter_server_extension(nbapp):
    """serve the Thalassa.ipynb with bokeh server"""
    Popen(["panel", "serve", "Thalassa", "--allow-websocket-origin=*"])
