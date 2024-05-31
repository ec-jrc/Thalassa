from __future__ import annotations

import enum
import logging
import pathlib
import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    import xarray

from . import api
from . import utils


logger = logging.getLogger(__name__)


class THALASSA_FORMATS(enum.Enum):
    UNKNOWN = "UNKNOWN"
    ADCIRC = "ADCIRC"
    SCHISM = "SCHISM"
    TELEMAC = "TELEMAC"
    GENERIC = "GENERIC"
    PYPOSEIDON = "PYPOSEIDON"


# fmt: off
EDGE_DIM = "edge"
FACE_DIM = "face"
NODE_DIM = "node"
VERTICAL_DIM = "layer"
CONNECTIVITY = "face_nodes"
VERTICE_DIM = "max_no_vertices"
X_DIM = "lon"
Y_DIM = "lat"

_GENERIC_DIMS = {
    NODE_DIM,
    "triface",
    "three",
}
_GENERIC_VARS = {
    X_DIM,
    Y_DIM,
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
_TELEMAC_DIMS = {
    "node",
}
_TELEMAC_VARS = {
    "x",
    "y",
    "ikle2",
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


def is_generic(ds: xarray.Dataset) -> bool:
    total_vars = list(ds.data_vars.keys()) + list(ds.coords.keys())
    return _GENERIC_DIMS.issubset(ds.dims) and _GENERIC_VARS.issubset(total_vars)


def is_schism(ds: xarray.Dataset) -> bool:
    total_vars = list(ds.data_vars.keys()) + list(ds.coords.keys())
    return _SCHISM_DIMS.issubset(ds.dims) and _SCHISM_VARS.issubset(total_vars)


def is_telemac(ds: xarray.Dataset) -> bool:
    total_vars = list(ds.data_vars.keys()) + list(ds.coords.keys()) + list(ds.attrs.keys())
    return _TELEMAC_DIMS.issubset(ds.dims) and _TELEMAC_VARS.issubset(total_vars)


def is_pyposeidon(ds: xarray.Dataset) -> bool:
    return _PYPOSEIDON_DIMS.issubset(ds.dims) and _PYPOSEIDON_VARS.issubset(ds.data_vars)


def is_adcirc(ds: xarray.Dataset) -> bool:
    return _ADCIRC_DIMS.issubset(ds.dims) and _ADCIRC_VARS.issubset(ds.data_vars)


def infer_format(ds: xarray.Dataset) -> THALASSA_FORMATS:
    if is_schism(ds):
        fmt = THALASSA_FORMATS.SCHISM
    elif is_telemac(ds):
        fmt = THALASSA_FORMATS.TELEMAC
    elif is_pyposeidon(ds):
        fmt = THALASSA_FORMATS.PYPOSEIDON
    elif is_generic(ds):
        fmt = THALASSA_FORMATS.GENERIC
    elif is_adcirc(ds):
        fmt = THALASSA_FORMATS.ADCIRC
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


def normalize_generic(ds: xarray.Dataset) -> xarray.Dataset:
    return ds


def normalize_schism(ds: xarray.Dataset) -> xarray.Dataset:
    ds = ds.rename(
        {
            "nSCHISM_hgrid_edge": EDGE_DIM,
            "nSCHISM_hgrid_face": FACE_DIM,
            "nSCHISM_hgrid_node": NODE_DIM,
            "SCHISM_hgrid_face_nodes": CONNECTIVITY,
            "nMaxSCHISM_hgrid_face_nodes": VERTICE_DIM,
            "SCHISM_hgrid_node_x": X_DIM,
            "SCHISM_hgrid_node_y": Y_DIM,
        },
    )
    if "nSCHISM_vgrid_layers" in ds.dims:
        # I.e. OLD Schism IO or "merged" new IO
        ds = ds.rename(
            {
                "nSCHISM_vgrid_layers": VERTICAL_DIM,
            },
        )
    # SCHISM output uses one-based indices for `face_nodes`
    # Let's ensure that we use zero-based indices everywhere.
    ds[CONNECTIVITY] -= 1
    return ds


def normalize_telemac(ds: xarray.Dataset) -> xarray.Dataset:
    ds = ds.rename(
        {
            "node": NODE_DIM,
            "x": X_DIM,
            "y": Y_DIM,
        },
    )
    if "plan" in ds.dims:
        ds = ds.rename(
            {
                "plan": VERTICAL_DIM,
            },
        )

    # TELEMAC output uses one-based indices for `face_nodes`
    # Let's ensure that we use zero-based indices everywhere.
    ds[CONNECTIVITY] = ((FACE_DIM, VERTICE_DIM), ds.attrs["ikle2"] - 1)
    return ds


def normalize_pyposeidon(ds: xarray.Dataset) -> xarray.Dataset:
    ds = ds.rename(
        {
            "nSCHISM_hgrid_face": FACE_DIM,
            "nSCHISM_hgrid_node": NODE_DIM,
            "SCHISM_hgrid_face_nodes": CONNECTIVITY,
            "nMaxSCHISM_hgrid_face_nodes": VERTICE_DIM,
            "SCHISM_hgrid_node_x": X_DIM,
            "SCHISM_hgrid_node_y": Y_DIM,
        },
    )
    return ds


def normalize_adcirc(ds: xarray.Dataset) -> xarray.Dataset:
    ds = ds.rename(
        {
            "x": X_DIM,
            "y": Y_DIM,
            "element": CONNECTIVITY,
            "nvertex": VERTICE_DIM,
            "nele": FACE_DIM,
        },
    )
    # ADCIRC output uses one-based indices for `face_nodes`
    # Let's ensure that we use zero-based indices everywhere.
    ds[CONNECTIVITY] -= 1
    return ds


NORMALIZE_DISPATCHER = {
    THALASSA_FORMATS.ADCIRC: normalize_adcirc,
    THALASSA_FORMATS.GENERIC: normalize_generic,
    THALASSA_FORMATS.SCHISM: normalize_schism,
    THALASSA_FORMATS.TELEMAC: normalize_telemac,
    THALASSA_FORMATS.PYPOSEIDON: normalize_pyposeidon,
}


def normalize(ds: xarray.Dataset, source_crs: int = 4326) -> xarray.Dataset:
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
        source_crs: The coordinate system of the dataset (default is WGS84)

    """
    logger.debug("Dataset normalization: Started")
    fmt = infer_format(ds)
    normalizer_func = NORMALIZE_DISPATCHER[fmt]
    normalized_ds = normalizer_func(ds)
    normalized_ds.attrs["source_crs"] = source_crs
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
