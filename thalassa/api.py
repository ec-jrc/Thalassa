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

class timeseries_data:
      def __init__(self):
         self.xys=[]
         self.vmax=-9999.0
         self.vmin=9999.0

def get_timeseries(source,tdata,dataset,pts_mode,fixed,dynamic):
    sxi, syi = dataset['SCHISM_hgrid_node_x'].data, dataset['SCHISM_hgrid_node_y'].data
    if not hasattr(tdata,'x0'): 
       tdata.x0, tdata.y0 = sxi.mean(), syi.mean()

    def add_remove_pts(x,y):
        #add new pt, or remove pt
        if None not in [x,y]:
           if pts_mode=='add pts':
              if len(tdata.xys)==0:
                 tdata.xys.append((x,y))
              else:
                 if tdata.xys[-1][0]!=x and tdata.xys[-1][1]!=y: 
                    tdata.xys.append((x,y))
           elif pts_mode=='remove pts':
              if len(tdata.xys)>0:
                 xys=np.array(tdata.xys)
                 dist=abs(xys[:,0]+1j*xys[:,1]-x-1j*y)
                 nid=np.nonzero(dist==dist.min())[0][0]
                 tdata.xys=[k for i,k in enumerate(tdata.xys) if i!=nid]

        #plot Points and label
        hpi=gv.Points(tdata.xys).opts(color='r',size=3,show_legend=False)
        hti=gv.HoloMap({i:gv.Text(*xy,'{}'.format(i+1)).opts(show_legend=False,fontsize=3) for i,xy in enumerate(tdata.xys)}).overlay()
        return hpi*hti

    def get_fixed_curve(x,y):
        hsi=hv.HoloMap({'{}'.format(i+1):get_curve_xy(*xy) for i,xy in enumerate(tdata.xys)}).overlay()
        return hsi

    def get_curve_xy(x,y):
        dist=abs(sxi+1j*syi-x-1j*y)
        nid=np.nonzero(dist==dist.min())[0][0]
        mti=dataset['time'].data
        myi=dataset['elev'].data[:,nid].copy()
        vmin,vmax=myi.min(),myi.max()
        tdata.vmin=tdata.vmin if tdata.vmin<=vmin else vmin
        tdata.vmax=tdata.vmax if tdata.vmax>=vmax else vmax
        hsi=hv.Curve((mti,myi),'time','elevation')
        return hsi

    hp=gv.DynamicMap(add_remove_pts,streams=[DoubleTap(source=source,transient=True)])
    hs=gv.DynamicMap(get_fixed_curve,streams=[DoubleTap(source=source,transient=True)])
    hd=hv.DynamicMap(get_curve_xy,streams=[PointerXY(x=tdata.x0,y=tdata.y0,source=source)]).opts(
       color='k',line_width=2,line_dash='dotted')

    #get the final curve
    ha=hd*hs if (fixed and dynamic) else (hs if fixed else hd)
    if fixed and (not dynamic) and len(tdata.xys)==0: ha=hd*hs
    #ha=ha.opts(height=250,responsive=True,align='end',active_tools=["pan", "wheel_zoom"])
    ha=ha.opts(height=250,responsive=True,align='end',ylim=(-0.1,0.1),active_tools=["pan", "wheel_zoom"])
    
    return hp, ha
