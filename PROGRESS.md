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
- [x] **CSP/HiGHS teardown segfault fixed** (the top native blocker): removed
      the legacy column-0 RHS sentinel in `add_row` that corrupted the LP matrix
      handed to HiGHS. ASan harness 60/60 clean, 67/67 pytest, `repro_seg.py`
      × 9 in-process clean. Root cause + ASan/MPS method in `docs/native-debugging.md`.

## Next
1. Task 5: end-to-end verification — `data/tableinput/TestTable.arb` headless
   (tabular-data flow via `read_table`/`set_in_table`), microdata flow, `.jjd`
   audit output.
2. Task 1 finish: document solver strategy (HiGHS = open-source requirement met); Dockerfile / cibuildwheel plan.
3. Task 3 finish: `apriori.py`/`recode`/`save` as needed by batch flow.
4. Task 6: packaging — `pyproject.toml` (scikit-build-core), multi-stage Dockerfile, GitHub Actions CI.
5. Task 8: delete `src/` (Java), `nbproject/`, SWIG wrappers, old resources; final grep sweep for java/swig/cplex/xpress.

## Blockers / watch items
- **(RESOLVED 2026-10-07) CSP/HiGHS teardown segfault — fixed.** The ~40%
  non-deterministic crash (surfacing in `Highs_destroy` / `HighsOptions` dtor,
  RC 133/139) was a **corrupted LP matrix**, not a solver-lifecycle bug.
  `add_row()` in `native/csp/src/cspsolve.c` appended a legacy CPLEX/XPRESS
  RHS sentinel (`rmatind=0, rmatval=rhs` → a coefficient on dummy column 0)
  to every cut row. Under HiGHS the RHS is passed separately (row bounds in
  `JJaddrows`), so the sentinel leaked a **spurious column-0 coefficient** into
  each cut row, producing a matrix whose structure is inconsistent with HiGHS's
  partitioned row representation; the dual simplex then faulted in
  `HighsSparseMatrix::update` (pivot search) and the heap clobbered at
  `Highs_destroy`. Fix: stop writing the sentinel (kept the `add_rows`
  `rcnt*(mac+1)` buffer sizing — also genuine). Pinned by **building HiGHS with
  ASan** (the fault then reports *inside* HiGHS at `iter 0`) + **dumping the
  crash LP to MPS** (`JJmpswrite`) which showed `c0 r1 1` / `c0 r2 1`.
  Verified: ASan `FullJJ` 60/60 clean; `uv run pytest` 67/67; `repro_seg.py OPT`
  × 9 in-process clean. Full method in **`docs/native-debugging.md`**.
- Watch (unfixed, latent): `deleterows`/`deleterow` in cspsolve.c compact
  `rind` *before* `JJdelsetrows`, so the delete mask can mark stale row
  positions. Also `put_base`/`Highs_setBasis` (cspbranc.c branch-resume) feeds
  raw CSP `stat` codes as basis values — fine for now (not in the in-loop solve
  path) but review if branch-resume misbehaves.
- Known caveat: `open_microdata` calls `clean_all` — safe only because tables are finalized after it; re-verify if ordering changes.
