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


def plot_mesh(
    ds: xr.Dataset,
    bbox: shapely.Polygon | None = None,
    title: str = "Mesh",
) -> gv.DynamicMap:
    """
    Plot the mesh of the dataset

    Parameters:
        ds: The dataset whose mesh we want to visualize.
        bbox: A Shapely polygon which will be used to (on-the-fly) crop the `dataset`.
        title: The title of the plot

    """
    ds = normalization.normalize_dataset(ds)
    if bbox:
        ds = utils.crop(ds, bbox)
    tiles = api.get_tiles()
    mesh = api.get_wireframe(ds)
    overlay = hv.Overlay((tiles, mesh)).opts(title=title).collate()
    return overlay


def plot(
    ds: xr.Dataset,
    variable: str = "max_elev",
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

    Parameters:
        ds: The dataset which will get rendered. It must adhere to the "thalassa schema"
        variable: The `dataset`'s variable which we want to visualize.
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
    if bbox:
        ds = utils.crop(ds, bbox)
    trimesh = api.create_trimesh(ds=ds, variable=variable)
    raster = api.get_raster(
        trimesh=trimesh,
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
    if show_mesh:
        mesh = api.get_wireframe(ds_or_trimesh=trimesh)
        overlay = hv.Overlay((tiles, raster, mesh))
    else:
        overlay = hv.Overlay((tiles, raster))
    return overlay.collate()


def plot_ts(
    ds: xr.Dataset,
    variable: str,
    source_plot: gv.DynamicMap,
) -> gv.DynamicMap:
    """
    Return an `hv.Curve` with the full timeseries of a specific node.

    The node is selected by clicking on `source_plot`.
    """
    ds = normalization.normalize_dataset(ds)
    ts = api.get_tap_timeseries(ds, variable, source_plot._raster)
    return ts
