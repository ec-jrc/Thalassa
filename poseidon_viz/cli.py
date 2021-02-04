from __future__ import annotations

import pathlib
import signal
import shlex
import subprocess
import sys

from typing import Any
from typing import Dict
from typing import List
from typing import Union

import typer

from . import utils
from . import paths
# from .utils import get_dataset
# from .utils import save_elevation_to_disk
# from .utils import save_grid_to_disk


def create_dir(path: pathlib.Path) -> None:
    try:
        path.mkdir(exist_ok=True, parents=True)
    except PermissionError:
        typer.echo(f"You don't have sufficient permissions to create the output directory: {path}")
        raise typer.Exit(1)


app = typer.Typer(help="Visualize pyPoseidon output")


@app.command(help="Extract grid data from the pyPoseidon NetCDF output")
def extract_grid(
    dataset: pathlib.Path = typer.Argument(
        ..., exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True, help="The netcdf file that got created by pyPoseidon"
    ),
    output: pathlib.Path = typer.Option(
        "data", file_okay=False, dir_okay=True, writable=True, resolve_path=True, help="The directory that will contain the output"
    ),
    target_crs: int = typer.Option(3857, help="The target CRS specified as an EPSG code")
) -> None:
    create_dir(output)
    dataset_name = dataset.stem
    dataset = utils.get_dataset(dataset)
    utils.save_grid_to_disk(dataset, output / "grid.npz", target_crs=target_crs)


@app.command(help="Extract elevation data from the pyPoseidon NetCDF output")
def extract_elevation(
    dataset: pathlib.Path = typer.Argument(
        ..., exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True, help="The netcdf file that got created by pyPoseidon"
    ),
    output: pathlib.Path = typer.Option(
        "data", file_okay=False, dir_okay=True, writable=True, resolve_path=True, help="The directory that will contain the output"
    ),
) -> None:
    create_dir(output)
    output_file = output / (dataset.stem + ".npz")
    dataset = utils.get_dataset(dataset)
    utils.save_elevation_to_disk(dataset, output_file)


@app.command(help="Start panel server")
def serve(
    scripts_dir: pathlib.Path = typer.Argument(
        "scripts", file_okay=False, dir_okay=True, readable=True, resolve_path=True, help="The directory that will contain the output"
    ),
    port: int = typer.Option(9000, help="The port where the panel server will be listening to")
) -> None:
    cmd = f"panel serve --port {port} --log-level trace --allow-websocket-origin localhost:{port} {scripts_dir}"
    if not scripts_dir.exists():
        msg = f"The provided scripts_dir does not exist: {scripts_dir}"
        typer.echo(msg)
        raise typer.Exit(1)
    subprocess.run(shlex.split(cmd), check=True)


@app.command(help="Create mp4 video")
def generate_video(
    dataset: pathlib.Path = typer.Argument(
        ..., exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True, help="The netcdf file that got created by pyPoseidon"
    ),
) -> None:
    from .panels import AAA
    dataset = utils.get_dataset(dataset)
    aaa = AAA(dataset)
    animation = aaa.frames(var='elev',title='SSH')
    animation.save("/tmp/elev2.mp4")


@app.command(help="Start panel server")
def serve(
    data_dir: pathlib.Path = typer.Argument(
        "data", file_okay=False, dir_okay=True, resolve_path=True,
        help="The directory that contains the output that will be visualized",
    ),
    port: int = typer.Option(0, help="Specify the port on which the server will be listening to. A random one is chosen by default."),
    websocket_origin: str = typer.Option("localhost", help="The host that can connect to the websocket"),
    show: bool = typer.Option(True, help="Whether to open the server in a new browser tab on start"),
) -> None:
    # Move imports in here for improved performance
    import panel
    from .panels import elevation_max
    from .panels import elevation
    from .panels import video
    from .panels import grid
    from .panels import about
    from .panels import time_series
    panel.serve(
        panels={
            "About": lambda: about(data_dir),
            "Mesh": lambda: grid(data_dir),
            "Max_Elevation": lambda: elevation_max(data_dir),
            "Elevation": lambda: elevation(data_dir),
            "Animation": lambda: video(data_dir),
            "Stations": lambda: time_series(data_dir)
        },
        title={
            "About": "General Info",
            "Mesh": "Display grid",
            "Max_Elevation": "Interactive map with the maximum elevation in the next 72hours",
            "Elevation": "Interactive maps with hourly elevation for the next 72hours",
            "Animation": "Video with the evolution of elevation data",
            "Stations": "Tide guage Time Series",
        },
        port=port,
        index=(paths.TEMPLATES / "index.html").resolve().as_posix(),
        show=show,
        websocket_origin=websocket_origin,
    )


# handle Ctrl-C
def sigint_handler(sig: Any, frame: Any) -> None:
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)
