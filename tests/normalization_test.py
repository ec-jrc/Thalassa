from __future__ import annotations

import pytest
import xarray as xr

from . import DATA_DIR
from thalassa import api
from thalassa import normalization
from thalassa.normalization import THALASSA_FORMATS

@pytest.mark.parametrize(
    "ds,expected_fmt",
    [
        pytest.param(api.open_dataset(DATA_DIR / "fort.63.nc", normalize=False), THALASSA_FORMATS.ADCIRC, id="ADCIRC"),
        pytest.param(api.open_dataset(DATA_DIR / "iceland.slf", normalize=False), THALASSA_FORMATS.TELEMAC, id="TELEMAC"),
        pytest.param(xr.Dataset(), THALASSA_FORMATS.UNKNOWN, id="Unknown"),
    ],
)
def test_infer_format(ds, expected_fmt):
    fmt = normalization.infer_format(ds)
    assert fmt == expected_fmt


@pytest.mark.parametrize(
    "path,expected",
    [
        pytest.param(DATA_DIR / "fort.63.nc", True, id="ADCIRC"),
        pytest.param(DATA_DIR / "iceland.slf", True, id="TELEMAC"),
        pytest.param(__file__, False, id="Unknown"),
    ],
)
def test_can_be_inferred(path, expected):
    result = normalization.can_be_inferred(path)
    assert result == expected
