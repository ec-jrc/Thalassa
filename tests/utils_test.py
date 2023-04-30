from __future__ import annotations

import pandas as pd
import xarray as xr

from thalassa import utils


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
