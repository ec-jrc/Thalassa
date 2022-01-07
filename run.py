from __future__ import annotations

import logging.config

import holoviews as hv
import panel as pn
from holoviews import opts as hvopts
from ruamel.yaml import YAML

import thalassa

# load configuration
yaml = YAML(typ="safe", pure=True)

with open("config.yml", "rb") as fd:
    config = yaml.load(fd.read())

# configure logging
logging.config.dictConfig(config["logging"])

# load bokeh
hv.extension("bokeh")
pn.extension(sizing_mode="scale_width")

# Set some defaults for the visualization of the graphs
hvopts.defaults(
    hvopts.Image(  # pylint: disable=no-member
        # Don't set both height and width, or the UI will not be responsive!
        # width=800,
        height=500,
        responsive=True,
        show_title=True,
        tools=["hover"],
        active_tools=["pan", "wheel_zoom"],
        align="end",
    ),
    hvopts.Layout(toolbar="right"),  # pylint: disable=no-member
)


ui = thalassa.ThalassaUI(
    display_variables=True,
    display_stations=True,
)

# https://panel.holoviz.org/reference/templates/Bootstrap.html
bootstrap = pn.template.BootstrapTemplate(
    site="example.com",
    title="Thalassa",
    logo="thalassa/static/logo.png",
    favicon="thalassa/static/favicon.png",
    sidebar=[ui.sidebar],
    sidebar_width=350,  # in pixels! must be an integer!
    # main_max_width="850px", #  must be a string!
    main=[ui.main],
)

bootstrap.servable()
