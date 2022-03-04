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
          self.layer     = None
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
      def __init__(self,MData,variable,layer):
         #dataset and header info
         self.source   = MData
         self.dataset  = MData.dataset
         self.format   = MData.format
         self.times    = MData.times
         #self.variable = variable 
         self.variable = 'elev'
         self.layer    = layer
         self.x        = MData.x
         self.y        = MData.y
         self.elnode   = MData.elnode
         self.x0       = self.x.mean()
         self.y0       = self.y.mean()

         #init. data related to time series
         self.xys      = []
         self.data     = []
         self.curve    = []

         #compute maximum side length
         e1,e2,e3=self.elnode.T         
         side1=abs((self.x[e1]-self.x[e2])+1j*(self.y[e1]-self.y[e2])).max()
         side2=abs((self.x[e2]-self.x[e3])+1j*(self.y[e2]-self.y[e3])).max()
         side3=abs((self.x[e3]-self.x[e1])+1j*(self.y[e3]-self.y[e1])).max()
         self.mdist=np.max([side1,side2,side3])

      def get_data(self,x,y):
          '''
          function for extracting time series@(x,y) from data
          '''
          dist=abs(self.x+1j*self.y-x-1j*y)
          node=np.nonzero(dist==dist.min())[0][0]
          mdata=utils.read_dataset(self.dataset,3,self.format,variable=self.variable,layer=self.layer,node=node)
          return dist.min(),mdata.copy()

      def get_timeseries(self,ymin,ymax,fmt):
          '''
          get time series plots
          '''

          def add_remove_pts(x,y):
              '''
              function to dynamically add or remove pts by double clicking on the map
              '''
              if fmt=='add pts':
                 if len(self.xys)==0:
                    mdist,mdata=self.get_data(x,y)
                    hcurve=hv.Curve((self.times,mdata),'time',self.variable).opts(tools=["hover"])
                    if mdist<=self.mdist:
                       self.xys.append((x,y))
                       self.data.append(mdata)
                       self.curve.append(hcurve)
                 else:
                    if self.xys[-1][0]!=x and self.xys[-1][1]!=y:
                       mdist,mdata=self.get_data(x,y)
                       hcurve=hv.Curve((self.times,mdata),'time',self.variable).opts(tools=["hover"])
                       if mdist<=self.mdist:
                          self.xys.append((x,y))
                          self.data.append(mdata)
                          self.curve.append(hcurve)
              elif fmt=='remove pts':
                 if len(self.xys)>0:
                    xys=np.array(self.xys)
                    dist=abs(xys[:,0]+1j*xys[:,1]-x-1j*y)
                    mdist=dist.min()
                    if mdist<=self.mdist:
                       nid=np.nonzero(dist==mdist)[0][0]
                       self.xys=[k for i,k in enumerate(self.xys) if i!=nid]
                       self.data=[k for i,k in enumerate(self.data) if i!=nid]
                       self.curve=[k for i,k in enumerate(self.curve) if i!=nid]
      
          def get_plot_point(x,y):
              if None not in [x,y]:
                 add_remove_pts(x,y)
      
              if ((x is None) or (y is None)) and len(self.xys)==0:
                 xys=[(self.x0,self.y0)]
                 hpoint=gv.Points(xys).opts(show_legend=False,visible=False)
                 htext=gv.HoloMap({i:gv.Text(*xy,'{}'.format(i+1)).opts(
                       show_legend=False,visible=False) for i,xy in enumerate(xys)}).overlay()
              else:
                 xys=self.xys
                 hpoint=gv.Points(xys).opts(color='r',size=3,show_legend=False)
                 htext=gv.HoloMap({i:gv.Text(*xy,'{}'.format(i+1)).opts(
                       show_legend=False,color='k',fontsize=3) for i,xy in enumerate(xys)}).overlay()
              return hpoint*htext
      
          def get_plot_curve(x,y):
              mdist,mdata=self.get_data(x,y)
              if mdist>self.mdist:
                 mdata=mdata*np.nan
              hdynamic=hv.Curve((self.times,mdata)).opts(color='k',line_width=2,line_dash='dotted')
              hcurve=hv.HoloMap({'dynamic':hdynamic,**{(i+1):k for i,k in enumerate(self.curve)}}).overlay()
              return hcurve
      
          hpoint=gv.DynamicMap(get_plot_point,streams=[DoubleTap(source=self.source.trimesh,transient=True)])
          hcurve=gv.DynamicMap(get_plot_curve,streams=[PointerXY(x=self.x0,y=self.y0,source=self.source.trimesh)]).opts(
                         height=400,legend_cols=len(self.xys)+1,legend_position='top',
                         ylim=(float(ymin),float(ymax)),responsive=True,align='end',active_tools=["pan", "wheel_zoom"])
          return hpoint,hcurve
