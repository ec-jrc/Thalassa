from __future__ import annotations

import pathlib

import geoviews as gv
import holoviews as hv
import pandas as pd
import panel as pn

from holoviews.operation.datashader import datashade, rasterize

from .utils import load_grid_from_disk
from .utils import load_elevation_from_disk

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from holoviews import opts

from matplotlib import animation

mpl.rc('animation', html='html5')
plt.rcParams["animation.html"] = "jshtml"
plt.rcParams['animation.embed_limit'] = '200.'
plt.style.use(['dark_background'])


class AAA:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def frames(self,**kwargs):

        cr = kwargs.get('coastlines', None)
        c_attrs = kwargs.get('coastlines_attrs', {})

        x = kwargs.get('x',self._obj.SCHISM_hgrid_node_x[:].values)
        y = kwargs.get('y',self._obj.SCHISM_hgrid_node_y[:].values)
        t = kwargs.get('t',self._obj.time.values)
        tri3 = kwargs.get('tri3',self._obj.SCHISM_hgrid_face_nodes.values[:,:3].astype(int))

        var = kwargs.get('var','depth')
        z = kwargs.get('z',self._obj[var].values)

        # set figure size
        xr = x.max() - x.min()
        yr = y.max() - y.min()
        ratio = yr/xr
        xf=12
        yf=np.ceil(12*ratio).astype(int)

        fig = plt.figure(figsize=(xf,yf))
        vmin = kwargs.get('vmin', z.min())
        vmax = kwargs.get('vmax', z.max())

        nv = kwargs.get('nv', 10)

        title = kwargs.get('title', None)

        vrange=np.linspace(vmin,vmax,nv,endpoint=True)

        #optional mask for the data
        mask = kwargs.get('mask',None)
        if 'mask' in kwargs:
            z = np.ma.masked_array(z,mask)
            z = z.filled(fill_value=-99999)

        ax = plt.axes()
        ax.set_aspect('equal')

        ims = []
        import time
        ttt = time.time()

        for i in range(len(t)):
            current_ttt = time.time()
            print(i, ttt - current_ttt)
            im = ax.tricontourf(x, y, tri3, z[i,:], vrange, vmin=vmin, vmax=vmax)#, transform=ccrs.PlateCarree())
            add_arts = im.collections
            text = 'time={}'.format(t[i])
            an = ax.annotate(text, xy=(0.05, -.1), xycoords='axes fraction')
            ims.append(add_arts + [an])

        if title:
            ax.set_title(title)

        v = animation.ArtistAnimation(fig, ims, interval=200, blit=False,repeat=False)
        plt.close()

        return v


def elevation_max(data_dir: pathlib.Path):
    # load data
    grid_path = data_dir / "grid.npz"
    elevation_max_path = data_dir / "elevation.max.npz"
    x, y, simplices = load_grid_from_disk(grid_path)
    z = load_elevation_from_disk(elevation_max_path)
    # create panel objects
    xyz_points = pd.DataFrame(dict(x=x, y=y, z=z))
    points = hv.Points(xyz_points, kdims=["x", "y"], vdims="z")
    trimesh = hv.TriMesh((simplices, points))
    opts.defaults(opts.WMTS(width=1200, height=900))
    datashaded_trimesh = (
        rasterize(trimesh, aggregator='mean')
        .opts(colorbar=True, cmap='Viridis', clim=(z.min(), z.max()), clabel='meters')
    )
    tiles = gv.WMTS('https://maps.wikimedia.org/osm-intl/{Z}/{X}/{Y}@2x.png')
    layout = tiles * datashaded_trimesh
    return layout


def video(data_dir: pathlib.Path):
    mp4 = (data_dir / "animation.mp4").resolve().as_posix()
    video = pn.pane.Video(mp4, width=640, height=360, loop=True)
    row = pn.Row(video.controls(jslink=True), video)
    return row


def grid(data_dir: pathlib.Path):
    # load data
    grid_path = data_dir / "grid.npz"
    x, y, simplices = load_grid_from_disk(grid_path)
    # create panel objects
    xy_points = pd.DataFrame(dict(x=x, y=y))
    points = hv.Points(xy_points, kdims=["x", "y"])
    trimesh = hv.TriMesh((simplices, points)).edgepaths
    datashaded_trimesh = (
        datashade(trimesh, precompute=True, cmap=['black'])
        .opts(width=1200, height=900)
    )
    tiles = gv.WMTS('https://maps.wikimedia.org/osm-intl/{Z}/{X}/{Y}@2x.png')
    layout = tiles * datashaded_trimesh
    return layout


def about():
   # 
   layout = pn.Column(
       "#The model",
       pn.Row(
        "Thalassa is powered by"
        "- [pyPoseidon](https://github.com/brey/pyPoseidon)"
        "- [SCHISM](https://github.com/schism-dev/schism)"
        "- [Panel](https://panel.holoviz.org/index.html)"
        ),
       pn.Row(
        "### Info\n\n"
        "- Ask a question on [Slack](https://pyposeidon.slack.com)\n"
   
        ),
        )
   return layout


