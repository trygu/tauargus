"""Pytest bootstrap: make the `src/` package importable without a wheel build.

The native extension (``_tauargus``) is built into ``src/tauargus/`` by
``cmake --build``; putting ``src`` on ``sys.path`` lets ``import pytauargus``
find both the Python sources and the compiled module.
"""

import sys
from pathlib import Path

import pytest

from pytauargus.engine import Engine, run_batch

SRC = Path(__file__).resolve().parent.parent / "src"
DATA = Path(__file__).resolve().parent.parent.parent / "data"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(scope="module")
def engine() -> Engine:
    """Computed tables from TestRecode.arb (pre-suppression)."""
    return run_batch(DATA / "TestRecode.arb")
