# tauargus-engine

Native, headless engine for statistical disclosure control (SDC) of tabular
data, plus a Python tool that drives it. It is a drop-in replacement for the
batch mode of legacy Tau-Argus 4.1: same `.arb` batch files, file formats and
outputs, without the GUI.

The project has two parts:

- **tauargus-engine** (`engine/`): the C/C++ libraries that do the work, built
  against the open-source [HiGHS](https://github.com/ERGO-Code/HiGHS) solver.
  The legacy CPLEX, XPRESS and SCIP backends are gone.
- **pytauargus** (`bindings/python/`): the Python package and `tauargus`
  command-line tool that link those libraries. Wheels bundle HiGHS and the
  engine.

## Relationship to the original Tau-Argus

This is the original Tau-Argus solver code, not a reimplementation:

- **Engine:** the C/C++ code is largely unchanged. The changes make it build
  with a modern toolchain (CMake, current GCC/Clang/MSVC), switch the solver
  backend to HiGHS, and make it self-contained.
- **Audit:** the standalone `intervalle.exe` audit program (Delphi, i.e. modern Pascal) is ported
  into the `csp` engine module, so the feasibility-interval audit runs in-process
  instead of as a separate executable.
- **Python package:** `pytauargus` is new. Its function signatures and way of
  working are borrowed from [rtauargus](https://github.com/InseeFrLab/rtauargus),
  the R wrapper around Tau-Argus.

## Install

From [PyPI](https://pypi.org/project/pytauargus/):

```bash
pip install pytauargus          # into the current environment
uv tool install pytauargus      # or: pipx install pytauargus (isolated, puts `tauargus` on PATH)
tauargus --version
```

Use it from Python as well:

```python
from pytauargus.engine import run_batch

run_batch("mybatch.arb")
```

Wheels bundle HiGHS and the engine libraries, so nothing else needs installing.
They are built for Python 3.10-3.13 on:

| Platform | Architecture |
|----------|--------------|
| macOS    | arm64 (Apple Silicon) |
| Linux (manylinux_2_28) | x86_64, aarch64 |
| Windows  | x64 |

Intel Macs and Windows ARM are not built, and there is no source
distribution; on those platforms see [Building from source](#building-from-source).
The same wheels are attached to each
[GitHub Release](https://github.com/trygu/tauargus/releases).

## Cloud native

Built to run unattended in containers, CI and batch services:

- **Headless:** no GUI, no display, no interactive prompts.
- **Self-contained:** one `pip install`; the solver (HiGHS) and native libraries
  are bundled in the wheel. No licensed solver, license server, system packages
  or Windows registry.
- **Stateless:** input and output are plain files in the working directory;
  scratch files go to the system temp directory.
- **Scriptable:** success is exit code 0; errors go to stderr with a non-zero
  exit code.
- **Portable:** wheels for Linux (manylinux_2_28, so any glibc 2.28+ image such
  as `python:3.x-slim`), macOS arm64 and Windows x64.

A ready-made image is published to GitHub Container Registry with each release
(linux/amd64 and linux/arm64):

```bash
docker run --rm -v "$PWD":/work ghcr.io/trygu/tauargus run batch.arb
```

Pin a version with `ghcr.io/trygu/tauargus:0.2.0`. To build your own image:

```dockerfile
FROM python:3.12-slim
RUN pip install --no-cache-dir pytauargus
WORKDIR /work
ENTRYPOINT ["tauargus"]
```

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

`<SOLVER>` tags in a batch file are accepted, but only HiGHS is used; any
other solver name logs a warning and the job continues.

Sample batches and fixtures are in [data/](data). The batch grammar, file
formats and parameters follow the legacy Tau-Argus 4.1 manual, which is bundled
in [docs/](docs).

## Writing batch inputs

Beyond running batches, `pytauargus` can *generate* them. The generator is a
port of [rtauargus](https://github.com/InseeFrLab/rtauargus), the R wrapper, so
it emits the exact file formats the engine reads:

```python
from pytauargus.arb import micro_arb

# writes a .arb batch: two tables (REGION, then SEXE) of the response var CA
micro_arb(
    asc_filename="donnees.asc",
    explanatory_vars=[["REGION"], ["SEXE"]],
    response_var="CA",
    safety_rules=["NK(1,85)", "FREQ(3,10)"],
    suppress="GH(.,100)",
    output_names=["tab1.csv", "tab2.csv"],
)
```

`pytauargus.hrc.write_hrc` produces `.hrc` hierarchy files and
`pytauargus.rda.write_rda` writes `.rda` metadata text. The generator does not
produce the fixed-width `.asc` microdata file itself (that step stays in your
pipeline); it references it by name.

## What it does

SDC reduces the risk that published tables disclose information about
individual respondents or businesses. A cell can be sensitive because too few
respondents contribute, a few dominate, or another contributor could estimate
a contribution. Deleting the value is often not enough, because totals and
bounds can reveal it, so related cells are protected too. This is the tabular
counterpart to [mu-Argus](https://github.com/INSEE/Argus), which protects
microdata.

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

## Audit (Intervalle)

After suppression, each suppressed cell still has a *range* of values it could
take and stay consistent with the published totals: its **realized lower and
upper bounds** (the *feasibility interval*). A suppressed cell is only truly
protected if that interval is small enough that the original value is no longer
reconstructible; a wide interval means the cell is still effectively *unsafe*.

In legacy Tau-Argus this was a **separate program** — `intervalle.exe`, a
standalone Delphi/Pascal executable. Tau-Argus wrote a `.JJ` file, launched the
executable externally, and read the intervals back. The operator had to install
it and keep it on the path, so it was the one part of the pipeline that did not
run in-process.

The rewrite folds it in: the audit logic is ported into the `csp` engine module
(`TauAuditJj`), so it runs in-process over a temporary `.JJ` file and needs
nothing external. Use it three ways:

- **CLI:** `tauargus audit mybatch.arb` — compute, suppress, then report each
  suppressed cell's realized interval and whether it is still unsafe.
- **Python:** `engine.audit(tab)` — returns one row per suppressed cell
  (`cell`, `min`, `max`, `value`, `status`, `unsafe`); the realized bounds are
  also stored on the table and readable via `get_table_cell`.
- **Export:** `tauargus save mybatch.arb --audit --format intermediate` writes
  the legacy INTERMEDIATE (type-5) audit file, including the realized-interval
  columns.

## Architecture

```
.arb batch  ->  tauargus CLI  ->  pytauargus  ->  tauargus-engine (C/C++)  ->  HiGHS
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
├── docs/        legacy Tau-Argus 4.1 manual and design notes
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
[LICENSE](LICENSE). Tau-Argus is © Statistics Netherlands, with contributions
from the original author teams of each solver module.

This software is provided "AS IS", without warranties or conditions of any
kind, express or implied.
