# UI Design Consideration — replacing the Java/Swing frontend

Status: **open design decision**. This doc is a consideration, not a committed
plan. The conclusion should be made explicit before any UI code is written, and
the UI work must be **split out as its own task / branch** regardless of
outcome (see end).

## 1. Background

- The legacy product is a Java/Swing desktop app (`src/tauargus/gui/*`,
  `nbproject/`, SWIG bindings). Task 8 wants to delete it.
- Task 8 is currently **BLOCKED** on the assumption that some interactive
  frontend must replace Swing before the Java layer can go.
- The rewrite's *product* is a **headless `.arb` batch CLI**
  (`python/`, `tau-argus` entry point). The `Engine` is already a clean,
  importable Python library over the pybind11 native core.

## 2. Decision point

There are two viable end states. Picking one unblocks Task 8 either way.

### Option A — No UI (default / recommended starting stance)

The product is the headless CLI + batch runner. Interactive needs (spec
authoring, table inspection, suppression tuning) are served by:
- the existing CLI verbs (`explore`, `specify`, `audit`, `tables`, `save`,
  `suppress`, `round`),
- machine-readable outputs (CSV / cell-records / INTERMEDIATE `.tab`) that feed
  notebooks, spreadsheets, or downstream dashboards,
- structured logging (`logger`) for batch observability.

**Pros:** smallest surface, fastest to a releasable product, no new platform
risk, nothing to keep in sync with the engine.
**Cons:** non-technical users lose the point-and-click workflow; exploratory
"what does this table look like before I suppress?" is a round-trip through the
CLI.

### Option B — Lightweight ANSI terminal UI

A TUI in the spirit of the OpenCode review/terminal aesthetic: monospace,
minimal chrome, keyboard-driven, panels/panes rather than modal dialogs. It
would be a **thin interactive layer over the same `Engine`** — not a rewrite:

- **Table browser** — render a computed table with per-cell status symbols
  (reuse `_status_symbol`), highlight unsafe/secondary cells.
- **Spec editor** — pick exp/response vars, safety rules; emit `.arb`.
- **Suppress/round workflow** — pick a method, preview the status-count delta
  before committing (mirrors the invariants the smoke tests assert).
- **Live log pane** — stream the engine's `logger` output.

Library choice (to be decided in the UI task): `textual` (rich, async, modern
aesthetic — closest to the OpenCode feel) or a lighter `rich` +
`prompt_toolkit` composition. Both are pure-Python and ship in the same wheel.

**Pros:** recovers interactivity without a JVM/desktop stack; stays terminal-
native and CI-friendly; reuses the engine as-is.
**Cons:** real maintenance surface; must stay in lockstep with engine
capabilities; terminal UIs are hard for heavy data grids (wide tables).

## 3. Recommendation

1. **Ship the product as Option A first.** The headless CLI is complete enough
   to be the product; do not gate it on a UI.
2. **If interactivity is wanted, do it as a dedicated ANSI-TUI task** (Option B),
   built *after* the engine features (apriori/cover, packaging) are stable, so
   the UI has a solid, quiet base to sit on.
3. Either way, **unblock Task 8 now**: the Swing app does not need a 1:1
   replacement to be deleted. If the team wants a UI, Option B is the
   replacement; if not, delete Swing outright.

## 4. Split-out requirement

The UI is **its own task and its own branch**, independent of the native engine
port and of packaging:
- Branch: `feat/ansi-ui` (or a separate repo, if we prefer).
- Depends on: `tauargus` Python package (engine + pybind) as a library.
- Does not touch: `native/*`, the batch parser, or solver backends.
- Acceptance: drives a real `.arb` end-to-end (specify → compute → suppress →
  save) from the terminal, matching what the CLI does.

Task 8 (delete `src/`, `nbproject/`, SWIG) is blocked on *this* decision being
made — not on the UI being built.
