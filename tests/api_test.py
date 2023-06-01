from __future__ import annotations

import geoviews as gv
import holoviews as hv
import pytest

from . import DATA_DIR
from thalassa import api
from thalassa import normalization

ADCIRC_NC = DATA_DIR / "fort.63.nc"


def test_main_api():
    variable = "zeta"
    ds = api.open_dataset(ADCIRC_NC)
    assert normalization.is_generic(ds)

    # Create objects
    trimesh = api.create_trimesh(ds, variable=variable, timestamp=ds.time[0])
    wireframe = api.get_wireframe(trimesh)
    raster = api.get_raster(trimesh)
    tap_ts = api.get_tap_timeseries(ds, variable, raster)
    pointer_ts = api.get_pointer_timeseries(ds, variable, raster)
    assert isinstance(wireframe, hv.DynamicMap)
    assert isinstance(raster, hv.DynamicMap)
    assert isinstance(tap_ts, hv.DynamicMap)
    assert isinstance(pointer_ts, hv.DynamicMap)

    # Render them!
    hv.render(raster, backend="bokeh")
    hv.render(wireframe, backend="bokeh")
    hv.render(tap_ts, backend="bokeh")
    hv.render(pointer_ts, backend="bokeh")


@pytest.mark.parametrize(
    "timestamp",
    [
        None,
        "timestamp",
        "max",
        "min",
    ],
)
@pytest.mark.parametrize("variable", [None, "zeta"])
def test_create_trimesh(timestamp, variable):
    ds = api.open_dataset(ADCIRC_NC)
    if timestamp == "timestamp":
        timestamp = ds.time[0]

    trimesh = api.create_trimesh(ds, variable=variable, timestamp=timestamp)
    assert isinstance(trimesh, gv.TriMesh)


def test_get_tiles():
    tiles = api.get_tiles()
    hv.render(tiles, backend="bokeh")
