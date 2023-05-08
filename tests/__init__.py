from __future__ import annotations

import pathlib

# specify package paths
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
TEST_DIR = ROOT_DIR / "tests"
DATA_DIR = TEST_DIR / "data"
