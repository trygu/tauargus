# tauargus-engine — τ-ARGUS native rewrite (open-source solvers, headless CLI)

A ground-up port of the legacy τ-ARGUS statistical-disclosure-control (SDC)
product. The original Java/Swing front-end and the commercial CPLEX / XPRESS /
SCIP solvers are gone. This rewrite:

- uses **open-source HiGHS** as the only solver backend (LP and MIP),
- is a **portable, cloud-native** C++ engine with a CMake build,
- ships a **headless Python CLI** that runs the same `.arb` batch files the
  legacy product understood — a drop-in replacement for the legacy front-end.

The rewrite is a **drop-in replacement**: it matches the observable behavior,
file I/O, and outputs of legacy τ-ARGUS 4.1.

> The legacy Java front-end still lives in `src/` as a read-only reference and
> is scheduled for deletion in a later task. Build and usage go through the
> native engine + Python layer, not `src/`.

## Architecture

Five C/C++ git submodules under `native/`, all built with CMake:

| Module | Role | Solver backend |
|--------|------|----------------|
| `core`   | Data model, Argus/JJ file I/O, SDC engine entry points (static) | solver-independent |
| `csp`    | Cell-suppression LP (branch-and-price) + the **intervalle audit** | HiGHS (LP) |
| `hitas`  | Hierarchical table suppression (HiTaS) | via `csp` (HiGHS) |
| `crp`    | Controlled rounding problem (iterative rounding + auditing) | HiGHS (MIP) |
| `rounder`| Thin dispatch layer over `crp` | via `crp` (HiGHS) |

A **Python layer** (`python/`) wraps the native engine with pybind11. The
package is **`pytauargus`** (import name), which exposes the **`tauargus`**
command-line tool. The native build is consumed by the Python build via
**scikit-build-core**.

```
.arb batch  →  tauargus CLI  →  Engine (python)  →  native core/csp/hitas/crp/rounder  →  HiGHS
```

## Requirements

- CMake ≥ 3.16, a C++11/C99 toolchain
- **HiGHS** (installed, with its CMake package):
  - macOS: `brew install highs`
  - Linux: `sudo apt-get install libhighs-dev` (or build from source)
  - Windows: build/install from source, then point at its CMake dir
- Python 3.10+ and [`uv`](https://docs.astral.sh/uv/) for the Python layer

## Build

Build the native engine (all five submodules) via the superbuild:

```bash
cmake -S native -B native/build \
      -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs
cmake --build native/build -j
```

Build the Python package (scikit-build-core drives the native CMake build
and links the five engines, then compiles the pybind11 module):

```bash
cd python
uv sync
uv build --wheel
```

Run the CLI directly from the source tree without installing:

```bash
cd python
uv run tauargus --help
```

To install the `tauargus` command from a fresh wheel:

```bash
uv tool install --force --reinstall dist/pytauargus-*.whl
```

> For fast in-tree iteration on the C++ bindings, configure the extension
> against `python/CMakeLists.txt` in a local `build-make/` dir and point
> `-Dpybind11_DIR` at the venv. See `python/CMakeLists.txt` and `AGENTS.md`.

## Using the CLI

```bash
tauargus --help
tauargus run        mybatch.arb      # parse and execute a batch file
tauargus compute    mybatch.arb      # table computation only
tauargus suppress   mybatch.arb      # compute, then apply suppression
tauargus round      mybatch.arb      # compute, then round (RND)
tauargus audit      mybatch.arb      # audit: feasibility intervals of suppressed cells
tauargus save       mybatch.arb -o out   # compute, then write tables
tauargus tables     mybatch.arb      # print a table summary
```

Example fixtures live in `data/` (e.g. `data/tableinput/`).

## Testing

```bash
cd python
uv run pytest        # 99 tests: native contracts + engine + CLI
```

## Project layout

```
.
├── native/                 # C/C++ engine — 5 git submodules, CMake superbuild
│   ├── CMakeLists.txt      #   superbuild: configures & builds all five
│   ├── core/               #   data model, Argus/JJ I/O, SDC engine (static lib)
│   ├── csp/                #   cell-suppression LP + intervall audit (HiGHS LP)
│   ├── hitas/              #   hierarchical suppression (links csp)
│   ├── crp/                #   controlled-rounding MIP (HiGHS MIP)
│   └── rounder/            #   thin dispatch layer over crp
│
├── python/                 # Python layer — pybind11 bindings + `pytauargus`
│   ├── CMakeLists.txt      #   builds the `_tauargus` extension into src/pytauargus/
│   ├── pyproject.toml      #   package metadata + `tauargus` console script
│   ├── cpp/                #   bindings: bind_core/csp/hitas/rounder + module.cpp
│   ├── src/pytauargus/     #   the Python package (engine.py, cli.py, batch.py)
│   │   └── _tauargus.*.so  #   compiled extension + bundled libtauargus_*.dylibs
│   └── tests/              #   pytest suite (99 tests)
│
├── data/                   # sample `.arb` batches + tabular fixtures
├── reference/              # read-only reference implementations
│   ├── intervale/          #   legacy intervall.exe audit (Pascal/FPC)
│   └── rtauargus/          #   R package wrapping the legacy binary — its docs
│                           #   and example data are used to cross-check our port
├── docs/                   # legacy τ-ARGUS 4.1 manual bundle + design notes
└── src/                    # legacy Java/Swing front-end (read-only, pending deletion)
```

`reference/rtauargus` is a third-party R package that wraps the original
τ-ARGUS binary. We don't build against it, but its **documentation and
example data** are a useful independent oracle while the port is still being
verified — handy for confirming our output matches the reference
implementation before the legacy code is fully retired.

## License

τ-ARGUS is © Statistics Netherlands (with contributions from the original
author teams of each solver module) and is distributed under the European
Union Public Licence (EUPL) v1.1 / EUPL-1.2. See `LICENSE`.

This software is distributed on an "AS IS" basis without warranties or
conditions of any kind, either express or implied.
