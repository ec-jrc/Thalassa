from __future__ import annotations

import logging.config
import typing

import numpy as np
import numpy.typing as npt
import pandas as pd
import xarray as xr
from ruamel.yaml import YAML

yaml = YAML(typ="safe", pure=True)

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    with open("config.yml", "rb") as fd:
        config = yaml.load(fd.read())

    logging.config.dictConfig(config["logging"])
    logger.debug(logging.getLogger("thalassa").handlers)


def generate_thalassa_ds(
    nodes: npt.NDArray[np.int_],
    triface_nodes: npt.NDArray[np.int_],
    lons: npt.NDArray[np.float_] | None = None,
    lats: npt.NDArray[np.float_] | None = None,
    time_range: pd.DateTimeIndex | None = None,
    **kwargs: dict[str, tuple[tuple[str], npt.NDArray[np.float_]]],
) -> xr.Dataset:
    """Return a "thalassa" dataset"""
    # Coordinates
    coords = dict(
        node=nodes,
        triface=range(len(triface_nodes)),
    )
    if time_range is not None:
        coords["time"] = (("time"), time_range)
    # Data Variables
    data_vars: dict[str, typing.Any] = {
        "triface_nodes": (("triface", "three"), triface_nodes),
        **kwargs,
    }
    if lons:
        data_vars["lon"] = (("node"), lons)
    if lats:
        data_vars["lat"] = (("node"), lats)
    ds = xr.Dataset(
        coords=coords,
        data_vars=data_vars,
    )
    return ds


_VISUALIZABLE_DIMS = {
    ("node",),
    ("time", "node"),
    ("time", "node", "layer"),
}


def is_variable_visualizable(ds: xr.Dataset, variable: str) -> bool:
    """
    Return `True` if thalassa can visualize the variable, `False` otherwise.
    """
    if variable in {"lon", "lat"}:
        return False
    return ds[variable].dims in _VISUALIZABLE_DIMS


def filter_visualizable_data_vars(ds: xr.Dataset, variables: typing.Iterable[str]) -> list[str]:
    visualizable = []
    for var in variables:
        if is_variable_visualizable(ds=ds, variable=var):
            visualizable.append(var)
    return visualizable


def split_quads(face_nodes: npt.NDArray[np.int_]) -> npt.NDArray[np.int_]:
    """
    https://gist.github.com/pmav99/5ded91f18ef096b080b2ed45598c7d1c
    """
    if face_nodes.shape[-1] != 4:
        return face_nodes

    # We assume that the nans only exist in the last column
    # Therefore the first 3 columns are the existing triangles
    existing_triangles = face_nodes[:, :3]

    # Identify the quads. They are the rows with nan in the last column
    # The nonzero() function is a speed optimization. With this, we only keep
    # the index  values we care about, instead of the whole boolean array
    quad_indexes = np.nonzero(~np.isnan(face_nodes).any(axis=1))
    quads = face_nodes[quad_indexes]

    # Create the new triangles
    quads_first_column = quads[:, 0]
    quads_last_two_columns = quads[:, -2:]
    new_triangles = np.c_[quads_first_column, quads_last_two_columns]

    # Append new triangles to the existing ones
    # Also cast to the proper type for Mypy
    new_face_nodes = typing.cast(
        npt.NDArray[np.int_],
        np.r_[existing_triangles, new_triangles].astype(int),
    )
    return new_face_nodes
    # return new_face_nodes.astype(int)


def get_index_of_nearest_node(ds: xr.Dataset, lon: float, lat: float) -> int:
    # https://www.unidata.ucar.edu/blogs/developer/en/entry/accessing_netcdf_data_by_coordinates
    # https://github.com/Unidata/python-workshop/blob/fall-2016/notebooks/netcdf-by-coordinates.ipynb
    dist = abs(ds.lon - lon) ** 2 + abs(ds.lat - lat) ** 2
    index_of_nearest_node = typing.cast(int, dist.argmin())
    return index_of_nearest_node


def extract_timeseries(ds: xr.Dataset, variable: str, lon: float, lat: float) -> xr.DataArray:
    index = get_index_of_nearest_node(ds=ds, lon=lon, lat=lat)
    return ds[variable].isel(node=index)


def drop_elements_crossing_idl(
    ds: xr.Dataset,
    max_lon: float = 10,
) -> xr.Dataset:
    """
    Drop triface elements crossing the International Date Line (IDL).

    ``max_lon`` is the maximum longitudinal "distance" in degrees for an element.

    What we are actually trying to do in this function is to identify mesh triangles that cross
    the IDL. The truth is that when you have a triplet of nodes you can't really know if the
    tirangle they create is the one in `[-180, 180]` or the one that crosses the IDL.
    So here we make one assumption: That we are dealing with a global mesh with a lot of elements.
    Therefore we assume that the elements that cross the IDL are the ones that:
    1. have 2 nodes with different longitudinal sign, e.g. -179 and 179
    2. the absolute of the difference of the longitudes is greater than a user defined threshold
       e.g. `|179 - (-179)| >= threshold`
    The second rule exists to remove false positives close to Greenwich (e.g. 0.1 and -0.1)
    These rules can lead to false positives close to the poles (e.g. latitudes > 89) especially
    if a small value for `max_lon` is used. Nevertheless, the main purpose of this function is
    to visualize data, so some false positives are not the end of the wold.
    """
    if max_lon <= 0:
        raise ValueError(f'Maximum longitudinal "distance" must be positive: {max_lon}')
    a, b, c = ds.triface_nodes.data.T
    lon = ds.lon.data
    lon_a = lon[a]
    lon_b = lon[b]
    lon_c = lon[c]
    # `np.asarray(condition).nonzero()` is equivalent to `np.where(condition)`
    # For more info check the help of `np.where()`
    condition = (
        # fmt: off
          ((lon_a * lon_b < 0) & (np.abs(lon_a - lon_b) >= max_lon))
        | ((lon_a * lon_c < 0) & (np.abs(lon_a - lon_c) >= max_lon))
        | ((lon_b * lon_c < 0) & (np.abs(lon_b - lon_c) >= max_lon))
        # fmt: on
    )
    indices_of_triface_nodes_crossing_idl = np.asarray(condition).nonzero()[0]
    ds = ds.drop_isel(triface=indices_of_triface_nodes_crossing_idl)
    return ds
