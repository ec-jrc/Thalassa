# pylint: disable=unused-argument,no-member
from __future__ import annotations

import glob
import logging
import os.path

import panel as pn
import xarray as xr

from . import api
from . import utils


logger = logging.getLogger(__name__)

DATA_DIR = "./data/"
DATA_GLOB = DATA_DIR + os.path.sep + "*"

# CSS Styles
ERROR = {"border": "3px solid red"}
INFO = {"border": "2px solid blue"}


# Help functions that log messages on stdout AND render them on the browser
def info(msg: str) -> pn.Column:
    logger.info(msg)
    return pn.pane.Markdown(msg, style=INFO)


def error(msg: str) -> pn.Column:
    logger.error(msg)
    return pn.pane.Markdown(msg, style=ERROR)


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

    def __init__(
        self,
        display_variables: bool = True,
        display_stations: bool = False,
    ) -> None:
        self._display_variables = display_variables
        self._display_stations = display_stations

        # data variables
        self._dataset: xr.Dataset
        self._variables: list[str]
        self._TimeseriesData=api.TimeseriesData()
        self._timestamp='None'

        # UI components
        self._main = pn.Column(info("## Please select a `dataset_file` and click on the `Render` button."))
        self._sidebar = pn.Column()

        ## Define widgets  # noqa
        self.dataset_file = pn.widgets.Select(
            name="Dataset file", options=sorted(filter(utils.can_be_opened_by_xarray, glob.glob(DATA_GLOB)))
        )
        # variables
        self.longitude_var = pn.widgets.Select(name="Longitude")
        self.latitude_var = pn.widgets.Select(name="Latitude")
        self.elevation_var = pn.widgets.Select(name="Elevation")
        self.simplices_var = pn.widgets.Select(name="Simplices")
        self.time_var = pn.widgets.Select(name="Time")
        # display options
        self.timestamp = pn.widgets.Select(name="Timestamp")
        self.relative_colorbox = pn.widgets.Checkbox(name="Relative colorbox")
        self.show_grid = pn.widgets.Checkbox(name="Show Grid")
        #time series
        self.timeseries = pn.widgets.Checkbox(name="Time Series (double click)",width=150)
        self.timeseries_pts=pn.widgets.RadioButtonGroup(options=['add pts','remove pts','clear'],width=300)
        self.timeseries_ymin = pn.widgets.TextInput(value='-1.0',name="ymin",width=100)
        self.timeseries_ymax = pn.widgets.TextInput(value='1.0',name="ymax",width=100)
        # stations
        self.stations_file = pn.widgets.Select(name="Stations file")
        self.stations = pn.widgets.CrossSelector(name="Stations")
        # render button
        self.render_button = pn.widgets.Button(name="Render", button_type="primary")

        self._define_widget_callbacks()
        self._populate_widgets()
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._sidebar.append(pn.Accordion(("Input Files", pn.WidgetBox(self.dataset_file)), active=[0]))
        if self._display_variables:
            self._sidebar.append(
                pn.Accordion(
                    (
                        "Variables",
                        pn.WidgetBox(
                            self.longitude_var,
                            self.latitude_var,
                            self.elevation_var,
                            self.simplices_var,
                            self.time_var,
                        ),
                    )
                )
            )
        self._sidebar.append(
            pn.Accordion(
                ("Display Options", pn.WidgetBox(self.timestamp, self.relative_colorbox,
                 self.show_grid,)),
                active=[0],
            ),
        )
        self._sidebar.append(
            pn.Accordion(
                ("Time Series", pn.WidgetBox(self.timeseries,
                 pn.Row(self.timeseries_ymin,self.timeseries_ymax),self.timeseries_pts,)),
                active=[0],
            ),
        )
        if self._display_stations:
            self._sidebar.append(
                pn.Accordion(("Stations", pn.WidgetBox(self.stations_file, self.stations))),
            )
        self._sidebar.append(self.render_button)

    def _define_widget_callbacks(self) -> None:
        # Dataset callback
        self.dataset_file.param.watch(fn=self._update_dataset_file, parameter_names="value")
        # Variable callbacks
        self.dataset_file.param.watch(
            fn=lambda event: self._set_variable(event, self.longitude_var, 1, "SCHISM_hgrid_node_x"),
            parameter_names="value",
        )
        self.dataset_file.param.watch(
            fn=lambda event: self._set_variable(event, self.latitude_var, 2, "SCHISM_hgrid_node_y"),
            parameter_names="value",
        )
        self.dataset_file.param.watch(
            fn=lambda event: self._set_variable(event, self.elevation_var, 0, "elev"),
            parameter_names="value",
        )
        self.dataset_file.param.watch(
            fn=lambda event: self._set_variable(event, self.simplices_var, 3, "SCHISM_hgrid_face_nodes"),
            parameter_names="value",
        )
        self.dataset_file.param.watch(
            fn=lambda event: self._set_variable(event, self.time_var, 4, "time"),
            parameter_names="value",
        )
        # Display options callbacks
        self.dataset_file.param.watch(fn=self._update_timestamp, parameter_names="value")
        self.timeseries.param.watch(fn=self._update_main,parameter_names="value")
        self.timeseries_pts.param.watch(fn=self._update_main,parameter_names="value")
        # Station callbacks
        #
        # Render button
        self.render_button.on_click(self._update_main)

    def _populate_widgets(self) -> None:
        self.dataset_file.param.trigger("value")

    @property
    def sidebar(self) -> pn.Column:
        return self._sidebar

    @property
    def main(self) -> pn.Column:
        return self._main

    def _update_dataset_file(self, event: pn.Event) -> None:
        logger.debug("Using dataset: %s", self.dataset_file.value)
        self._dataset = utils.open_dataset(self.dataset_file.value, load=False)
        self._variables = list(self._dataset.variables.keys())  # type: ignore[arg-type]

    def _set_variable(self, event: pn.Event, widget: pn.Widget, index: int, schism_name: str) -> None:
        # logger.debug("Updating %s", widget.name)
        if schism_name in self._variables:
            value = schism_name
        else:
            try:
                value = self._variables[index]
            except IndexError:
                logger.error("Not enough variables: %d, %s", index, self._variables)
                raise
        widget.param.set_param(options=self._variables, value=value)

    def _update_timestamp(self, event: pn.Event) -> None:
        dataset_timestamps = self._dataset[self.time_var.value].to_pandas().dt.to_pydatetime()
        dataset_options = ["MAXIMUM"] + [v.strftime("%Y-%m-%d %H-%M-%S") for v in dataset_timestamps]
        # self.timestamp.param.set_param(options=dataset_options, value="MAXIMUM")
        self.timestamp.param.set_param(options=dataset_options, value=dataset_timestamps[0])

    def _debug_ui(self) -> None:
        logger.debug("Widget values:")
        widgets = [obj for (name, obj) in self.__dict__.items() if isinstance(obj, pn.widgets.Widget)]
        for widget in widgets:
            logger.debug("%s: %s", widget.name, widget.value)

    def _update_main(self, event: pn.Event) -> None:
        logger.info("Starting: _update_main")
        # Not sure what is going on here, but panel seems to shallow exceptions within callbacks
        # Having an explicit try/except at least allows to log the error
        try:
            if self._timestamp!=self.timestamp.value:
               self._debug_ui()
               self._dataset = utils.open_dataset(self.dataset_file.value, load=True)
               trimesh = api.get_trimesh(
                   self._dataset,
                   self.longitude_var.value,
                   self.latitude_var.value,
                   self.elevation_var.value,
                   self.simplices_var.value,
                   self.time_var.value,
                   timestamp=self.timestamp.value,
               )
               logger.debug("Created trimesh")
               dmap = api.get_elevation_dmap(trimesh, show_grid=self.show_grid.value)
               logger.debug("Created dynamic map")

               #save plot for efficiency
               self.trimesh,self.dmap,self._timestamp=trimesh,dmap,self.timestamp.value

            #update time series
            if self.timeseries.value:
               if self.timeseries_pts.value=='clear':
                  self._TimeseriesData.clear()
               hpoint,hcurve=api.get_timeseries(
                   self.trimesh,
                   self._TimeseriesData,
                   self._dataset,
                   self.timeseries_ymin.value,
                   self.timeseries_ymax.value,
                   self.timeseries_pts.value,
               )
               self._main.objects = [self.dmap*hpoint,hcurve]
               logger.info("update timeseries")
            else:
               self._main.objects = [self.dmap.opts(height=650)]

            logger.info("check objects: {}".format(len(self._main.objects)))
        except Exception:
            logger.exception("Failed in _update_main")
            raise
        logger.info("Finished: _update_main")
