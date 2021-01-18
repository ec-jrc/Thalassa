import pathlib


_CURRENT_FILE  = pathlib.Path(__file__).expanduser().resolve()
PACKAGE = _CURRENT_FILE.parent
REPO = PACKAGE.parent
TEMPLATES = PACKAGE / "templates"

