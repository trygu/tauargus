# Tau-Argus Rewrite — Progress

Branches: `master` (mainline, 0.3.0) + `tui` (TUI). Goal: HiGHS solvers,
portable cloud-native build, headless Python CLI.

## Verified checkpoints (details in ARCHIVE.md)
- [x] Core: WRITETABLE type-5, apriori, MOD/OPT/RND, audit (Intervalle).
- [x] Task 4 headless CLI; rename to `pytauargus`; self-contained wheel +
  CI → GH Release + PyPI + GHCR. **Release 0.2.0**; example notebooks.
- [x] **High-level API — DataFrame `protect()`** (2026-10-10, PR #5) →
  **Release 0.3.0** on PyPI (wheels cp310–cp313; no cp314 yet).

## In flight — TUI (branch `tui`, `bindings/tui/`, pkg `pytauargus-tui`)
- [x] Skeleton + `model.py` view-model (TDD): `Session` wraps one Engine;
  `table()/grid()` expose exp/resp/rules + per-cell value+status via the
  Python API only (`get_table_cell`, `get_var_code`, `_status_symbol`).
- [x] `app.py` Textual app (textual 8.x): navigator + grid (status colours) +
  cell detail (value/status/interval) + log line; j/k table switch; s=OPT,
  r=RND, a=audit, o=save `.tab`. 13 tests green (7 model + 6 Pilot).
- [ ] Next: preview-delta for suppress/round (fresh run + status-count diff,
  design §B.3); spec editing / `.arb` emission; own tag scheme `tui-v*`.
- Dev: `bindings/tui/.venv` (py3.13) on the released `pytauargus==0.3.0`
  wheel; `.venv/bin/python -m pytest`.
- Note: `pytauargus.__init__.__version__` is stale (0.2.1) in the 0.3.0 tree.

## Next (priority order, non-TUI)
1. **GHCR rename** — 0.2.1 verified on `ghcr.io/trygu/tauargus-engine`;
   delete old `trygu/tauargus` package.
2. **Top-level project rename** (repo/package naming) — decide + execute.
3. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.

## Watch items
- OPT/MOD deadline expiry needs separate coverage; positive limits pass.
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Parquet as the microdata dataframe backend (not started).
- Ref: `piargus` (`references/piargus`, transient) — compare API/flow, drop after.
