from __future__ import annotations

import holoviews as hv
import pytest

import thalassa
from . import DATA_DIR


@pytest.fixture(scope="session")
def fort_ds():
    ds = thalassa.open_dataset(DATA_DIR / "fort.63.nc")
    return ds


def test_sanity_check_no_node_dimension(fort_ds):
    with pytest.raises(ValueError) as exc:
        thalassa.plotting._sanity_check(ds=fort_ds.drop_dims("node"), variable="nvell")
    assert "include 'node'" in str(exc.value)


def test_sanity_check_multiple_dimensions(fort_ds):
    with pytest.raises(ValueError) as exc:
        thalassa.plotting._sanity_check(ds=fort_ds, variable="zeta")
    assert "the only dimension of 'zeta' is `node`" in str(exc.value)


def test_plot(fort_ds):
    dmap = thalassa.plot(ds=fort_ds.isel(time=0), variable="zeta")
    assert isinstance(dmap, hv.DynamicMap)


def test_plot_show_mesh(fort_ds):
    dmap = thalassa.plot(ds=fort_ds.isel(time=0), variable="zeta", show_mesh=True)
    assert isinstance(dmap, hv.DynamicMap)


def test_plot_show_nodes(fort_ds):
    dmap = thalassa.plot(ds=fort_ds.isel(time=0), variable="zeta", show_nodes=True)
    assert isinstance(dmap, hv.DynamicMap)


def test_plot_show_mesh_show_nodes(fort_ds):
    dmap = thalassa.plot(ds=fort_ds.isel(time=0), variable="zeta", show_mesh=True, show_nodes=True)
    assert isinstance(dmap, hv.DynamicMap)


def test_plot_mesh(fort_ds):
    dmap = thalassa.plot_mesh(ds=fort_ds)
    assert isinstance(dmap, hv.DynamicMap)


def test_plot_nodes(fort_ds):
    hv.extension("bokeh")
    plot = thalassa.plot_nodes(ds=fort_ds)
    assert isinstance(plot, hv.Overlay)


def test_plot_ts(fort_ds):
    main_plot = thalassa.plot(ds=fort_ds.isel(time=0), variable="zeta")
    dmap = thalassa.plot_ts(ds=fort_ds, variable="zeta", source_plot=main_plot)
    assert isinstance(dmap, hv.DynamicMap)
