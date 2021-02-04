from __future__ import annotations

import pathlib

import geoviews as gv
import holoviews as hv
import pandas as pd
import panel as pn

from holoviews.operation.datashader import datashade, rasterize

from .paths import STATIC
from .utils import load_grid_from_disk
from .utils import load_elevation_from_disk
from .utils import get_dataset

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from bokeh.models import HoverTool
import tarfile
from bokeh.models.formatters import DatetimeTickFormatter
from holoviews.streams import Selection1D
import geoviews.tile_sources as gvts
import hvplot.pandas
import base64

from holoviews import opts

from matplotlib import animation

mpl.rc('animation', html='html5')
plt.rcParams["animation.html"] = "jshtml"
plt.rcParams['animation.embed_limit'] = '200.'
plt.style.use(['dark_background'])


DISCLAIMER_TEXT = """\
### Disclaimer

These visualizations are provided as a proof of concept research tool.

This information is provided "as is" and it is purely indicative and should not be used for any
decision making process.

""".strip()

ABOUT_TEXT = """\

# The model

- An unstructured grid with variable size is used to simulate the storm surge globally.
  Current runs utilize 128 cores on a HPC infrastructure.

- The Bathymetric dataset used is GEBCO 2019.

- The atmospheric forcing is the 10m wind speed and sea level atmospheric pressure retrieved
  automatically from the ECMWF high-resolution forecast (HRES) system.

- The operational system runs twice per day using the 00:00 and 12:00 meteo data and produces hourly
  storm surge level forecasts for the next 72 hours.

- The simulation timestep is 300-400 sec. Vvirtual stations where setup where data for validation is
  available. Map data of the whole model domain is saved every 1 hour.

# The software

Thalassa is powered by

- [pyPoseidon](https://github.com/brey/pyPoseidon)

- [SCHISM](https://github.com/schism-dev/schism)

- [Panel](https://panel.holoviz.org/index.html)
)

# Info

- Ask a question on [Slack](https://pyposeidon.slack.com)

""".strip()


def get_disclaimer():
    disclaimer = pn.pane.Markdown(DISCLAIMER_TEXT, width=1000, height=80, background='#f0f0f0')
    return disclaimer


def get_logo():
    logo_path = STATIC / "thalassa.png"
    encoded_logo = base64.b64encode(logo_path.read_bytes())
    html_logo_tag = f"<a class='navbar-brand' href='./' id='logo'><img src='data:image/png;base64,{encoded_logo.decode('utf8')}' width='142px' height='120px' alt='Thalassa Logo'></img></a>"
    logo = pn.pane.HTML(html_logo_tag, width=200, align="center")
    return logo


def get_header(title: str):
    logo = get_logo()
    header = pn.Row(logo, pn.layout.Tabs(), pn.layout.Tabs(), pn.layout.Tabs(), pn.layout.Tabs(), title)
    return header


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

    header = get_header(title="## Max elevation for the next 72 hours")
    disclaimer = get_disclaimer()

    return pn.Column(header, layout, disclaimer)


def elevation(data_dir: pathlib.Path):
    # load data
    grid_path = data_dir / "grid.npz"
    elevation_path = data_dir / "elevation.nc"
    x, y, simplices = load_grid_from_disk(grid_path)
    z = get_dataset(elevation_path)
    # create panel objects
    xyz_points = pd.DataFrame(dict(x=x, y=y, z=z.elev.isel(time=0).values))
    points = hv.Points(xyz_points, kdims=["x", "y"], vdims="z")
    opts.defaults(opts.WMTS(width=1200, height=900))

    def time_mesh(time):
        points.data.z = z.elev.sel(time=time).values
        return hv.TriMesh((simplices, points))#, crs=ccrs.GOOGLE_MERCATOR)

    meshes = hv.DynamicMap(time_mesh, kdims='Time').redim.values(Time=z.time.values)

    datashaded_trimesh = (
        rasterize(meshes, aggregator='mean')
        .opts(colorbar=True, cmap='Viridis', clim=(z.elev.values.min(), z.elev.values.max()), clabel='meters')
    )

    tiles = gv.WMTS('https://maps.wikimedia.org/osm-intl/{Z}/{X}/{Y}@2x.png')

    t_widget = pn.widgets.Select()

    @pn.depends(t_widget)
    def t_plot(time):
        return tiles * datashaded_trimesh

    header = get_header(title="## Time Steps")

    text = '''
      # USAGE
      Use the toolbox on the right to zoom in/out.
      '''
    footer = pn.Row(pn.pane.Markdown(text))
    disclaimer = get_disclaimer()

    return pn.Column(header, t_plot, footer, disclaimer)


def video(data_dir: pathlib.Path):
    header = get_header(title="## Animation")
    mp4 = (data_dir / "animation.mp4").resolve().as_posix()
    video = pn.pane.Video(mp4, width=640, height=360, loop=True)
    row = pn.Row(video.controls(jslink=True), video)
    disclaimer = get_disclaimer()
    return pn.Column(header, row, disclaimer)


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
    header = get_header(title="## Mesh")
    disclaimer = get_disclaimer()
    return pn.Column(header, layout, disclaimer)


def about(data_dir: pathlib.Path):
    layout = pn.pane.Markdown(ABOUT_TEXT, width=1000, height=600)
    header = get_header(title="## About")
    disclaimer = get_disclaimer()
    return pn.Column(header, layout, disclaimer)


def time_series(data_dir: pathlib.Path):
    tiles_widget = pn.widgets.Select(options=gvts.tile_sources, name="Web Map Tile Services")
    widgets = pn.WidgetBox(tiles_widget, margin=5)
    header = get_header(title="## Validation")
    l_path = data_dir / "stations.csv"
    stations = pd.read_csv(l_path, index_col=[0])

    # https://github.com/holoviz/hvplot/issues/180
    hover = HoverTool(
        tooltips=[
            ("Name", "@Name"),
            #                            ("Group", "@Group")
        ]
    )

    tgs = stations.hvplot.points(
        x="lon", y="lat", hover_cols=["Name"], geo=True, tools=["tap", hover], selection_line_color="red", s=100, color="orange"
    )

    def get_data(name):
        s_path = data_dir / "stations.tar.gz"
        with tarfile.open(s_path, "r:*") as tar:
            #    print(tar.getnames())
            csv_path = "STATIONS/sim_{}.csv".format(name)
            dfa = pd.read_csv(tar.extractfile(csv_path), index_col=[0, 1])
        df = dfa.loc["l0"]
        df = df.drop_duplicates()
        df = df.reset_index()
        df.columns = ["Time", "Elevation"]
        df["Elevation"] = df.Elevation.astype(float)
        df["Time"] = pd.to_datetime(df["Time"])
        df["Time"] = df.Time.dt.tz_localize("UTC")
        return df

    # https://towardsdatascience.com/advanced-data-visualization-with-holoviews-e7263ad202e
    # https://github.com/holoviz/holoviews/issues/1713
    dtf = DatetimeTickFormatter(days="%d-%m-%Y", months="%d-%m-%Y", years="%m-%Y")

    # https://github.com/holoviz/hvplot/issues/180
    hover1 = HoverTool(
        tooltips=[("Time", "@Time{%F}"), ("Elevation", "@Elevation")],
        formatters={
            "@Time": "datetime",  # use 'datetime' formatter for '@date' field
        },
    )

    def select_tg(index):
        if not index:
            df = pd.DataFrame({"Time": [], "Elevation": []}).hvplot(
                "Time", "Elevation", color="green", width=833, height=250, padding=0.1
            )
            name = ""
        else:
            name = tgs.data.iloc[index[0]].Name
            df = get_data(name)
        dataset = hv.Dataset(df)
        return hv.Curve(dataset, kdims=["Time"], vdims=["Elevation"]).opts(
            color="green", width=833, height=350, padding=0.1, framewise=True, xformatter=dtf, title=name, tools=[hover1]
        )

    index_stream = Selection1D(source=tgs, index=[])
    graph = hv.DynamicMap(select_tg, streams=[index_stream])

    @pn.depends(tiles_widget)
    def tplot(tile):
        return tile.opts(height=500, width=833) * tgs

    body = pn.Column(pn.Row(tplot, tiles_widget), pn.Row(pn.panel(graph)))

    text = """
      # USAGE

      Use the toolbox on the right to zoom in/out.

      On the map use Esc to go back to full selection'
      """
    footer = pn.Row(pn.pane.Markdown(text))
    disclaimer = get_disclaimer()
    return pn.Column(header, body, footer, disclaimer)
