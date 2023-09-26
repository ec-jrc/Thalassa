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
    ds = normalization.normalize_dataset(ds)
    if bbox:
        ds = utils.crop(ds, bbox)
    trimesh = api.create_trimesh(ds=ds, variable=variable)
    raster = api.get_raster_from_trimesh(
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
