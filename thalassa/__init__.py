"""
Thalassa is a library for visualizing unstructured mesh data with a focus on large scale sea level data

"""
from __future__ import annotations

from .api import open_dataset
from .normalization import normalize
from .plotting import plot
from .plotting import plot_mesh
from .plotting import plot_ts
from .utils import crop


__all__: list[str] = [
    "crop",
    "normalize",
    "open_dataset",
    "plot",
    "plot_mesh",
    "plot_ts",
]
