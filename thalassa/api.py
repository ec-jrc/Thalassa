from __future__ import annotations

import functools
import logging
import operator
import os
import typing as T
import warnings

from . import normalization
from . import utils

# from holoviews import opts as hvopts

if T.TYPE_CHECKING:  # pragma: no cover
    import bokeh.models
    import geoviews
    import holoviews
    import xarray
    from holoviews.streams import Stream
    from bokeh.models.formatters import DatetimeTickFormatter

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
    **kwargs: dict[str, T.Any],
) -> xarray.Dataset:
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
    import xarray as xr

    default_kwargs: dict[str, T.Any] = dict(
        mask_and_scale=True,
        cache=False,
        drop_variables=ADCIRC_VARIABLES_TO_BE_DROPPED,
    )
    with warnings.catch_warnings(record=True):
        ds = xr.open_dataset(path, **(default_kwargs | kwargs))
    if normalize:
        ds = normalization.normalize(ds)
    return ds


def get_dtf() -> DatetimeTickFormatter:
    from bokeh.models.formatters import DatetimeTickFormatter

    dtf = DatetimeTickFormatter(
        hours="%m/%d %H:%M",
        days="%m/%d %H",
        months="%Y/%m/%d",
        years="%Y/%m",
    )
    return dtf


def create_trimesh(
    ds_or_trimesh: geoviews.TriMesh | xarray.Dataset,
    variable: str | None = None,
) -> geoviews.TriMesh:
    """
    Create a ``geoviews.TriMesh`` object from the provided dataset.

    Parameters:
        ds_or_trimesh: The dataset containing the variable we want to visualize.
            If a trimesh object is passed, then return it immediately.
        variable: The data variable we want to visualize
    """
    import geoviews as gv
    from geoviews.operation import project
    from cartopy import crs

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
    with utils.timer("trimesh: reproject points to GOOGLE_MERCATOR"):
        points_gv = project(points_gv, projection=crs.GOOGLE_MERCATOR)
    trimesh = gv.TriMesh((ds.triface_nodes.data, points_gv), name=variable)
    return trimesh


def get_tiles(url: str = "http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png") -> geoviews.Tiles:
    """
    Return a WMTS using the provided `url`.

    Parameters:
        url: The URL of the Tiling Service. It defaults to Openstreetmap.

    """
    import geoviews as gv

    tiles = gv.WMTS(url)
    return tiles


def get_wireframe(
    ds_or_trimesh: geoviews.TriMesh | xarray.Dataset,
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
    hover: bool = True,
) -> geoviews.DynamicMap:
    """Return a ``DynamicMap`` with a wireframe of the mesh."""
    import holoviews.operation.datashader as hv_operation_datashader

    trimesh = create_trimesh(ds_or_trimesh)
    kwargs = dict(element=trimesh.edgepaths, precompute=True)
    if x_range:
        kwargs["x_range"] = x_range
    if y_range:
        kwargs["y_range"] = y_range
    wireframe = hv_operation_datashader.rasterize(**kwargs).opts(
        tools=["hover"] if hover else [],
        cmap=["black"],
        title="Mesh",
    )
    wireframe = hv_operation_datashader.dynspread(wireframe)
    return wireframe


def get_raster(
    ds_or_trimesh: geoviews.TriMesh | xarray.Dataset,
    variable: str | None = None,
    title: str = "",
    cmap: str = "plasma",
    colorbar: bool = True,
    clabel: str = "",
    clim_min: float | None = None,
    clim_max: float | None = None,
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
) -> geoviews.DynamicMap:
    """
    Return a ``DynamicMap`` with a rasterized image of the variable.

    Uses ``datashader`` behind the scenes.
    """
    import holoviews.operation.datashader as hv_operation_datashader

    trimesh = create_trimesh(ds_or_trimesh=ds_or_trimesh, variable=variable)
    kwargs = dict(element=trimesh, precompute=True)
    if x_range:
        kwargs["x_range"] = x_range
    if y_range:
        kwargs["y_range"] = y_range
    raster = hv_operation_datashader.rasterize(**kwargs).opts(
        cmap=cmap,
        clabel=clabel,
        colorbar=colorbar,
        clim=(clim_min, clim_max),
        title=title or trimesh.name,
        tools=["hover"],
    )
    return raster


def get_hover(variable: str) -> bokeh.models.HoverTool:
    import bokeh.models

    hover = bokeh.models.HoverTool(
        tooltips=[
            ("time", "@{time}{%F %T}"),
            (f"{variable}", f"@{variable}"),
        ],
        formatters={
            "@{time}": "datetime",
        },
    )
    return hover



def _get_stream_timeseries(
    ds: xarray.Dataset,
    variable: str,
    source_raster: geoviews.DynamicMap,
    stream_class: Stream,
    title_template: str,
    fontscale: float = 1,
) -> geoviews.DynamicMap:
    import geoviews as gv
    import holoviews as hv
    import holoviews.streams as hv_streams
    import pyproj

    to_wgs84 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326").transform

    if stream_class not in {hv_streams.Tap, hv_streams.PointerXY}:
        raise ValueError("Unsupported Stream class. Please choose either Tap or PointerXY")

    ds = ds[["lon", "lat", variable]]
    hover = get_hover(variable)
    initial_render = True

    def callback(x: float, y: float) -> holoviews.Curve:
        logger.debug("tsplot: start - %s, %s", x, y)
        nonlocal initial_render
        if initial_render or (not utils.is_point_in_the_raster(raster=source_raster, lon=x, lat=y)):
            # if the point is not inside the mesh, then omit the timeseries
            node_index = float("NaN")
            lon = x
            lat = y
            title = "Please click on the map!"
            plot = hv.Curve([])
        else:
            x, y = to_wgs84(x, y)
            node_index = utils.get_index_of_nearest_node(ds=ds, lon=x, lat=y)
            logger.debug("tsplot: node index: %s", node_index)
            ts = ds.isel(node=node_index)
            lon = float(ts.lon.data)
            lat = float(ts.lat.data)
            with utils.timer("tsplot: loaded ts in"):
                ts[variable].load()
            title = title_template.format(lon=lon, lat=lat, variable=variable, node_index=node_index)
            plot = hv.Curve(ts[variable])
        logger.info("tsplot: title: %s", title)
        initial_render = False
        plot = plot.opts(
            title=title,
            framewise=True,
            padding=0.05,
            show_grid=True,
            tools=[hover],
            xformatter=get_dtf(),
            fontscale=fontscale,
        )
        logger.debug("tsplot: end")
        return plot

    stream = stream_class(x=0, y=0, source=source_raster)
    dmap = gv.DynamicMap(callback, streams=[stream])
    return dmap


def get_station_timeseries(
    stations: xarray.Dataset,
    pins: geoviews.DynamicMap,
) -> holoviews.DynamicMap:   # pragma: no cover
    import holoviews as hv
    import pandas as pd

    def callback(index: list[int]) -> holoviews.Curve:
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
            ds = stations.isel(node=df.index[index])[columns]  # type: ignore[assignment]
        dataset = hv.Dataset(ds)
        curve1 = hv.Curve(dataset, kdims=["stime"], vdims=["elev_sim"], label="Simulation")
        curve2 = hv.Curve(dataset, kdims=["time"], vdims=["elev_obs"], label="Observation")
        components = [curve1, curve2]
        overlay = functools.reduce(operator.mul, components).opts(
            hv.opts.Curve(
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

    stream = hv.streams.Selection1D(source=pins, index=[])
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
    stations: xarray.Dataset,
    pins: geoviews.DynamicMap,
) -> holoviews.DynamicMap:  # pragma: no cover
    import holoviews as hv
    import pandas as pd

    def callback(index: list[int]) -> holoviews.Table:
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
            df.columns = pd.Index(["value"])
        table = hv.Table(df, kdims=["attribute"])
        return table

    stream = hv.streams.Selection1D(source=pins, index=[])
    dmap = hv.DynamicMap(callback, streams=[stream])
    return dmap


def get_station_pins(stations: xarray.Dataset) -> geoviews.Points:
    import geoviews as gv

    df = stations[["lon", "lat", "location"]].to_dataframe()
    pins = gv.Points(df, kdims=["lon", "lat"], vdims=["location"])
    pins = pins.opts(color="red", marker="circle_dot", size=10, tools=["tap", "hover"])
    return pins


def get_tap_timeseries(
    ds: xarray.Dataset,
    variable: str,
    source_raster: geoviews.DynamicMap,
    title_template: str = "{variable} - Node={node_index} Lon={lon:.6f} Lat={lat:.6f}",
    fontscale: float = 1,
) -> geoviews.DynamicMap:
    import holoviews.streams as hv_streams

    dmap = _get_stream_timeseries(
        ds=ds,
        variable=variable,
        source_raster=source_raster,
        stream_class=hv_streams.Tap,
        title_template=title_template,
        fontscale=fontscale,
    )
    return dmap


def get_pointer_timeseries(
    ds: xarray.Dataset,
    variable: str,
    source_raster: geoviews.DynamicMap,
    title_template: str = "",
    fontscale: float = 1,
) -> geoviews.DynamicMap:
    import holoviews.streams as hv_streams

    dmap = _get_stream_timeseries(
        ds=ds,
        variable=variable,
        source_raster=source_raster,
        stream_class=hv_streams.PointerXY,
        title_template=title_template,
        fontscale=fontscale,
    )
    return dmap


def extract_timeseries(ds: xarray.Dataset, variable: str, lon: float, lat: float) -> xarray.DataArray:
    index = utils.get_index_of_nearest_node(ds=ds, lon=lon, lat=lat)
    # extracted = ds[[variable, "lon", "lat"]].isel(node=index)
    return ds[variable].isel(node=index)


# def plot_timeseries(ds: xarray.DataArray, lon: float, lat: float) -> geoviews.DynamicMap:
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
