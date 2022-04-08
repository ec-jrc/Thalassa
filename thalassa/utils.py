from __future__ import annotations

import contextlib
import importlib
import logging
import os
import pathlib
import sys
import numpy as np 
import xarray as xr
logger = logging.getLogger(__name__)

def read_dataset(fname,method=0,dataset_format="SCHISM",prj='epsg:4326',
                 time=None,variable=None,layer=None,node=None):
    '''
    function to read information of dataset    
    Inputs:
       fname:    path of dataset file, or file handle (xr.Dataset)
       method:   different ways to read dataset
                 0: open dataset; 1: read header information; 
                 2: read dataset snapshot; 3: read time series 
       dataset_format: format of dataset 
       prj:      projection of dataset coordinate
       time:     timestamp or index of timestamp for dataset snapshot
       variable: variable to be read
       layer:    layer for 3D variables 
       node:     index of node for reading time series (for method=3)

    note: only SCHISM format is defined so far
    '''

    #open dataset
    if isinstance(fname, xr.Dataset): #already open
       ds=fname
    else:
       if fname.endswith(".nc"):
           ds = xr.open_dataset(fname, mask_and_scale=True)
       elif fname.endswith(".zarr") or fname.endswith(".zip"):
           ds = xr.open_dataset(fname, mask_and_scale=True, engine="zarr")
       else:
           raise ValueError(f"unknown format of dataset: {fname}")

    #retrun file handle and data_format
    if method==0:
       #infer data format
       if 'SCHISM_hgrid_face_nodes' in [*ds.variables]:
          dataset_format=='SCHISM'
       else:
          dataset_format=None

       if dataset_format is None:
           raise ValueError(f"unknown model of dataset: {fname}; please define its format and read method")

       return ds,dataset_format

    #read dataset
    if dataset_format=="SCHISM":
       if method==1: #extract header information of dataset
          #variables to be hidden from user
          hvars=[
              'time', 'SCHISM_hgrid', 'SCHISM_hgrid_face_nodes', 'SCHISM_hgrid_edge_nodes', 
              'SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y', 'node_bottom_index', 'SCHISM_hgrid_face_x',
              'SCHISM_hgrid_face_y', 'ele_bottom_index', 'SCHISM_hgrid_edge_x', 'SCHISM_hgrid_edge_y',
              'edge_bottom_index', 'depth', 'sigma', 'dry_value_flag', 'coordinate_system_flag', 
              'minimum_depth', 'sigma_h_c', 'sigma_theta_b', 'sigma_theta_f', 'sigma_maxdepth', 'Cs', 
              'wetdry_node', 'wetdry_elem', 'wetdry_side', 'zcor'] 

          times=ds['time'].to_pandas().dt.to_pydatetime()
          variables=[i for i in ds.variables if (i not in hvars)]
          x=ds.variables['SCHISM_hgrid_node_x'].values
          y=ds.variables['SCHISM_hgrid_node_y'].values
          elnode=ds.variables['SCHISM_hgrid_face_nodes'].values

          #split quads          
          if elnode.shape[1]==4:
             eid=np.nonzero(~((np.isnan(elnode[:,-1]))|(elnode[:,-1]<0)))[0]
             elnode=np.r_[elnode[:,:3],np.c_[elnode[eid,0][:,None], elnode[eid,2:]]]
          if elnode.max()>=len(x):
             elnode=elnode-1
          elnode=elnode.astype('int')

          return ds,times,variables,x,y,elnode

       elif method==2: #extract one snapshot of dataset
          #time index
          if isinstance(time,int): 
             tid=time
          else:
             times=ds['time'].to_pandas().dt.to_pydatetime()
             tid=np.nonzero(np.array(times)==timestamp)[0][0]

          #2D and 3D variables
          if ds.variables[variable].ndim==1:
             mdata=ds.variables[variable].values
          elif ds.variables[variable].ndim==2:
             mdata=ds.variables[variable][tid].values
          elif ds.variables[variable].ndim==3:
             if layer=='surface':
                mdata=ds.variables[variable][tid,:,-1].values
             elif layer=='bottom':
                if 'node_bottom_index' in [*ds.variables]:
                   zid=ds.variables['node_bottom_index'][:].values.astype('int')
                   pid=np.arange(len(zid))
                   mdata=ds.variables[variable][tid].values[pid,zid]
                else:
                   mdata=ds.variables[variable][tid,:,0].values
             else:
                mdata=ds.variables[variable][tid,:,layer].values

          return mdata

       elif method==3: #extract time series
          if ds.variables[variable].ndim==2:
             mdata=ds.variables[variable][:,node].values
          elif ds.variables[variable].ndim==3:
             if layer=='surface':
                zid=-1
             elif layer=='bottom':
                if 'node_bottom_index' in [*ds.variables]:
                   zid=ds.variables['node_bottom_index'][node].values.astype('int')
                else:
                   zid=0
             else:
                zid=layer
             mdata=ds.variables[variable][:,node,zid].values
          
          return mdata 

       else:
        raise ValueError(f"unknown read method for SCHISM model: {method}")
    else:
        raise ValueError(f"unknown model (read method needs to be defined): {dataset_format}")

def reload(module_name: str) -> None:
    """
    Reload source code when working interactively, e.g. on jupyterlab

    Source: https://stackoverflow.com/questions/28101895/
    """
    # In order to avoid having ipython as a hard dependency we need to inline the import statement
    from IPython.lib import deepreload  # type: ignore  # pylint: disable=import-outside-toplevel

    # Get a handle of the module object
    module = importlib.import_module(module_name)

    # sys.modules contains all the modules that have been imported so far.
    # Reloading all the modules takes too long.
    # Therefore let's create a list of modules that we should exclude from the reload procedure
    to_be_excluded = {key for (key, value) in sys.modules.items() if module_name not in key}

    # deepreload uses print(). Let's disable it with a context manager
    # https://stackoverflow.com/a/46129367/592289
    with open(os.devnull, "w", encoding="utf-8") as fd, contextlib.redirect_stdout(fd):
        # OK, now let's reload!
        deepreload.reload(module, exclude=to_be_excluded)

def can_be_opened_by_xarray(path):
    try:
        read_dataset(path)
    except ValueError:
        logger.debug("path cannot be opened by xarray: %s", path)
        return False
    else:
        return True
