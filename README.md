# τ-ARGUS (native engine + CLI)

A native, headless rewrite of **τ-ARGUS**, the statistical disclosure control
(SDC) tool statistics agencies use to protect tabular data before publication.
It ships as the `tauargus` command-line tool and the `pytauargus` Python
package, and aims to be a drop-in replacement for legacy τ-ARGUS 4.1 batch
runs: same `.arb` batch files, same file I/O, same outputs.

- Runs `.arb` batch files without a GUI, so it suits servers and pipelines.
- Uses the open-source [HiGHS](https://github.com/ERGO-Code/HiGHS) solver. The
  legacy CPLEX, XPRESS and SCIP backends are gone.
- Self-contained wheels bundle HiGHS and the engine libraries.

## Install

Download a wheel for your platform from the
[GitHub Releases](https://github.com/trygu/tauargus/releases) page, then:

```bash
uv tool install ./pytauargus-*.whl     # or: pipx install ./pytauargus-*.whl
tauargus --version
```

Wheels are built for Python 3.10–3.13 on:

| Platform | Architecture |
|----------|--------------|
| macOS    | arm64 (Apple Silicon) |
| Linux (manylinux_2_28) | x86_64 |
| Windows  | x64 |

Intel Macs, Linux ARM and Windows ARM are not built. Wheels are also published to PyPI
when the maintainers enable it; otherwise use the Releases page.

## Quick start

```bash
tauargus run data/TestRecode.arb
```

## Command-line usage

```bash
tauargus run      mybatch.arb    # parse and execute a batch file
tauargus compute  mybatch.arb    # table computation only
tauargus suppress mybatch.arb    # compute, then apply suppression
tauargus round    mybatch.arb    # compute, then round
tauargus audit    mybatch.arb    # feasibility intervals of suppressed cells
tauargus save     mybatch.arb    # compute, then write tables
tauargus tables   mybatch.arb    # print a table summary
```

Sample batches and fixtures are in [data/](data). The batch grammar, file
formats and parameters follow the legacy τ-ARGUS 4.1 manual, which is bundled
in [docs/](docs).

## What τ-ARGUS does

It reduces the risk that published tables disclose information about
individual respondents or businesses. A cell can be sensitive because too few
respondents contribute, a few dominate, or another contributor could estimate
a contribution. Deleting the value is often not enough, because totals and
bounds can reveal it, so τ-ARGUS also protects related cells. It is the
tabular counterpart to [μ-ARGUS](https://github.com/INSEE/Argus), which
protects microdata.

A batch file drives the whole pipeline:

```text
input data + metadata
  -> define table dimensions and response
  -> define sensitivity rules and protection requirements
  -> construct or read the table
  -> identify primary sensitive cells
  -> protect: secondary suppression + audit, or controlled rounding
  -> write release table + report
```

## Architecture

```
.arb batch  ->  tauargus CLI  ->  pytauargus  ->  native C++ engine  ->  HiGHS
```

The engine is C++11, built from five git submodules under `engine/native/`:

| Module   | Role |
|----------|------|
| `core`   | Data model, Argus/JJ file I/O, SDC engine entry points |
| `csp`    | Cell-suppression LP (branch-and-price) and feasibility audit |
| `hitas`  | Hierarchical table suppression (HiTaS); links `csp` |
| `crp`    | Controlled rounding (iterative rounding, audit) |
| `rounder`| Dispatch layer over `crp` |

```
.
├── engine/      C/C++ engine; CMakeLists.txt is a superbuild of the 5 submodules
├── bindings/
│   └── python/  pybind11 bindings (cpp/), pytauargus package (src/), tests/
├── data/        sample .arb batches and tabular fixtures
├── docs/        legacy τ-ARGUS 4.1 manual and design notes
└── src/         legacy Java/Swing front-end (read-only, pending removal)
```

## Building from source

Requirements:

- CMake ≥ 3.16 and a C++11 compiler
- Python 3.10+ and [uv](https://docs.astral.sh/uv/)
- [HiGHS](https://github.com/ERGO-Code/HiGHS) with its CMake package:
  `brew install highs` (macOS), `sudo apt-get install libhighs-dev`
  (Debian/Ubuntu), or [build from source](https://github.com/ERGO-Code/HiGHS#building)

Clone with submodules (`git clone --recurse-submodules`), then build the
Python package. scikit-build-core drives CMake and compiles the pybind11
module:

```bash
cd bindings/python
uv sync                                          # environment + native extension
uv build --wheel                                 # dist/pytauargus-*.whl
uv tool install --force dist/pytauargus-*.whl    # puts `tauargus` on PATH
```

To build only the native engine:

```bash
cmake -S engine -B engine/build -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs
cmake --build engine/build -j
```

Wheels built this way link HiGHS at its install path. The release wheels
bundle it; see [wheels.yml](.github/workflows/wheels.yml).

## Testing

```bash
cd bindings/python
uv sync --extra test
uv run pytest
```

## License

Distributed under the European Union Public Licence (EUPL) v1.2; see
[LICENSE](LICENSE). τ-ARGUS is © Statistics Netherlands, with contributions
from the original author teams of each solver module.

This software is provided "AS IS", without warranties or conditions of any
kind, express or implied.
