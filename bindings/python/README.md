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
docker run --rm -v "$PWD":/work ghcr.io/trygu/tauargus-engine run batch.arb
```

Pin a version with `ghcr.io/trygu/tauargus-engine:0.2.1`. To build your own image:

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
<OPENMETADATA>  "tau_testW.rda"
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
[data/](https://github.com/trygu/tauargus-engine/tree/rewrite/data) folder.

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

## Audit (Intervalle)

A suppressed cell has a range of values it could take while staying consistent
with the published totals — its **realized lower/upper bounds**, the
*feasibility interval*. Protection requires sufficient uncertainty to meet the
configured protection requirements. A narrow interval can reveal the original
value or constrain it too closely; interval width alone does not establish
protection. The audit checks for insufficient protection.

In legacy Tau-Argus this ran in a **separate** `intervalle.exe` (standalone
Delphi/Pascal executable); Tau-Argus wrote a `.JJ` file, launched it externally
and read the intervals back. The rewrite ports that logic into the engine
(`TauAuditJj` in the `csp` module), so it runs in-process over a temporary
`.JJ` file with nothing external to install:

```python
from pytauargus.engine import run_batch

engine = run_batch("demo.arb")
rows = engine.audit(0)   # one dict per suppressed cell:
# {"cell", "min", "max", "value", "status", "unsafe"}
```

The realized bounds are stored on the table (readable via `get_table_cell`).
`tauargus save demo.arb --audit --format intermediate` writes the legacy
INTERMEDIATE (type-5) audit file with the realized-interval columns.

## Python API

```python
from pytauargus.engine import run_batch

engine = run_batch("demo.arb")   # parse and execute; returns the Engine
```

Lower-level pieces: `pytauargus.batch.parse_batch(path)` returns the parsed
command list, and `pytauargus.engine.Engine` executes commands one at a time.

## Generating batch inputs

`pytauargus` also *writes* the batch inputs, as a port of
[rtauargus](https://github.com/InseeFrLab/rtauargus), so it emits the exact
formats the engine reads:

```python
from pytauargus.arb import micro_arb

micro_arb(
    asc_filename="donnees.asc",
    explanatory_vars=[["REGION"], ["SEXE"]],
    response_var="CA",
    safety_rules=["NK(1,85)", "FREQ(3,10)"],
    suppress="GH(.,100)",
    output_names=["tab1.csv", "tab2.csv"],
)
```

`micro_arb` writes a `.arb` batch; `pytauargus.hrc.write_hrc` writes `.hrc`
hierarchy files and `pytauargus.rda.write_rda` writes `.rda` metadata text.
The generator does not produce the fixed-width `.asc` microdata file itself;
it references that file by name.

## Example notebooks

`notebooks/` contains three **executed, output-saved** notebooks that double
as API documentation (every code cell runs against the verified public API):

| Notebook | Covers |
|----------|--------|
| [`01_quickstart`](notebooks/01_quickstart.ipynb) | import, the test data, `parse_rda`/`Metadata`, `run_batch`, table + cell inspection |
| [`02_protection_and_audit`](notebooks/02_protection_and_audit.ipynb) | safety rules → OPT/MOD/RND suppression → status distribution → `audit()` realized intervals (Intervalle) → export |
| [`03_generators`](notebooks/03_generators.ipynb) | `micro_arb`, `write_rda`/`rda_text`, `write_hrc`, generate→run round-trip |

Run them interactively, or headless (the same command CI could use):

```bash
# interactive
uv sync --extra notebooks
uv run --with jupyterlab jupyter lab notebooks/

# headless: execute every notebook and re-save its outputs
uv run --with nbclient --with nbformat --with ipykernel python notebooks/_run.py
```

`uv run --with nbclient --with nbformat --with ipykernel pytest -k notebooks`
executes them as tests too (the test skips when `nbclient` is absent, so the
default `uv run pytest` gate stays dependency-free).

## License

EUPL-1.2. Tau-Argus is (c) Statistics Netherlands.
