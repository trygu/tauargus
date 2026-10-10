# pytauargus

Statistical disclosure control (SDC) for tabular data, as a Python package and
a headless `tauargus` command. It runs legacy Tau-Argus 4.1 `.arb` batch files
without the GUI and solves with the open-source
[HiGHS](https://github.com/ERGO-Code/HiGHS) solver. Part of
[tauargus-engine](https://github.com/trygu/tauargus).

## Install

```bash
pip install pytauargus
tauargus --version
```

Wheels bundle HiGHS and the native engine; no other installation is needed.
Available for Python 3.10-3.13 on macOS arm64, Linux x86_64 and aarch64 (manylinux_2_28) and
Windows x64. Other platforms: build from source (see the repository).

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

Pin a version with `ghcr.io/trygu/tauargus:0.1.1`. To build your own image:

```dockerfile
FROM python:3.12-slim
RUN pip install --no-cache-dir pytauargus
WORKDIR /work
ENTRYPOINT ["tauargus"]
```

## What problem it solves

Publishing a table can disclose information about individual respondents: a
cell with few contributors, or one dominated by a single contributor. Such
*primary* cells are suppressed, but totals would still reveal them, so *secondary*
cells are suppressed as well, chosen to minimise information loss. Alternatively
the table can be controlled-rounded. `tauargus` does this from a batch file.

## Quick start

Put the data (`.asc`), its metadata (`.rda`) and a batch file in one folder.
Paths in a batch file are relative to the working directory.

```text
<OPENMICRODATA> "tau_testW.asc"
<OPENMETADATA>  "Tau_TestW.rda"
<SPECIFYTABLE>  "Size""Region"|"Var2"||
<SAFETYRULE>    NK(2,75)|NK(0,0)
<READMICRODATA>
<SUPPRESS>      MOD(1)
<WRITETABLE>    (1,3,AS-,"safe-table.txt")
```

```bash
tauargus run demo.arb
```

This reads the microdata, builds the Size x Region table of `Var2`, flags cells
failing the dominance rule `NK(2,75)` (two largest contributors may not make up
more than 75 %), applies secondary suppression with the modular method, and
writes the protected table as code/value pairs, with suppressed values masked.
The sample inputs are in the repository's
[data/](https://github.com/trygu/tauargus/tree/rewrite/data) folder.

## Batch file commands

| Command | Purpose |
|---------|---------|
| `<OPENMICRODATA>` / `<OPENTABLEDATA>` | Input data file (microdata or a ready table) |
| `<OPENMETADATA>` | `.rda` metadata describing the file layout and variables |
| `<SPECIFYTABLE>` | Explanatory variables, response, shadow and cost variables |
| `<SAFETYRULE>` | Sensitivity rules, e.g. `P(p,n)`, `NK(n,k)`, `FREQ(min,safety)` |
| `<READMICRODATA>` / `<READTABLE>` | Build or read the tables |
| `<RECODE>` | Recode a variable, e.g. via a `.grc` file |
| `<SUPPRESS>` | Protection method: `GH`, `MOD`, `OPT`, `NET`, `RND` (rounding), `CTA` |
| `<WRITETABLE>` | Export: `(TabNo,Type,Options,"file")`; types 1 CSV, 2 pivot CSV, 3 code/value, 4 SBS, 5 intermediate, 6 JJ |
| `<SOLVER>` | Accepted for compatibility; only HiGHS is used. Other names log a warning |
| `<LOGBOOK>` | Write a log file |

The grammar and parameters follow the legacy Tau-Argus 4.1 manual.

## Command line

```bash
tauargus run      batch.arb   # execute the whole batch
tauargus explore  batch.arb   # load data + metadata, list variables
tauargus compute  batch.arb   # table computation only
tauargus suppress batch.arb   # compute, then apply suppression
tauargus round    batch.arb   # compute, then round
tauargus audit    batch.arb   # feasibility intervals of suppressed cells
tauargus save     batch.arb   # compute, then write tables
tauargus tables   batch.arb   # print a table summary
tauargus version
```

Exit code is 0 on success and non-zero on an error, with a message on stderr,
so it fits into scripts and pipelines.

## Python API

```python
from pytauargus.engine import run_batch

engine = run_batch("demo.arb")   # parse and execute; returns the Engine
```

Lower-level pieces: `pytauargus.batch.parse_batch(path)` returns the parsed
command list, and `pytauargus.engine.Engine` executes commands one at a time.

## License

EUPL-1.2. Tau-Argus is (c) Statistics Netherlands.
