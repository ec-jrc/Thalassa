from __future__ import annotations

import logging

import geoviews as gv
import holoviews as hv
import pandas as pd
import xarray as xr
from holoviews.operation.datashader import dynspread
from holoviews.operation.datashader import rasterize
from holoviews.streams import PointerXY
import numpy as np

logger = logging.getLogger(__name__)

# Load bokeh backend
hv.extension("bokeh")


def get_trimesh(
    dataset: xr.Dataset,
    longitude_var: str,
    latitude_var: str,
    elevation_var: str,
    simplices_var: str,
    time_var: str,
    timestamp: str | pd.Timestamp,
) -> gv.TriMesh:
    simplices = dataset[simplices_var].values
    columns = [longitude_var, latitude_var, elevation_var]
    if timestamp == "MAXIMUM":
        points_df = dataset.max(time_var)[columns].to_dataframe()
    elif timestamp == "MINIMUM":
        points_df = dataset.min(time_var)[columns].to_dataframe()
    else:
        points_df = dataset.sel({time_var: timestamp})[columns].to_dataframe().drop(columns=time_var)
    points_df = points_df.reset_index(drop=True)
    points_gv = gv.Points(points_df, kdims=[longitude_var, latitude_var], vdims=elevation_var)
    trimesh = gv.TriMesh((simplices, points_gv))
    return trimesh


def get_tiles() -> gv.Tiles:
    tiles = gv.WMTS("http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png")
    return tiles


def get_wireframe(trimesh: gv.TriMesh) -> hv.Layout:
    wireframe = dynspread(rasterize(trimesh.edgepaths, precompute=True))
    return wireframe


def get_elevation_dmap(trimesh: gv.TriMesh, show_grid: bool = False) -> hv.Overlay:
    tiles = get_tiles()
    elevation = rasterize(trimesh, precompute=True).opts(  # pylint: disable=no-member
        title="Elevation Forecast",
        colorbar=True,
        clabel="meters",
        show_legend=True,
    )
    logger.debug("show grid: %s", show_grid)
    if show_grid:
        overlay = tiles * elevation * get_wireframe(trimesh=trimesh)
    else:
        overlay = tiles * elevation
    return overlay

def get_timeseries(fid,source=None):
    fdata=fid._dataset
    sxi,syi=fdata['SCHISM_hgrid_node_x'].data,fdata['SCHISM_hgrid_node_y'].data
    def get_timeseries_xy(x,y):
        dist=abs(sxi+1j*syi-x-1j*y); nid=np.nonzero(dist==dist.min())[0][0]
        mti=fdata['time'].data; myi=fdata['elev'].data[:,nid].copy()
        ha=hv.Curve((mti,myi),'time','elevation')
        return ha

    #fixed station
    xys=((3.0,37),(30,33)) #todo: read fixed stations from inputs
    hs=hv.HoloMap({'P_{}'.format(i+1):get_timeseries_xy(*xy) for i,xy in enumerate(xys)})

    #dynamic
    hd=hv.DynamicMap(get_timeseries_xy,streams=[PointerXY(x=0,y=0,source=source)])
    hd=hd.opts(color='k',line_width=2,line_dash='dotted')

    #points
    hp=hv.HoloMap({'P_{}'.format(i+1):hv.Points(xy).opts(color='r') for i,xy in enumerate(xys)})

    return hd*hs.overlay(),hp.overlay()
