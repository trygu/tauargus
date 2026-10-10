# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI replacing Java/Swing.

## Verified checkpoints (details in ARCHIVE.md)
- [x] WRITETABLE type-5 (INTERMEDIATE) + apriori + MOD/OPT/RND + tabular flow.
- [x] Task 4 headless CLI; CSP/HiGHS teardown segfault fixed; Task 3 `cover`.
- [x] **Audit (Intervalle) ported** — `TauAuditJj` (HiGHS), `Engine.audit`,
  `cmd_audit`, `+AR`/`AR+` type-5 bounds columns, `--audit` on `save`.
- [x] **Cleanup + rename + restructure** (2026-10-09) — `tauargus`→`pytauargus`,
  `engine/`+`bindings/` split; details in ARCHIVE.md.
- [x] **Self-contained wheel + x-platform CI** (2026-10-10): HiGHS src + engine +
  repair (delocate/auditwheel/delvewheel) → GH Release + PyPI + GHCR. All legs
  verified on the 0.2.0 run (mac arm64, linux x86_64+aarch64, win x64).
- [x] **rtauargus reference submodule** (2026-10-10) at `references/rtauargus`
  (InseeFrLab v1.3.6) — a *generator* front-end (writes .tab/.rda/.hrc/.arb).
- [x] **`.hrc`/`.arb`/`.rda` writers ported** (2026-10-10): `hrc.py`, `arb.py`
  (`micro_arb`+safety/apriori), `rda.py` (`write_rda`), `util.py`. 174 tests green,
  validated vs base-R ground truth. Details in ARCHIVE.md.
- [x] **Release 0.2.0** (2026-10-10): `.arb`/`.rda` writers + README (generator +
  Intervalle/audit sections). 16 wheels on PyPI; GHCR `:0.2.0`+`:latest`. 0.1.0
  immutable.

## Next (priority order)
1. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.
2. **ANSI-UI (SPLIT OUT, `docs/ui-design.md`)**: TUI vs headless-CLI-only (rec: headless).
3. Task 8 (BLOCKED on #2): keep `src/` Java until UI decision.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows` (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Native: `SetTableCellCost` success not visible via `GetTableCell`;
  `GetVarCodeProperties` ok=False on non-hier codes — use `GetVarCode`.
- Parquet as the microdata dataframe backend (separate discussion, not started).
