# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.

## Goal
Port Tau-Argus to HiGHS open-source solvers with a portable cloud-native build and a headless Python CLI replacing the Java/Swing frontend.

## Verified checkpoints
- [x] 74/74 tests green (`cd python && uv run pytest`); `uv build --wheel` OK.
- [x] MOD/OPT/RND suppression ported end-to-end (HITAS/CRP/HiGHS).
- [x] **Task 4: headless CLI** — `tauargus/cli.py` (run/explore/specify/compute/
  suppress/round/audit/save/tables/version); entry point `tau-argus`.
- [x] **CSP/HiGHS teardown segfault fixed**: legacy column-0 RHS sentinel in
  `add_row` corrupted the LP matrix. ASan + MPS method in `docs/native-debugging.md`.
- [x] **Tabular (pre-aggregated) table flow** — `data/tableinput/TestTable.arb`
  runs headless end-to-end. `engine.read_table` = 3-phase port of Java
  `TableSet.read` (SetInCodeList → SetTotalsInCodeList → SetTable/SafetyInfo →
  buildCell/SetInTable → CompletedTable). `_execute` dispatches `OpenTableData`
  → `parse_rda_table`. 7 new tests in `python/tests/test_table_smoke.py`.

## Next
1. Task 5 finish: `.jjd` audit output; confirm microdata flow unchanged.
2. Task 1 finish: document solver strategy; Dockerfile / cibuildwheel plan.
3. Task 3 finish: `apriori.py` / `recode` / `save` as needed by batch flow.
4. Task 6: packaging — Dockerfile, GitHub Actions CI.
5. Task 8: delete `src/` (Java), `nbproject/`, SWIG; final grep sweep.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows` —
  delete mask can mark stale positions (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after it.
- Tabular fixture `pp.tab` has internally inconsistent subtotals; `<READTABLE>
  1T` recomputes totals from leaves, so total cells can differ ~1.0 from the file.
