Large Scale Sea level visualizations of unstructured mesh data
===============================================================

Thalassa is a developmental prototype for visualizing large scale results of hydrodynamic simulations.

## Obtaining Data

You will need some data to visualize. If you don't have any you can download a sample dataset
created with [pyposeidon](https://github.com/ec-jrc/pyPoseidon/):

```
mkdir data
wget -O data/dataset.nc    https://static.techrad.eu/thalassa/dataset.nc
```

## Deploying on a server

1. Install the dependencies with

```
pip install -r requirements/requirements.txt
```

2. Run the panel server with:

```
panel serve ./thalassa
```

For the record, `panel serve` is a thin wrapper around the [bokeh server](https://docs.bokeh.org/en/latest/docs/user_guide/server.html#).
It provides lot's of command line options which can useful in various deployments scenarios.
Of particular interest might be `--num-procs` which spawns multiple workers and
`--allow-websocket-origin`. Make sure to check the docs:

- https://panel.holoviz.org/user_guide/Deploy_and_Export.html#launching-a-server-on-the-commandline
- https://docs.bokeh.org/en/latest/docs/user_guide/server.html#basic-reverse-proxy-setup
- `panel serve --help`

## Developing

### Prerequisites

For managing dependencies we make use of poetry `groups` and plugins so you need [poetry](https://github.com/python-poetry/poetry) >= 1.2.
At least for now, the easiest way to install it is to use [pipx](https://github.com/pypa/pipx):

```
pipx install 'poetry==1.2.0a2'
pipx inject poetry poetry-export-plugin  # Only needed if you want to export a requirements.txt out of the pyproject.toml
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
panel serve ./thalassa --autoreload
```

#### Inside jupyterlab

Open the `Thalassa.ipynb` in jupyterlab

## License

The project is released under the EUPL v1.2 license.
