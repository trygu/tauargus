# Tau-Argus Rewrite — Progress

Branches: `master` (mainline, 0.3.0) + `tui` (TUI). Goal: HiGHS solvers, headless CLI.

## Verified checkpoints (details in ARCHIVE.md)
- [x] Core: WRITETABLE type-5, apriori, MOD/OPT/RND, audit (Intervalle).
- [x] Headless CLI; self-contained wheel + CI → PyPI + GHCR. Release 0.2.0;
  notebooks. DataFrame `protect()` (PR #5) → **Release 0.3.0** (cp310–cp313).

## In flight — TUI (branch `tui`, `bindings/tui/`, pkg `pytauargus-tui`)
- [x] `model.py` view-model + `app.py` Textual app (navigator, status-coloured
  grid, cell detail, log line; j/k tables, s=OPT, r=RND, a=audit, o=save).
  13 tests green; **human-verified in a real terminal** (2026-10-11).
- [ ] Next: (1) file-picker startup (no-arg, `FilePicker` for `*.arb`);
  (2) preview-delta for suppress/round (§B.3); (3) spec editing/`.arb` emit;
  own tag scheme `tui-v*`.
- Dev: py3.13 venv on the PyPI `pytauargus==0.3.0` wheel. Note:
  `pytauargus.__init__.__version__` is stale (0.2.1) in the 0.3.0 tree.

## Next (priority order, non-TUI)
1. **GHCR rename** — 0.2.1 verified; delete old `trygu/tauargus` package.
2. **Top-level project rename** (repo/package naming) — decide + execute.
3. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.

## Watch items
- **TUI segfault on suppress** (2026-10-11; ASan tomorrow): tui venv is the
  PyPI wheel — first re-point it at a local ASan engine build (editable
  `bindings/python` from `engine/build-asan`), reproduce with s/r, get the
  ASan stack. Likely the ~40% `Highs_destroy` segfault.
- OPT/MOD deadline expiry needs separate coverage; positive limits pass.
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Parquet as the microdata dataframe backend (not started).
- Ref: `piargus` (`references/piargus`, transient) — compare API/flow, drop after.
