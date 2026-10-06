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

## Current (in flight)
- Task 4: `tauargus/cli.py` — `run file.arb`, `explore`, `specify`, `compute`,
  `suppress`, `round`, `audit`, `save`, `tables`; entry point
  `tau-argus = tauargus.cli:main`.

## Next
1. Task 1 finish: document solver strategy (HiGHS = open-source requirement met); Dockerfile / cibuildwheel plan.
2. Task 3 finish: `apriori.py`/`recode`/`save` as needed by batch flow.
3. Task 5: end-to-end verification — `data/TestTable.arb` headless, microdata flow, `.jjd` audit output.
4. Task 6: packaging — `pyproject.toml` (scikit-build-core), multi-stage Dockerfile, GitHub Actions CI.
5. Task 8: delete `src/` (Java), `nbproject/`, SWIG wrappers, old resources; final grep sweep for java/swig/cplex/xpress.

## Blockers / watch items
- CSP/HiGHS teardown segfault: previously non-deterministic (~40%) crash in
  `Highs_destroy` during/after AHiTaS. Not reproduced in the current 51-test
  run; keep an eye on it if suppression tests start flaking.
- Known caveat: `open_microdata` calls `clean_all` — safe only because tables are finalized after it; re-verify if ordering changes.
