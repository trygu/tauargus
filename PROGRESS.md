# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.

## Goal
Port Tau-Argus to HiGHS open-source solvers with a portable cloud-native build and a headless Python CLI replacing the Java/Swing frontend.

## Verified checkpoints (details in ARCHIVE.md)
- [x] 85/85 tests green (`cd python && uv run pytest`); `uv build --wheel` OK.
- [x] WRITETABLE type-5 (INTERMEDIATE) audit file ported.
- [x] **`apriori` ported** (`apply_apriori`; S/U/P/M/ML, C/W, PL; `--expand-bogus`).
- [x] MOD/OPT/RND suppression ported end-to-end (HITAS/CRP/HiGHS).
- [x] Task 4: headless CLI (run/explore/specify/compute/suppress/round/
  apriori/audit/save/tables/version); entry point `tau-argus`.
- [x] CSP/HiGHS teardown segfault fixed (see `docs/native-debugging.md`).
- [x] Tabular (pre-aggregated) table flow runs headless end-to-end.

## Next (in priority order)
1. **Task 3: `cover`** — legacy `<COVER>` (batch.java:281) = `setProtectCoverTable`
   + `ADDITIVITY_NOT_REQUIRED` + `LinkedTables` (obscure, "not in the manual").
   **Scope down before porting.** Currently a no-op warning in `_execute`.
2. Task 5: only `+AR` realized-interval columns remain (deferred; needs
   external `intervalle.exe`). INTERMEDIATE audit + CSV flow done.
3. Task 1 finish: document solver strategy; Dockerfile / cibuildwheel plan.
4. Task 6: packaging — Dockerfile, GitHub Actions CI.
5. **ANSI-UI (SPLIT OUT — own task/branch, `docs/ui-design.md`)**: decide
   ANSI TUI (OpenCode-style) vs headless-CLI-only (rec: headless first).
6. Task 8 (BLOCKED on #5 decision, not on UI build): keep `src/` (Java) /
   `nbproject/` / SWIG until the UI decision is made. No UI → delete Swing.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows`
  — delete mask can mark stale positions (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Native quirks: `SetTableCellCost` success not visible via `GetTableCell`
  cost field; `GetVarCodeProperties` returns ok=False on non-hierarchical
  codes — use `GetVarCode` for code strings.
