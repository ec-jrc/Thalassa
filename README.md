Large Scale Sea level visualizations of unstructured mesh data
===============================================================

Thalassa is a library/application for visualizing large scale results of hydrodynamic simulations.



https://user-images.githubusercontent.com/411196/146007390-88e8cc59-9ae9-4a15-83fd-f7f1f2d724c2.mp4



## Obtaining Data

You will need some data to visualize. If you don't have any you can download a sample dataset
created with [pyposeidon](https://github.com/ec-jrc/pyPoseidon/):

```
mkdir ./data
wget -O data/dataset.nc https://static.techrad.eu/thalassa/dataset.nc
```

## Deploying on a server

1. Install the binary dependencies:

- `python 3.9`
- `proj < 8`

2. Install the python dependencies with

```
pip install -r requirements/requirements.txt
```

3. Run the panel server with:

```
panel serve ./run.py
```

For the record, `panel serve` is a thin wrapper around the [bokeh
server](https://docs.bokeh.org/en/latest/docs/user_guide/server.html#).  It provides lots of
command line options which can useful in various deployments scenarios.  Of particular interest
might be `--num-procs` which spawns multiple workers and `--allow-websocket-origin`. Make sure to
check the docs:

- https://panel.holoviz.org/user_guide/Deploy_and_Export.html#launching-a-server-on-the-commandline
- https://docs.bokeh.org/en/latest/docs/user_guide/server.html#basic-reverse-proxy-setup
- `panel serve --help`

## Developing

### Prerequisites

For managing dependencies we use poetry.

```
pipx install poetry
```

### Install dependencies

Just run:

```
poetry install
```

and please make sure to also install the [pre-commit](https://pre-commit.com/) hooks:

```
pre-commit install
```

### Running Thalassa

#### As a web application

It should be as simple as:

```
panel serve ./run.py --autoreload
```

#### Inside jupyterlab

Open the `Thalassa.ipynb` in jupyterlab

## License

The project is released under the EUPL v1.2 license.
