"""Tests for the one-call :func:`pytauargus.protect` pipeline.

Split by native-engine risk:

* ``run=False`` (write the ``.asc``/``.rda``/``.arb`` only) is pure Python and
  runs in-process — deterministic and fast.
* the full run (suppress + write ``.tab`` -> :class:`TableResult`) drives the
  native HiGHS solver, so it runs in a *fresh subprocess* (one solver per
  process; multiple solvers in one process can segfault — see ``test_cli.py``).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pytauargus.protect import protect, ProtectResult

SRC = Path(__file__).resolve().parent.parent / "src"

# A small 2-dim microdata: 2 x 2 categorical crossing, numeric response.
# Region x Size, response "Val". Small enough that a single OPT solve is fast.
MICRO = {
    "Region": ["Os", "Os", "Ws", "Ws"],
    "Size": ["1", "2", "1", "2"],
    "Var2": [10.0, 20.0, 30.0, 40.0],
}


# ===========================================================================
# run=False — file generation only (no native engine)
# ===========================================================================
def test_run_false_writes_files(tmp_path):
    res = protect(MICRO, ["Region", "Size"], response="Var2",
                  safety_rules="P(25)", run=False,
                  workdir=str(tmp_path))

    assert isinstance(res, ProtectResult)
    # input + batch files are written; the .tab output is only written when
    # the engine actually runs (run=True), so it is absent here.
    for key in ("asc", "rda", "arb"):
        assert key in res.files, f"missing {key} in {res.files}"
        assert Path(res.files[key]).exists(), f"{key} not written"
    assert "tab1" in res.files
    assert not Path(res.files["tab1"]).exists()
    assert res.tables == []
    assert res.engine is None
    assert res.workdir == str(tmp_path)


def test_run_false_arb_content(tmp_path):
    res = protect(MICRO, ["Region", "Size"], response="Var2",
                  safety_rules="P(25)", suppress="OPT(.,9)", run=False,
                  workdir=str(tmp_path))
    arb = Path(res.files["arb"]).read_text(encoding="utf-8")
    assert '<OPENMICRODATA>' in arb and res.files["asc"] in arb
    assert '<OPENMETADATA>' in arb and res.files["rda"] in arb
    # SPECIFYTABLE: quoted expl vars + response, no shadow/cost
    assert '<SPECIFYTABLE> "Region""Size"|"Var2"||' in arb
    assert '<SAFETYRULE> P(25)' in arb
    # SUPPRESS: the first paren arg is the table number (placeholder -> 1);
    # the max-time (,9) is preserved.
    assert "<SUPPRESS> OPT(1,9)" in arb
    # WRITETABLE: simple intermediate (SO+) to the tab file
    assert ('<WRITETABLE> (1,5,SO+,"%s")' % res.files["tab1"]) in arb


def test_run_false_arb_content_no_rules(tmp_path):
    res = protect(MICRO, ["Region", "Size"], response="Var2", run=False,
                  workdir=str(tmp_path))
    arb = Path(res.files["arb"]).read_text(encoding="utf-8")
    # no safety rule -> bare <SAFETYRULE> (empty = use given status)
    assert "<SAFETYRULE> " in arb
    # default suppress OPT(1)
    assert "<SUPPRESS> OPT(1)" in arb


def test_run_false_rda_types(tmp_path):
    """to_microdata type inference flows into the .rda variable types."""
    res = protect(MICRO, ["Region", "Size"], response="Var2", run=False,
                  workdir=str(tmp_path))
    rda = Path(res.files["rda"]).read_text(encoding="utf-8").upper()
    # categorical (character) variables
    assert "REGION" in rda and "SIZE" in rda
    # response is numeric
    assert "NUMERIC" in rda


def test_multi_table_recycling(tmp_path):
    res = protect(MICRO, [["Region"], ["Size"]], response="Var2",
                  safety_rules="P(25)", run=False, workdir=str(tmp_path))
    arb = Path(res.files["arb"]).read_text(encoding="utf-8")
    assert '<SPECIFYTABLE> "Region"|"Var2"||' in arb
    assert '<SPECIFYTABLE> "Size"|"Var2"||' in arb
    # single suppress spec -> table numbers recalculated 1,2
    assert "<SUPPRESS> OPT(1)" in arb
    assert "<SUPPRESS> OPT(2)" in arb
    assert "tab1" in res.files and "tab2" in res.files


def test_requires_response():
    with pytest.raises(TypeError):
        protect(MICRO, ["Region", "Size"], response=None, run=False,
                workdir="/tmp")


def test_accepts_list_of_dicts(tmp_path):
    rows = [{"Region": r, "Size": s, "Var2": v}
            for (r, s), v in zip(zip(MICRO["Region"], MICRO["Size"]),
                                 MICRO["Var2"])]
    res = protect(rows, ["Region", "Size"], response="Var2", run=False,
                  workdir=str(tmp_path))
    assert Path(res.files["asc"]).exists()


# ===========================================================================
# Full run — subprocess isolation (native solver)
# ===========================================================================
def _run_protect_subprocess(micro, tables, response, suppress):
    code = (
        "import json\n"
        "from pytauargus.protect import protect\n"
        f"res = protect(json.loads({json.dumps(micro)!r}), "
        f"json.loads({json.dumps(tables)!r}), response={response!r}, "
        f"safety_rules='P(25,1000)', suppress={suppress!r})\n"
        "out = {\n"
        "  'n_tables': len(res.tables),\n"
        "  'files': res.files,\n"
        "  'results': [\n"
        "     {'n': t.n_cells, 'status': t.status(), 'safe': t.safe(),\n"
        "      'unsafe': t.unsafe(), 'cols': t.columns}\n"
        "     for t in res.tables],\n"
        "}\n"
        "print(json.dumps(out))\n"
    )
    env = dict(os.environ, PYTHONPATH=str(SRC) + os.pathsep
               + os.environ.get("PYTHONPATH", ""))
    # The real work is done before the native HiGHS solver tears down, so we
    # treat a valid JSON payload on stdout as success. The interpreter can
    # still die during HiGHS teardown (the documented fragility — see
    # test_cli.py / test_suppress.py): a non-zero rc *after* the JSON is
    # printed (teardown segfault) is fine, but a process killed by a signal
    # with no output at all (e.g. rc=-9 under full-suite resource contention)
    # is transient, so retry once before failing.
    proc = None
    for attempt in range(2):
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, env=env,
            cwd=str(Path(__file__).resolve().parent),
        )
        if proc.stdout.strip():
            break
        if proc.returncode >= 0 or attempt == 1:
            break  # real failure (Python error) or retries exhausted
    out_text = proc.stdout.strip()
    if not out_text:
        raise AssertionError(
            "protect() subprocess produced no output (rc=%s):\nSTDERR:\n%s"
            % (proc.returncode, proc.stderr))
    try:
        return json.loads(out_text.splitlines()[-1])
    except json.JSONDecodeError:
        raise AssertionError(
            "protect() subprocess produced invalid JSON (rc=%s):\nSTDOUT:\n%s\n"
            "STDERR:\n%s" % (proc.returncode, proc.stdout, proc.stderr))


def test_protect_full_run_subprocess():
    out = _run_protect_subprocess(MICRO, [["Region", "Size"]], "Var2", "OPT(1)")
    assert out["n_tables"] == 1
    r = out["results"][0]
    # 2 x 2 crossing + total rows/cols (the rda carries <TOTCODE> "Total")
    # -> 3 x 3 = 9 cells
    assert r["n"] == 9
    assert r["cols"] == ["Region", "Size", "Var2", "freq", "cost",
                         "status", "lower", "upper"]
    assert len(r["status"]) == 9
    assert set(r["status"]) <= {"S", "U", "P", "M", "E"}
    # the tab file was actually written
    assert Path(out["files"]["tab1"]).exists()
    # status/safe/unsafe align row-wise
    for st, sf in zip(r["status"], r["safe"]):
        if st in ("U", "M"):
            assert sf == "x"
        else:
            assert isinstance(sf, (int, float))
