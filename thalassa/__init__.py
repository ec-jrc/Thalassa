"""
Thalassa is a library for visualizing unstructured mesh data with a focus on large scale sea level data

"""
from __future__ import annotations

import importlib.metadata

from .api import open_dataset
from .normalization import normalize
from .plotting import plot
from .plotting import plot_mesh
from .plotting import plot_ts
from .utils import crop


__version__ = importlib.metadata.version("thalassa")

__all__: list[str] = [
    "__version__",
    "crop",
    "normalize",
    "open_dataset",
    "plot",
    "plot_mesh",
    "plot_ts",
]
