# Tau-Argus Rewrite — Progress

Branches: `master` (mainline) + `tui` (TUI work). History: see `ARCHIVE.md`.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI replacing Java/Swing.

## Verified checkpoints (details in ARCHIVE.md)
- [x] Core: WRITETABLE type-5, apriori, MOD/OPT/RND, audit (Intervalle) ported.
- [x] Task 4 headless CLI; cleanup+rename to pytauargus; Task 3 `cover`.
- [x] Self-contained wheel + x-platform CI → GH Release + PyPI + GHCR.
- [x] **Release 0.2.0** (2026-10-10): `.arb`/`.rda`/`.hrc` writers + README;
  16 wheels on PyPI; GHCR `:0.2.0`+`:latest`.
- [x] **Example notebooks** (2026-10-10): `bindings/python/notebooks/` —
  quickstart / protection+audit / generators, executed with saved outputs;
  headless runner `_run.py`, `notebooks` extra, optional `test_notebooks.py`
  (skips without nbclient). READMEs link them.
- [x] **`micro.py` rda bug fixed**: `write_rda_1var` dropped the `\n` before
  the first body line (R `paste(sep="\n")` contract); `test_micro.py` split
  fixed (R `strsplit` = regex, applied per block). 177 tests green.
- [x] Positive OPT/MOD time-limit regressions + corrected audit docs (ARCHIVE).

## Next (priority order)
1. **GHCR rename → `tauargus-engine`** — 0.2.1 verified (`:0.2.1`+`:latest`).
   Remaining: delete old `trygu/tauargus` package.
2. **Top-level project rename** (repo/package naming) — decide + execute later.
3. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.
4. **ANSI-TUI design** (`docs/ui-design.md`): headless CLI is the product;
   `textual` TUI as own PyPI `pytauargus-tui` (`bindings/tui/`). TUI on `tui` branch.

## Watch items
- OPT/MOD deadline expiry needs separate coverage; positive limits pass.
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Parquet as the microdata dataframe backend (not started).
- **Ref: `piargus`** (`references/piargus`, lverweijen) — Python τ-ARGUS
  wrapper; compare its API/flow against `pytauargus` (transient, drop after).
