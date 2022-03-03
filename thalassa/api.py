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
from . import utils
hv.extension("bokeh")

logger = logging.getLogger(__name__)

def get_tiles() -> gv.Tiles:
    tiles = gv.WMTS("http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png")
    return tiles

class MapData:
      '''
      define a class to store data related to dynamic map
      '''
      def __init__(self):
          #dataset info
          self.name      = None
          self.format    = None
          self.prj       = None
          #header info 
          self.dataset   = None #file handle -> xr.Dataset 
          self.times     = None
          self.variables = None
          #connectivity
          self.x         = None
          self.y         = None
          self.elnode    = None
          #dataset snapshot
          self.time      = None
          self.variable  = None
          self.data      = None
          self.grid      = None
          self.trimesh   = None
          self.trimap    = None
          self.tiles     = get_tiles()

      def get_data(self,time,variable,layer):
          '''
          extract a snapshot from dataset 
          '''
          self.time     = time
          self.variable = variable
          self.layer    = layer
          tid=int(np.nonzero(np.array(self.times)==time)[0][0])
          self.data=utils.read_dataset(self.dataset,2,self.format,time=tid,variable=variable,layer=layer)

      def get_plot_map(self): 
          '''
          plot a snapshot: only SCHISM method is defined so far
          '''
          if self.format=="SCHISM":
             if self.x.min()<-360 or self.x.max()>360 or self.y.min()<-90 or self.y.max()>90: 
                raise ValueError(f"check dataset projection: abs(lat)>360 or abs(lon)>90")
             df=pd.DataFrame({'longitude':self.x, 'latitude':self.y, 'data':self.data})
             pdf=gv.Points(df,kdims=['longitude','latitude'],vdims='data')
             self.trimesh=gv.TriMesh((self.elnode,pdf))
             if self.grid is None:
                self.grid=dynspread(rasterize(self.trimesh.edgepaths, precompute=True))
             self.trimap=rasterize(self.trimesh, precompute=True).opts(
                       title=f"SCHISM Forecast: {self.variable}",
                       colorbar=True,
                       clabel="meters",
                       cmap="jet",
                       show_legend=True,
                      )
          else:
             raise ValueError(f"please define plot method for dataset format: {dataset_format}")
      
class TimeseriesData:
      '''
      define a class to store data related to time series points
      '''
      def __init__(self):
         self.init=False
      def clear(self):
          self.init=False

def extract_timeseries(x,y,sx,sy,dataset,variable):
    '''
    function for extracting time series@(x,y) from data
    '''
    dist=abs(sx+1j*sy-x-1j*y)
    mdist=dist.min()
    nid=np.nonzero(dist==mdist)[0][0]
    mdata=dataset[variable].data[:,nid].copy()
    return mdist,mdata

def add_remove_pts(x,y,data,dataset,fmt,variable):
    '''
    function to dynamically add or remove pts by double clicking on the map
    '''
    if fmt=='add pts':
       if len(data.xys)==0:
          mdist,mdata=extract_timeseries(x,y,data.sx,data.sy,dataset,variable)
          hcurve=hv.Curve((data.time,mdata),'time',variable).opts(tools=["hover"])
          if mdist<=data.mdist:
             data.xys.append((x,y))
             data.elev.append(mdata)
             data.curve.append(hcurve)
       else:
          if data.xys[-1][0]!=x and data.xys[-1][1]!=y:
             mdist,mdata=extract_timeseries(x,y,data.sx,data.sy,dataset,variable)
             hcurve=hv.Curve((data.time,mdata),'time',variable).opts(tools=["hover"])
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

def get_timeseries(MData,data,ymin,ymax,fmt):
    '''
    get time series plots
    '''

    source, dataset = MData.trimesh, MData.dataset
    variable='elev'  #todo: add an input for time series variable

    #initialize timeseries_data
    if data.init is False:
       #find the maximum side length
       x,y=MData.x,MData.y   #tmp fix, improve: todo
       e1,e2,e3=MData.elnode.T

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
           add_remove_pts(x,y,data,dataset,fmt,variable)

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
        mdist,mdata=extract_timeseries(x,y,data.sx,data.sy,dataset,variable)
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
