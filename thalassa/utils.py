from __future__ import annotations

import logging.config
import os
import pathlib
import typing

import numpy as np
import numpy.typing as npt
import xarray as xr
from ruamel.yaml import YAML

yaml = YAML(typ="safe", pure=True)

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    with open("config.yml", "rb") as fd:
        config = yaml.load(fd.read())

    logging.config.dictConfig(config["logging"])
    logger.debug(logging.getLogger("thalassa").handlers)


def open_dataset(path: str | os.PathLike[str], load: bool = False) -> xr.Dataset:
    path = pathlib.Path(path)
    kwargs: dict[str, typing.Any] = dict(mask_and_scale=True, cache=False)
    if path.suffix in (".nc", ".netcdf"):
        # ADCIRC datasets are not compatible with xarray:
        # They fail with the error:
        #   "dimension 'neta' already exists as a scalar variable",
        #   "dimension 'nvel' already exists as a scalar variable",
        # Source: https://github.com/pydata/xarray/issues/1709#issuecomment-343714896
        #
        # The workaround we have for this is to drop the problematic variables
        # As an implementation detail we make use of an xarray "feature" which ignores
        # non-existing names in `drop_variables`. So we can use `drop_variables=[...]` even
        # if we are opening a dataset from a different solver.
        # This may cause  issues if different solvers use `neta/nvel` as dimension/variable
        # names, but at least for now it seems to be good enough.
        kwargs["engine"] = "netcdf4"
        kwargs["drop_variables"] = ["neta", "nvel"]
    elif path.suffix in (".zarr", ".zip") or path.is_dir():
        kwargs["engine"] = "zarr"
    # TODO: extend with GeoTiff, Grib etc
    else:
        raise ValueError(f"Don't know how to handle this: {path}")
    ds = xr.open_dataset(path, **kwargs)
    if load:
        # load dataset to memory
        ds.load()
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
