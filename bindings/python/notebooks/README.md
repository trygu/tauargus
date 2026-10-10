# pytauargus example notebooks

Three executed, output-saved notebooks that double as API documentation. Every
code cell runs against the verified public API; the markdown explains the
surface it exercises.

| # | Notebook | What it covers |
|---|----------|----------------|
| 1 | [`01_quickstart.ipynb`](01_quickstart.ipynb) | import, the test data, `parse_rda`/`Metadata`, `run_batch`, table + cell inspection |
| 2 | [`02_protection_and_audit.ipynb`](02_protection_and_audit.ipynb) | safety rules → OPT/MOD/RND suppression → status distribution → `audit()` realized feasibility intervals (Intervalle) → CSV / INTERMEDIATE export |
| 3 | [`03_generators.ipynb`](03_generators.ipynb) | `micro_arb`, `write_rda`/`rda_text`, `write_hrc`, and a generate→run round-trip |

## Running

From `bindings/python/`:

```bash
# interactive
uv sync --extra notebooks
uv run --with jupyterlab jupyter lab notebooks/

# headless: execute every notebook and re-save its outputs
uv run --with nbclient --with nbformat --with ipykernel python notebooks/_run.py
```

The notebooks locate the repo `data/` fixtures by walking up from the current
directory, and write their scratch outputs to `notebooks/out/` (gitignored).

`tests/test_notebooks.py` executes the same notebooks under pytest (it skips
when `nbclient` is not installed, keeping the default `uv run pytest` gate
fast and dependency-free).

## Helpers

- `_build.py` — regenerates the `.ipynb` files from the cells defined in the
  script (the single source of truth for notebook content).
- `_run.py` — executes the notebooks with `nbclient` and saves outputs.
