# tauargus-engine

A native rewrite of **τ-ARGUS**, the statistical disclosure control (SDC)
engine used by statistics agencies to anonymize official statistics before
publication.

## What it does

When a statistics agency publishes a table (population, income, employment,
...), small cell counts can reveal who is who — if only 2 people in a region
fall into an income band, their records are effectively identifiable. SDC
prevents that before publication:

- **Suppression** — hide the cells that would give too much away, without
  making the table useless.
- **Controlled rounding** — round cells to a base (e.g. 5 or 10) so no
  individual value is identifiable, while keeping row and column totals
  consistent.
- **Auditing** — check that the published table cannot be reversed to
  recover the original data.

τ-ARGUS runs this whole pipeline from a declarative `.arb` batch file:
load microdata → compute tables → suppress or round → audit → save. This
rewrite is a **drop-in replacement for legacy τ-ARGUS 4.1**: same batch
files, same file I/O, same output.

## How it works

The engine is C++, built from five modules that converge on the open-source
[HiGHS](https://github.com/ERGO-Code/HiGHS) solver (the legacy commercial
CPLEX/XPRESS/SCIP backends are gone):

| Module | Role |
|--------|------|
| `core`   | Data model, Argus/JJ file I/O, SDC engine entry points |
| `csp`    | Cell-suppression LP (branch-and-price) + feasibility audit |
| `hitas`  | Hierarchical table suppression (HiTaS) |
| `crp`    | Controlled rounding (iterative rounding + audit) |
| `rounder`| Dispatch layer over `crp` |

A Python binding (`pytauargus`) wraps the engine and provides the
**`tauargus`** command-line tool:

```
.arb batch  →  tauargus CLI  →  native engine  →  HiGHS
```

## Quick start

```bash
# from the source tree
cd bindings/python
uv sync
uv run tauargus run ../../data/TestRecode.arb
```

Or install the `tauargus` command from a built wheel:

```bash
uv build --wheel
uv tool install --force --reinstall dist/pytauargus-*.whl
```

## Using the CLI

```bash
tauargus run      mybatch.arb    # parse and execute a batch file
tauargus compute  mybatch.arb    # table computation only
tauargus suppress mybatch.arb    # compute, then apply suppression
tauargus round    mybatch.arb    # compute, then round
tauargus audit    mybatch.arb    # audit: feasibility intervals of suppressed cells
tauargus save     mybatch.arb    # compute, then write tables
tauargus tables   mybatch.arb    # print a table summary
```

Example fixtures live in `data/`.

## Requirements

- CMake ≥ 3.16, a C++11 toolchain
- **HiGHS** with its CMake package: `brew install highs` (macOS),
  `sudo apt-get install libhighs-dev` (Linux)
- Python 3.10+ and [`uv`](https://docs.astral.sh/uv/) for the Python layer

## Building from source

Build the native engine:

```bash
cmake -S engine -B engine/build \
      -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs
cmake --build engine/build -j
```

Build the Python package (scikit-build-core drives the CMake build and
compiles the pybind11 module):

```bash
cd bindings/python
uv sync
uv build --wheel
```

> For fast in-tree iteration on the C++ bindings, configure against
> `bindings/python/CMakeLists.txt` in a local `build-make/` dir and point
> `-Dpybind11_DIR` at the venv.

## Testing

```bash
cd bindings/python
uv sync --extra test
uv run pytest        # 99 tests: native contracts + engine + CLI
```

## Project layout

```
.
├── engine/                 # C/C++ engine — language-agnostic core
│   ├── CMakeLists.txt      #   superbuild: configures & builds all five submodules
│   └── native/             #   the 5 git submodules
│       ├── core/           #     data model, Argus/JJ I/O, SDC engine (static lib)
│       ├── csp/            #     cell-suppression LP + feasibility audit (HiGHS LP)
│       ├── hitas/          #     hierarchical suppression (links csp)
│       ├── crp/            #     controlled-rounding (HiGHS MIP)
│       └── rounder/        #     thin dispatch layer over crp
│
├── bindings/               # per-language front-ends (Python now, R planned)
│   └── python/             #   pybind11 bindings + `pytauargus` package
│       ├── cpp/            #     bindings: bind_core/csp/hitas/rounder + module.cpp
│       ├── src/pytauargus/ #     the Python package (engine.py, cli.py, batch.py)
│       └── tests/          #     pytest suite (99 tests)
│
├── data/                   # sample `.arb` batches + tabular fixtures
├── reference/              # read-only reference implementations
│   ├── intervale/          #   legacy intervall.exe audit (Pascal/FPC)
│   └── rtauargus/          #   (planned) R package — oracle for cross-checking
├── docs/                   # legacy τ-ARGUS 4.1 manual bundle + design notes
└── src/                    # legacy Java/Swing front-end (read-only, pending deletion)
```

## License

τ-ARGUS is © Statistics Netherlands (with contributions from the original
author teams of each solver module) and is distributed under the European
Union Public Licence (EUPL) v1.1 / EUPL-1.2. See `LICENSE`.

This software is distributed on an "AS IS" basis without warranties or
conditions of any kind, either express or implied.
