"""Pytest bootstrap: make the `src/` package importable without a wheel build.

The native extension (``_tauargus``) is built into ``src/tauargus/`` by
``cmake --build``; putting ``src`` on ``sys.path`` lets ``import tauargus``
find both the Python sources and the compiled module.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
