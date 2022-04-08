# pylint: disable=unused-argument,no-member
from __future__ import annotations

import glob
import logging
import os.path
import panel as pn
import xarray as xr
from pyproj import Transformer
from . import api
from . import utils

logger = logging.getLogger(__name__)
DATA_DIR = "data" + os.path.sep + "*"

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

    def __init__( self, display_stations: bool = False) -> None:
        self._display_stations = display_stations

        #UI components
        self._main = pn.Column(error("## Please select a `dataset_file` and click on the `Render` button."))
        self._sidebar = pn.Column()

        #Define widgets  
        self.dataset_file = pn.widgets.Select(
            name="Dataset file", options=sorted(filter(utils.can_be_opened_by_xarray, glob.glob(DATA_DIR))),
        )
        #self.dataset_format    = pn.widgets.Select(name="Format",options=["SCHISM",])
        self.prj               = pn.widgets.TextInput(value='epsg:4326',name="Projection")
        self.time              = pn.widgets.Select(name="Time")
        self.variable          = pn.widgets.Select(name="Variable")
        self.layer             = pn.widgets.Select(name="Layer",options=["surface","bottom"],value="surface")
        self.relative_colorbox = pn.widgets.Checkbox(name="Relative colorbox")
        self.show_grid         = pn.widgets.Checkbox(name="Show Grid")

        #time series
        self.timeseries        = pn.widgets.Checkbox(name="Time Series (double click)")
        self.timeseries_variable = pn.widgets.Select(name="Variable")
        self.timeseries_layer  = pn.widgets.Select(name="Layer",options=["surface","bottom"],value="surface")
        self.timeseries_pts    = pn.widgets.RadioButtonGroup(options=['add pts','remove pts','clear'])
        self.timeseries_ymin   = pn.widgets.TextInput(value='-1.0',name="ymin")
        self.timeseries_ymax   = pn.widgets.TextInput(value='1.0',name="ymax")

        #stations
        self.stations_file     = pn.widgets.Select(name="Stations file")
        self.stations          = pn.widgets.CrossSelector(name="Stations")

        # render button
        self.render_button     = pn.widgets.Button(name="Render", button_type="primary")

        self._define_widget_callbacks()
        self._populate_widgets()
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._sidebar.append(
            pn.Accordion(
                ("Input Files", pn.WidgetBox(self.dataset_file, self.prj, #pn.Row(self.dataset_format,self.prj),
                 self.time, pn.Row(self.variable,self.layer), pn.Row(self.relative_colorbox,self.show_grid),)),
                active=[0],
            ),
        )
        self._sidebar.append(
            pn.Accordion(
                ("Time Series", pn.WidgetBox(self.timeseries, #pn.Row(self.timeseries_variable,self.timeseries_layer),
                 pn.Row(self.timeseries_ymin, self.timeseries_ymax), self.timeseries_pts,)),
                active=[0],
            ),
        )
        if self._display_stations:
            self._sidebar.append(
                pn.Accordion(("Stations", pn.WidgetBox(self.stations_file, self.stations))),
            )
        self._sidebar.append(self.render_button)

    def _define_widget_callbacks(self) -> None:
        #Dataset callback
        self.dataset_file.param.watch(fn=self._read_header_info, parameter_names="value")
        self.prj.param.watch(fn=self._read_header_info,parameter_names="value")
        #timeseries callback
        self.timeseries.param.watch(fn=self._update_main,parameter_names="value")
        self.timeseries_pts.param.watch(fn=self._update_main,parameter_names="value")
        #self.timeseries_variable.param.watch(fn=self._init_timeseries,parameter_names="value")
        #self.timeseries_layer.param.watch(fn=self._init_timeseries,parameter_names="value")
        #Station callbacks
        #Render button
        self.render_button.on_click(self._update_main)

    def _populate_widgets(self) -> None:
        self.dataset_file.param.trigger("value")

    @property
    def sidebar(self) -> pn.Column:
        return self._sidebar

    @property
    def main(self) -> pn.Column:
        return self._main

    def _read_header_info(self,event: pn.Event): 
        self._MData=api.MapData()
        self.dataset_format=utils.read_dataset(self.dataset_file.value)[1]
        hdata=utils.read_dataset(self.dataset_file.value,1,self.dataset_format,self.prj.value)
        self._MData.name      = self.dataset_file.value
        self._MData.format    = self.dataset_format
        self._MData.prj       = self.prj.value
        self._MData.dataset   = hdata[0]
        self._MData.times     = hdata[1]
        self._MData.variables = hdata[2]
        self._MData.x         = hdata[3]
        self._MData.y         = hdata[4]
        self._MData.elnode    = hdata[5]
        self._MData.grid      = None

        #transform projection
        if self.prj.value!='epsg:4326':
           self._MData.y, self._MData.x = Transformer.from_crs(self.prj.value,'epsg:4326').transform(self._MData.x,self._MData.y)
        
        self.time.param.set_param(options=[*hdata[1]], value=hdata[1][0])
        self.variable.param.set_param(options=hdata[2], value=hdata[2][0])
        self.timeseries_variable.param.set_param(options=hdata[2], value=hdata[2][0])

        #initilize Timeseries class
        self._init_timeseries(event)
        #self._TSData=api.TimeseriesData(self._MData)

    def _init_timeseries(self,event: pn.Event):
        #self._TSData=api.TimeseriesData(self._MData, self.timeseries_variable.value, self.timeseries_layer.value)
        self._TSData=api.TimeseriesData(self._MData, self.timeseries_variable.value, self.layer.value)

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
            if self._MData.time!=self.time.value or self._MData.variable!=self.variable.value or self._MData.layer!=self.layer.value:
               #if self._MData.variable!=self.variable.value or self._MData.layer!=self.layer.value:
               #   self._TSData=api.TimeseriesData(self._MData)

               #read dataset snapshot values 
               self._debug_ui()
               self._MData.get_data(self.time.value,self.variable.value,self.layer.value)

               #get plots of  trimesh and dmap 
               self._MData.get_plot_map()
               logger.debug("Created dynamic map")

            #update dynamic map            
            if self.show_grid.value:
               dmap=self._MData.tiles * self._MData.trimap * self._MData.grid
            else:
               dmap=self._MData.tiles * self._MData.trimap

            #update time series
            if self.timeseries.value:
               if self.timeseries_pts.value=='clear':
                  self._TSData=api.TimeseriesData(self._MData)
               hpoint,hcurve=self._TSData.get_timeseries(self.timeseries_ymin.value,
                                 self.timeseries_ymax.value, self.timeseries_pts.value)

            #display map and time series
            if self.timeseries.value:
               self._main.objects = [dmap*hpoint,hcurve]
               logger.info("update timeseries")
            else:
               self._main.objects = [dmap.opts(height=650)]

            logger.info("check objects: {}".format(len(self._main.objects)))
        except Exception:
            logger.exception("Failed in _update_main")
            raise
        logger.info("Finished: _update_main")
