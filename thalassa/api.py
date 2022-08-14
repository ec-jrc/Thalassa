from __future__ import annotations

import logging

import geoviews as gv
import holoviews as hv
import numpy as np
import pandas as pd
import xarray as xr

from holoviews.operation.datashader import dynspread
from holoviews.operation.datashader import rasterize
from holoviews.streams import PointerXY
from holoviews.streams import Tap
from holoviews.streams import Stream


from .utils import get_index_of_nearest_node

logger = logging.getLogger(__name__)

hv.extension("bokeh")


def create_trimesh(
    ds: xr.Dataset,
    variable: str,
    timestamp: str | pd.Timestamp | None = None,
    layer: int | None = None,
) -> gv.TriMesh:
    columns = ["lon", "lat", variable]
    if layer is not None:
        ds = ds.isel(layer=layer)
    if timestamp == "max":
        points_df = ds[columns].max("time").to_dataframe()
    elif timestamp == "min":
        points_df = ds[columns].min("time").to_dataframe()
    elif timestamp:
        points_df = ds.sel({"time": timestamp})[columns].to_dataframe().drop(columns="time")
    else:
        points_df = ds[columns].to_dataframe()
    points_df = points_df.reset_index(drop=True)
    points_gv = gv.Points(points_df, kdims=["lon", "lat"], vdims=[variable])
    trimesh = gv.TriMesh((ds.triface_nodes.values, points_gv))
    return trimesh


def get_tiles() -> gv.Tiles:
    tiles = gv.WMTS("http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png")
    return tiles


def get_wireframe(trimesh: gv.TriMesh) -> gv.DynamicMap:
    wireframe = dynspread(rasterize(trimesh.edgepaths, precompute=True)).opts(tools=[])
    return wireframe


def get_raster(
    trimesh: gv.TriMesh,
    title: str = "",
    clabel: str = "",
    clim_min: float | None = None,
    clim_max: float | None = None,
) -> gv.DynamicMap:
    raster = rasterize(trimesh, precompute=True).opts(
        cmap="viridis",
        clabel=clabel,
        colorbar=True,
        clim=(clim_min, clim_max),
        title=title,
        tools=["hover"],
    )
    return raster


def is_point_in_the_mesh(raster: gv.DynamicMap, lon: float, lat: float) -> bool:
    """Return `True` if the point is inside the mesh of the `raster`, `False` otherwise"""
    breakpoint()
    raster_dataset = raster.values()[0].data
    data_var_name = raster.ddims[-1].name
    interpolated = raster_dataset[data_var_name].interp(dict(lon=lon, lat=lat)).values
    return ~np.isnan(interpolated)


def _get_stream_timeseries(
    ds: xr.Dataset,
    variable: str,
    source_raster: gv.DynamicMap,
    stream_class: Stream,
    layer: int | None = None,
) -> gv.DynamicMap:

    if stream_class not in {Tap, PointerXY}:
        raise ValueError("Unsupported Stream class. Please choose either Tap or PointerXY")

    if layer is not None:
        ds = ds.isel(layer=layer)
    ds = ds[["lon", "lat", variable]]

    def callback(x: float, y: float) -> hv.Curve:
        if not is_point_in_the_mesh(raster=source_raster, lon=x, lat=y):
            # if the point is not inside the mesh, then omit the timeseries
            title = f"{variable} - Lon={x:.3f} Lat={y:.3f}"
            plot = hv.Curve([]).opts(
                title=title,
                framewise=True,
                padding=0.1,
                show_grid=True,
                tools=["hover"],
            )
        else:
            node_index = get_index_of_nearest_node(ds=ds, lon=x, lat=y)
            ts = ds.isel(node=node_index)
            title = f"{variable} - Lon={ts.lon.values:.3f} Lat={ts.lat.values:.3f}"
            plot = (
                hv.Curve(ts[variable])
                .redim(variable, range=(ts[variable].min(), ts[variable].max()))
                .opts(
                    title=title,
                    framewise=True,
                    padding=0.1,
                    show_grid=True,
                    tools=["hover"],
                )
            )
        return plot

    stream = stream_class(x=0, y=0, source=source_raster)
    dmap = gv.DynamicMap(callback, streams=[stream])
    return dmap


def get_tap_timeseries(
    ds: xr.Dataset,
    variable: str,
    source_raster: gv.DynamicMap,
    layer: int | None = None,
) -> gv.DynamicMap:
    dmap = _get_stream_timeseries(
        ds=ds,
        variable=variable,
        source_raster=source_raster,
        stream_class=Tap,
        layer=layer,
    )
    return dmap


def get_pointer_timeseries(
    ds: xr.Dataset,
    variable: str,
    source_raster: gv.DynamicMap,
    layer: int | None = None,
) -> gv.DynamicMap:
    dmap = _get_stream_timeseries(
        ds=ds,
        variable=variable,
        source_raster=source_raster,
        stream_class=PointerXY,
        layer=layer,
    )
    return dmap


def extract_timeseries(ds: xr.Dataset, variable: str, lon: float, lat: float) -> xr.DataArray:
    index = get_index_of_nearest_node(ds=ds, lon=lon, lat=lat)
    # extracted = ds[[variable, "lon", "lat"]].isel(node=index)
    return ds[variable].isel(node=index)


def plot_timeseries(ts: xr.DataArray, lon: float, lat: float) -> gv.DynamicMap:
    node_index = get_index_of_nearest_node(ds=ds, lon=lon, lat=lat)
    node_lon = ds.lon.isel(node_index)
    node_lat = ds.lat.isel(node_index)
    title = f"Lon={x:.3f} Lat={y:.3f} - {node_lon}, {node_lat}"
    plot = (
        hv.Curve(ts)
        .redim(variable, range=(ts.min(), ts.max()))
        .opts(title=title, framewise=True, padding=0.1, show_grid=True)
    )
    return plot
