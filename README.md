Thalassa
========

[![Documentation Status](https://readthedocs.org/projects/thalassa/badge/?version=latest)](https://thalassa.readthedocs.io/en/latest/?badge=latest) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/ec-jrc/Thalassa) ![CI](https://github.com/ec-jrc/Thalassa/actions/workflows/run_tests.yml/badge.svg)[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ec-jrc/Thalassa/master?urlpath=lab)

Thalassa is a library for visualizing unstructured mesh data with a focus on large scale sea level data

It builds upon [geoviews](https://geoviews.org/) and [datashader](https://datashader.org/)
and can easily handle meshes with millions of nodes interactively.

<!-- https://user-images.githubusercontent.com/411196/146007390-88e8cc59-9ae9-4a15-83fd-f7f1f2d724c2.mp4 -->

Thalassa is currently supporting visualization of the output of the following solvers:

- [Schism](https://github.com/schism-dev/schism)
- [ADCIRC](https://adcirc.org/)

Adding support for new solvers is relatively straight-forward.

## Installation

### PyPI

1. Install the binary dependencies:

- `python >= 3.9`

2. Install from PyPI with:

```
pip install thalassa
```

### Conda

You can also install using conda/mamba:

```bash
mamba install -y -c conda-forge thalassa
```

## Obtaining Data

You will need some data to visualize. You can download sample datasets from the following links:

- 2D Output from the [STOFS-2D Global]() model which uses ADCIRC from [here](https://noaa-gestofs-pds.s3.amazonaws.com/stofs_2d_glo.20230501/stofs_2d_glo.t00z.fields.cwl.nc) (12GB)
- 3D Output from the [STOFS-3D Atlantic](https://noaa-nos-stofs3d-pds.s3.amazonaws.com/README.html) model which uses Schism 5.9 (old IO) from [here](https://noaa-nos-stofs3d-pds.s3.amazonaws.com/STOFS-3D-Atl-shadow-VIMS/20220430/schout_20220501.nc) (12GB)
- 2D Output from the [STOFS-3D Atlantic](https://noaa-nos-stofs3d-pds.s3.amazonaws.com/README.html) model which uses Schism 5.10 (new IO) from [here](https://noaa-nos-stofs3d-pds.s3.amazonaws.com/STOFS-3D-Atl/stofs_3d_atl.20230501/stofs_3d_atl.t12z.fields.out2d_nowcast.nc) (3GB)

## Thalassa-server

[thalassa-server](https://github.com/oceanmodeling/thalassa-server) is an web-application leveraging the `thalassa` library
and [panel](https://panel.holoviz.org/). Check-it out!

## Developing

### Prerequisites

For developing we are using [poetry](https://pre-commit.com/) and [pre-commit](https://pre-commit.com/).
You can install both with [pipx](https://github.com/pypa/pipx):

```
# poetry
pipx install poetry
pipx inject poetry poetry-dynamic-versioning
pipx inject poetry poetry-plugin-export
# pre-commit
pipx install pre-commit
```

### Install dependencies

Just run:

```
make init
```

## License

The project is released under the EUPL v1.2 license which is compatible with GPL v3
