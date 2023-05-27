Thalassa
========

<style>body {text-align: justify}</style>

[![Documentation Status](https://readthedocs.org/projects/thalassa/badge/?version=latest)](https://thalassa.readthedocs.io/en/latest/?badge=latest) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/ec-jrc/Thalassa) ![CI](https://github.com/ec-jrc/Thalassa/actions/workflows/run_tests.yml/badge.svg)[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ec-jrc/Thalassa/master?urlpath=lab)

Thalassa ia a library for visualizing unstructured mesh data.

It builds upon [geoviews](https://geoviews.org/) and [datashader](https://datashader.org/)
and can easily handle meshes with millions of nodes interactively.

<!-- https://user-images.githubusercontent.com/411196/146007390-88e8cc59-9ae9-4a15-83fd-f7f1f2d724c2.mp4 -->

Thalassa is currently supporting visualization of the output of the following solvers:

- [Schism](https://github.com/schism-dev/schism)
- [ADCIRC](https://adcirc.org/)

Adding support for new solvers is relatively straight-forward.

## Thalassa-server

[thalassa-server](https://github.com/oceanmodeling/thalassa-server) is an web-application leveraging the `thalassa` library
and [panel](https://panel.holoviz.org/). Check-it out!

## License

The project is released under the EUPL v1.2 license which is compatible with GPL v3
