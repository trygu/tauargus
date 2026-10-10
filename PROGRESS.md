# Tau-Argus Rewrite — Progress

Branches: `master` (mainline) + `tui` (TUI). This work is on
`feature/dataframe-protect`; fixes stay on the active feature branch.
Goal: HiGHS solvers, portable cloud-native build, headless Python CLI.

## Verified checkpoints (details in ARCHIVE.md)
- [x] Core: WRITETABLE type-5, apriori, MOD/OPT/RND, audit (Intervalle).
- [x] Task 4 headless CLI; rename to `pytauargus`; self-contained wheel +
  CI → GH Release + PyPI + GHCR. **Release 0.2.0**; example notebooks.
- [x] **High-level API — DataFrame `protect()`** (2026-10-10, this branch):
  DataFrame/dict -> native batch -> type-5 `TableResult`; optional pandas.

## Verified fix (2026-10-10; PR #4 merged into feature/dataframe-protect)
- macOS `protect()` abort: ASan confirmed native score-buffer overflow in
  Python binding. Allocate from native table capacities; no crash retries.
- Public `protect` import recursion fixed. Plain/weighted/holding regression
  cases: 11 pass with ASan; 216 pass, 3 skip in full release-build suite.
- Original input: 60 fresh-process runs clean under ASan and 60 in release.
- CI run 38072531248: macOS, Linux x86_64 and Linux ARM64 all pass.
- Native PR #1 merged into `rewrite`; temporary fix branches removed.

## Next (priority order)
1. **GHCR rename → `tauargus-engine`** — 0.2.1 verified. Delete old
   `trygu/tauargus` package.
2. **Top-level project rename** (repo/package naming) — decide + execute.
3. Task 1: document solver strategy (legacy roles → HiGHS); Dockerfile.
4. **ANSI-TUI** (`textual`, own `pytauargus-tui`) on `tui` branch.

## Watch items
- Positive OPT/MOD time limits passed regression checks on master (PR #3).
- `open_microdata` calls `clean_all` — safe only because tables finalize after.
- Parquet as the microdata dataframe backend (not started).
- Ref: `piargus` (`references/piargus`, transient) — compare API/flow, drop after.
