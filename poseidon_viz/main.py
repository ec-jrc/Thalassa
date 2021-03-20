import panel as pn
import paths
import utils
data_dir = paths.PACKAGE.parent / 'data'
from panels import elevation_max
from panels import elevation
from panels import video
from panels import grid
from panels import about
from panels import time_series

dataset_path = data_dir / "dataset.nc"
dataset = utils.get_dataset(dataset_path)

pn.serve(
    panels={
        "About": lambda: about(data_dir),
        "Mesh": lambda: grid(dataset),
        "Elevation": lambda: elevation_max(dataset),
        "Forecast": lambda: elevation(dataset),
        "Animation": lambda: video(data_dir),
        "Stations": lambda: time_series(data_dir)
    },
    title={
        "About": "General Info",
        "Mesh": "Display grid",
        "Elevation": "Interactive map with the maximum elevation in the next 72hours",
        "Forecast": "Interactive maps with hourly elevation for the next 72hours",
        "Animation": "Video with the evolution of elevation data",
        "Stations": "Tide guage Time Series",
    },
#    port=80,
    index=(paths.TEMPLATES / "index.html").resolve().as_posix(),
    show=True,
    websocket_origin='localhost',
)
