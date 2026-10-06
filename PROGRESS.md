# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.

## Goal
Port Tau-Argus to HiGHS open-source solvers with a portable cloud-native build and a headless Python CLI replacing the Java/Swing frontend.

## Current (in flight)
- Fix native CSP/HiGHS segfault (native/csp): non-deterministic (~40%) crash in `Highs_destroy` via `JJfreeprob`/`unload_lp` during/after AHiTaS. Blocks stable full-suite runs.

## Next
1. Task 1 finish: document solver strategy (HiGHS = open-source requirement met); Dockerfile / cibuildwheel plan.
2. Task 3 finish: `apriori.py`/`recode`/`save` as needed by batch flow.
3. Task 4: `tauargus/cli.py` — `run file.arb`, `explore`, `specify`, `compute`, `suppress`, `round`, `audit`, `save`, `tables`; entry point `tau-argus = tauargus.cli:main`.
4. Task 5: end-to-end verification — `data/TestTable.arb` headless, microdata flow, `.jjd` audit output.
5. Task 6: packaging — `pyproject.toml` (scikit-build-core), multi-stage Dockerfile, GitHub Actions CI.
6. Task 8: delete `src/` (Java), `nbproject/`, SWIG wrappers, old resources; final grep sweep for java/swig/cplex/xpress.

## Blockers
- CSP/HiGHS teardown segfault (above) — full `uv run pytest` intermittently crashes (RC 133/139) after suppression.
- Known caveat: `open_microdata` calls `clean_all` — safe only because tables are finalized after it; re-verify if ordering changes.
