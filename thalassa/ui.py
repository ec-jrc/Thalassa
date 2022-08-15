# pylint: disable=unused-argument,no-member
from __future__ import annotations

import gc
import glob
import logging
import os.path
import pathlib

import geoviews as gv
import panel as pn
import xarray as xr

from . import api
from . import utils
from . import normalization


logger = logging.getLogger(__name__)

DATA_DIR = "./data/"
DATA_GLOB = DATA_DIR + os.path.sep + "*"


MISSING_DATA_DIR = pn.pane.Alert(
    f"## Directory <{DATA_DIR}> is missing. Please create it and add some suitable netcdf files.",
    alert_type="danger",
)
EMPTY_DATA_DIR = pn.pane.Alert(
    f"## Directory <{DATA_DIR}> exists but it is empty. Please add some suitable netcdf files.",
    alert_type="danger",
)
CHOOSE_FILE = pn.pane.Alert(
    "## Please select a *Dataset* and click on the **Render** button.",
    alert_type="info",
)
UNKNOWN_FORMAT = pn.pane.Alert(
    f"## The selected dataset is in an unknown format. Please choose a different file.",
    alert_type="danger",
)
PLEASE_RENDER = pn.pane.Alert(
    f"## Please click on the **Render** button to visualize the selected *Variable*",
    alert_type="info",
)


def choose_initial_message() -> pn.pane.Alert:
    if not pathlib.Path(DATA_DIR).is_dir():
        message = MISSING_DATA_DIR
    elif not sorted(filter(utils.can_be_opened_by_xarray, glob.glob(DATA_GLOB))):
        message = EMPTY_DATA_DIR
    else:
        message = CHOOSE_FILE
    return message


class ThalassaUI:  # pylint: disable=too-many-instance-attributes
    """
    This UI is supposed to be used with a Bootstrap-like template supporting
    a "main" and a "sidebar":
    - `sidebar` will contain the widgets that control what will be rendered in the main area.
      E.g. things like which `source_file` to use, which timestamp to render etc.
    - `main` will contain the rendered graphs.
    In a nutshell, an instance of the `UserInteface` class will have two private attributes:
    - `_main`
    - `_sidebar`
    These objects should be of `pn.Column` type. You can append
    """

    def __init__(self) -> None:
        self._dataset: xr.Dataset
        self._previous_raster: gv.DynamicMap | None = None

        # UI components
        self._main = pn.Column(CHOOSE_FILE)
        self._sidebar = pn.Column()

        # Define widgets
        self.dataset_file = pn.widgets.Select(
            name="Dataset file",
            options=[""] + sorted(filter(utils.can_be_opened_by_xarray, glob.glob(DATA_GLOB))),
        )
        self.variable = pn.widgets.Select(name="Variable")
        self.layer = pn.widgets.Select(name="Layer")
        self.time = pn.widgets.Select(name="Time")
        self.relative_colorbox = pn.widgets.Checkbox(name="Relative colorbox", disabled=False)
        self.show_mesh = pn.widgets.Checkbox(name="Show Mesh")
        self.show_timeseries = pn.widgets.Checkbox(name="Show Timeseries")
        self.render_button = pn.widgets.Button(name="Render", button_type="primary")

        # Setup UI
        self._sidebar.append(
            pn.WidgetBox(
                self.dataset_file,
                self.variable,
                self.layer,
                self.time,
                pn.Row(self.show_timeseries, self.show_mesh),
            )
        )
        self._sidebar.append(self.render_button)
        logger.debug("UI setup: done")

        # Define callback
        self.dataset_file.param.watch(fn=self._update_dataset_file, parameter_names="value")
        self.variable.param.watch(fn=self._update_layer, parameter_names="value")
        self.render_button.on_click(self._update_main)
        logger.debug("Callback definitions: done")

        initial_message = choose_initial_message()
        self._reset_ui(message=initial_message)

    def _reset_ui(self, message: pn.pane.Alert) -> None:
        self.variable.param.set_param(options=[], disabled=True)
        self.time.param.set_param(options=[], disabled=True)
        self.layer.param.set_param(options=[], disabled=True)
        self.show_timeseries.param.set_param(disabled=True)
        self.show_mesh.param.set_param(disabled=True)
        self.relative_colorbox.param.set_param(disabled=True)
        self._main.objects = [message]

    def _update_dataset_file(self, event: pn.Event) -> None:
        # local variables
        dataset_file = self.dataset_file.value

        if not dataset_file:
            logger.debug("No dataset has been selected. Resetting the UI.")
            self._reset_ui(message=CHOOSE_FILE)
        else:
            try:
                logger.debug("Trying to normalize the selected dataset: %s", dataset_file)
                self._dataset = normalization.normalize_dataset(utils.open_dataset(dataset_file, load=False))
            except ValueError as exc:
                logger.exception("Normalization failed. Resetting the UI")
                self._reset_ui(message=UNKNOWN_FORMAT)
            else:
                logger.exception("Normalization succeeded. Setting widgets")
                variables = utils.filter_visualizable_data_vars(
                    self._dataset, self._dataset.data_vars.keys()
                )
                self.variable.param.set_param(options=variables, disabled=False)
                self.show_mesh.param.set_param(disabled=False)
                self.relative_colorbox.set_param(disabled=False)
                self._main.objects = [PLEASE_RENDER]

    def _update_layer(self, event: pn.Event) -> None:
        try:
            ds = self._dataset
            variable = self.variable.value
            # handle layer
            if variable and "layer" in ds[variable].dims:
                layers = ds.layer.values.tolist()
                self.layer.disabled = False
                self.layer.param.set_param(options=layers)  # , value=layers[0])
            else:
                self.layer.param.set_param(options=[])
                self.layer.disabled = True
            # handle time
            if variable and "time" in ds[variable].dims:
                # self.show_timeseries.disabled = False
                self.time.disabled = False
                self.time.param.set_param(options=["max"] + list(ds.time.values))
            else:
                self.show_timeseries.disabled = True
                self.time.disabled = True
                self.time.param.set_param(options=[])
        except:
            logger.exception("error layer")

    def _debug_ui(self) -> None:
        logger.info("Widget values:")
        widgets = [obj for (name, obj) in self.__dict__.items() if isinstance(obj, pn.widgets.Widget)]
        for widget in widgets:
            logger.error("%s: %s", widget.name, widget.value)

    def _get_spinner(self) -> pn.Column:
        """Return a `pn.Column` with an horizontally/vertically aligned spinner."""
        column = pn.Column(
            pn.layout.Spacer(height=100),
            pn.Row(
                pn.layout.HSpacer(),
                pn.Row(pn.indicators.LoadingSpinner(value=True, width=150, height=150)),
            ),
        )
        return column

    def _update_main(self, event: pn.Event) -> None:
        try:
            # XXX For some reason, which I can't understand
            # Inside this specific callback, the logger requires to be WARN and above...
            logger.warning("Updating main")
            self._debug_ui()

            # Since each graph takes up to a few GBs of RAM, before we create the new graph we should remove
            # the old one. In order to do so we need to remove *all* the references to the old raster. This includes:
            # - the `_main` column
            # - the `self._previous_raster`

            # Before removing the old raster, we should retrieve it's Bounding Box
            # This will allow us to restore the zoom level after re-clicking on the Render button.
            if self._previous_raster:
                bbox = api.get_bbox_from_raster(self._previous_raster)
                x_range = api.get_x_range_from_bbox(bbox)
                y_range = api.get_y_range_from_bbox(bbox)
            else:
                x_range = None
                y_range = None

            # Now remove the first reference to the old raster
            self._previous_raster = None

            # We would like to show to the users that something is being computed,
            # therefore we replace the second reference to the raster (the one in the _main
            # column) with a spinner
            self._main.objects = [*self._get_spinner().objects]

            # Let's make an explicit call to `gc.collect()`. This will make sure
            # that the references to the old raster are removed before the creation of the new one,
            # thus RAM usage should remain low(-ish).
            gc.collect()

            # Each time a graph is rendered, data are loaded from the dataset
            # This increases the RAM usage over time. E.g. when loading the second variable,
            # the first one remains in RAM.
            # In order to avoid this, we re-open the dataset in order to get a clean Dataset
            # instance without anything loaded into memory
            ds = normalization.normalize_dataset(utils.open_dataset(self.dataset_file.value, load=False))

            # local variables
            variable = self.variable.value
            timestamp = self.time.value
            layer = int(self.layer.value) if self.layer.value is not None else None

            # create plots
            trimesh = api.create_trimesh(ds=ds, variable=variable, timestamp=timestamp, layer=layer)
            tiles = api.get_tiles()

            raster = api.get_raster(trimesh=trimesh, x_range=x_range, y_range=y_range)

            # Keep a reference to the previous raster instance.
            # This one will be used for restoring the zoom level, when we render a new variable
            self._previous_raster = raster

            # Create Colorbar widgets and link them to the raster
            clim_min = pn.widgets.FloatInput(name="Colorbar min")
            clim_max = pn.widgets.FloatInput(name="Colorbar max")
            clim_min.jslink(raster, value="color_mapper.low")
            clim_max.jslink(raster, value="color_mapper.high")
            # clim_min.jslink(raster, value="color_mapper.low", bidirectional=True)
            # clim_max.jslink(raster, value="color_mapper.high", bidirectional=True)

            # create the Layout that will get rendered and and add it to the `_main` Column.
            if self.show_mesh.value:
                mesh = api.get_wireframe(trimesh, x_range=x_range, y_range=y_range)
                plot = tiles * raster * mesh
            else:
                plot = tiles * raster

            # If the variable depends on `time` and `show_timeseries` has been checked,
            # then plot the timeseries, too
            # For the record, (and this is probably a panel bug), if we use
            #     self._main.append(ts_plot)
            # then the timeseries plot does not get updated each time we click on the
            # DynamicMap. By replacing the `objects` though, then the updates work fine.
            if "time" in ds[variable].dims and self.show_timeseries.value:
                pass
            #     ts_plot = api.get_tap_timeseries(ds=ds, variable=variable, source_raster=raster, layer=layer)
            #     self._main.objects = [
            #         pn.WidgetBox(clim_min, clim_max),
            #         ts_plot,
            #         plot,
            #     ]
            else:
                self._main.objects = [
                    pn.Row(clim_min, clim_max),
                    plot,
                ]
        except:
            logger.exception("Something went wrong")

    @property
    def sidebar(self) -> pn.Column:
        return self._sidebar

    @property
    def main(self) -> pn.Column:
        return self._main
