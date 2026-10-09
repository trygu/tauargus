# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI replacing Java/Swing.

## Verified checkpoints (details in ARCHIVE.md)
- [x] 89/89 tests green (`cd python && uv run pytest`); `uv build --wheel` OK.
- [x] WRITETABLE type-5 (INTERMEDIATE) audit file ported.
- [x] **`apriori` ported** (`apply_apriori`; S/U/P/M/ML, C/W, PL; `--expand-bogus`).
- [x] MOD/OPT/RND suppression ported end-to-end (HITAS/CRP/HiGHS).
- [x] Task 4: headless CLI (run/explore/specify/compute/suppress/round/
  apriori/audit/save/tables/version); entry point `tau-argus`.
- [x] CSP/HiGHS teardown segfault fixed (see `docs/native-debugging.md`).
- [x] Tabular (pre-aggregated) table flow runs headless end-to-end.
- [x] **Task 3: `cover`** — `<COVER>` sets `_protect_cover_table`; threads
  `for_cover_table` into `CompletedTable` (native already supported it) so a
  non-additive cover table is read without `TABLENOTADDITIVE`. GUI `LinkedTables`
  (`intervalle.exe`) out of scope for headless. 4 tests in `tests/test_cover.py`.

## Next (in priority order)
1. Task 5: only `+AR` realized-interval columns remain (deferred; needs
   external `intervalle.exe`). INTERMEDIATE audit + CSV flow done.
2. Task 1 finish: document solver strategy; Dockerfile / cibuildwheel plan.
3. Task 6: packaging — Dockerfile, GitHub Actions CI.
4. **ANSI-UI (SPLIT OUT — own task/branch, `docs/ui-design.md`)**: decide
   ANSI TUI (OpenCode-style) vs headless-CLI-only (rec: headless first).
5. Task 8 (BLOCKED on #4 decision, not on UI build): keep `src/` (Java) /
   `nbproject/` / SWIG until the UI decision is made. No UI → delete Swing.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows`
  — delete mask can mark stale positions (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Native quirks: `SetTableCellCost` success not visible via `GetTableCell`
  cost field; `GetVarCodeProperties` returns ok=False on non-hierarchical
  codes — use `GetVarCode` for code strings.
