from __future__ import annotations

import logging

import geoviews as gv
import holoviews as hv
import shapely
import xarray as xr

from . import api
from . import normalization
from . import utils

logger = logging.getLogger(__name__)


def _sanity_check(ds: xr.Dataset, variable: str) -> None:
    dims = ds[variable].dims
    if "node" not in dims:
        msg = (
            f"Only variables whose dimensions include 'node' can be plotted. "
            f"The dimensions of variable '{variable}' are: {ds[variable].dims}"
        )
        raise ValueError(msg)
    if dims != ("node",):
        msg = (
            f"In order to plot variable '{variable}', the dataset must be filtered in such a way "
            f"that the only dimension of '{variable}' is `node`. Please use `.sel()` or `.isel()` "
            f"to filter the dataset accordingly. Current dimensions are: {ds[variable].dims}"
        )
        raise ValueError(msg)


def plot_mesh(
    ds: xr.Dataset,
    bbox: shapely.Polygon | None = None,
    title: str = "Mesh",
) -> gv.DynamicMap:
    """
    Plot the mesh of the dataset

    Examples:
        ``` python
        import thalassa

        ds = thalassa.open_dataset("some_netcdf.nc")
        thalassa.plot_mesh(ds)
        ```

        If we want to on-the-fly crop the dataset we can pass `bbox`, too:

        ``` python
        import shapely
        import thalassa

        bbox = shapely.box(0, 0, 1, 1)
        ds = thalassa.open_dataset("some_netcdf.nc")
        thalassa.plot_mesh(ds, bbox=bbox)
        ```

    Parameters:
        ds: The dataset whose mesh we want to visualize. It must adhere to the "thalassa schema"
        bbox: A Shapely polygon which will be used to (on-the-fly) crop the `dataset`.
        title: The title of the plot.

    """
    ds = normalization.normalize(ds)
    if bbox:
        ds = utils.crop(ds, bbox)
    tiles = api.get_tiles()
    mesh = api.get_wireframe(ds)
    overlay = hv.Overlay((tiles, mesh)).opts(title=title).collate()
    return overlay


def plot(
    ds: xr.Dataset,
    variable: str,
    bbox: shapely.Polygon | None = None,
    title: str = "",
    cmap: str = "plasma",
    colorbar: bool = True,
    clabel: str = "",
    clim_min: float | None = None,
    clim_max: float | None = None,
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
    show_mesh: bool = False,
) -> gv.DynamicMap:
    """
    Return the plot of the specified `variable`.

    Examples:
        ``` python
        import thalassa

        ds = thalassa.open_dataset("some_netcdf.nc")
        thalassa.plot(ds, variable="zeta_max")
        ```

        When we plot time dependent variables we need to filter the data
        in such a way that `time` is no longer a dimension.
        For example to plot the map of the first timestamp of variable `zeta`:

        ``` python
        import thalassa

        ds = thalassa.open_dataset("some_netcdf.nc")
        thalassa.plot(ds.isel(time=0), variable="zeta")
        ```

        Often, it is quite useful to limit the range of the colorbar:

        ``` python
        import thalassa

        ds = thalassa.open_dataset("some_netcdf.nc")
        thalassa.plot(ds, variable="zeta", clim_min=1, clim_max=3, clabel="meter")
        ```

        If we want to on-the-fly crop the dataset we can pass `bbox`, too:

        ``` python
        import shapely
        import thalassa

        bbox = shapely.box(0, 0, 1, 1)
        ds = thalassa.open_dataset("some_netcdf.nc")
        thalassa.plot(ds, variable="depth", bbox=bbox)
        ```

    Parameters:
        ds: The dataset which will get visualized. It must adhere to the "thalassa schema".
        variable: The dataset's variable which we want to visualize.
        bbox: A Shapely polygon which will be used to (on-the-fly) crop the `dataset`.
        title: The title of the plot. Defaults to `variable`.
        cmap: The colormap to use.
        colorbar: Boolean flag indicating whether the plot should have an integrated colorbar.
        clabel: A caption for the colorbar. Useful for indicating e.g. units
        clim_min: The lower limit for the colorbar.
        clim_max: The upper limit for the colorbar.
        x_range: A tuple indicating the minimum and maximum longitude to be displayed.
        y_range: A tuple indicating the minimum and maximum latitude to be displayed.
        show_mesh: A boolean flag indicating whether the mesh should be overlayed on the rendered variable.
            Enabling this makes rendering slower.

    """
    ds = normalization.normalize(ds)
    _sanity_check(ds=ds, variable=variable)
    if bbox:
        ds = utils.crop(ds, bbox)
    trimesh = api.create_trimesh(ds_or_trimesh=ds, variable=variable)
    raster = api.get_raster(
        ds_or_trimesh=trimesh,
        variable=variable,
        x_range=x_range,
        y_range=y_range,
        cmap=cmap,
        colorbar=colorbar,
        clim_min=clim_min,
        clim_max=clim_max,
        title=title,
        clabel=clabel,
    )
    tiles = api.get_tiles()
    components = [tiles, raster]
    if show_mesh:
        mesh = api.get_wireframe(ds)
        components.append(mesh)
    overlay = hv.Overlay(components)
    dmap = overlay.collate()
    # Keep a reference of the raster DynamicMap, in order to be able to retrieve it from plot_ts
    dmap._raster = raster
    return dmap


def plot_ts(
    ds: xr.Dataset,
    variable: str,
    source_plot: gv.DynamicMap,
) -> gv.DynamicMap:
    """
    Return a plot with the full timeseries of a specific node.

    The node that will be visualized is selected by clicking on `source_plot`.

    Examples:
        ``` python
        import thalassa

        ds = thalassa.open_dataset("some_netcdf.nc")
        main_plot = thalassa.plot(ds, variable="zeta_max")
        ts_plot = thalassa.plot_ts(ds, variable="zeta", source_plot=main_plot)

        (main_plot.opts(width=600) + ts_plot.opts(width=600)).cols(1)
        ```

    Parameters:
        ds: The dataset which will get visualized. It must adhere to the "thalassa schema"
        variable: The dataset's variable which we want to visualize.
        source_plot: The plot instance which be used to select the coordinates of the node.
            Normally, you get this instance by calling `plot()`.
    """
    ds = normalization.normalize(ds)
    ts = api.get_tap_timeseries(ds, variable, source_plot._raster)
    return ts
