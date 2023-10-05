from __future__ import annotations

import enum
import logging
import pathlib

import xarray as xr

from . import api
from . import utils


logger = logging.getLogger(__name__)


class THALASSA_FORMATS(enum.Enum):
    UNKNOWN = "UNKNOWN"
    ADCIRC = "ADCIRC"
    SCHISM = "SCHISM"
    GENERIC = "GENERIC"
    PYPOSEIDON = "PYPOSEIDON"


# fmt: off
_GENERIC_DIMS = {
    "node",
    "triface",
    "three",
}
_GENERIC_VARS = {
    "lon",
    "lat",
    "triface_nodes",
}
_SCHISM_DIMS = {
    "nSCHISM_hgrid_edge",
    "nSCHISM_hgrid_face",
    "nSCHISM_hgrid_node",
    "nMaxSCHISM_hgrid_face_nodes",
}
_SCHISM_VARS = {
    "SCHISM_hgrid_node_x",
    "SCHISM_hgrid_node_y",
    "SCHISM_hgrid_face_nodes",
}
_PYPOSEIDON_DIMS = {
    "nSCHISM_hgrid_face",
    "nSCHISM_hgrid_node",
    "nMaxSCHISM_hgrid_face_nodes",
}
_PYPOSEIDON_VARS = {
    "SCHISM_hgrid_node_x",
    "SCHISM_hgrid_node_y",
    "SCHISM_hgrid_face_nodes",
}
_ADCIRC_DIMS = {
    "node",
    "nele",
    "nvertex",
}
_ADCIRC_VARS = {
    "element",
}
# fmt: on


def is_generic(ds: xr.Dataset) -> bool:
    total_vars = list(ds.data_vars.keys()) + list(ds.coords.keys())
    return _GENERIC_DIMS.issubset(ds.dims) and _GENERIC_VARS.issubset(total_vars)


def is_schism(ds: xr.Dataset) -> bool:
    total_vars = list(ds.data_vars.keys()) + list(ds.coords.keys())
    return _SCHISM_DIMS.issubset(ds.dims) and _SCHISM_VARS.issubset(total_vars)


def is_pyposeidon(ds: xr.Dataset) -> bool:
    return _PYPOSEIDON_DIMS.issubset(ds.dims) and _PYPOSEIDON_VARS.issubset(ds.data_vars)


def is_adcirc(ds: xr.Dataset) -> bool:
    return _ADCIRC_DIMS.issubset(ds.dims) and _ADCIRC_VARS.issubset(ds.data_vars)


def infer_format(ds: xr.Dataset) -> THALASSA_FORMATS:
    if is_schism(ds):
        fmt = THALASSA_FORMATS.SCHISM
    elif is_adcirc(ds):
        fmt = THALASSA_FORMATS.ADCIRC
    elif is_pyposeidon(ds):
        fmt = THALASSA_FORMATS.PYPOSEIDON
    elif is_generic(ds):
        fmt = THALASSA_FORMATS.GENERIC
    else:
        fmt = THALASSA_FORMATS.UNKNOWN
    logger.debug("Inferred format: %s", fmt)
    return fmt


def can_be_inferred(path: str | pathlib.Path) -> bool:
    logger.debug("Trying to open: %s", path)
    try:
        ds = api.open_dataset(path, normalize=False)
    except ValueError:
        return False
    fmt = infer_format(ds)
    if fmt == THALASSA_FORMATS.UNKNOWN:
        result = False
    else:
        result = True
    return result


def normalize_generic(ds: xr.Dataset) -> xr.Dataset:
    return ds


def normalize_schism(ds: xr.Dataset) -> xr.Dataset:
    ds = ds.rename(
        {
            "nSCHISM_hgrid_edge": "edge",
            "nSCHISM_hgrid_face": "face",
            "nSCHISM_hgrid_node": "node",
            "SCHISM_hgrid_face_nodes": "face_nodes",
            "nMaxSCHISM_hgrid_face_nodes": "max_no_vertices",
            "SCHISM_hgrid_node_x": "lon",
            "SCHISM_hgrid_node_y": "lat",
        },
    )
    if "nSCHISM_vgrid_layers" in ds.dims:
        # I.e. OLD Schism IO or "merged" new IO
        ds = ds.rename(
            {
                "nSCHISM_vgrid_layers": "layer",
            },
        )
    # SCHISM output uses one-based indices for `face_nodes`
    # Let's ensure that we use zero-based indices everywhere.
    ds["face_nodes"] -= 1
    return ds


def normalize_pyposeidon(ds: xr.Dataset) -> xr.Dataset:
    ds = ds.rename(
        {
            "nSCHISM_hgrid_face": "face",
            "nSCHISM_hgrid_node": "node",
            "SCHISM_hgrid_face_nodes": "face_nodes",
            "nMaxSCHISM_hgrid_face_nodes": "max_no_vertices",
            "SCHISM_hgrid_node_x": "lon",
            "SCHISM_hgrid_node_y": "lat",
        },
    )
    return ds


def normalize_adcirc(ds: xr.Dataset) -> xr.Dataset:
    ds = ds.rename(
        {
            "x": "lon",
            "y": "lat",
            "element": "face_nodes",
            "nvertex": "max_no_vertices",
            "nele": "face",
        },
    )
    # ADCIRC output uses one-based indices for `face_nodes`
    # Let's ensure that we use zero-based indices everywhere.
    ds["face_nodes"] -= 1
    return ds


NORMALIZE_DISPATCHER = {
    THALASSA_FORMATS.ADCIRC: normalize_adcirc,
    THALASSA_FORMATS.GENERIC: normalize_generic,
    THALASSA_FORMATS.SCHISM: normalize_schism,
    THALASSA_FORMATS.PYPOSEIDON: normalize_pyposeidon,
}


def normalize(ds: xr.Dataset) -> xr.Dataset:
    """
    Normalize the `dataset` i.e. convert it to the "Thalassa Schema".

    Examples:
        ``` python
        import thalassa
        import xarray as xr

        ds = xr.open_dataset("some_netcdf.nc")
        ds = thalassa.normalize(ds)
        print(ds)
        ```

    Parameters:
        ds: The dataset we want to convert.

    """
    logger.debug("Dataset normalization: Started")
    fmt = infer_format(ds)
    normalizer_func = NORMALIZE_DISPATCHER[fmt]
    normalized_ds = normalizer_func(ds)
    # Handle quad elements
    # Splitting quad elements to triangles, means that the number of faces increases
    # There are two options:
    # 1. We insert new faces and we keep on using `face_nodes`
    # 2. We define a new variable and a new dimension which specifically address triangular elements
    # I'd rather avoid altering the values of the provided netcdf file therefore we go for option #2,
    # i.e. we create the `triface_nodes` variable.
    if "triface_nodes" not in ds.data_vars:
        if "max_no_vertices" in normalized_ds.dims and len(normalized_ds.max_no_vertices) == 4:
            triface_nodes = utils.split_quads(normalized_ds.face_nodes.values)
        else:
            triface_nodes = normalized_ds.face_nodes.values
        normalized_ds["triface_nodes"] = (("triface", "three"), triface_nodes)
    logger.debug("Dataset normalization: Finished")
    return normalized_ds
