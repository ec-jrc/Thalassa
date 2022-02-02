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

#----------------------------------------------------------------------------------------
#time series
#----------------------------------------------------------------------------------------
class TimeseriesData:
      '''
      define a class to store data related to time series points
      '''
      def __init__(self):
         self.init=False
      def clear(self):
          self.init=False

def extract_timeseries(x,y,sx,sy,data):
    '''
    function for extracting time series@(x,y) from data
    '''
    dist=abs(sx+1j*sy-x-1j*y)
    mdist=dist.min()
    nid=np.nonzero(dist==mdist)[0][0]
    mdata=data['elev'].data[:,nid].copy()
    return mdist,mdata

def add_remove_pts(x,y,data,dataset,fmt):
    '''
    function to dynamically add or remove pts by double clicking on the map
    '''
    if fmt=='add pts':
       if len(data.xys)==0:
          mdist,mdata=extract_timeseries(x,y,data.sx,data.sy,dataset)
          hcurve=hv.Curve((data.time,mdata),'time','elevation').opts(tools=["hover"])
          if mdist<=data.mdist:
             data.xys.append((x,y))
             data.elev.append(mdata)
             data.curve.append(hcurve)
       else:
          if data.xys[-1][0]!=x and data.xys[-1][1]!=y:
             mdist,mdata=extract_timeseries(x,y,data.sx,data.sy,dataset)
             hcurve=hv.Curve((data.time,mdata),'time','elevation').opts(tools=["hover"])
             if mdist<=data.mdist:
                data.xys.append((x,y))
                data.elev.append(mdata)
                data.curve.append(hcurve)
    elif fmt=='remove pts':
       if len(data.xys)>0:
          xys=np.array(data.xys)
          dist=abs(xys[:,0]+1j*xys[:,1]-x-1j*y)
          mdist=dist.min()
          if mdist<=data.mdist:
             nid=np.nonzero(dist==mdist)[0][0]
             data.xys=[k for i,k in enumerate(data.xys) if i!=nid]
             data.elev=[k for i,k in enumerate(data.elev) if i!=nid]
             data.curve=[k for i,k in enumerate(data.curve) if i!=nid]
    else:
       pass

def get_timeseries(source,data,dataset,ymin,ymax,fmt):
    '''
    get time series plots
    '''
    #initialize timeseries_data
    if data.init is False:
       #find the maximum side length
       x,y=dataset['SCHISM_hgrid_node_x'].data,dataset['SCHISM_hgrid_node_y'].data
       e1,e2,e3=dataset['SCHISM_hgrid_face_nodes'].data.T
       s1=abs((x[e1]-x[e2])+1j*(y[e1]-y[e2])).max()
       s2=abs((x[e2]-x[e3])+1j*(y[e2]-y[e3])).max()
       s3=abs((x[e3]-x[e1])+1j*(y[e3]-y[e1])).max()

       #save data
       data.sx, data.sy, data.x0, data.y0  = x, y, x.mean(), y.mean()
       data.mdist=np.max([s1,s2,s3])
       data.time=dataset['time'].data
       data.xys=[]
       data.elev=[]
       data.curve=[]
       data.init=True

    def get_plot_point(x,y):
        if None not in [x,y]:
           add_remove_pts(x,y,data,dataset,fmt)

        if ((x is None) or (y is None)) and len(data.xys)==0:
           xys=[(data.x0,data.y0)]
           hpoint=gv.Points(xys).opts(show_legend=False,visible=False)
           htext=gv.HoloMap({i:gv.Text(*xy,'{}'.format(i+1)).opts(
                 show_legend=False,visible=False) for i,xy in enumerate(xys)}).overlay()
        else:
           xys=data.xys
           hpoint=gv.Points(xys).opts(color='r',size=3,show_legend=False)
           htext=gv.HoloMap({i:gv.Text(*xy,'{}'.format(i+1)).opts(
                 show_legend=False,color='k',fontsize=3) for i,xy in enumerate(xys)}).overlay()
        return hpoint*htext

    def get_plot_curve(x,y):
        mdist,mdata=extract_timeseries(x,y,data.sx,data.sy,dataset)
        if mdist>data.mdist:
           mdata=mdata*np.nan
        hdynamic=hv.Curve((data.time,mdata)).opts(color='k',line_width=2,line_dash='dotted')
        hcurve=hv.HoloMap({'dynamic':hdynamic,**{(i+1):k for i,k in enumerate(data.curve)}}).overlay()
        return hcurve

    hpoint=gv.DynamicMap(get_plot_point,streams=[DoubleTap(source=source,transient=True)])
    hcurve=gv.DynamicMap(get_plot_curve,streams=[PointerXY(x=data.x0,y=data.y0,source=source)]).opts(
          height=400,legend_cols=len(data.xys)+1,legend_position='top',
          ylim=(float(ymin),float(ymax)),responsive=True,align='end',active_tools=["pan", "wheel_zoom"])

    return hpoint,hcurve
