# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI replacing Java/Swing.

## Verified checkpoints (details in ARCHIVE.md)
- [x] 99/99 tests green (`cd bindings/python && uv run pytest`); wheel OK.
- [x] WRITETABLE type-5 (INTERMEDIATE) + apriori + MOD/OPT/RND + tabular flow.
- [x] Task 4: headless CLI (run/explore/specify/compute/suppress/round/apriori/audit/save/tables/version).
- [x] CSP/HiGHS teardown segfault fixed; Task 3 `cover` (4 tests).
- [x] **Audit (Intervalle) ported to native `csp`** — `TauAuditJj` (HiGHS);
  pybind `audit_jj`; contract tests incl. manual §2.15 (X11 → [3,6]).
- [x] **Audit wired into engine + CLI**: `Engine.audit`, `cmd_audit`,
  `+AR`/`AR+` type-5 realized-bounds columns, `--audit` on `save`.
- [x] **Cleanup** (2026-10-09): legacy cruft removed from all 5 engine repos;
  legacy `doc/` removed; READMEs rewritten; CLI `tau-argus` → `tauargus`.
- [x] **pytauargus rename** (`7a6ff3d`): Python package `tauargus`→`pytauargus`
  (CLI stays `tauargus`); wheel self-contained via CMake `install()` rules.
- [x] **engine/+bindings/ restructure** (2026-10-09): `native/`→`engine/native/`,
  superbuild → `engine/CMakeLists.txt`, `python/`→`bindings/python/`. 5 submodule
  SHAs preserved. **CRP bundling fixed**: wheel now ships `libCRP.dylib`
  (rounder links it) — `round` verified working from an isolated venv.

## Next (priority order)
1. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile/cibuildwheel.
2. Task 6: packaging — Dockerfile, GitHub Actions CI.
3. **ANSI-UI (SPLIT OUT, `docs/ui-design.md`)**: TUI vs headless-CLI-only (rec: headless).
4. Task 8 (BLOCKED on #3): keep `src/` Java + parent-root legacy until UI decision.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows` (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Native: `SetTableCellCost` success not visible via `GetTableCell`; `GetVarCodeProperties`
  ok=False on non-hier codes — use `GetVarCode`.
