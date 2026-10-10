# Tau-Argus Rewrite — Progress

Branches: `master` (mainline) + `tui` (TUI). DataFrame work merged to
`master` in PR #5; preparing release 0.3.0 on the mainline.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI.

## Verified checkpoints (details in ARCHIVE.md)
- [x] Core: WRITETABLE type-5, apriori, MOD/OPT/RND, audit (Intervalle).
- [x] Task 4 headless CLI; rename to `pytauargus`; self-contained wheel +
  CI → GH Release + PyPI + GHCR. **Release 0.2.0**; example notebooks.
- [x] **High-level API — DataFrame `protect()`** (2026-10-10, PR #5):
  DataFrame/dict -> native batch -> type-5 `TableResult`; optional pandas.
- [x] Positive OPT/MOD time-limit regressions + corrected audit docs (PR #3).
- [x] macOS `protect()` score-buffer overflow + public import fixed (PR #4).
- [x] DataFrame examples in all three notebooks and both READMEs refreshed.
  37 executed code cells; relative-workdir regression fixed; 219 tests pass.

## Current release — 0.3.0 on `master`
- PR #5 merged; all eight review findings resolved and six CI checks green.
- Version/lock and release docs updated; full Python suite (three notebooks)
  and native CTest pass. Ready to tag and publish.

## Next (priority order)
1. **GHCR rename → `tauargus-engine`** — 0.2.1 verified. Delete old
   `trygu/tauargus` package.
2. **Top-level project rename** (repo/package naming) — decide + execute.
3. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.
4. **ANSI-TUI** (`textual`, own `pytauargus-tui`) on `tui` branch.

## Watch items
- OPT/MOD deadline expiry needs separate coverage; positive limits pass.
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Parquet as the microdata dataframe backend (not started).
- Ref: `piargus` (`references/piargus`, transient) — compare API/flow, drop after.
