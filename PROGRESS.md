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
  `rtauargus/R/hrc.R`) — `write_hrc` + helpers, tech-neutral. 30 tests in
  `tests/test_hrc.py`, validated against base-R ground truth.
- [x] **`.arb` + `.rda` writers ported** (2026-10-10): `arb.py`
  (`micro_arb`+`specif_safety`/`suppr_writetable`/`apriori_batch`), `rda.py`
  (`write_rda`), `util.py` (`cite`/`norm_path`/`df_param_defaut`/`following_dup`).
  174 tests green; validated vs base-R ground truth. Details in ARCHIVE.md.

## Next (priority order)
1. **Release 0.2.0 in flight** (2026-10-10): `.arb`/`.rda` writers + README
   (generator + Intervalle/audit sections). Tag `py-v0.2.0` -> wheels.yml ->
   GH Release + PyPI + GHCR. 0.1.0 already published (immutable).
2. Validate Linux/Windows/aarch64 legs of wheels.yml on the 0.2.0 CI run.
3. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.
3. **ANSI-UI (SPLIT OUT, `docs/ui-design.md`)**: TUI vs headless-CLI-only (rec: headless).
4. Task 8 (BLOCKED on #3): keep `src/` Java until UI decision.

## Watch items
- `deleterows`/`deleterow` (cspsolve.c) compact `rind` before `JJdelsetrows` (latent).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Native: `SetTableCellCost` success not visible via `GetTableCell`;
  `GetVarCodeProperties` ok=False on non-hier codes — use `GetVarCode`.
- Parquet as the microdata dataframe backend (separate discussion, not started).
