from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import shapely
import xarray as xr

from . import DATA_DIR
from thalassa import api
from thalassa import utils


ADCIRC_NC = DATA_DIR / "fort.63.nc"


def test_crop():
    ds = api.open_dataset(ADCIRC_NC)
    assert len(ds.node) == 3070
    bbox = shapely.box(-72.6, 40.75, -72.2, 40.9)
    cropped_ds = utils.crop(ds, bbox=bbox)
    assert len(cropped_ds.node) == 1363


def test_generate_thalassa_ds():
    ds = utils.generate_thalassa_ds(
        nodes=range(3),
        triface_nodes=[[0, 1, 2]],
    )
    assert isinstance(ds, xr.Dataset)
    assert set(ds.dims) == {"triface", "three", "node"}
    assert set(ds.coords) == {"triface", "node"}
    assert set(ds.data_vars) == {"triface_nodes"}


def test_generate_thalassa_ds_time():
    ds = utils.generate_thalassa_ds(
        nodes=range(3),
        triface_nodes=[[0, 1, 2]],
        time_range=pd.date_range("2001-01-01", periods=1),
    )
    assert isinstance(ds, xr.Dataset)
    assert set(ds.dims) == {"triface", "three", "node", "time"}
    assert set(ds.coords) == {"triface", "node", "time"}
    assert set(ds.data_vars) == {"triface_nodes"}


def test_generate_thalassa_ds_lon_lat():
    ds = utils.generate_thalassa_ds(
        nodes=range(3),
        triface_nodes=[[0, 1, 2]],
        lons=[-179, -179, 179],
        lats=[10, 12, 11],
    )
    assert isinstance(ds, xr.Dataset)
    assert set(ds.dims) == {"triface", "three", "node"}
    assert set(ds.coords) == {"triface", "node"}
    assert set(ds.data_vars) == {"triface_nodes", "lon", "lat"}


def test_generate_thalassa_ds_time_lon_lat():
    ds = utils.generate_thalassa_ds(
        nodes=range(3),
        triface_nodes=[[0, 1, 2]],
        lons=[-179, -179, 179],
        lats=[10, 12, 11],
        time_range=pd.date_range("2001-01-01", periods=1),
    )
    assert isinstance(ds, xr.Dataset)
    assert set(ds.dims) == {"triface", "three", "node", "time"}
    assert set(ds.coords) == {"triface", "node", "time"}
    assert set(ds.data_vars) == {"triface_nodes", "lon", "lat"}


def test_generate_thalassa_ds_time_lon_lat_additional_variables():
    ds = utils.generate_thalassa_ds(
        nodes=range(3),
        triface_nodes=[[0, 1, 2]],
        lons=[-179, -179, 179],
        lats=[10, 12, 11],
        time_range=pd.date_range("2001-01-01", periods=2),
        depth=(("node"), [100, 200, 300]),
        elevation=(("time", "node"), [[101, 201, 301], [99, 199, 299]]),
    )
    assert isinstance(ds, xr.Dataset)
    assert set(ds.dims) == {"triface", "three", "node", "time"}
    assert set(ds.coords) == {"triface", "node", "time"}
    assert set(ds.data_vars) == {"triface_nodes", "lon", "lat", "depth", "elevation"}


@pytest.mark.parametrize(
    "lons",
    [
        pytest.param([-179, -179, 179], id="both points close to IDL"),
        pytest.param([-5, -5, 175], id="one point close to IDL and the other in different quarter"),
        pytest.param([-175, -175, 5], id="one point close to IDL and the other in different quarter"),
    ],
)
def test_drop_elements_crossing_idl_single_element_is_dropped(lons):
    orig_ds = utils.generate_thalassa_ds(
        nodes=range(3),
        triface_nodes=[[0, 1, 2]],
        lons=lons,
        lats=[10, 12, 11],
    )
    ds = utils.drop_elements_crossing_idl(orig_ds)
    assert len(ds.triface) == 0
    assert ds.triface_nodes.shape == (0, 3)


def test_drop_elements_crossing_idl_single_element_remains():
    orig_ds = utils.generate_thalassa_ds(
        nodes=range(4),
        triface_nodes=[[0, 1, 2], [1, 2, 3]],
        lons=[-178, -179, -179, 179],
        lats=[11, 10, 12, 11],
    )
    ds = utils.drop_elements_crossing_idl(orig_ds)
    assert len(ds.triface) == 1
    assert ds.triface_nodes.shape == (1, 3)
    assert np.array_equal(ds.triface_nodes.data, np.array([[0, 1, 2]]))


def test_drop_elements_crossing_idl_no_elements_crossing_no_elements_dropped():
    orig_ds = utils.generate_thalassa_ds(
        nodes=range(4),
        triface_nodes=[[0, 1, 2], [1, 2, 3]],
        lons=[10, 11, 12, 13],
        lats=[11, 10, 12, 11],
    )
    ds = utils.drop_elements_crossing_idl(orig_ds)
    assert orig_ds.equals(ds)


def test_generate_mesh_polygon():
    ds = utils.generate_thalassa_ds(
        nodes=range(4),
        triface_nodes=[[0, 1, 2], [1, 2, 3]],
        lons=[10, 10, 12, 12],
        lats=[20, 22, 20, 22],
    )
    gdf = utils.generate_mesh_polygon(ds)
    assert gdf.geometry[0].area == 4
