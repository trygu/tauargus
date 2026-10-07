# Tau-Argus Rewrite — Agent Rules

Port SDC tool to HiGHS solver, portable cloud-native build, and headless Python CLI (replacing Java/Swing).

## Context & Execution Constraints (Strict)
- Read `PROGRESS.md` first. It is the single source of truth for current state and next steps.
- **Single-task limit:** Work ONLY on the active task in `PROGRESS.md`. Complete it, verify it, update `PROGRESS.md`, and stop.
- **No speculative reads:** Never dump entire C/C++ files into context. Read targeted line ranges (max 80 lines per tool call).
- **Diagnostics first:** When debugging crashes/memory issues, run tests under AddressSanitizer (`-fsanitize=address`) and inspect the ASan stack trace before touching code. Do NOT guess root causes.

## Architecture
- Native C/C++ engine: 5 git submodules under `native/`:
  `core` (static), `csp` (HiGHS LP), `hitas` (links csp), `crp` (HiGHS MIP), `rounder` (links crp).
  Build/commit INSIDE each submodule first, then bump pointers in the parent repo.
- Solver backend: Pure HiGHS (`<highs/interfaces/highs_c_api.h>`). No CPLEX, XPRESS, or legacy SCIP.
- Python layer: `python/` (pybind11 bindings + `tauargus` package). Target product is headless `.arb` batch CLI.
- Legacy to ignore: `src/tauargus/` (Java frontend to be deleted in Task 8). Do NOT inspect or edit.

## Build Commands (macOS / Apple Silicon)
- Highs Brew prefix: `-DHighs_DIR=$(brew --prefix)/lib/cmake/Highs`
- Submodule build:
  `cmake -S native/<mod> -B native/<mod>/build -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs && cmake --build native/<mod>/build`
- Superbuild (all 5):
  `cmake -S native -B native/build -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs && cmake --build native/build`
- ASan build (native debugging) — use a SEPARATE dir so it doesn't clobber the
  release `native/build`:
  `cmake -S native -B native/build-asan -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs -DCMAKE_C_FLAGS="-fsanitize=address -fno-omit-frame-pointer -g" -DCMAKE_CXX_FLAGS="-fsanitize=address -fno-omit-frame-pointer -g" && cmake --build native/build-asan`
  (For faults inside HiGHS, also build HiGHS itself with ASan — full recipe in
  `docs/native-debugging.md`.)

## Verification
- Python test suite: `cd python && uv run pytest`
- Wheel package: `cd python && uv build --wheel`
- Smoke test: Import built module, `TauArgus().version()` → `1.1.4.11`

## Commit & Hygiene Rules
- Surgical edits: Use targeted search/replace or patches. Avoid re-writing full files.
- Commit cadence: Submodule commit first -> parent submodule bump + `PROGRESS.md` update.
- Never stage build artifacts (`.venv/`, `build/`, `dist/`, `*.so`, `*.dylib`, `native/build/`).
- No Windows registry APIs: Use environment variables, config files, or `tempfile`.
