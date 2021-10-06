import logging.config

import panel as pn  # type: ignore
from ruyaml import YAML

from thalassa.web_ui import Thalassa

# load configuration
yaml = YAML(typ="safe", pure=True)

with open("config.yml", "rb") as fd:
    config = yaml.load(fd.read())

# configure logging
logging.config.dictConfig(config["logging"])

# Create the panel deployable app
# https://panel.holoviz.org/user_guide/Deploy_and_Export.html#launching-a-server-on-the-commandline
thalassa = Thalassa(name="Thalassa")
layout = pn.Row(thalassa.param, thalassa.view)
layout.servable()
