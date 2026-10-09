# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI replacing Java/Swing.

## Verified checkpoints (details in ARCHIVE.md)
- [x] 99/99 tests green (`cd bindings/python && uv run pytest`); wheel OK.
- [x] WRITETABLE type-5 (INTERMEDIATE) + apriori + MOD/OPT/RND + tabular flow.
- [x] Task 4 headless CLI; CSP/HiGHS teardown segfault fixed; Task 3 `cover`.
- [x] **Audit (Intervalle) ported** — `TauAuditJj` (HiGHS), `Engine.audit`,
  `cmd_audit`, `+AR`/`AR+` type-5 bounds columns, `--audit` on `save`.
- [x] **Cleanup** (2026-10-09): legacy cruft removed from all 5 engine repos;
  READMEs rewritten; CLI `tau-argus` → `tauargus`.
- [x] **pytauargus rename** (`7a6ff3d`): package `tauargus`→`pytauargus`
  (CLI stays `tauargus`); wheel self-contained via CMake `install()`.
- [x] **engine/+bindings/ restructure**: `native/`→`engine/native/`,
  superbuild → `engine/CMakeLists.txt`, `python/`→`bindings/python/`;
  `libCRP.dylib` bundled (rounder links it).
- [x] **Self-contained wheel + cross-platform CI** (2026-10-09):
  platform-aware binding CMake (dylib/so/dll); `wheels.yml` builds HiGHS
  from source + engine + `pip wheel` + delocate/auditwheel/delvewheel
  repair → GitHub Release assets (+ optional PyPI on tag). macOS leg
  verified end-to-end; Linux/Windows pending a CI run.

## Next (priority order)
1. Validate Linux/Windows legs of wheels.yml in CI; publish first release.
2. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.
3. **ANSI-UI (SPLIT OUT, `docs/ui-design.md`)**: TUI vs headless-CLI-only (rec: headless).
4. Task 8 (BLOCKED on #3): keep `src/` Java + parent-root legacy until UI decision.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows` (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Native: `SetTableCellCost` success not visible via `GetTableCell`; `GetVarCodeProperties`
  ok=False on non-hier codes — use `GetVarCode`.
