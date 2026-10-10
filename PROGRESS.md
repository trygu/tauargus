# Tau-Argus Rewrite — Progress

Branch: `rewrite`. History/completed work: see `ARCHIVE.md`.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI replacing Java/Swing.

## Verified checkpoints (details in ARCHIVE.md)
- [x] 129/129 tests green (`cd bindings/python && uv run pytest`); wheel OK.
- [x] WRITETABLE type-5 (INTERMEDIATE) + apriori + MOD/OPT/RND + tabular flow.
- [x] Task 4 headless CLI; CSP/HiGHS teardown segfault fixed; Task 3 `cover`.
- [x] **Audit (Intervalle) ported** — `TauAuditJj` (HiGHS), `Engine.audit`,
  `cmd_audit`, `+AR`/`AR+` type-5 bounds columns, `--audit` on `save`.
- [x] **Cleanup + rename + restructure** (2026-10-09): legacy cruft removed;
  `tauargus`→`pytauargus`; `libCRP.dylib` bundled; root cleanup.
- [x] **Self-contained wheel + x-platform CI** (2026-10-09): `wheels.yml` = HiGHS src
  + engine + repair (delocate/auditwheel/delvewheel) → GH Release (+opt PyPI).
  macOS leg verified end-to-end; Linux/Windows pending a CI run.
- [x] **rtauargus reference submodule** (2026-10-10) at `references/rtauargus`
  (InseeFrLab v1.3.6). It is a *generator* front-end (writes .tab/.rda/.hrc/.arb),
  opposite side of our *parser+engine*.
- [x] **HRC writer ported** (2026-10-10): `pytauargus/hrc.py` (port of
  `rtauargus/R/hrc.R`) — `write_hrc` + helpers, tech-neutral (dict-of-columns in,
  `.hrc` text out). 30 ported tests in `tests/test_hrc.py`, validated against
  base-R ground truth. Round-trip guard (write→lead-strip) added.

## Next (priority order)
0. Port remaining rtauargus tests: micro `.rda` writer + `.arb` text contract
   (`test_micro_arb.R`, `test_micro_asc_rda.R`); bring in non-duplicated test
   data; document gaps (no `.tab`/`.hst` generator, no `.hrc` native getter).
1. Validate Linux/Windows legs of wheels.yml in CI; publish first release.
2. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.
3. **ANSI-UI (SPLIT OUT, `docs/ui-design.md`)**: TUI vs headless-CLI-only (rec: headless).
4. Task 8 (BLOCKED on #3): keep `src/` Java until UI decision.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows` (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Native: `SetTableCellCost` success not visible via `GetTableCell`;
  `GetVarCodeProperties` ok=False on non-hier codes — use `GetVarCode`.
- Parquet as the microdata dataframe backend (separate discussion, not started).
