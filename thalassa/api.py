from __future__ import annotations

import logging
import operator
import os
import typing
import warnings
from functools import reduce

import geoviews as gv
import holoviews as hv
import pandas as pd
import xarray as xr
from bokeh.models import HoverTool
from bokeh.models.formatters import DatetimeTickFormatter
from holoviews import opts as hvopts
from holoviews.operation.datashader import dynspread
from holoviews.operation.datashader import rasterize
from holoviews.streams import PointerXY
from holoviews.streams import Selection1D
from holoviews.streams import Stream
from holoviews.streams import Tap

from . import normalization
from . import utils

logger = logging.getLogger(__name__)


# ADCIRC datasets are not compatible with xarray:
# They fail with the error:
#   "dimension 'neta' already exists as a scalar variable",
#   "dimension 'nvel' already exists as a scalar variable",
# Source: https://github.com/pydata/xarray/issues/1709#issuecomment-343714896
#
# The workaround we have for this is to drop the problematic variables
# As an implementation detail we make use of an xarray "feature" which ignores
# non-existing names in `drop_variables`. So we can use `drop_variables=[...]` even
# if we are opening a dataset from a different solver.
# This may cause  issues if different solvers use `neta/nvel` as dimension/variable
# names, but at least for now it seems to be good enough.
ADCIRC_VARIABLES_TO_BE_DROPPED = ["neta", "nvel", "max_nvdll", "max_nvell"]


def open_dataset(
    path: str | os.PathLike[str],
    normalize: bool = True,
    **kwargs: dict[str, typing.Any],
) -> xr.Dataset:
    """
    Open the file specified at ``path`` using ``xarray`` and return an ``xarray.Dataset``.

    If `normalize` is `True` then convert the dataset to the "Thalassa schema", too.
    Additional `kwargs` are passed on to `xarray.open_dataset()`.

    !!! note

        This function is just a wrapper around `xarray.open_dataset()`. The reason we need
        it is because the netcdfs files created by ADCIRC are not compatible with `xarray`,
        at least not when using the defaults. This function automatically detects the
        problematic variables (e.g. `neta` and `nvel`) and drops them.

    Examples:
        ``` python
        import thalassa

        ds = thalassa.open_dataset("some_netcdf.nc")
        print(ds)
        ```

    Parameters:
        path: The path to the dataset file (netCDF, zarr, grib)
        normalize: Boolean flag indicating whether the dataset should be converted/normalized to the "Thalassa schema".
            Normalization is currently only supported for ``SCHISM`` and ``ADCIRC`` netcdf files.
        kwargs: The ``kwargs`` are being passed through to ``xarray.open_dataset``.

    """
    default_kwargs: dict[str, typing.Any] = dict(
        mask_and_scale=True,
        cache=False,
        drop_variables=ADCIRC_VARIABLES_TO_BE_DROPPED,
    )
    with warnings.catch_warnings(record=True):
        ds = xr.open_dataset(path, **(default_kwargs | kwargs))  # type: ignore[arg-type]
    if normalize:
        ds = normalization.normalize(ds)
    return ds


def get_dtf() -> DatetimeTickFormatter:
    dtf = DatetimeTickFormatter(
        hours="%m/%d %H:%M",
        days="%m/%d %H",
        months="%Y/%m/%d",
        years="%Y/%m",
    )
    return dtf


def create_trimesh(
    ds_or_trimesh: gv.TriMesh | xr.Dataset,
    variable: str | None = None,
) -> gv.TriMesh:
    """
    Create a ``gv.TriMesh`` object from the provided dataset.

    Parameters:
        ds_or_trimesh: The dataset containing the variable we want to visualize.
            If a trimesh object is passed, then return it immediately.
        variable: The data variable we want to visualize
    """
    if isinstance(ds_or_trimesh, gv.TriMesh):
        # This is already a trimesh, nothing to do
        return ds_or_trimesh
    # create the trimesh object
    ds = ds_or_trimesh
    columns = ["lon", "lat"]
    if variable is not None:
        columns.append(variable)
    points_df = ds[columns].to_dataframe().reset_index(drop=True)
    if variable:
        points_gv = gv.Points(points_df, kdims=["lon", "lat"], vdims=[variable])
    else:
        points_gv = gv.Points(points_df, kdims=["lon", "lat"])
    trimesh = gv.TriMesh((ds.triface_nodes.data, points_gv), name=variable)
    return trimesh


def get_tiles(url: str = "http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png") -> gv.Tiles:
    """
    Return a WMTS using the provided `url`.

    Parameters:
        url: The URL of the Tiling Service. It defaults to Openstreetmap.

    """
    tiles = gv.WMTS(url)
    return tiles


def get_wireframe(
    ds_or_trimesh: gv.TriMesh | xr.Dataset,
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
) -> gv.DynamicMap:
    """Return a ``DynamicMap`` with a wireframe of the mesh."""
    trimesh = create_trimesh(ds_or_trimesh)
    kwargs = dict(element=trimesh.edgepaths, precompute=True)
    if x_range:
        kwargs["x_range"] = x_range
    if y_range:
        kwargs["y_range"] = y_range
    wireframe = rasterize(**kwargs).opts(tools=["hover"], cmap=["black"], title="Mesh")
    wireframe = dynspread(wireframe)
    return wireframe


def get_raster(
    ds_or_trimesh: gv.TriMesh | xr.Dataset,
    variable: str | None = None,
    title: str = "",
    cmap: str = "plasma",
    colorbar: bool = True,
    clabel: str = "",
    clim_min: float | None = None,
    clim_max: float | None = None,
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
) -> gv.DynamicMap:
    """
    Return a ``DynamicMap`` with a rasterized image of the variable.

    Uses ``datashader`` behind the scenes.
    """
    trimesh = create_trimesh(ds_or_trimesh=ds_or_trimesh, variable=variable)
    kwargs = dict(element=trimesh, precompute=True)
    if x_range:
        kwargs["x_range"] = x_range
    if y_range:
        kwargs["y_range"] = y_range
    logger.debug("rasterize kwargs: %s", kwargs)
    raster = rasterize(**kwargs).opts(
        cmap=cmap,
        clabel=clabel,
        colorbar=colorbar,
        clim=(clim_min, clim_max),
        title=title or trimesh.name,
        tools=["hover"],
    )
    return raster


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
        if not utils.is_point_in_the_raster(raster=source_raster, lon=x, lat=y):
            # if the point is not inside the mesh, then omit the timeseries
            title = f"Lon={x:.3f} Lat={y:.3f}"
            plot = hv.Curve([])
        else:
            node_index = utils.get_index_of_nearest_node(ds=ds, lon=x, lat=y)
            ts = ds.isel(node=node_index)
            title = f"Lon={ts.lon.data:.3f} Lat={ts.lat.data:.3f}"
            plot = hv.Curve(ts[variable])
            plot = plot.redim(
                variable,
                range=(ts[variable].min(), ts[variable].max()),
            )
        # setup hover
        hover = HoverTool(
            tooltips=[
                ("time", "@time{%F %T}"),
                (f"{variable}", f"@{variable}"),
            ],
            formatters={
                "@time": "datetime",
            },
        )
        # apply opts
        plot = plot.opts(
            title=title,
            framewise=True,
            padding=0.05,
            show_grid=True,
            tools=[hover],
            xformatter=get_dtf(),
        )
        return plot

    stream = stream_class(x=0, y=0, source=source_raster)
    dmap = gv.DynamicMap(callback, streams=[stream])
    return dmap


def get_station_timeseries(
    stations: xr.Dataset,
    pins: gv.DynamicMap,
) -> hv.DynamicMap:
    def callback(index: list[int]) -> hv.Curve:
        # sometimes there are multiple pins with the same lon/lat
        # When one of these pins gets selected index contains the indices of both pins
        # This causes an exception to be raised.
        # TODO: Until we decide how to resolve this, we just pick the first pin, no matter what.
        if len(index) >= 2:
            logger.warning("TS: multiple pins selected: %r", index)
            index = [index[0]]
        logger.warning("TS: Choosing the first one: %r", index)
        columns = ["stime", "elev_sim", "time", "elev_obs"]
        if not index:
            title = "No stations selected"
            ds = pd.DataFrame(columns=columns)
        else:
            df = pins.data
            title = df.iloc[index[0]].location
            ds = stations.isel(node=df.index[index])[columns]
        dataset = hv.Dataset(ds)
        curve1 = hv.Curve(dataset, kdims=["stime"], vdims=["elev_sim"], label="Simulation")
        curve2 = hv.Curve(dataset, kdims=["time"], vdims=["elev_obs"], label="Observation")
        components = [curve1, curve2]
        overlay = reduce(operator.mul, components).opts(
            hvopts.Curve(
                padding=0.05,
                title=title,
                framewise=True,
                xlabel="Time",
                ylabel="Elevation",
                tools=["hover"],
                xformatter=get_dtf(),
            ),
        )
        return overlay

    stream = Selection1D(source=pins, index=[])
    dmap = hv.DynamicMap(callback, streams=[stream])
    return dmap


_STATION_VARIABLES = [
    "ioc_code",
    "lat",
    "lon",
    "location",
    "Mean Absolute Error",
    "RMSE",
    "Scatter Index",
    "percentage RMSE",
    "BIAS or mean error",
    "Standard deviation of residuals",
    "Correlation Coefficient",
    "R^2",
    "Nash-Sutcliffe Coefficient",
    "lamda index",
]


def get_station_table(
    stations: xr.Dataset,
    pins: gv.DynamicMap,
) -> hv.DynamicMap:
    def callback(index: list[int]) -> hv.Table:
        # sometimes there are multiple pins with the same lon/lat
        # When one of these pins gets selected index contains the indices of both pins
        # This causes an exception to be raised.
        # TODO: Until we decide how to resolve this, we just pick the first pin, no matter what.
        if len(index) >= 2:
            logger.warning("ST: multiple pins selected: %r", index)
            index = [index[0]]
        logger.warning("ST: Choosing the first one: %r", index)
        if not index:
            df = pd.DataFrame(columns=["attribute", "value"]).set_index("attribute")
        else:
            ds = stations.isel(node=pins.data.index[index])
            df = ds[_STATION_VARIABLES].to_dataframe().T
            df.index.name = "attribute"
            df.columns = ["value"]
        table = hv.Table(df, kdims=["attribute"])
        return table

    stream = Selection1D(source=pins, index=[])
    dmap = hv.DynamicMap(callback, streams=[stream])
    return dmap


def get_station_pins(stations: xr.Dataset) -> gv.Points:
    df = stations[["lon", "lat", "location"]].to_dataframe()
    pins = gv.Points(df, kdims=["lon", "lat"], vdims=["location"])
    pins = pins.opts(color="red", marker="circle_dot", size=10, tools=["tap", "hover"])
    return pins


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
    index = utils.get_index_of_nearest_node(ds=ds, lon=lon, lat=lat)
    # extracted = ds[[variable, "lon", "lat"]].isel(node=index)
    return ds[variable].isel(node=index)


# def plot_timeseries(ds: xr.DataArray, lon: float, lat: float) -> gv.DynamicMap:
#     node_index = utils.get_index_of_nearest_node(ds=ds, lon=lon, lat=lat)
#     node_lon = ds.lon.isel(node_index)
#     node_lat = ds.lat.isel(node_index)
#     title = f"Lon={x:.3f} Lat={y:.3f} - {node_lon}, {node_lat}"
#     plot = (
#         hv.Curve(ds)
#         .redim(variable, range=(ts.min(), ts.max()))
#         .opts(title=title, framewise=True, padding=0.05, show_grid=True)
#     )
#     return plot
