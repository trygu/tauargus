"""View-model tests for the TUI.

These encode the legacy contract the TUI reads from the engine: the same
tables, codes, cell values and status symbols the CLI and notebooks already
produce for ``TestRecode.arb``. The model layer must expose them as plain
Python so the textual widgets never touch the native bindings directly.
"""

from pathlib import Path

import pytest

from pytauargus_tui.model import Session

DATA = Path(__file__).resolve().parent.parent.parent.parent / "data"
ARB = DATA / "TestRecode.arb"


@pytest.fixture(scope="module")
def session() -> Session:
    return Session.from_arb(ARB)


def test_table_count(session):
    assert session.n_tables == 2


def test_table_meta(session):
    t0 = session.table(0)
    assert t0.exp_vars == ("Size", "Region")
    assert t0.resp_var == "Var2"
    assert t0.n_cells == 126
    t1 = session.table(1)
    assert t1.exp_vars == ("Region", "IndustryCode")
    assert t1.n_cells == 12726


def test_grid_shape(session):
    g = session.grid(0)
    assert g.row_var == "Size"
    assert g.col_var == "Region"
    assert len(g.rows) == 7
    assert len(g.cols) == 18
    assert len(g.cells) == 7
    assert all(len(row) == 18 for row in g.cells)


def test_grid_cell_values(session):
    g = session.grid(0)
    # Every populated cell has an int status in the known range and a float value.
    for row in g.cells:
        for cell in row:
            assert isinstance(cell.status, int)
            assert 1 <= cell.status <= 14
            assert isinstance(cell.value, float)
            assert cell.symbol in ("S", "U", "P", "M", "E", "?")


def test_grid_total_cell_count(session):
    g = session.grid(0)
    assert sum(len(row) for row in g.cells) == g.tab.n_cells


def test_status_names(session):
    g = session.grid(0)
    # The pre-suppression sample batch is fully safe, so the first cell is safe.
    assert g.cells[0][0].status_name in ("safe", "safe_manual")


def test_rule_display(session):
    t0 = session.table(0)
    # The batch declares NK(2,75) for table 1 (0-based index 0).
    assert any("NK" in r and "2" in r and "75" in r for r in t0.rules)
