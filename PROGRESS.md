# Tau-Argus Rewrite — Progress & Handoff

Working branch: `rewrite`

## Goal
1. Port to the open source solver and make it cloud native and portable
2. Clean up the code
3. Port the Swing/Java UI to Python with a CLI-based UI
4. Remove all traces of Java

## Architecture (as-is)

- **Native C++ engine** (the real SDC computation) lives in 5 git submodules under `native/`:
  - `native/core`  — data model, Argus/JJ file I/O, table compute engine (`TauArgus` class). Builds as static lib `tauargus_core`. Has CMakeLists.txt, **builds cleanly on macOS** (only warnings).
  - `native/csp`   — cell suppression (branch-and-price LP). LP backend = **HiGHS** (VSCIP target via `src/Jjsolver.c`). Builds as shared lib `tauargus_csp`. Needs `find_package(Highs REQUIRED)`.
  - `native/crp`   — controlled rounding (CP/S/XP/XM main programs). CMakeLists supports **SCIP** via FetchContent (`-DUSE_SCIP=ON`); CPLEX/XPRESS optional/commented. **SCIP backend uses removed LPI API — needs rewrite** (see Task 1).
  - `native/hitas` — hierarchical/iterative suppression (modular `AHiTaS` + optimal `FullJJ`). **Now has CMakeLists**, builds shared `tauargus_hitas`, links `tauargus_csp`.
  - `native/rounder` — rounder driver (calls CRP `DoRound`). Makefile only; needs CMakeLists.
- **Java frontend** in `src/tauargus/` (90 files, ~38k LOC):
  - `model/` — batch.java (`.arb` batch file parsing, 1358 lines), TableSet, OptiSuppress (suppression orchestration, 1776 lines), Application, Metadata, SaveTable, etc.
  - `gui/` — Swing dialogs/panels (to be replaced by CLI)
  - `service/TableService.java` — the integration seam: calls native `TauArgus` object (SWIG/JNI) for ExploreFile/SetTable/ComputeTables/suppress/round/audit.
  - `extern/dataengine/` — SWIG-generated Java (IProgressListener, TauArgus wrapper). References `TauArgusJavaJNI`.
- **Solver selection** (Java side, `Application.java`): SOLVER_XPRESS=1, SOLVER_CPLEX=2, SOLVER_SOPLEX=3 (labelled "SCIP"). Batch file `<SOLVER>` tag picks it. OptiSuppress writes AMPL/LP files and invokes solver-specific `.sol` parsing (CTA_*.sol naming: cplex, xpress, glpk, cbc, sym).
- **Old Windows binaries** (dlls/exes) were already deleted in the rewrite branch; submodules replaced them.
- SWIG interface: `native/core/src/TauArgusJava.swg` + generated `TauArgusJava_wrap.cpp/.h` — to be replaced by pybind11.
- Core public API: `native/core/src/TauArgus.h` — ~172 methods (the surface to bind).

## Environment (this machine, macOS/Apple Silicon)
- cmake 4.4.2, clang++ (AppleClang 21), g++, make
- python3 3.14.7 (/opt/homebrew/bin/python3)
- **HiGHS and SCIP already installed via brew** (needed by csp/crp)
- No pybind11 Python package confirmed yet — check `python3 -c "import pybind11"`.

## Verified builds
- [x] `native/core` configures + builds to `libtauargus_core.a` on macOS (warnings only: sprintf deprecations, 1 dangling-assignment in TauArgus.cpp:6020, 1 unused function).
- [x] `native/csp` configures + builds to `libtauargus_csp.dylib` with HiGHS (`-DHighs_DIR=$(brew --prefix)/lib/cmake/Highs`). Warnings only (C-as-C++ deprecation, 1 unused var `cspgomo.c:57`). Exports `SCIPv::CSP*` (HiGHS-backed) + global `CSPdefinestoptime`, `JJ*`.
- [x] `native/hitas` configures + builds to `libtauargus_hitas.dylib`, links `tauargus_csp` + HiGHS. Exports `HiTaSCtrl::{AHiTaS,FullJJ,SetJJconstants*,GetVersion,...}`. (See "hitas porting" notes below.)
- [x] `native/crp` — **DONE: rewired SCIP backend → HiGHS.** `libCRP.dylib` builds (links `libhighs.1.dylib`), all `S_CRP*` entry points export, and a numeric MIP test solves correctly (2-cell total constraint → a 12→10, b 13→15, obj LB=UB=4). Both `crpS*.c` now compile as **C++** (HiGHS header `const`s need C++ internal linkage). Banner silenced via `output_flag`+`log_to_console` (must re-apply after every `Highs_clear` — it resets options). See "crp porting" notes.
- [x] `native/rounder` — **DONE: CMakeLists + build-verified.** `libtauargus_rounder.dylib` builds (links `libCRP.dylib`, exports `RounderCtrl::*`, dlopen `RTLD_NOW` OK). Removed the stale duplicated `src/WrapCRP.h` (drifted non-`extern` copy that would collide with CRP's C++ definitions); rounder now uses CRP's canonical header via a PUBLIC include dir. `RounderCtrl.h`'s `__declspec(dllexport)` → portable `ROUNDER_EXPORT` macro.
- [x] **Top-level `native/CMakeLists.txt` superbuild** — builds all 5 modules (core, csp, hitas, crp, rounder) in one tree; all libs land in `native/build/lib/`. Auto-detects Homebrew HiGHS on macOS.

## TODO

### Task 1 — Open source solver + cloud native + portable  (in_progress)
- [x] Build-verify `core`, `csp`, `hitas` on macOS with HiGHS.
- [x] Build-verify `crp` on macOS with HiGHS (rewritten from SCIP; see notes).
- [x] Build-verify `rounder` (CMakeLists links `CRP`).
- [x] Add CMakeLists for rounder (mirror hitas style; hitas already done).
- [x] Add a top-level `native/CMakeLists.txt` superbuild that builds all 5 modules in one tree.
- [ ] Decide solver strategy for the Python port: keep C++ engine + open source LP solvers (HiGHS/SCIP) = "open source solver" requirement satisfied. Document it.
- [ ] Dockerfile: manylinux/mac compatible image with HiGHS + build deps; or use cibuildwheel for wheels later.

### Task 2 — Python bindings (pybind11) replacing SWIG/JNI
- [ ] Add `pybind11` module to core CMakeLists (option BUILD_PYTHON=ON)
- [ ] Bind the `TauArgus` class public API (start with the methods TableService/batch use: CleanAll, SetProgressListener, SetInFileInfo, ExploreFile, SetNumberTab, SetTable, SetTableSafety, ComputeTables, GetMinimumCellValue, ThroughTable, GetVarNumberOfCodes, GetVarCode, GetErrorString, suppress/round/audit entry points, undo, JJ write/read)
- [ ] Progress callback: std::function<int()> or py callback for UpdateProgress
- [ ] Verify with a small Python script: load data/tau_testW.asc, explore, compute one table

### Task 3 — Port model/service layer to Python
- [ ] `tauargus/batch.py` — parse `.arb` batch files (port batch.java: 1358 lines; tags: <SET>, <OPEN>, <TABLE>, <SPECIFY>, <SOLVER>, <RECODE>, <SAVE>, etc.)
- [ ] `tauargus/tableset.py`, `metadata.py`, `variable.py` — data classes mirroring Java model
- [ ] `tauargus/service.py` — port TableService.java orchestration
- [ ] `tauargus/suppress.py` — port OptiSuppress.java orchestration (primary/secondary, CTA, GHMiter, Hitas, round, audit, linked tables)
- [ ] `tauargus/apriori.py`, `recode`, `save` — as needed by batch flow

### Task 4 — CLI UI replacing Swing
- [ ] `tauargus/cli.py` (argparse or click): subcommands:
  - `run file.arb` — full batch (headless, primary path for cloud)
  - `explore`, `specify`, `compute`, `suppress`, `round`, `audit`, `save`, `recode`
  - `tables` — list/inspect tables
  - `progress` via logging to stderr
- [ ] Console output formatting (rich optional) for table display replacing PanelTable
- [ ] Entry point `tau-argus = tauargus.cli:main`

### Task 5 — End-to-end verification
- [ ] Run `data/TestTable.arb` (and `data/tableinput/TestTable.arb`) headless; compare output .ttf/.tab against known-good if available
- [ ] Microdata flow with `data/tau_testW.asc`
- [ ] Suppress + round + audit on sample; check .jjd output
- [ ] Add pytest suite under `tests/`

### Task 6 — Cloud native / portable packaging
- [ ] `pyproject.toml` (setuptools or scikit-build-core; native libs built as part of install or shipped as wheels)
- [ ] Dockerfile (python:3.12-slim + HiGHS + build tools; multi-stage)
- [ ] GitHub Actions CI: build native + python on ubuntu/mac/windows, run tests
- [ ] README rewrite: install (pip / docker / from source), CLI usage, solver notes

### Task 7 — Cleanup
- [ ] Delete commented-out dead code, old NetBeans artifacts (nbproject/), MakefileAction/MakefileRobert/NBMakefile, .dsp/.dsw/.idb files, SWIG wrapper cpp/h, old resources (oldicons, .ico, .jpg splash)
- [ ] Remove Windows-only remnants (Versioninfo.rc optional — keep behind WIN32 guard, fine)
- [ ] Normalize line endings (CRLF→LF; git warns about it)

### Task 8 — Remove Java traces
- [ ] Delete `src/` (all Java), `build.xml`, `nbproject/`, `manifest.mf`, `Makefile` (old top-level Java makefile — check it first), `TauArgus.properties` (if only used by Java), `Error.txt`/`ErrorStrings.txt` (check usage; likely Java resources)
- [ ] Keep: native/, data/, doc/, manuals (PDFs), LICENSE, PROGRESS.md
- [ ] Update .gitmodules URLs if moving repos (currently trygu/* forks)
- [ ] Final grep sweep for `java|swing|swig|JNI|cplex|xpress` references in remaining docs/code

## Key files to read first (for any resumed session)
- `native/core/src/TauArgus.h` — full API surface (~172 methods)
- `native/core/src/TauArgus.cpp` — implementation (large)
- `src/tauargus/service/TableService.java` — how native is driven (microdata + table flows)
- `src/tauargus/model/batch.java` — .arb batch file grammar
- `src/tauargus/model/OptiSuppress.java` — suppression/rounding orchestration + solver dispatch
- `src/tauargus/model/Application.java` — solver constants, global state, registry access (Windows registry! — replace with config file/env for portability)
- `native/csp/src/Jjsolver.c` — HiGHS shim (the open-source LP entry point)
- `native/crp/src/crpXmain.c` etc. — controlled rounding solver backends (SCIPV/CPLEXV/XPRESSV defines)

## hitas porting (done this session)
The original hitas `Makefile` is Windows/MinGW + SWIG + hardcoded CPLEX/XPRESS/SCIP-3.1.1 paths. Ported to CMake and rewired to the open-source CSP engine:
- Removed `#include "cplex.h"`, `"xprs.h"`, `<scip/scip.h>`, `<scip/scipdefplugins.h>`, `"objscip/objscip.h"` from `HiTaSCtrl.cpp`.
- `HiTaSCtrl::CloseSolver` → no-op (CSP engine is linked in; nothing to close). `HiTaSCtrl::CheckStart` → accepts `SCIP`/`CPLEX`/`XPRESS` names, logs "using HiGHS", returns 0. Removed all license/env/solver-lifecycle code.
- `WrapCSP.{h,cpp}`: deleted `CPLEXv` + `XPRESSv` namespaces; every dispatcher now routes to the single `SCIPv::` CSP API (which the HiGHS-built `tauargus_csp` exports).
- `Amain.h`: removed `namespace CPLEXv` / `SCIPv{SCIP*_scip; SCIP_LPI**Env;}` / `XPRESSv` blocks (referenced removed solver types; redundant with `WrapCSP.h`).
- `HiTaSCtrl.h`: replaced `class __declspec(dllexport)` with portable `HITAS_EXPORT` macro (dllexport only on Windows).
- Fixed macOS-portable headers: `<malloc.h>` (doesn't exist) removed from `ATabs.h`,`AHier.h`; `<vector.h>`→`<vector>` in `AMiscFunc.cpp`; added `<cassert>` to `AMiscFunc.cpp`.
- Excluded SWIG wrapper `HiTaSCtrl_wrap.*` (pybind11 replaces it).
- Result: `libtauargus_hitas.dylib` links `@rpath/libtauargus_csp.dylib` + HiGHS; `HiTaSCtrl` methods exported.

## crp porting — DECISION: back with HiGHS (same as csp)  (next)
**Big find (CONFIRMED):** HiGHS's C API header is at
`/opt/homebrew/Cellar/highs/1.15.1/include/highs/interfaces/highs_c_api.h`
(i.e. `<highs/interfaces/highs_c_api.h>`; NOT `highs/highs_c_api.h` — that path does not exist). It is already on the include path since `csp/src/Jjsolver.c` includes it that way. Verified (Highs 1.15.1 via brew) that it covers **everything** both crp solver files need, so we drop SCIP entirely and do exactly what csp does:

### Confirmed HiGHS C API surface (grep-verified in the header)
- Lifecycle: `Highs_create()`, `Highs_free`, `Highs_clear` (line 374 — "empties" the model in place; perfect for the audit re-solve loop), `Highs_writeModel`.
- Pass model in one shot (COO/CSC/CSR):
  - `Highs_passLp(num_col, num_row, num_nz, a_format, sense, offset, col_cost, col_lower, col_upper, row_lower, row_upper, a_start, a_index, a_value)` (line 485)
  - `Highs_passMip(...same..., integrality[])` (line 503) — `integrality[k]`: 0=continuous, 1=integer, 2=semi-continuous, 3=semi-integer, 4=implicit-integer. Binary = integer + bounds [0,1].
  - Formats: `kHighsMatrixFormatColwise=1` (CSC) / `kHighsMatrixFormatRowwise=2` (CSR). Senses: `kHighsObjSenseMinimize=1`, `kHighsObjSenseMaximize=-1`.
- Solve + read back: `Highs_run` (line 429), `Highs_getModelStatus` (line 1023, `kHighsModelStatusOptimal` etc.), `Highs_getSolution(highs, col_value, col_dual, row_value, row_dual)` (line 994 — returns **primal AND dual** in one call; `col_dual` = the "reduced cost"/dj, `row_dual` = constraint multipliers). `Highs_getBasis` for basis statuses.
- Cheap mutation (used by the audit re-solve loop): `Highs_changeColCost` (1597), `Highs_changeColsCostBySet` (1626), `Highs_changeColBounds` (1652), `Highs_changeColsBoundsBySet` (1687), `Highs_changeColsIntegralityBySet` (1559), `Highs_changeObjectiveSense` (1503), `Highs_changeObjectiveOffset` (1513), `Highs_addCols` (1404).
- Also present if needed: `Highs_postsolve` (446), `Highs_getDualRay` (1038), `Highs_getDualUnboundednessDirection` (1057), `Highs_writeSolution(Pretty)`.

### File-by-file port plan
- **`crpSmain.c`** (1037 lines, the main controlled-rounding **MIP**): currently *modern* SCIP (`SCIPcreate`, `SCIPcreateVar` w/ `SCIP_VARTYPE_BINARY/INTEGER/CONTINUOUS`, `SCIPaddCons`, `SCIPsolve`, `SCIPgetVars`). → Replace `SCIP*Env` global with `void* h = Highs_create()`; assemble model into CSC arrays + integrality vector; one `Highs_passMip`; `Highs_run`; check `Highs_getModelStatus`; read `Highs_getSolution(col_value, ...)`. Binary SCIP vars (bound [0,1]) map to integer + bounds [0,1].
- **`crpSaudit.c`** (325 lines, the audit **LP** re-solved per variable with duals + reduced costs): currently the **removed SCIP 3.x LPI API** (`SCIPlpiCreate/AddCols/AddRows/ChgObj/ChgBounds/SolvePrimal/SolveDual/GetSol/GetCols`, `SCIP_LPI*`). → Build once with `Highs_passLp`; per iteration: `Highs_changeColCost`/`Highs_changeColBounds`/`Highs_changeColsCostBySet` + `Highs_run` + `Highs_getSolution(col_value, col_dual, row_value, row_dual)`. The old LPI code fetched `dj` (reduced costs) via `SCIPlpiGetSol` — HiGHS gives the same value directly in `col_dual`, so no manual `dj[k] = -Σ dual·coef` recompute is needed (that fallback only applies if HiGHS leaves `col_dual` unset for a non-optimized LP).
- CPLEX (`crpCmain.c`) / XPRESS (`crpXmain.c`) already `#ifdef`-excluded. `WrapCRP.c` dispatch is clean (name routing only, no solver-specific code).
- **CMake**: replaced `USE_SCIP`/FetchContent-SCIP in `native/crp/CMakeLists.txt` with `find_package(Highs REQUIRED)` + `target_link_libraries(CRP PRIVATE highs::highs)`. Kept the `SCIPV` define to minimize churn (the "S" files are now HiGHS-backed).

### crp porting — implementation notes (verified, builds + numeric MIP test passes)
- **Compile the two HiGHS files as C++** (`set_source_files_properties(src/crpSmain.c src/crpSaudit.c PROPERTIES LANGUAGE CXX)`). Reason: in **C**, `const` file-scope constants in `highs_c_api.h` (e.g. `kHighsIis*`) have *external* linkage → including the header in two TUs gives duplicate-symbol link errors. In **C++** they have internal linkage (one per TU) → link OK. (csp does the same thing.)
- Consequence: the two files' **K&R function definitions were converted to ANSI** (K&R is illegal in C++11+). `exact.c`/`WrapCRP.c` stay C.
- `crpmain.h`'s `CRPmessage`/`CRPextratime` global declarations were made `extern` — as bare file-scope declarations they are *tentative definitions* in C but *definitions* in C++, which clashed with the single real definition in `WrapCRP.c:32-33`.
- **`ZERO`/`INF`/`MAX_TIME`**: declared `extern` directly in `crpSmain.c` (C linkage). Could NOT `#include "WrapCRP.h"` from a C++ TU: WrapCRP.h declares `CRPmessage`/`CRPextratime` *outside* its `extern "C"` block while `crpmain.h` declares them *inside* → "different language linkage" conflict.
- **`Highs_inf` does not exist in the C API.** Use `#define CRP_HIGHS_INF 1.0e20` (HiGHS treats 1e20 as infinite; same as csp/Jjsolver.c).
- **`Highs_clear()` resets ALL options to defaults** (re-enables `log_to_console`). The quiet options (`output_flag=0`, `log_to_console=0`) must be **re-applied after every `Highs_clear`** or the HiGHS banner + solve log flood stdout. (This is invisible to a smoke test that only calls open/close — the banner only appears on the first `Highs_run`.)
- **`S_solvesubproblem` LPI dead code dropped**: the old `SCIPlpiGetBounds`/`ChgBounds` bound-tightening was a no-op (bound was reassigned to itself, so the restore-`if` never fired); `dj`/`dual`/`yval` outputs are always NULL at the only call site (`S_CRPauditing`), so only the objective value is read back (`Highs_changeColCost` ±1 → `Highs_run` → `Highs_getObjectiveValue`; flip sign for sense=-1).
- **`S_MIPmodel`**: assembles the MIP in CSR (`kHighsMatrixFormatRowwise`) + `integrality[]` (0=cont, 1=integer; binary = integer with bounds [0,1]) → one `Highs_passMip` → `Highs_run` → status switch → `Highs_getSolution` (primal) + `Highs_getObjectiveValue`. The SCIP event handler (progress / time-limit extension via `CRPextratime`) was **dropped** — no C-API equivalent; `CRPnodes` read best-effort from the `mip_nodes` info key (0 if unavailable).
- `S_CRPauditing` calls `S_loadsubproblem` (builds the audit LP via `Highs_passLp`, MAXIMIZE) then `S_solvesubproblem` per unsafe cell.
- **Verified**: `libCRP.dylib` links `libhighs.1.dylib`; `S_CRP{open,close,loadprob,optimize,printsolution,auditing,free}prob` all export; dlopen smoke + a 2-cell MIP (total-25) solved correctly (a 12→10, b 13→15, obj 4).

## Next Move
1. **Task 6 — Dockerize / cloud-native packaging.** Write a `Dockerfile` (manylinux base, HiGHS + build deps, superbuild via `native/CMakeLists.txt`) producing a portable image; document the reproducible build. (Task 1's remaining sub-items are all checked off except the Dockerfile itself.)
2. **Task 2 — pybind11 bindings** replacing SWIG/JNI for the headless path (hitas `FullJJ`, crp `do_round`, csp `CSP*`). pybind11 not yet installed on this machine.
3. End-to-end verification against `data/` sample `.asc`/`.arb`/`.ttf` files once bindings exist.

## Notes / decisions
- "Open source solver" = replace CPLEX/XPRESS usage with HiGHS (csp) + SCIP (crp). Both already installed on this machine; csp/crp CMake already support them.
- Windows registry access in Java (WinRegistry.java, SystemUtils.getReg*) must become config file or env vars in the Python port (portability requirement).
- Temp dir / file conventions (Application.getTempFile) → use tempfile module + explicit work dir option in CLI.
- Progress listeners: Java property change events → Python callbacks / logging.
- Do NOT attempt to port the 20+ Swing dialogs one-by-one; the CLI + headless batch path is the product.
