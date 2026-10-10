# Tau-Argus Rewrite — Archive

Historical/completed state, extracted from `PROGRESS.md` on 2026-10-06
(repo meta-cleanup). See `PROGRESS.md` for current state.

Branch: `rewrite`

## Original goals
1. Port to the open source solver and make it cloud native and portable
2. Clean up the code
3. Port the Swing/Java UI to Python with a CLI-based UI
4. Remove all traces of Java

## Architecture (as-is, at analysis time)
- **Native C++ engine** in 5 git submodules under `native/`:
  - `native/core` — data model, Argus/JJ file I/O, table compute engine (`TauArgus` class). Static lib `tauargus_core`.
  - `native/csp` — cell suppression (branch-and-price LP), LP backend **HiGHS** (`src/Jjsolver.c`). Shared lib `tauargus_csp`.
  - `native/crp` — controlled rounding (CP/S/XP/XM main programs).
  - `native/hitas` — hierarchical/iterative suppression (`AHiTaS` + `FullJJ`). Links `tauargus_csp`.
  - `native/rounder` — rounder driver (calls CRP `DoRound`).
- **Java frontend** in `src/tauargus/` (90 files, ~38k LOC): `model/` (batch.java 1358 lines, OptiSuppress 1776 lines, Application, Metadata, SaveTable), `gui/` (Swing), `service/TableService.java` (integration seam via SWIG/JNI), `extern/dataengine/` (SWIG-generated).
- Solver selection (Java `Application.java`): SOLVER_XPRESS=1, CPLEX=2, SOPLEX=3 ("SCIP"); batch `<SOLVER>` tag picks it.
- SWIG interface `native/core/src/TauArgusJava.swg` — replaced by pybind11.
- Core public API: `native/core/src/TauArgus.h` — ~172 methods.

## Environment (macOS/Apple Silicon)
cmake 4.4.2, AppleClang 21, python3 3.14.7 (/opt/homebrew), HiGHS 1.15.1 via brew.

## Verified builds (all done)
- [x] `native/core` → `libtauargus_core.a` on macOS (warnings only).
- [x] `native/csp` → `libtauargus_csp.dylib` with HiGHS. Exports `SCIPv::CSP*` + globals.
- [x] `native/hitas` → `libtauargus_hitas.dylib`, links csp + HiGHS.
- [x] `native/crp` → HiGHS MIP backend (rewritten from SCIP). `libCRP.dylib` links `libhighs.1.dylib`; numeric MIP test passes.
- [x] `native/rounder` → `libtauargus_rounder.dylib`, links CRP. Removed stale duplicated `src/WrapCRP.h`.
- [x] Top-level `native/CMakeLists.txt` superbuild — all 5 modules, libs in `native/build/lib/`.

## hitas porting notes (done)
- Removed `cplex.h`/`xprs.h`/SCIP includes from `HiTaSCtrl.cpp`; `CloseSolver` no-op; `CheckStart` logs "using HiGHS".
- `WrapCSP.{h,cpp}`: single `SCIPv::` CSP API only.
- `HITAS_EXPORT` macro replaces `__declspec(dllexport)`.
- macOS fixes: removed `<malloc.h>`, `<vector.h>`→`<vector>`, added `<cassert>`.
- SWIG wrapper `HiTaSCtrl_wrap.*` excluded.

## crp porting notes (done, HiGHS-backed)
- HiGHS C API header: `<highs/interfaces/highs_c_api.h>` (NOT `highs/highs_c_api.h`).
- `crpSmain.c` (MIP): `Highs_passMip` (CSR + integrality) → `Highs_run` → `Highs_getModelStatus` → `Highs_getSolution`.
- `crpSaudit.c` (audit LP): `Highs_passLp` + `Highs_changeColCost`/`Highs_changeColBounds` per iteration; `col_dual` gives reduced costs directly.
- Both files compiled as **C++** (C++ internal linkage for header `const`s; K&R defs converted to ANSI).
- `Highs_clear()` resets ALL options — re-apply `output_flag=0` + `log_to_console=0` after every clear.
- No `Highs_inf` in C API; `#define CRP_HIGHS_INF 1.0e20`.
- CMake: `find_package(Highs REQUIRED)` + `highs::highs`; kept `SCIPV` define for churn minimization.
- Verified: all `S_CRP*` entry points export; 2-cell MIP (total-25) solved correctly.

## Python port — completed state
Headless Python CLI path is **end-to-end functional** for the microdata flow.
`data/TestRecode.arb` runs to completion; **47 tests green**.
- **pybind11 module** (`python/cpp/bind_{core,hitas,rounder}.cpp`): ~54 `TauArgus` methods + `HiTaSCtrl` + `RounderCtrl`. Wheel via `uv build --wheel` (self-contained, `@loader_path` rpath). Smoke: `TauArgus().version()` → `1.1.4.11`.
- **`batch.py`** — legacy-compatible `.arb` parser (18 command dataclasses, tokenizer, status machine).
- **`engine.py`** — `parse_rda`/`parse_rda_table` mirror `Metadata.read*Metadata`; `Engine.run_batch` drives the native engine end-to-end (clean → set info → vars → explore → tables → compute → recodes).
- Native-call fidelity fixes: kwargs `is_numeric`/`is_hierarchical`; `set_hierarchical_digits` trims trailing-zero levels; `set_table` `max_scaled_cost >= 1`, shadow var defaults to response var; `set_table_safety` holding thresholds match `TableSet.readSafetyRule`; Recode: 3 paths (digit truncation, `<TREERECODE>` file via `get_var_code` lookup, classic `DoRecode`).

## Key files (reference)
- `native/core/src/TauArgus.h` — full API surface (~172 methods)
- `src/tauargus/service/TableService.java` — how native is driven
- `src/tauargus/model/batch.java` — .arb grammar
- `src/tauargus/model/OptiSuppress.java` — suppression/rounding orchestration
- `src/tauargus/model/Application.java` — solver constants, Windows registry (to replace)
- `native/csp/src/Jjsolver.c` — HiGHS LP shim
- `native/crp/src/crpSmain.c` / `crpSaudit.c` — HiGHS MIP/LP

## Notes / decisions
- "Open source solver" = HiGHS for csp (LP) and crp (MIP); SCIP dropped.
- Windows registry (WinRegistry.java, SystemUtils.getReg*) → config file / env vars.
- Temp dir conventions → `tempfile` module + explicit work-dir option in CLI.
- Progress listeners → Python callbacks / logging.
- Do NOT port Swing dialogs one-by-one; CLI + headless batch is the product.

## Completed task sub-items (Tasks 1, 2 partial)
Task 1 (open source solver + portable): core/csp/hitas/crp/rounder build-verified with HiGHS; rounder CMakeLists; superbuild.
Task 2 (pybind11): module built & linked; ~54 methods bound; verified with smoke tests.
Task 3 (model/service layer): batch.py, engine.py (metadata parse + orchestration) done; suppress.py/apriori/recode/save pending.

## Suppress/round smoke tests (done 2026-10-06)
`python/tests/test_suppress.py` rewritten to assert the engine's *observable*
invariants (the old assertions were wrong):
- MOD (AHiTaS) / OPT (FullJJ) leave the target unsafe cell's status (3)
  unchanged but mark neighbouring safe cells secondary (status 11/12) →
  assert "secondary count increases".
- RND (CRP/HiGHS) stores values via `SetRoundedResponse`; `get_table_cell_value`
  returns the original response (not the rounded one), so a "multiple of base"
  check on that getter is invalid. Assert: do_round succeeds, values stay
  non-negative, and a base below `_min_round_base` raises BatchError.
- Per-cell LPL/UPL (`GetTableCellProtectionLevels`) return sentinel values
  (e.g. 0.01) for safe cells → not usable as a range check.
- Each test uses a fresh `Engine` (function-scoped fixture in the test file):
  running a second suppression on an already-modified table crashes the native
  engine.

## OPEN BUG (native/csp, HiGHS teardown segfault)
Non-deterministic (~40%) segfault in `Highs_destroy` (HiGHS `HighsOptions`
destructor) reached from `JJfreeprob` → `unload_lp` during/after `AHiTaS` in
`native/csp` (Cspmain.c `PPCSPoptimize`, `cspsolve.c` global `JJLPptr lp`).
Symptom: full `uv run pytest` intermittently dies RC 133/139 after a suppress
test; single suppress tests pass in isolation. Needs a native `native/csp`
fix (LP lifecycle: `load_lp` in read_prob / `unload_lp` paths) — see PROGRESS.md
"Current". Not a Python/test issue.

## Completed detailed checkpoints (2026-10-09)
- WRITETABLE type-5 (INTERMEDIATE) audit file ported (`Engine.write_intermediate_table`),
  `get_table_cell` pybind binding, `+SO`/`+HI`/`+SE`, CLI `save --format intermediate`.
  `+AR` realized-interval columns deferred (needs external `intervalle.exe`).
  Legacy batch number = `safeFileFormat+1` → intermediate is **5** (4=SBS),
  matching 0-based Java constant `FILE_FORMAT_INTERMEDIATE=4`.
- Tabular (pre-aggregated) table flow: `data/tableinput/TestTable.arb` runs
  headless; `engine.read_table` = 3-phase port of Java `TableSet.read`
  (SetInCodeList → SetTotalsInCodeList → SetTable/SafetyInfo → buildCell/
  SetInTable → CompletedTable). 7 tests in `test_table_smoke.py`.
  Note: `pp.tab` subtotals internally inconsistent; `1T` recomputes from
  leaves, so total cells can differ ~1.0 from the file.
- Apriori ported (`Engine.apply_apriori`, `_bogus_range`, `_apply_apriori_change`),
  port of `APriori.processAprioryFile`. Headerless file `<c1>;<c2>;<TYPE>
  [;v1 [;v2]]`; first line validated AND applied. Types S/U/P/M/ML (status),
  C/W (cost), PL (prot-level, unsafe cells 3..9 only); AB unimplemented.
  `--expand-bogus` = single-child chain. CLI verb `apriori`. 9 tests in
  `test_apriori.py`. Native quirk: `SetTableCellCost` returns True but
  `GetTableCell` cost field is a different store (legacy read cost from the
  Java-side cell cache). `GetVarCodeProperties` returns ok=False for all
  non-hierarchical codes → apriori builds its code index from `GetVarCode`.
- **Task 3 `cover`**: `Engine._protect_cover_table` + `for_cover_table`; 4 tests.
- **Intervalle (audit) source** pinned as submodule `reference/intervalle`
  (`430b67b`) — the Pascal/FPC reference the native audit port mirrors.

## Submodule + README cleanup (2026-10-09)
Legacy cruft removed from all five `native/` submodules and the top-level
README rewritten for the rewrite. Per repo (submodule commit first, then
parent pointer bump):
- **core** `894f4c0`: dropped `Help/` (66 HTML), `nbproject/`, `NBMakefile`/
  `MakefileRobert`/`MakefileAction`/`Makefile`, `.github/` (stale Java-DLL CI),
  and the COM/VB6/SWIG sources in `src/` (GhmiterANCO, TauArgCtrl, StdAfx,
  NewTauArgus, TauArgusJava_wrap, `.dsp`/`.dsw`/`.idl`/`.rc`, images). 112 files.
- **csp** `e3a2b84`: dropped `nbproject/`, old Makefiles, dead `CSPLOAD.H`.
- **hitas** `25d935a`: dropped `nbproject/`, old Makefiles, SWIG `hitasctrl.swg`,
  generated `dist/` Java stubs, `.dep.inc`, dead `APCSPglobs.h`/`pcspmain.h`
  + untracked CPLEX/XPRESS solver headers.
- **crp** `571b3f5`: dropped CPLEX/XPRESS solver variants (`crpC*`/`crpX*`),
  `XXRounder/` + its CMake option, `nbproject/`, `Makefile`, `crp.pc.in`,
  stale `build.yml` (referenced removed `-DUSE_SCIP`), 6-line `WrapCRP.h` stub.
- **rounder** `1981385`: dropped `nbproject/`, `Makefile`, `RounderCtrl.swg`,
  `.dep.inc`.
Top-level `README.md` rewritten: native-rewrite overview, module table, HiGHS
build + `uv` CLI usage, tests. (Parent-root legacy files — `Makefile`,
`build.xml`, `nbproject/`, old manual PDFs, runtime logs — left for Task 8.)

(The older "OPEN BUG: HiGHS teardown segfault" note above is RESOLVED — see
the CSP/HiGHS teardown checkpoint in PROGRESS.md / `docs/native-debugging.md`.)

## pytauargus rename + engine//bindings/ restructure (2026-10-09)
- **`pytauargus` rename** (commit `7a6ff3d`): Python package `tauargus`→`pytauargus`
  (CLI command stays `tauargus`). Project identity = `tauargus-engine`. Only the
  Python layer renamed — C libraries keep `tauargus` names (`libtauargus_*`,
  `_tauargus` ext, `TauArgus`/`HiTaSCtrl`/`RounderCtrl` classes, `tauargus_native`).
  Wheel made self-contained via CMake `install()` (ext + csp/hitas/rounder dylibs).
- **Directory restructure**: `native/`→`engine/native/` (submodules, SHAs preserved
  via `.git/modules/` intact), superbuild moved to `engine/CMakeLists.txt`
  (`add_subdirectory(native/...)`), `python/`→`bindings/python/`. Updated `.gitmodules`
  paths, `bindings/python/CMakeLists.txt` `NATIVE_*`, test `DATA` paths (4 parents),
  `.gitignore`, `AGENTS.md`, `README.md` (layout tree).
- **Consolidation rejected**: a single `libtauargus_engine` is blocked by the
  **two global-namespace `IProgressListener` classes** (`core`: `UpdateProgress`;
  `hitas`: 7 methods). Both `TauArgus.h` and `HiTaSCtrl.h` include it; the per-module
  include-path trick (csp takes hitas's via PRIVATE include) is what makes separate
  libs work. Keeping 5 separate libs + per-binding TU isolation (current model).
- **CRP wheel fix**: `libtauargus_rounder.dylib` links `@rpath/libCRP.dylib`, but the
  wheel previously bundled only csp/hitas/rounder → `tauargus round` would dyld-fail
  from an installed wheel. Now `libCRP.dylib` is copied (POST_BUILD) + `install(FILES)`.
  Verified: isolated venv `tauargus round ... --tab 1` runs CRP/HiGHS, exit 0.
- Gate: superbuild rebuilds clean at `engine/`; 99/99 tests green; self-contained
  wheel (`_tauargus` + csp/hitas/rounder/CRP dylibs) verified in isolated venv.

## Self-contained wheels + cross-platform CI (2026-10-09)
- **Problem:** the engine dylibs linked HiGHS at its absolute install path
  (`/opt/homebrew/opt/highs/lib/libhighs.1.dylib` on macOS), so a wheel only
  worked where HiGHS happened to live there.
- **Fix (macOS, verified):** `delocate-wheel` (console script, not `-m`)
  bundles HiGHS into `pytauargus/.dylibs/` and rewrites refs to
  `@loader_path/.dylibs/...`. Verified: repaired wheel installed in an
  isolated venv runs `tauargus round` (exit 0, HiGHS bundled).
- **Platform-aware binding CMake** (`bindings/python/CMakeLists.txt`): resolves
  engine lib names per OS (`.dylib`/`.a` macOS, `.so`/`.a` Linux, `.lib`+`.dll`
  Windows) and sets the right BUILD/INSTALL rpath. Previously hardcoded
  `.dylib` — macOS-only.
- **`wheels.yml`** (GitHub Actions, manual matrix — not cibuildwheel, which
  can't see the sibling `engine/` the Python CMake links against):
  - jobs: macos-14/arm64 + macos-13/x86_64, manylinux2014 (container), windows-2022;
    CPython 3.10–3.13.
  - each: HiGHS from source (`HIGHS_TAG`, cached) → engine superbuild (cached) →
    `pip wheel bindings/python --no-deps` → repair (delocate/auditwheel/delvewheel)
    → upload artifact.
  - release job (on `v*` tag): download artifacts → **GitHub Release assets**
    (softprops/action-gh-release) → optional PyPI publish (`vars.PYPI_ENABLED`).
- **Known gaps (need a real CI run):** Linux auditwheel `--exclude` for libstdc++
  and the manylinux CPython path; Windows delvewheel HiGHS DLL discovery. The
  macOS leg is fully proven locally.

## Submodule + root cleanup (2026-10-09)
- **`reference/intervalle` submodule dropped** (`6115cbd`): the audit is fully
  ported natively (`TauAuditJj` in `engine/native/csp`), so the Pascal reference
  is no longer needed in-tree. The upstream repo (sdcTools/intervalle) stays
  available for cross-checks.
- **Legacy Java-era root files removed**: `BUILDINFO.TXT`, `Error.txt`,
  `ErrorStrings.txt`, `MAKEINFO`, `Makefile`, `TauArgus.properties`,
  `TauManualV4.0.pdf` / `TauManualV4.1.pdf` (superseded by
  `docs/tau-argus-4.1-markdown-bundle/`), `TauNews.html`, `_TauChanges.txt`,
  `build.xml`, `manifest.mf`, `tau-Argus_CTA_help.pdf`, `tauARGUS.css`, and
  the whole `nbproject/` NetBeans tree. Untracked runtime output
  (`.DS_Store`, `CSPlogfile.txt`, `HiTaS.log`, `Highs.log`, `JJUit.dat`,
  `cspSCIP.*`, `hierinfo.dat`, `sdc.lp`) deleted from disk.
- `.gitattributes` slimmed (dropped `*.java`/`*.form`/`*.properties` rules;
  added `*.pdf` binary). Root now contains only: docs, `engine/`,
  `bindings/`, `data/`, `src/` (Java, kept for Task 8), and top-level
  project files.

## README rewrite (2026-10-10)
README rewritten: no Greek letters; top-level project is `tauargus-engine`
(C/C++ libraries under `engine/`), `pytauargus` is the Python package/CLI using them.

## `.arb` + `.rda` writer ports (2026-10-10)
Generator-side file writers ported from `references/rtauargus`, so the Python
package can emit the exact `.arb`/`.rda`/`.hrc` batch inputs our own engine
parser consumes (fixture generator + round-trip validator).

- `pytauargus/util.py` — `cite`, `norm_path` (R `normalizePath(mustWork=FALSE)`
  semantics: returns path unchanged when it doesn't resolve, absolute when it
  does), `df_param_defaut`, `following_dup`, `output_extensions`.
- `pytauargus/arb.py` — `micro_arb`, `specif_safety`, `suppr_writetable`,
  `apriori_batch`, `norm_apriori_params` (port of `R/micro_arb.R`).
- `pytauargus/rda.py` — `write_rda_1var`, `write_rda`, `rda_text` (port of
  `R/micro_asc_rda.R::write_rda*`; the `.rda` text writer only).

Tests: `tests/test_arb.py`, `tests/test_rda.py`, `tests/test_util.py` — direct
translations of `test_micro_arb.R`, `test_micro_asc_rda.R` (write_rda block),
`test_util.R`. All expected values captured by running the pure-R source in
base R. **174 tests green.**

Port notes / gotchas:
- macOS: `datetime.now().strftime("%Z")` is empty (libiconv quirk); use
  `datetime.now().astimezone().strftime(...)` to match R's `Sys.time()` zone.
- `specif_safety`/`write_rda` build each table's block as one string with
  embedded `\n`; the *file* is written with a real `writeLines`/join so
  `<SUPPRESS>`/`<WRITETABLE>` land on separate file lines.

Gaps (intentionally NOT ported): the `micro_asc_rda()` orchestrator that also
emits the fixed-width `.asc` via `gdata::write.fwf` and computes
position/width/digits from microdata — a separate `.asc` generator, not part of
the `.rda` writer. No `.tab`/`.hst` generator, no native `.hrc` getter
(matches the rtauargus gap list).
