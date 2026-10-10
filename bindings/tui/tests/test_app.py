"""TUI app tests (headless, via textual's Pilot).

Drive the real app against ``data/TestRecode.arb``: load, navigator,
grid shape, cell detail, table switching, and the action keys.
"""

import time
from pathlib import Path

import pytest
from textual.widgets import DataTable, ListView

from pytauargus_tui.app import TauArgusApp

DATA = Path(__file__).resolve().parent.parent.parent.parent / "data"
ARB = DATA / "TestRecode.arb"


async def wait_for(pilot, pred, timeout=30.0, what="condition"):
    deadline = time.monotonic() + timeout
    while not pred():
        if time.monotonic() > deadline:
            raise AssertionError(f"timed out waiting for {what}")
        await pilot.pause()


@pytest.fixture
def app() -> TauArgusApp:
    return TauArgusApp(ARB)


def grid(app) -> DataTable:
    return app.query_one("#grid", DataTable)


async def test_app_loads_batch(app):
    async with app.run_test(size=(120, 35)) as pilot:
        await wait_for(pilot, lambda: app.session is not None, what="session load")
        assert app.session.n_tables == 2
        nav = app.query_one("#nav", ListView)
        await wait_for(pilot, lambda: len(nav.children) == 2, what="nav rows")
        # Table 0 = Size(7 rows) x Region(18 cols) + 1 label column.
        await wait_for(pilot, lambda: grid(app).row_count == 7, what="grid")
        assert len(grid(app).columns) == 19
        assert app.current_table == 0


async def test_grid_cell_status_colors(app):
    async with app.run_test(size=(120, 35)) as pilot:
        await wait_for(pilot, lambda: app.session is not None)
        await wait_for(pilot, lambda: grid(app).row_count == 7, what="grid")
        # Every data cell is a rich Text with a style (status colour).
        from rich.text import Text

        ncols = len(grid(app).columns)
        for r in range(grid(app).row_count):
            for c in range(1, ncols):
                val = grid(app).get_cell(f"r{r}", f"c{c - 1}")
                assert isinstance(val, Text)
                assert val.style in ("green", "red", "cyan", "yellow", "dim")


async def test_table_switch_jk(app):
    async with app.run_test(size=(120, 35)) as pilot:
        await wait_for(pilot, lambda: app.session is not None)
        await wait_for(pilot, lambda: grid(app).row_count == 7, what="grid")
        await pilot.press("j")
        assert app.current_table == 1
        # Table 1 = Region(18 rows) x IndustryCode(707 cols) + label column.
        await wait_for(pilot, lambda: grid(app).row_count == 18, what="grid 1")
        assert len(grid(app).columns) == 708
        await pilot.press("k")
        assert app.current_table == 0
        await wait_for(pilot, lambda: grid(app).row_count == 7, what="grid 0")


async def test_cell_detail(app):
    async with app.run_test(size=(120, 35)) as pilot:
        await wait_for(pilot, lambda: app.session is not None)
        await wait_for(pilot, lambda: grid(app).row_count == 7, what="grid")
        g = grid(app)
        g.move_cursor(row=1, column=2)
        await wait_for(
            pilot,
            lambda: "value=" in app.detail_text and "status=" in app.detail_text,
            what="cell detail",
        )
        assert "cell (" in app.detail_text


async def test_suppress_action_logs(app):
    async with app.run_test(size=(120, 35)) as pilot:
        await wait_for(pilot, lambda: app.session is not None)
        await wait_for(pilot, lambda: grid(app).row_count == 7, what="grid")
        await pilot.press("s")
        await wait_for(pilot, lambda: "OPT applied" in app.log_text, what="OPT log")
        # Grid is rebuilt after the action (same shape for this all-safe table).
        assert grid(app).row_count == 7


async def test_save_action_writes_tab(app, tmp_path):
    # Point the app at a copy of the batch so `out/` lands in tmp_path.
    import shutil

    arb = tmp_path / "TestRecode.arb"
    shutil.copy(ARB, arb)
    # The batch references data files relative to the arb's directory.
    for f in ("tau_testW.asc", "tau_testW.rda", "GK.grc", "IndCode2.grc",
              "region2.hrc"):
        shutil.copy(DATA / f, tmp_path / f)
    app = TauArgusApp(arb)
    async with app.run_test(size=(120, 35)) as pilot:
        await wait_for(pilot, lambda: app.session is not None, what="load")
        await wait_for(pilot, lambda: grid(app).row_count == 7, what="grid")
        await pilot.press("o")
        await wait_for(pilot, lambda: app.log_text.startswith("saved "),
                       what="save log")
        out = tmp_path / "out" / "table_1.tab"
        assert out.is_file()
        content = out.read_text()
        assert len(content.splitlines()) > 7
