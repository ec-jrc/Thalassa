from __future__ import annotations

import contextlib
import importlib
import logging
import os
import pathlib
import sys

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


def reload(module_name: str) -> None:
    """
    Reload source code when working interactively, e.g. on jupyterlab

    Source: https://stackoverflow.com/questions/28101895/
    """
    # In order to avoid having ipython as a hard dependency we need to inline the import statement
    from IPython.lib import deepreload  # type: ignore  # pylint: disable=import-outside-toplevel

    # Get a handle of the module object
    module = importlib.import_module(module_name)

    # sys.modules contains all the modules that have been imported so far.
    # Reloading all the modules takes too long.
    # Therefore let's create a list of modules that we should exclude from the reload procedure
    to_be_excluded = {key for (key, value) in sys.modules.items() if module_name not in key}

    # deepreload uses print(). Let's disable it with a context manager
    # https://stackoverflow.com/a/46129367/592289
    with open(os.devnull, "w", encoding="utf-8") as fd, contextlib.redirect_stdout(fd):
        # OK, now let's reload!
        deepreload.reload(module, exclude=to_be_excluded)


def can_be_opened_by_xarray(path):
    try:
        open_dataset(path)
    except ValueError:
        logger.debug("path cannot be opened by xarray: %s", path)
        return False
    else:
        return True
