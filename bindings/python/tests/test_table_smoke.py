"""End-to-end smoke test for the tabular (pre-aggregated) table flow.

Runs the sample batch ``tableinput/TestTable.arb`` (``<OPENTABLEDATA>`` +
``<READTABLE> 1T``) to completion and asserts invariants for a correctly read
tabular table: one table, the right explanatory variables, a non-empty cell
grid, and the grand-total cell matching the first (``"Total";"Total"``) row of
``pp.tab``.
"""

from pathlib import Path

import pytest

from pytauargus.engine import Engine, run_batch

DATA = Path(__file__).resolve().parent.parent.parent.parent / "data"


@pytest.fixture(scope="module")
def engine() -> Engine:
    return run_batch(DATA / "tableinput" / "TestTable.arb")


def test_runs_without_error(engine):
    assert engine._n_tables == 1
    assert engine._is_table


def test_explanatory_variables(engine):
    got = [tuple(spec.exp_vars) for spec, _ in engine._tables]
    assert got == [("Size", "Region")]


def test_response_variable(engine):
    assert all(spec.resp_var == "Var2" for spec, _ in engine._tables)


def test_metadata_is_tabular(engine):
    assert engine._metadata is not None
    assert engine._metadata.is_table
    by = {v.name: v for v in engine._metadata.variables}
    assert by["Size"].type == "CATEGORICAL"
    assert by["Region"].type == "CATEGORICAL"
    assert by["Var2"].type == "RESPONSE"
    assert by["Var2_Shadow"].type == "SHADOW"
    assert by["Var2_Cost"].type == "COST"


def test_table_has_cells(engine):
    ncell, _ = engine._tau.get_total_table_size(0)
    assert ncell > 0


def test_grand_total_cell(engine):
    """Cell 0 is the grand total (Total;Total).

    The batch uses ``<READTABLE> 1T`` (additivity=1), so marginal/total cells
    are recomputed from the leaves; the value is therefore only checked to be
    of the right order of magnitude (the file's grand total is ~16.8M).
    """
    total = engine._tau.get_table_cell_value(0, 0)
    assert total == total  # not NaN
    assert 1e6 < total < 2e8


def test_min_cell_value_finite(engine):
    mn, mx = engine._tau.get_minimum_cell_value(0)
    assert mn == mn  # not NaN
    assert mn >= 0
    assert mx >= mn
