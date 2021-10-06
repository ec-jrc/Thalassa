from __future__ import annotations

import holoviews as hv  # type: ignore
import pandas as pd  # type: ignore
import xarray as xr
from holoviews import opts as hvopts
from holoviews.operation.datashader import dynspread  # type: ignore
from holoviews.operation.datashader import rasterize  # type: ignore

# Load bokeh backend
hv.extension("bokeh")


def get_trimesh(
    ds: xr.Dataset,
    longitude_var: str,
    latitude_var: str,
    elevation_var: str,
    simplices_var: str,
    time_var: str,
) -> hv.TriMesh:
    # Prepare the data
    lons = ds[longitude_var].values
    lats = ds[latitude_var].values
    simplices = ds[simplices_var].values
    elevation = ds[elevation_var].max(dim=time_var).values
    # Create holoviews objects
    points_df = pd.DataFrame(dict(longitude=lons, latitude=lats, elevation=elevation))
    points_hv = hv.Points(points_df, kdims=["longitude", "latitude"], vdims="elevation")
    trimesh = hv.TriMesh((simplices, points_hv))
    return trimesh


def get_wireframe_and_max_elevation(trimesh: hv.TriMesh) -> hv.Layout:
    # pylint: disable=no-member
    wireframe = dynspread(rasterize(trimesh.edgepaths)).opts(title="Wireframe")
    elevation = rasterize(trimesh).opts(
        title="Max Elevation",
        colorbar=True,
        clabel="meters",
        show_legend=True,
    )
    layout = (elevation + wireframe).cols(1)
    layout = layout.opts(
        hvopts.Image(width=800, height=400, show_title=True, tools=["hover"]),
        hvopts.Layout(toolbar="right"),
    )
    return layout
