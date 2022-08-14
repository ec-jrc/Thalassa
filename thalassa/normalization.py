from __future__ import annotations

import logging
import enum

import xarray as xr

from .utils import split_quads


logger = logging.getLogger(__name__)


class KNOWN_FORMATS(enum.Enum):
    SCHISM = "SCHISM"
    GENERIC = "GENERIC"


_GENERIC_DIMS = {"time", "node", "face", "layer", "max_no_vertices"}
_GENERIC_VARS = {"lon", "lat", "face_nodes"}
_SCHISM_DIMS = {
    "time",
    "nSCHISM_hgrid_edge",
    "nSCHISM_hgrid_face",
    "nSCHISM_hgrid_node",
    "nSCHISM_vgrid_layers",
    "nMaxSCHISM_hgrid_face_nodes",
}
_SCHISM_VARS = {"SCHISM_hgrid_node_x", "SCHISM_hgrid_node_y", "SCHISM_hgrid_face_nodes"}


def is_generic(ds: xr.Dataset) -> bool:
    return _GENERIC_DIMS.issubset(ds.dims) and _GENERIC_VARS.issubset(ds.data_vars)


def is_schism(ds: xr.Dataset) -> bool:
    return _SCHISM_DIMS.issubset(ds.dims) and _SCHISM_VARS.issubset(ds.data_vars)


def infer_format(ds: xr.Dataset) -> KNOWN_FORMATS:
    if is_schism(ds):
        return KNOWN_FORMATS.SCHISM
    elif is_generic(ds):
        return KNOWN_FORMATS.GENERIC
    else:
        logger.debug("dataset dims: %s", ds.dims)
        logger.debug("dataset vars: %s", ds.data_vars.keys())
        raise ValueError("Unknown format")


def normalize_schism(ds: xr.Dataset) -> xr.Dataset:
    ds = ds.rename(
        {
            "nSCHISM_hgrid_edge": "edge",
            "nSCHISM_hgrid_face": "face",
            "nSCHISM_hgrid_node": "node",
            "nSCHISM_vgrid_layers": "layer",
            "SCHISM_hgrid_face_nodes": "face_nodes",
            "nMaxSCHISM_hgrid_face_nodes": "max_no_vertices",
            "SCHISM_hgrid_node_x": "lon",
            "SCHISM_hgrid_node_y": "lat",
        }
    )
    # SCHISM output uses one-based indices for `face_nodes`
    # while PyPoseidon uses zero-based indices
    # Let's ensure that we use zero-based indices everywhere.
    if ds.face_nodes.min().values == 1:
        ds["face_nodes"] -= 1
    return ds


NORMALIZE_DISPATCHER = {
    KNOWN_FORMATS.SCHISM: normalize_schism,
    KNOWN_FORMATS.GENERIC: lambda ds: ds,
}


def normalize_dataset(ds: xr.Dataset) -> xr.Dataset:
    format = infer_format(ds)
    logger.debug("inferred format: %s", format)
    normalizer_func = NORMALIZE_DISPATCHER[format]
    normalized_ds = normalizer_func(ds)
    # Handle quad elements
    # Splitting quad elements to triangles, means that the number of faces increases
    # There are two options:
    # 1. We insert new faces and we keep on using `face_nodes`
    # 2. We define a new variable and a new dimension which specifically address triangular elements
    # I'd rather avoid altering the values of the provided netcdf file therefore we go for option #2,
    # i.e. we create the `triface_nodes` variable.
    if len(normalized_ds.max_no_vertices) == 4:
        triface_nodes = split_quads(normalized_ds.face_nodes.values)
    else:
        triface_nodes = normalized_ds.face_nodes.values
    normalized_ds["triface_nodes"] = (("triface", "three"), triface_nodes)
    return normalized_ds
