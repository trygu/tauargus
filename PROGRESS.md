# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI replacing Java/Swing.

## Verified checkpoints (details in ARCHIVE.md)
- [x] 99/99 tests green (`cd python && uv run pytest`); `uv build --wheel` OK.
- [x] WRITETABLE type-5 (INTERMEDIATE) + apriori + MOD/OPT/RND + tabular flow.
- [x] Task 4: headless CLI (run/explore/specify/compute/suppress/round/apriori/audit/save/tables/version).
- [x] CSP/HiGHS teardown segfault fixed; Task 3 `cover` (4 tests).
- [x] **Audit (Intervalle) ported to native `csp`** — `TauAuditJj` (HiGHS);
  pybind `audit_jj`; contract tests incl. manual §2.15 (X11 → [3,6]).
- [x] **Audit wired into engine + CLI**: `Engine.audit`, real `cmd_audit`,
  `+AR`/`AR+` type-5 realized-bounds columns, `--audit` on `save`
  (7 tests in `tests/test_audit_engine.py`).
- [x] **Cleanup** (2026-10-09): legacy COM/SWIG/NetBeans/Makefile/CPLEX/XPRESS
  cruft removed from all 5 `native/` repos (core `894f4c0`, csp `e3a2b84`,
  hitas `25d935a`, crp `571b3f5`, rounder `1981385`); legacy `doc/` removed;
  all 5 submodule READMEs + top-level README rewritten; CLI renamed
  `tau-argus` → `tauargus`. Rebuild + 99/99 green + wheel OK.

## Next (in priority order)
1. Task 1 finish: document solver strategy (legacy solver roles → HiGHS
   backends); Dockerfile / cibuildwheel plan.
2. Task 6: packaging — Dockerfile, GitHub Actions CI.
3. **ANSI-UI (SPLIT OUT — own task/branch, `docs/ui-design.md`)**: ANSI TUI vs
   headless-CLI-only (rec: headless first).
4. Task 8 (BLOCKED on #3): keep `src/` (Java) + parent-root legacy until UI decision.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows`
  — delete mask can mark stale positions (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Native quirks: `SetTableCellCost` success not visible via `GetTableCell`;
  `GetVarCodeProperties` ok=False on non-hier codes — use `GetVarCode`.
