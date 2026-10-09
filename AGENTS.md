# Tau-Argus Rewrite — Agent Rules

Port SDC tool to HiGHS solver, portable cloud-native build, and headless Python CLI (replacing Java/Swing).

## 1. Context & Token Preservation (CRITICAL)
- **Terminal output discipline:** NEVER run tests or build commands that print unbounded raw logs into chat context.
  - Redirect verbose output: `<cmd> > /tmp/run.log 2>&1`
  - Inspect ONLY relevant lines: `tail -n 25 /tmp/run.log` or `grep -E "ERROR|CRASH|===|FAIL" /tmp/run.log`
  - Never run shell loops (e.g. `seq 1 25`) directly echoing stdout into context. Summarize results in a single log file.
- **Line reading limits:** Read maximum 60 lines per tool call (`limit=60`). Never read entire files.
- **No speculative code edits:** When debugging crashes, do not add arbitrary debug prints across multiple files. Run under ASan, get the exact stack trace, fix the flagged site, and verify.

## 2. Checkpoint & Progress Discipline
- **Micro-checkpoints:** You MUST update `PROGRESS.md` at every significant discovery or phase transition, NOT just when a task is 100% finished:
  1. When a hypothesis is confirmed or invalidated (e.g. "Invalidated: matsz buffer overflow").
  2. When an ASan stack trace is captured and root cause is identified.
  3. When a submodule build succeeds under new flags.
  4. When an in-flight task is verified.
- **State format:** Keep `PROGRESS.md` strictly under 35 lines. Completed items are moved to `ARCHIVE.md` immediately.

## 3. Source of Truth for Legacy Behavior (READ FIRST)
- **`docs/tau-argus-4.1-markdown-bundle/`** — the legacy τ-ARGUS 4.1 manual (PDF + 10.8k-line
  agent reference + 77 figure assets). This is the **source of truth** for legacy behavior:
  file formats, `.arb` batch grammar, parameters, and SDC mathematics. The rewrite must be a
  **drop-in replacement** for legacy τ-ARGUS: match its observable behavior, file I/O, and outputs.
  Part I (agent reference) is task-oriented; Part II is the page-by-page transcription.
- **`reference/intervalle/`** — the legacy `intervalle.exe` audit program (Pascal/FPC submodule).
  Reference implementation for the audit (intervals) + synthetic values; target of the native port.

## 4. Architecture & Boundaries
- Native C/C++ engine: 5 git submodules under `native/`:
  `core` (static), `csp` (HiGHS LP), `hitas` (links csp), `crp` (HiGHS MIP), `rounder` (links crp).
  Build/commit INSIDE each submodule first, then bump pointers in the parent repo.
- Solver backend: Pure HiGHS (`<highs/interfaces/highs_c_api.h>`). No CPLEX, XPRESS, or legacy SCIP.
- Python layer: `python/` (pybind11 bindings + `tauargus` package). Target product is headless `.arb` batch CLI.
- Legacy to ignore: `src/tauargus/` (Java frontend to be deleted in Task 8). Do NOT inspect or edit.

## 5. Build Commands (macOS / Apple Silicon)
- Highs Brew prefix: `-DHighs_DIR=$(brew --prefix)/lib/cmake/Highs`
- Submodule build:
  `cmake -S native/<mod> -B native/<mod>/build -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs && cmake --build native/<mod>/build`
- Superbuild (all 5):
  `cmake -S native -B native/build -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs && cmake --build native/build`
- ASan build (native debugging) — use separate dir to preserve release build:
  `cmake -S native -B native/build-asan -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs -DCMAKE_C_FLAGS="-fsanitize=address -fno-omit-frame-pointer -g" -DCMAKE_CXX_FLAGS="-fsanitize=address -fno-omit-frame-pointer -g" && cmake --build native/build-asan`
  (Preload runtime for Python: `DYLD_INSERT_LIBRARIES="$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)" uv run ...`)

## 6. Verification & Commits
- **TDD:** The agent is an avid TDD fan. For every feature/port, write the test
  *first* (it encodes the legacy contract), watch it fail for the right reason,
  then implement until green. A feature is not done until its test passes.
- Verification: `cd python && uv run pytest` | `uv build --wheel`
- Surgical edits: Use targeted search/replace or patches. Avoid full-file rewrites.
- Commit cadence: Submodule commit first -> parent submodule bump + `PROGRESS.md` update.
- Never stage build artifacts (`.venv/`, `build/`, `dist/`, `*.so`, `*.dylib`, `native/build/`).
- No Windows registry APIs: Use environment variables, config files, or `tempfile`.
