# Tau-Argus Rewrite — Agent Rules

Port the SDC tool to open-source solvers (HiGHS), a portable cloud-native build,
and a headless Python CLI (replacing the Java/Swing frontend).

## Read first
- `PROGRESS.md` is the single source of truth. Read it, and update it on every
  verified checkpoint (build, test, decision, cleared blocker).

## Architecture
- Native C++ engine: 5 git submodules under `native/` — `core` (static),
  `csp` (HiGHS LP), `hitas` (links csp), `crp` (HiGHS MIP), `rounder` (links crp).
  Build/commit **inside** each submodule, then bump its pointer in the parent.
- `python/` — pybind11 bindings + `tauargus` package (batch parser, engine,
  CLI). This is the product: headless `.arb` batch path, not GUI.
- `src/tauargus/` — legacy Java frontend (to be deleted, Task 8).
- `data/` — sample `.asc`/`.rda`/`.arb` files for end-to-end verification.
- All solver backends converge on **HiGHS** (no CPLEX/XPRESS/old-SCIP).
  HiGHS C API header is `<highs/interfaces/highs_c_api.h>`.

## Build (macOS/Apple Silicon)
- HiGHS via brew: `-DHighs_DIR=$(brew --prefix)/lib/cmake/Highs`
- One module: `cmake -S native/<mod> -B native/<mod>/build -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs && cmake --build native/<mod>/build`
- Superbuild (all 5): `cmake -S native -B native/build -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs && cmake --build native/build`

## Verify / test
- Python tests (47): `cd python && uv run pytest`
- Wheel: `cd python && uv build --wheel`
- Smoke: import built module, `TauArgus().version()` → `1.1.4.11`

## Rules
- Prefer editing existing files; follow each file's conventions.
- Commit early and often at every verified checkpoint: submodules first,
  then parent (pointer + `PROGRESS.md`).
- Keep build artefacts out of git: `.venv/`, `build/`, `dist/`, `*.so`,
  `*.dylib`, `native/build/` are gitignored — never stage them.
- No Windows registry access; use config file / env vars / tempfile.
