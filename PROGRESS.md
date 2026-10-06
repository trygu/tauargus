# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.

## Goal
Port Tau-Argus to HiGHS open-source solvers with a portable cloud-native build and a headless Python CLI replacing the Java/Swing frontend.

## Verified checkpoints
- [x] 51/51 tests green (`cd python && uv run pytest`), including MOD/OPT/RND suppression
      smoke tests on `data/TestRecode.arb`.
- [x] MOD/OPT/RND ported end-to-end: PrepareHITAS/AHiTaS, WriteJJFormat/FullJJ,
      correctRoundJJ/DoRound (CRP/HiGHS) — matches the Java flow.
- [x] `native/core` OOB cell-access fix (recoded tables) committed + pointer bumped.
- [x] **Task 4: headless CLI** — `tauargus/cli.py` with `run`, `explore`,
      `specify`, `compute`, `suppress`, `round`, `audit`, `save`, `tables`,
      `version`; entry point `tau-argus = tauargus.cli:main`. 67/67 tests green
      (51 + 16 new CLI tests in `python/tests/test_cli.py`).
- [x] Fixed `write_csv`/`write_cell_records` latent segfault: `DimSequence`
      must be the identity `{0..9}` (Java `SaveTable.MAXDIM`), not empty —
      empty made native `WriteCSV` deref null. Now `engine.IDENTITY_DIM_SEQUENCE`.

## Next
1. **Fix the CSP/HiGHS teardown segfault** (see Blockers): LP lifecycle in
   `native/csp` so `AHiTaS`/`FullJJ` teardown no longer crashes `Highs_destroy`.
2. Task 5: end-to-end verification — `data/tableinput/TestTable.arb` headless
   (tabular-data flow via `read_table`/`set_in_table`), microdata flow, `.jjd`
   audit output.
3. Task 1 finish: document solver strategy (HiGHS = open-source requirement met); Dockerfile / cibuildwheel plan.
4. Task 3 finish: `apriori.py`/`recode`/`save` as needed by batch flow.
5. Task 6: packaging — `pyproject.toml` (scikit-build-core), multi-stage Dockerfile, GitHub Actions CI.
6. Task 8: delete `src/` (Java), `nbproject/`, SWIG wrappers, old resources; final grep sweep for java/swig/cplex/xpress.

## Blockers / watch items
- **CSP/HiGHS teardown segfault (top native fix):** non-deterministic (~40%)
  crash in `Highs_destroy` (HiGHS `HighsOptions` dtor) reached from
  `JJfreeprob` → `unload_lp` during/after `AHiTaS` in `native/csp`
  (`Cspmain.c` `PPCSPoptimize`, `cspsolve.c` global `JJLPptr lp`).
  Symptom: `uv run pytest` intermittently dies RC 133/139 after a suppress
  test. CLI tests now run each native command in a fresh subprocess to
  contain it, but the crash is engine-level and must be fixed in `native/csp`.
- Known caveat: `open_microdata` calls `clean_all` — safe only because tables are finalized after it; re-verify if ordering changes.
