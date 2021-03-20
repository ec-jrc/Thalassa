from __future__ import annotations

import pathlib

from typing import Tuple

import numpy as np
import pyproj
import xarray as xr


def get_dataset(path: pathlib.Path) -> xr.Dataset:
    dataset = xr.open_dataset(path)
    return dataset


def convert_lat_lon_to_xy(longitudes: np.array, latitudes: np.array, target_crs: int = 3857) -> Tuple[np.array, np.array]:
    """ Convert `(latitude, longitude)` arrays to the `target_crs` """
    transformer = pyproj.Transformer.from_crs(crs_from=4326, crs_to=target_crs, always_xy=True)
    x_points, y_points = transformer.transform(longitudes, latitudes, errcheck=True)
    return x_points, y_points


def save_grid_to_disk(dataset: xr.Dataset, output: pathlib.Path, target_crs: int = 3857) -> None:
    """ Save the definition of the grid on disk after reprojecting to `EPSG:3857` """
    longitudes=dataset.SCHISM_hgrid_node_x.values
    latitudes=dataset.SCHISM_hgrid_node_y.values
    x, y = convert_lat_lon_to_xy(longitudes, latitudes)
    # We opt to save the grid uncompressed since the benefit from compression is relatively small (~2x)
    # while uncompressing takes significantly more time than loading (especially on SSDs).
    np.savez(output, x=x, y=y, simplices=dataset.SCHISM_hgrid_face_nodes.values)

def extract_grid(dataset: xr.Dataset, target_crs: int = 3857) -> None:
    """ Save the definition of the grid on disk after reprojecting to `EPSG:3857` """
    longitudes=dataset.SCHISM_hgrid_node_x.values
    latitudes=dataset.SCHISM_hgrid_node_y.values
    x, y = convert_lat_lon_to_xy(longitudes, latitudes)
    # We opt to save the grid uncompressed since the benefit from compression is relatively small (~2x)
    # while uncompressing takes significantly more time than loading (especially on SSDs).
    return x, y, dataset.SCHISM_hgrid_face_nodes.values


def save_elevation_to_disk(dataset: xr.Dataset, output: pathlib.Path) -> None:
    """ Save the elevation data to disk """
    np.savez(output, elevation=dataset.elev.values)
    np.savez(output.parent / "elevation.max.npz", elevation=dataset.elev.max("time").values)


def load_grid_from_disk(grid_path: pathlib.Path) -> Tuple[np.array, np.array, np.array]:
    """ Read the definition of the grid from disk """
    with np.load(grid_path) as npz:
        x = npz["x"]
        y = npz["y"]
        simplices = npz["simplices"]
    return x, y, simplices


def load_elevation_from_disk(grid_path: pathlib.Path) -> np.array:
    with np.load(grid_path) as npz:
        elevation = npz["elevation"]
    return elevation
