from __future__ import annotations

import glob
import logging
import os.path
import pathlib
from typing import Any

import holoviews as hv  # type: ignore
import panel as pn  # type: ignore
import param  # type: ignore
from holoviews import opts as hvopts

from . import utils
from . import visuals


logger = logging.getLogger(__name__)

DATA_DIR = "./data/"
DATA_DIR_GLOB = DATA_DIR + os.path.sep + "*"

# CSS Styles
ERROR = {"border": "4px solid red"}
INFO = {"border": "2px solid blue"}

# Set some defaults for the visualization of the graphs
hvopts.defaults(
    hvopts.Image(width=800, height=400, show_title=True, tools=["hover"]),  # pylint: disable=no-member
    hvopts.Layout(toolbar="right"),  # pylint: disable=no-member
)

# Help functions that log them on stdout AND render them on the browser
# Callbacks should return these functions. E.g:
#
#     def _some_callback(self):
#          try:
#              foo()
#          except Exception:
#              return error("Foo failed", is_exception=True)
#


def info(msg: str) -> pn.pane.Markdown:
    logger.info(msg)
    return pn.pane.Markdown(msg, style=INFO)


def error(msg: str) -> pn.pane.Markdown:
    logger.error(msg)
    return pn.pane.Markdown(msg, style=ERROR)


def exception(msg: str) -> pn.pane.Markdown:
    logger.exception(msg)
    return pn.pane.Markdown(msg, style=ERROR)


class XarrayFileSelector(param.FileSelector):
    """A `param.FileSelector` that filters out files that cannot be opened by Xarray"""

    def update(self) -> None:
        candidate_paths = glob.glob(self.path)
        self.objects = sorted(filter(utils.can_be_opened_by_xarray, candidate_paths))
        if self.default in self.objects:  # type: ignore
            return
        self.default = self.objects[0] if self.objects else None


class Thalassa(param.Parameterized):
    source_file: str = XarrayFileSelector(path=DATA_DIR_GLOB)
    longitude_var: str = param.ObjectSelector(objects=[""])
    latitude_var: str = param.ObjectSelector(objects=[""])
    elevation_var: str = param.ObjectSelector(objects=[""])
    simplices_var: str = param.ObjectSelector(objects=[""])
    time_var: str = param.ObjectSelector(objects=[""])
    # ll_coord: float = param.XYCoordinates()
    # ur_coord: float = param.XYCoordinates()
    relative_colorbar: bool = param.Boolean(True)
    show_wireframe: bool = param.Boolean(False)
    render: Any = param.Event(default=False)

    def _check_sanity(self) -> str:
        if not pathlib.Path(DATA_DIR).exists():
            return "## The DATA_DIR does not exist. Create it and restart the server"
        if not self.param["source_file"].objects:
            return (
                "## The DATA_DIR does not contain any files that can be opened by xarray. "
                "Populate it and restart the server."
            )
        return ""

    @param.depends("source_file", watch=True)
    def _update_source_file(self) -> None:
        """Callback that gets called each time the `source_file` combobox value gets updated"""
        # We just got a new value on source_file.
        # We need to get the list of variables contained in the file and
        # use them to populate the `*_var` comboboxes
        ds = utils.open_dataset(self.source_file)
        variables = list(ds.variables)
        self.param["longitude_var"].objects = variables
        self.param["latitude_var"].objects = variables
        self.param["elevation_var"].objects = variables
        self.param["simplices_var"].objects = variables
        self.param["time_var"].objects = variables

        # Just to make things a bit easier for the user, let's pre-populate the comboboxes.
        # Let's also use some simple heuristics in order to make working with SCHISM output easier
        self.elevation_var = str(variables[0])
        self.longitude_var = (
            "SCHISM_hgrid_node_x" if "SCHISM_hgrid_node_x" in variables else str(variables[1])
        )
        self.latitude_var = (
            "SCHISM_hgrid_node_y" if "SCHISM_hgrid_node_y" in variables else str(variables[2])
        )
        self.simplices_var = (
            "SCHISM_hgrid_face_nodes" if "SCHISM_hgrid_face_nodes" in variables else str(variables[3])
        )
        self.time_var = "time" if "time" in variables else str(variables[4])

    @param.depends("relative_colorbar", watch=True)
    def _toggle_elevation_colorbar(self):
        raise NotImplementedError("Toggle absolute/relative colormap")

    def _view(self) -> pn.Column:
        # sanity check
        sanity_error = self._check_sanity()
        if sanity_error:
            return error(sanity_error)

        # This is a hack. I (pmav99) don't know how to properly fix this using `param.Selectors`.
        # When the UI gets rendered on the browser for the first time the `source_file` combobox
        # displays a default value (the first suitable file in the `DATA_DIR` directory), but the
        # `source_file` object value is still `None`. The problem is that if there is just a single
        # suitable file in `DATA_DIR` then even when you select the file, the object value does not
        # change and the `_update_source_file()` callback does not get called....
        # Therefore, in order to populate the `source_file` object
        # with the proper path, we should explicitly set the value of the object.
        if self.source_file is None:
            self.source_file = self.param["source_file"].objects[0]
            return info("## Choose source file and variables and click on 'Render'")

        logger.debug("Using source_file: %s", self.source_file)
        logger.debug("Using longitude_var: %s", self.longitude_var)
        logger.debug("Using latitude_var: %s", self.latitude_var)
        logger.debug("Using elevation_var: %s", self.elevation_var)
        logger.debug("Using simplices_var: %s", self.simplices_var)
        logger.debug("Using time_var: %s", self.time_var)

        logger.debug("Open dataset")
        ds = pn.state.as_cached(
            key=self.source_file,
            fn=utils.open_dataset,
            path=self.source_file,
            load=True,
        )

        logger.debug("Create trimesh")
        trimesh = visuals.get_trimesh(
            ds=ds,
            longitude_var=self.longitude_var,
            latitude_var=self.latitude_var,
            elevation_var=self.elevation_var,
            simplices_var=self.simplices_var,
            time_var=self.time_var,
        )

        # Render main plot
        output = visuals.get_max_elevation(trimesh)

        # Render additional plots
        if self.show_wireframe:
            output += visuals.get_wireframe(trimesh)

        # Ensure that additional plots are displayed in a single column
        if isinstance(output, hv.Layout):
            output = output.cols(1)

        return pn.Column(output)

    @param.depends("render", watch=False)
    def view(self) -> hv.Layout:
        """
        Callback that renders the right column of the UI (i.e. the graphs)

        Gets called the first time the UI gets rendered and every time you click on the "Render" button.
        """
        # The param callbacks are silencing all exceptions...
        # This makes it really hard to debug what went wrong.
        # That's why we wrap the actual callback in a try/except clause
        try:
            return self._view()
        except Exception:  # pylint: disable=broad-except
            return exception("Something went wrong")
