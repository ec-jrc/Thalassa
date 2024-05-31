from __future__ import annotations

import geoviews as gv
import holoviews as hv
import pytest

from . import DATA_DIR
from thalassa import api
from thalassa import normalization

ADCIRC_NC = DATA_DIR / "fort.63.nc"
SELAFIN1 = DATA_DIR / "r2d_malpasset-char_p2.slf"
SELAFIN2 = DATA_DIR / "r2d.V1P3.slf"

@pytest.mark.parametrize(
    "file,variable,crs",
    [
        pytest.param(ADCIRC_NC, "zeta", 4326),
        pytest.param(SELAFIN1, "S", None),
        pytest.param(SELAFIN2, "HAUTEUR_HM0", 4326),
    ],
)
def test_main_api(file, variable, crs):
    ds = api.open_dataset(file, source_crs=crs)
    assert normalization.is_generic(ds)

    # Create objects
    trimesh = api.create_trimesh(ds.sel(time=ds.time[0]), variable=variable)
    wireframe = api.get_wireframe(trimesh)
    nodes = api.get_nodes(trimesh)
    raster = api.get_raster(trimesh)
    tap_ts = api.get_tap_timeseries(ds, variable, raster)
    pointer_ts = api.get_pointer_timeseries(ds, variable, raster)

    # Render them!
    hv.render(nodes, backend="bokeh")
    hv.render(pointer_ts, backend="bokeh")
    hv.render(raster, backend="bokeh")
    hv.render(tap_ts, backend="bokeh")
    hv.render(wireframe, backend="bokeh")

    assert isinstance(nodes, (gv.Points, hv.Points))
    assert isinstance(pointer_ts, hv.DynamicMap)
    assert isinstance(raster, hv.DynamicMap)
    assert isinstance(tap_ts, hv.DynamicMap)
    assert isinstance(wireframe, hv.DynamicMap)


@pytest.mark.parametrize(
    "file,variable,crs",
    [
        pytest.param(ADCIRC_NC, "zeta", 4326),
        pytest.param(SELAFIN1, "S", None),
        pytest.param(SELAFIN2, "HAUTEUR_HM0", 4326),
    ],
)
def test_create_trimesh(file, variable, crs):
    ds = api.open_dataset(file, source_crs=crs)
    trimesh = api.create_trimesh(ds, variable=variable)
    assert isinstance(trimesh, (gv.TriMesh, hv.TriMesh))


def test_get_tiles():
    tiles = api.get_tiles()
    hv.render(tiles, backend="bokeh")
    assert isinstance(tiles, gv.WMTS), type(tiles)
