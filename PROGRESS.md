# Tau-Argus Rewrite — Progress

Branches: `master` (mainline) + `tui` (TUI). This work is on
`feature/dataframe-protect` (branch protection: no direct master commits).
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI.

## Verified checkpoints (details in ARCHIVE.md)
- [x] Core: WRITETABLE type-5, apriori, MOD/OPT/RND, audit (Intervalle).
- [x] Task 4 headless CLI; rename to `pytauargus`; self-contained wheel +
  CI → GH Release + PyPI + GHCR. **Release 0.2.0**; example notebooks.
- [x] **High-level API — DataFrame `protect()`** (2026-10-10, this branch):
  one-call `protect(df|dict, tables, response, ...)` ->
  `TableResult` (`safe()`/`status()`/`unsafe()`/`dataframe()`).
  `TableResult` + `parse_simple_tab` read the engine's type-5 `SO+` tab.
  `dataframe.py`: `to_microdata` (pandas/polars/dict, duck-typed core),
  `make_frame` (pandas extra, no hard dep). `run=False` = file-only mode.
  **Root-cause fix:** `Variable.is_numeric` wrongly included CATEGORICAL/
  CAT_RESP -> native `ConvertNumeric` on cat codes -> `ISNOTNUMERIC` (1018)
  in `explore_file`. e2e runs in a fresh subprocess (HiGHS teardown is
  flaky; JSON-on-stdout is the success signal, retry on signal-kill).
  **213 passed, 3 skipped** (pandas active; polars/nbclient optional).

## Next (priority order)
1. **GHCR rename → `tauargus-engine`** — 0.2.1 verified. Delete old
   `trygu/tauargus` package.
2. **Top-level project rename** (repo/package naming) — decide + execute.
3. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.
4. **ANSI-TUI** (`textual`, own `pytauargus-tui`) on `tui` branch.

## Watch items
- OPT/MOD nonzero `max_time` → deterministic segfault (solver time-limit);
  notebooks/READMEs use `0`. (`Highs_destroy` segfault FIXED 2026-10-07.)
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Parquet as the microdata dataframe backend (not started).
- Ref: `piargus` (`references/piargus`, transient) — compare API/flow, drop after.
