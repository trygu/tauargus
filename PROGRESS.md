# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI replacing Java/Swing.

## Verified checkpoints (details in ARCHIVE.md)
- [x] 92/92 tests green (`cd python && uv run pytest`); `uv build --wheel` OK.
- [x] WRITETABLE type-5 (INTERMEDIATE) audit file ported.
- [x] **`apriori` ported** (`apply_apriori`; S/U/P/M/ML, C/W, PL; `--expand-bogus`).
- [x] MOD/OPT/RND suppression ported end-to-end (HITAS/CRP/HiGHS).
- [x] Task 4: headless CLI (run/explore/specify/compute/suppress/round/apriori/audit/save/tables/version).
- [x] CSP/HiGHS teardown segfault fixed (see `docs/native-debugging.md`).
- [x] Tabular (pre-aggregated) table flow runs headless end-to-end.
- [x] **Task 3: `cover`** — `_protect_cover_table` + `for_cover_table`; 4 tests.
- [x] Intervalle (audit) source pinned as submodule `reference/intervalle`.
- [x] **Audit (Intervalle) ported to native `csp`** — `TauAuditJj` (HiGHS) reads the
  JJ file in-process (no `intervalle.exe`), legacy primsec contract
  (u/m vars, Int bounds, safe terms → RHS); pybind `audit_jj`; 3 contract tests
  incl. manual §2.15 example (X11 → [3,6]).

## Next (in priority order)
1. Task 5 finish: `Engine.audit(tab)` (write JJ → `audit_jj` →
   `set_realized_lower_and_upper`), real `cmd_audit`, `+AR` realized-bounds
   columns in the type-5 INTERMEDIATE writer.
2. Task 1 finish: document solver strategy; Dockerfile / cibuildwheel plan.
3. Task 6: packaging — Dockerfile, GitHub Actions CI.
4. **ANSI-UI (SPLIT OUT — own task/branch, `docs/ui-design.md`)**: ANSI TUI vs
   headless-CLI-only (rec: headless first).
5. Task 8 (BLOCKED on #4): keep `src/` (Java) / `nbproject/` / SWIG until the
   UI decision. No UI → delete Swing.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows`
  — delete mask can mark stale positions (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Native quirks: `SetTableCellCost` success not visible via `GetTableCell`;
  `GetVarCodeProperties` ok=False on non-hier codes — use `GetVarCode`.
