from __future__ import annotations

import logging
import pathlib
import typing

import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)


def open_dataset(path: str | pathlib.Path, load: bool = False) -> xr.Dataset:
    path = pathlib.Path(path)
    if path.suffix == ".nc":
        ds = xr.open_dataset(path, mask_and_scale=True)
    elif path.suffix in (".zarr", ".zip") or path.is_dir():
        ds = xr.open_dataset(path, mask_and_scale=True, engine="zarr")
    # TODO: extend with GeoTiff, Grib etc
    else:
        raise ValueError(f"Don't know how to handle this: {path}")
    if load:
        # load dataset to memory
        ds.load()
    return ds


def can_be_opened_by_xarray(path):
    try:
        open_dataset(path)
    except ValueError:
        logger.debug("path cannot be opened by xarray: %s", path)
        return False
    else:
        return True


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


def filter_visualizable_data_vars(ds: xr.Dataset, variables: typing.Sequence[str]) -> list[str]:
    visualizable = []
    for var in variables:
        if is_variable_visualizable(ds=ds, variable=var):
            visualizable.append(var)
    return visualizable


def split_quads(face_nodes: np.array) -> np.array:
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
    new_face_nodes = np.r_[existing_triangles, new_triangles].astype(int)
    return new_face_nodes.astype(int)


def get_index_of_nearest_node(ds: xr.Dataset, lon: float, lat: float) -> int:
    # https://www.unidata.ucar.edu/blogs/developer/en/entry/accessing_netcdf_data_by_coordinates
    # https://github.com/Unidata/python-workshop/blob/fall-2016/notebooks/netcdf-by-coordinates.ipynb
    dist = abs(ds.lon - lon) ** 2 + abs(ds.lat - lat) ** 2
    index_of_nearest_node = dist.argmin()
    return index_of_nearest_node


def extract_timeseries(ds: xr.Dataset, variable: str, lon: float, lat: float) -> xr.DataArray:
    index = get_index_of_nearest_node(ds=ds, lon=lon, lat=lat)
    return ds[variable].isel(node=index)
