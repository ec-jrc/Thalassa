from __future__ import annotations

import logging

import geoviews as gv
import holoviews as hv
import pandas as pd
import xarray as xr
from holoviews.operation.datashader import dynspread
from holoviews.operation.datashader import rasterize
from holoviews.streams import PointerXY,DoubleTap
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

def get_timeseries(fid):
    fdata=fid._dataset; source=fid.timeseries_source
    sxi,syi=fdata['SCHISM_hgrid_node_x'].data,fdata['SCHISM_hgrid_node_y'].data
    if not hasattr(fid,'x0'): fid.x0,fid.y0=sxi.mean(),syi.mean()

    def add_remove_pts(x,y):
        #add new pt, or remove pt
        if None not in [x,y]:
           if fid.timeseries_pts.value=='add pts':
              if len(fid.xys)==0:
                 fid.xys.append((x,y))
              else:
                 if fid.xys[-1][0]!=x and fid.xys[-1][1]!=y: fid.xys.append((x,y))
           elif fid.timeseries_pts.value=='remove pts':
              if len(fid.xys)>0:
                 xys=np.array(fid.xys); dist=abs(xys[:,0]+1j*xys[:,1]-x-1j*y)
                 nid=np.nonzero(dist==dist.min())[0][0]; fid.xys=[k for i,k in enumerate(fid.xys) if i!=nid]
           #fid.timeseries_len.value=not fid.timeseries_len.value

        #plot Points and label
        hpi=gv.Points(fid.xys).opts(color='r',size=3,show_legend=False)
        hti=gv.HoloMap({i:gv.Text(*xy,'{}'.format(i+1)).opts(show_legend=False,fontsize=3) for i,xy in enumerate(fid.xys)}).overlay()
        return hpi*hti

    def get_fixed_curve(x,y):
        hsi=hv.HoloMap({'{}'.format(i+1):get_curve_xy(*xy) for i,xy in enumerate(fid.xys)}).overlay()
        return hsi

    def get_curve_xy(x,y):
        dist=abs(sxi+1j*syi-x-1j*y);  nid=np.nonzero(dist==dist.min())[0][0]
        mti=fdata['time'].data;       myi=fdata['elev'].data[:,nid].copy()
        hsi=hv.Curve((mti,myi),'time','elevation')
        return hsi

    hp=gv.DynamicMap(add_remove_pts,streams=[DoubleTap(source=source,transient=True)])
    hs=gv.DynamicMap(get_fixed_curve,streams=[DoubleTap(source=source,transient=True)])
    hd=hv.DynamicMap(get_curve_xy,streams=[PointerXY(x=fid.x0,y=fid.y0,source=source)]).opts(
       color='k',line_width=2,line_dash='dotted')

    #get the final curve
    fixed,dynamic=fid.timeseries_fixed.value,fid.timeseries_dynamic.value
    ha=hd*hs if (fixed and dynamic) else (hs if fixed else hd)
    if fixed and (not dynamic) and len(fid.xys)==0: ha=hd*hs

    fid._main.objects = [fid.timeseries_dmap*hp, ha.opts(height=250,responsive=True,align='end',active_tools=["pan", "wheel_zoom"])]
    return

