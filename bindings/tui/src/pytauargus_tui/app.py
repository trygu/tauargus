r"""tauargus-tui — Textual terminal UI over the pytauargus engine.

Design: ``docs/ui-design.md`` (Option B). The app is a thin view over one
``pytauargus`` Engine (via the :mod:`pytauargus_tui.model` view-model); every
action calls the same Python API the headless CLI uses, and the TUI
re-implements no engine behaviour.

Layout (design §B.1)::

    ┌ tables & vars ┬──────────────────────── grid ────────────────────────┐
    │ 1 SIZE|REGION ▸│ SIZE\REGION  R1    R2    R3    TOTAL                 │
    │ 2 REG|IND      │  R1        S     U     S     S                       │
    ├───────────────┴───────────────────────────────────────────────────────┤
    │ cell (R2, R3): value=12  status=U (unsafe_rule)  interval=[4, 30]     │
    ├───────────────────────────────────────────────────────────────────────┤
    │ ▸ log: table 1: 126 cells   ▸ hint: j/k=table s=suppress r=round ...  │
    └───────────────────────────────────────────────────────────────────────┘

Keymap: ``j``/``k`` or the navigator select a table; ``s``=OPT suppress,
``r``=RND round, ``a``=audit, ``o``=save intermediate ``.tab``, ``q``=quit.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Label, ListView, Static
from textual.widgets._list_view import ListItem
from textual.worker import WorkerState

from .model import Cell, Session, TableGrid, TableMeta

# Status symbol → colour (design §B.1).
_STATUS_COLOR = {
    "S": "green",
    "U": "red",
    "P": "cyan",
    "M": "yellow",
    "E": "dim",
    "?": "default",
}

_HINT = "j/k=table  s=suppress  r=round  a=audit  o=save  q=quit"


def _fmt(value: float) -> str:
    """Compact number for terminal display (ints without a decimal point)."""
    if value == int(value):
        return str(int(value))
    return f"{value:.2f}"


class _EngineLogHandler(logging.Handler):
    """Forward the pytauargus engine log stream into the TUI status line."""

    def __init__(self, app: "TauArgusApp") -> None:
        super().__init__()
        self._app = app

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._app.call_from_thread(self._app.push_log, msg)
        except Exception:
            pass


class TauArgusApp(App):
    """Tau-Argus TUI: navigator + grid + detail + log over one Engine."""

    TITLE = "tau-argus"
    CSS = """
    Screen { layout: vertical; }
    #body { layout: horizontal; height: 1fr; }
    #nav { width: 30; border: round $primary; }
    #grid { width: 1fr; border: round $primary; }
    #detail { height: 3; border: round $primary; }
    #logline { height: 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j", "table_next", "Next table"),
        Binding("k", "table_prev", "Prev table"),
        Binding("s", "suppress", "Suppress (OPT)"),
        Binding("r", "round", "Round (RND)"),
        Binding("a", "audit", "Audit"),
        Binding("o", "save", "Save .tab"),
    ]

    def __init__(self, arb_path: Path) -> None:
        super().__init__()
        self._arb = Path(arb_path)
        self._session: Optional[Session] = None
        self._tab: int = 0
        self._grid: Optional[TableGrid] = None
        self._detail = ""
        self._log = "ready"
        self._log_handler: Optional[_EngineLogHandler] = None

    # -- inspection surface (used by tests / embedders) ----------------------
    @property
    def session(self) -> Optional[Session]:
        return self._session

    @property
    def current_table(self) -> int:
        return self._tab

    @property
    def detail_text(self) -> str:
        return self._detail

    @property
    def log_text(self) -> str:
        return self._log

    # -- compose ---------------------------------------------------------------
    def compose(self) -> ComposeResult:
        with Horizontal(id="body"):
            yield ListView(id="nav")
            yield DataTable(id="grid", cursor_type="cell")
        yield Static("", id="detail")
        yield Static("", id="logline")
        yield Footer()

    # -- lifecycle ---------------------------------------------------------------
    def on_mount(self) -> None:
        self._log_handler = _EngineLogHandler(self)
        self._log_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger("pytauargus").addHandler(self._log_handler)
        self._set_log(f"loading {self._arb.name} ...")
        self.run_worker(self._load, group="engine", exclusive=True, thread=True,
                        description="load")

    def on_unmount(self) -> None:
        if self._log_handler is not None:
            logging.getLogger("pytauargus").removeHandler(self._log_handler)
            self._log_handler = None

    def _load(self) -> Session:
        return Session.from_arb(self._arb)

    # -- worker events --------------------------------------------------------------
    def on_worker_state_changed(self, event) -> None:
        w = event.worker
        if w.group != "engine":
            return
        if w.state is WorkerState.SUCCESS:
            if w.description == "load":
                self._session = w.result
                self._populate_nav()
                self._set_log(f"loaded {self._session.n_tables} table(s)")
                self._select_table(0)
            elif w.description == "grid":
                self._grid = w.result
                self._populate_grid()
                self._set_log(f"table {self._tab + 1}: {self._grid.tab.n_cells} cells")
            elif w.description == "action":
                self._grid = self._session.grid(self._tab)
                self._populate_grid()
                self._set_log(w.result)
        elif w.state is WorkerState.ERROR:
            self._set_log(f"error: {w.error}")

    # -- navigator --------------------------------------------------------------------
    def _populate_nav(self) -> None:
        nav = self.query_one("#nav", ListView)
        for i, t in enumerate(self._session.tables()):
            label = f"{i + 1}  {'|'.join(t.exp_vars)} | {t.resp_var}"
            nav.append(ListItem(Label(label)))

    def on_list_view_selected(self, event) -> None:
        self._select_table(event.index)

    def action_table_next(self) -> None:
        if self._session is not None and self._tab < self._session.n_tables - 1:
            self._select_table(self._tab + 1)

    def action_table_prev(self) -> None:
        if self._session is not None and self._tab > 0:
            self._select_table(self._tab - 1)

    def _select_table(self, i: int) -> None:
        self._tab = i
        meta = self._session.table(i)
        self.query_one("#grid", DataTable).clear(columns=True)
        self._set_detail(self._table_detail(meta))
        self._set_log(f"table {i + 1}: loading grid ...")
        self.run_worker(lambda: self._session.grid(i), group="engine",
                        exclusive=True, thread=True, description="grid")

    # -- grid --------------------------------------------------------------------------
    @staticmethod
    def _cell_text(cell: Cell) -> Text:
        color = _STATUS_COLOR.get(cell.symbol, "default")
        return Text(_fmt(cell.value), style=color)

    def _populate_grid(self) -> None:
        g = self._grid
        if g is None:
            return
        grid = self.query_one("#grid", DataTable)
        grid.clear(columns=True)
        header = f"{g.row_var}\\{g.col_var}" if g.col_var else g.row_var
        grid.add_column(header, key="rl")
        if g.col_var is not None:
            for ci in range(len(g.cols)):
                grid.add_column(g.cols[ci], key=f"c{ci}")
        else:
            grid.add_column(g.tab.resp_var, key="c0")
        for ri, row in enumerate(g.cells):
            values: List[object] = [Text(g.rows[ri], style="bold")]
            values.extend(self._cell_text(c) for c in row)
            grid.add_row(*values, key=f"r{ri}")
        grid.move_cursor(row=0, column=1)

    def on_data_table_cell_selected(self, event) -> None:
        self._on_cell_coordinate(event.coordinate)

    def on_data_table_cell_highlighted(self, event) -> None:
        # Follow the cursor (hover / keyboard) so the detail pane stays live.
        self._on_cell_coordinate(event.coordinate)

    def _on_cell_coordinate(self, coordinate) -> None:
        if self._grid is None:
            return
        r, c = coordinate.row, coordinate.column
        if r < 0 or r >= len(self._grid.cells):
            return
        row = self._grid.cells[r]
        if c < 1 or c - 1 >= len(row):
            return
        self._set_cell_detail(r, c - 1)

    # -- detail pane -----------------------------------------------------------------------
    def _table_detail(self, meta: TableMeta) -> str:
        rules = " ".join(meta.rules) if meta.rules else "no safety rules"
        return (f"table {meta.index + 1}: {' | '.join(meta.exp_vars)} | "
                f"{meta.resp_var}   {meta.n_cells} cells  {rules}")

    def _set_cell_detail(self, r: int, c: int) -> None:
        g = self._grid
        cell = g.cells[r][c]
        pos = f"({g.rows[r]}"
        if g.col_var is not None:
            pos += f", {g.cols[c]}"
        pos += ")"
        text = (f"cell {pos}: value={_fmt(cell.value)}  "
                f"status={cell.symbol} ({cell.status_name})")
        # Realised feasibility interval, when this table has been audited
        # (row-major cell index matches the audit row's ``cell`` key).
        n_cols = len(g.cols) if g.col_var is not None else 1
        idx = r * n_cols + c
        for row in self._session.audit_rows(g.tab.index):
            if row.get("cell") == idx:
                text += f"  interval=[{_fmt(row['min'])}, {_fmt(row['max'])}]"
                break
        self._set_detail(text)

    # -- actions ---------------------------------------------------------------------------
    def action_suppress(self) -> None:
        self._run_action("OPT")

    def action_round(self) -> None:
        self._run_action("RND")

    def action_audit(self) -> None:
        self._run_action("AUDIT")

    def action_save(self) -> None:
        self._run_action("SAVE")

    def _run_action(self, what: str) -> None:
        if self._session is None:
            return
        self._set_log(f"table {self._tab + 1}: {what.lower()} ...")
        self.run_worker(lambda: self._action(what), group="engine",
                        exclusive=True, thread=True, description="action")

    def _action(self, what: str) -> str:
        from pytauargus.batch import Suppress

        s = self._session
        tab = self._tab
        if what == "OPT":
            s.suppress(Suppress(kind="OPT", tab_no=tab + 1))
            return f"table {tab + 1}: OPT applied"
        if what == "RND":
            base = s.engine._min_round_base(tab)
            s.suppress(Suppress(kind="RND", tab_no=tab + 1, rnd_base=base))
            return f"table {tab + 1}: rounded (base {base})"
        if what == "AUDIT":
            rows = s.audit(tab)
            return f"table {tab + 1}: audited {len(rows)} cell(s)"
        if what == "SAVE":
            out_dir = self._arb.parent / "out"
            out_dir.mkdir(exist_ok=True)
            path = out_dir / f"table_{tab + 1}.tab"
            s.write_intermediate_table(tab, str(path),
                                       with_audit=bool(s.audit_rows(tab)))
            return f"saved {path}"
        raise ValueError(what)

    # -- status line --------------------------------------------------------------------------
    def _set_detail(self, text: str) -> None:
        self._detail = text
        self.query_one("#detail", Static).update(text)

    def _set_log(self, text: str) -> None:
        self._log = text
        self.query_one("#logline", Static).update(
            f"▸ log: {text}   ▸ hint: {_HINT}")

    def push_log(self, msg: str) -> None:
        self._set_log(msg)


def main(argv: Optional[List[str]] = None) -> int:
    """Console entry point: ``tauargus-tui <batch.arb>``."""
    p = argparse.ArgumentParser(
        prog="tauargus-tui",
        description="Tau-Argus terminal UI over the pytauargus engine")
    p.add_argument("arb", help="path to a .arb batch file")
    args = p.parse_args(argv)
    app = TauArgusApp(Path(args.arb))
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
