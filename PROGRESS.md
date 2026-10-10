# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.
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

## Next (priority order)
1. **GHCR package rename → `tauargus-engine`** (user request, in flight):
   0.2.1 re-release pushes `ghcr.io/trygu/tauargus-engine`; then run
   `delete-old-gcr.yml` to remove `trygu/tauargus` from GHCR.
2. **Top-level project rename** (repo/package naming) — decide + execute later.
3. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.
4. **ANSI-TUI design tightened** (`docs/ui-design.md`): Option A (headless
   CLI) is the product; Option B = `textual` TUI as **own PyPI package
   `pytauargus-tui`** (`bindings/tui/`, script `tauargus-tui`). Task 8
   unblocked either way; TUI later on `feat/ansi-ui`.

## Watch items
- OPT/MOD nonzero `max_time` → deterministic native segfault (solver
  time-limit code); notebooks/READMEs use `0` (no limit).
- Non-deterministic ~40% `Highs_destroy` segfault (pre-existing, ARCHIVE).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Parquet as the microdata dataframe backend (not started).
