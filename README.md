Large Scale Sea level visualizations of unstructured mesh data
===============================================================

This is a developmental prototype for visualizing large scale results of hydrodynamic simulations.

Thalassa is powered by

- [pyPoseidon](https://github.com/brey/pyPoseidon)

- [SCHISM](https://github.com/schism-dev/schism)

- [Panel](https://panel.holoviz.org/index.html)

## Instalation

Start by cloning the repository:

### Option 1: Use a virtualenv

Your system needs to have:

- python>=3.8
- geos
- gdal=3.2.1
- proj `<8`
- poetry

There are multiple ways to satisfy these requirements, e.g. using your distro's package manager,
compiling from source, etc. An easy way to proceed is to create a conda environment like the
following:

```
conda create -n Thalassa pip python=3.8 geos gdal=3.2.1 proj=7 poetry
```

Afterwards, activate the new conda environment, create a virtualenv and install the dependencies using
poetry:

```
conda activate Thalassa
python3 -m venv .venv
source .venv/bin/activate
poetry install
```

You are ready to go!

### Option 2: Use conda

Install the dependencies in a conda environment with:

```
conda env create -f binder/environment.yml
```

### Option3: Use docker

```
docker/build.sh
```

This will create a docker image

## Obtaining Data

You will need some data. If you don't have any you can download a sample dataset from here:

```
wget -O data/animation.mp4 https://static.techrad.eu/thalassa/animation.mp4
wget -O data/dataset.nc    https://static.techrad.eu/thalassa/dataset.nc
wget -O data/stations.csv  https://static.techrad.eu/thalassa/stations.csv
wget -O data/stations.zip  https://static.techrad.eu/thalassa/stations.zip
wget -O data/thalassa.png  https://static.techrad.eu/thalassa/thalassa.png
```

## Running Thalassa

### Conda or virtualenv

If you used conda or virtualenv, you can launch the Thalassa web server with:

```
pv serve --websocket-origin='localhost:9000' --port 9000
```

An image should open on your visit http://localhost:9000

### docker

If you build the docker image, execute:

```
docker/run.sh
```

This will start a webserver listening on port 61112. So visit: http://localhost:61112

**NOTE**: If you want to deploy this on a server, you will probably want to change the
`websocket-origin` in `docker/run.sh` to something more secure (e.g. to a subdomain).

## License
* The project is released under the EUPL v1.2 license.
