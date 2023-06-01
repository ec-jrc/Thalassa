<style>body {text-align: justify}</style>

### PyPI

1. Install the binary dependencies:

    - `python >= 3.9`
    - `geos`

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
