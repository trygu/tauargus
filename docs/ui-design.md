# UI Design — replacing the Java/Swing frontend

Status: **Option A is the shipped product. Option B (ANSI TUI) is a scoped,
ready-to-build design** on its own branch. The decision below unblocks Task 8
(evaluate-and-delete the Swing layer) either way.

## 1. Background

- The legacy product is a Java/Swing desktop app (`src/tauargus/gui/*`,
  `nbproject/`, SWIG bindings). Task 8 wants to delete it.
- Task 8 was **BLOCKED** on the assumption that an interactive frontend must
  replace Swing first. That assumption is dropped: **deleting Swing does not
  require a 1:1 replacement to exist yet.**
- The rewrite's *product* is a **headless `.arb` batch CLI**
  (`bindings/python/`, entry point `tauargus`). The `Engine`
  (`pytauargus.engine.Engine`) is a clean, importable Python library over the
  pybind11 native core, and `pytauargus.cli` already exposes the full verb
  surface. The TUI is a **thin presentation layer over that same library** —
  it does not reimplement any engine behavior.

## 2. Decision

Two viable end states. Picking one unblocks Task 8 either way.

### Option A — No UI (the shipped product, recommended default)

The product is the headless CLI + batch runner. Interactive needs (spec
authoring, table inspection, suppression tuning) are served by:
- the CLI verbs: `run`, `explore`, `specify`, `compute`, `suppress`, `round`,
  `apriori`, `audit`, `save`, `tables`, `version`;
- machine-readable outputs (CSV, INTERMEDIATE `.tab`, audit rows) that feed
  the example notebooks, spreadsheets, or dashboards;
- structured `logger` output for batch observability.

**Pros:** smallest surface, fastest to a releasable product, no new platform
risk, nothing to keep in sync with the engine.
**Cons:** non-technical users lose point-and-click; "what does this table look
like before I suppress?" is a CLI round-trip.

### Option B — Lightweight ANSI terminal UI

A TUI in the OpenCode terminal aesthetic: monospace, minimal chrome,
keyboard-driven, **panes not modal dialogs**. A thin interactive layer over the
`Engine` — not a rewrite.

**Library: `textual`** (decided). It is a pure-Python TUI framework with
widgets, panes, key handling, and live updates — the closest fit to the
OpenCode feel, and it ships a virtualized `DataTable` (so wide tables do not
break the terminal, the main risk with a home-rolled `rich` grid).
`rich` + `prompt_toolkit` is the fallback if we want fewer moving parts, but
it forces us to hand-wire pane layout and focus; `textual` gives that for free.

**Distribution: its own PyPI package, `pytauargus-tui`** (decided). It is a
separate project — its own `pyproject.toml`, version, wheel, and release
cadence — but **lives in this monorepo** (`bindings/tui/`, sibling to
`bindings/python/`) and is developed on its **own branch** while in flight, so:
- the core `pytauargus` wheel stays minimal — `textual` is never a dependency
  of it (no extra, no subcommand in the core `tauargus` CLI);
- the TUI can move (features, breaking UI changes) without bumping the engine
  release;
- `pip install pytauargus-tui` pulls `pytauargus>=<min>` (the native engine +
  CLI) as its only engine dependency.

- Console script: `tauargus-tui` (distinct from the core `tauargus` CLI).
- Depends on: `pytauargus>=0.2.1`, `textual>=0.50`.
- Release: its own tag scheme (e.g. `tui-v*`) + wheel; can reuse the existing
  `wheels.yml` pattern once the layout is proven.

### B.1 Layout

```
┌ tables & vars ┬──────────────────────── grid ────────────────────────┐
│ 1 REGION|CA ▸ │ REGION\CA  R1    R2    R3    TOTAL                   │
│ 2 SEXE  |CA   │  R1        S     U     S     S                       │
│ 3 AGE   |CA   │  R2        U     S     U     U                       │
│             │  R3        S     S     S     S                         │
│ [vars]      │  TOTAL     S     U     S     S                         │
├──────────────┴───────────────────────────────────────────────────────┤
│ cell (R2, R3): value=12  status=U (unsafe_rule)  interval=[4, 30]    │
├──────────────────────────────────────────────────────────────────────┤
│ ▸ log: Computed 3 tables. / ▸ hint: s=suppress r=round a=audit o=save │
└──────────────────────────────────────────────────────────────────────┘
```

- **Left pane** — table navigator (one row per `specify_table`) + the
  explanatory/response vars and active safety rules for the selected table.
- **Center pane** — the computed table as a `DataTable`: rows = one
  explanatory var's codes, columns = the others; each cell shows the value and
  is colored by status category.
- **Detail pane** (bottom) — the selected cell's value, full status name, and
  — when the table has been audited — its realized feasibility interval.
- **Log/status line** (bottom) — the engine's `logger` stream + a one-line
  keymap hint.

Status color = the `_status_symbol` category from `pytauargus.engine`
(`S` safe=green, `U` unsafe=red, `P` protect_manual=cyan, `M`
secondary_unsafe=yellow, `E` empty=dim). Full status names come from
`pytauargus.cli._STATUS_NAMES` (1–14).

### B.2 Feature → API map

Every action is a call the CLI already makes — the TUI adds no engine code.

| Pane / action | Real `pytauargus` surface |
|---------------|---------------------------|
| Open data | `open_microdata(data_file, Metadata)` (or `run_batch(arb)` for a ready batch) |
| Table navigator | `eng._n_tables`, `eng._tables[i]` (`spec.exp_vars`, `spec.resp_var`, safety rules) |
| Grid cell value + status | `eng._tau.get_table_cell(tab, dim, 0)` → `res[1]`=value, `res[10]`=status; size via `get_total_table_size`, bounds via `get_minimum_cell_value` |
| Detail: feasibility interval | `eng.audit(tab)` → rows `{cell,min,max,value,status,unsafe}` |
| Suppress / round | `eng.suppress(Suppress(kind="OPT"/"MOD"/"RND", tab_no=…, rnd_base=eng._min_round_base(tab)))` |
| Apriori | `eng.apply_apriori(Apriory(…))` |
| Save / export | `eng.write_table(WriteTable(…))`, `eng.write_intermediate_table(tab, path, with_audit=True)` |
| Emit a new `.arb` | the generator (`pytauargus.arb.micro_arb`) — the spec editor writes the same file `run_batch` reads |

### B.3 The protect/round "preview before committing"

The engine is **stateful and has no in-place undo** — `run_batch` / compute
is the unit of action, and `suppress` mutates the running tables. So the
"preview" is **not** a tentative in-place edit; it is a **fresh run and a
diff**, which is exactly what the CLI and notebook 02 already do:

1. Hold the current `.arb` (the spec).
2. On "preview OPT/MOD/RND on table N": run a **throwaway** `run_batch` of the
   same `.arb` with the suppression appended, and compute the per-status
   counts before (no suppression) and after.
3. Show the delta table (e.g. `safe 104→101`, `unsafe_rule 1→1`,
   `secondary_unsafe 0→3`) — the same invariant the smoke tests assert.
4. On confirm: adopt that run as the working state (its tables become the
   grid) and/or write outputs. Nothing is lost because any `.arb` can be
   re-run to reset.

This keeps the TUI honest about the engine's real capabilities instead of
promising an undo it does not have.

### B.4 State model

- One `Engine` per open session; the TUI is a view over it.
- The grid caches per-table cell values after compute; recompute on any spec
  change (new var, new rule, method choice).
- The spec is always materialized as a `.arb` (the spec editor edits and
  re-writes it), so "commit" = write outputs, and "reset" = re-run the `.arb`.
- No UI state is persisted; relaunch reloads from files.

### B.5 Non-goals

- No new solver or batch-parser logic; no native code touched.
- No GUI/desktop stack; terminal-only.
- No multi-document / project session files.
- No 1:1 recreation of the Swing screens — only the workflow the CLI covers.

## 3. Recommendation

1. **Ship the product as Option A.** The headless CLI is the complete
   product; do not gate it on a UI.
2. **Build Option B as a dedicated task on its own branch, shipped as its own
   PyPI package `pytauargus-tui`** *after* the engine features (apriori/cover)
   and packaging are stable, so the UI sits on a quiet base. It is now fully
   specified above (library = `textual`, layout, keymap, feature→API map,
   preview semantics) and is ready to implement.
3. **Unblock Task 8 now.** Swing does not need a 1:1 replacement to be
   deleted. If the team wants a UI, Option B is it; if not, delete Swing
   outright and revisit B later.

## 4. Split-out requirement (Option B)

The UI is **its own task, its own branch, and its own PyPI package**
(`pytauargus-tui`), independent of the native engine port and of core
packaging:
- Branch: `feat/ansi-ui` (in this monorepo); source lives in `bindings/tui/`.
- Distribution: `pytauargus-tui` — its own `pyproject.toml`/version/**wheel**;
  depends on `pytauargus>=<min>` + `textual`; console script `tauargus-tui`.
- Does not touch: `engine/native/*`, the batch parser, or solver backends.
  The core `pytauargus` wheel and CLI are unchanged by the TUI.
- Acceptance: drives a real `.arb` end-to-end in the terminal —
  specify → compute → preview suppress/round → save — and produces the same
  outputs and the same status-count deltas as the CLI and the smoke tests.

Task 8 (delete `src/`, `nbproject/`, SWIG) is blocked on **this decision**,
not on the TUI being built.
