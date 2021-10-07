from __future__ import annotations

import geoviews as gv  # type: ignore
import holoviews as hv  # type: ignore
import pandas as pd  # type: ignore
import xarray as xr
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
) -> gv.TriMesh:
    # local aliases
    lons = ds[longitude_var].values
    lats = ds[latitude_var].values
    simplices = ds[simplices_var].values
    # get max elevation
    max_elevation = ds[elevation_var].max(dim=time_var).values
    # Create holoviews objects
    points_df = pd.DataFrame(dict(lons=lons, lats=lats, max_elevation=max_elevation))
    points_gv = gv.Points(points_df, kdims=["lons", "lats"], vdims="max_elevation")
    trimesh = gv.TriMesh((simplices, points_gv))
    return trimesh


def get_tiles() -> gv.Tiles:
    tiles = gv.WMTS("http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png")
    return tiles


def get_wireframe(trimesh: gv.TriMesh) -> hv.Layout:
    # If we want the wireframe plot to be connected to the main plot
    # we need create the overlay with tiles too.
    # That being said, we might be able to use a more lightweight tile for the wireframe
    tiles = get_tiles()
    wireframe = dynspread(rasterize(trimesh.edgepaths, precompute=True))
    wireframe = wireframe.opts(title="Wireframe")  # pylint: disable=no-member
    return tiles * wireframe


def get_max_elevation(trimesh: gv.TriMesh) -> hv.Layout:
    tiles = get_tiles()
    elevation = rasterize(trimesh, precompute=True).opts(  # pylint: disable=no-member
        title="Max Elevation",
        colorbar=True,
        clabel="meters",
        show_legend=True,
    )
    return tiles * elevation
