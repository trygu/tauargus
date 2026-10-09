"""Tests for the legacy ``.arb`` batch parser.

These pin the command sequence and per-command arguments for the sample
batch files, matching the grammar in ``src/tauargus/model/batch.java``.
"""

import pytest

from pytauargus.batch import (
    BatchError,
    OpenMicrodata,
    OpenTableData,
    OpenMetadata,
    SpecifyTable,
    SafetyRule,
    ReadMicrodata,
    ReadTable,
    Recode,
    GoInteractive,
    parse_batch,
)
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent.parent.parent / "data"


class TestTestRecode:
    def test_command_sequence(self):
        cmds = parse_batch(DATA / "TestRecode.arb")
        kinds = [type(c).__name__ for c in cmds]
        assert kinds == [
            "OpenMicrodata",
            "OpenMetadata",
            "SpecifyTable",
            "SafetyRule", "SafetyRule",
            "SpecifyTable",
            "SafetyRule", "SafetyRule",
            "ReadMicrodata",
            "Recode", "Recode", "Recode",
            "GoInteractive",
        ]

    def test_open_microdata(self):
        cmds = parse_batch(DATA / "TestRecode.arb")
        assert isinstance(cmds[0], OpenMicrodata)
        assert cmds[0].file == "tau_testW.asc"

    def test_open_metadata(self):
        cmds = parse_batch(DATA / "TestRecode.arb")
        assert isinstance(cmds[1], OpenMetadata)
        assert cmds[1].file == "tau_testW.rda"

    def test_table_1(self):
        cmds = parse_batch(DATA / "TestRecode.arb")
        t = cmds[2]
        assert isinstance(t, SpecifyTable)
        assert t.exp_vars == ["Size", "Region"]
        assert t.resp_var == "Var2"
        assert t.shadow_var == ""
        assert t.cost_var == ""

    def test_table_2(self):
        cmds = parse_batch(DATA / "TestRecode.arb")
        t = cmds[5]
        assert isinstance(t, SpecifyTable)
        assert t.exp_vars == ["Region", "IndustryCode"]
        assert t.resp_var == "Var2"

    def test_safety_rules(self):
        cmds = parse_batch(DATA / "TestRecode.arb")
        rules = [c for c in cmds if isinstance(c, SafetyRule)]
        assert [(r.kind, r.args) for r in rules] == [
            ("NK", ["2", "75"]), ("NK", ["0", "0"]),
            ("NK", ["2", "75"]), ("NK", ["0", "0"]),
        ]

    def test_read_microdata(self):
        cmds = parse_batch(DATA / "TestRecode.arb")
        assert isinstance(cmds[8], ReadMicrodata)

    def test_recodes(self):
        cmds = parse_batch(DATA / "TestRecode.arb")
        recs = [c for c in cmds if isinstance(c, Recode)]
        assert [(r.tab_no, r.var_name, r.recode_file) for r in recs] == [
            (1, "Size", "GK.grc"),
            (1, "Region", "2"),
            (2, "IndustryCode", "IndCode2.grc"),
        ]

    def test_go_interactive(self):
        cmds = parse_batch(DATA / "TestRecode.arb")
        assert isinstance(cmds[-1], GoInteractive)


class TestTableInput:
    def test_command_sequence(self):
        cmds = parse_batch(DATA / "tableinput" / "TestTable.arb")
        kinds = [type(c).__name__ for c in cmds]
        assert kinds == [
            "OpenTableData",
            "OpenMetadata",
            "SpecifyTable",
            "ReadTable",
            "GoInteractive",
        ]

    def test_open_table_data(self):
        cmds = parse_batch(DATA / "tableinput" / "TestTable.arb")
        assert isinstance(cmds[0], OpenTableData)
        assert cmds[0].file == "pp.tab"

    def test_specify_table_with_shadow_and_cost(self):
        cmds = parse_batch(DATA / "tableinput" / "TestTable.arb")
        t = cmds[2]
        assert t.exp_vars == ["Size", "Region"]
        assert t.resp_var == "Var2"
        assert t.shadow_var == "Var2_Shadow"
        assert t.cost_var == "Var2"

    def test_read_table(self):
        cmds = parse_batch(DATA / "tableinput" / "TestTable.arb")
        rt = cmds[3]
        assert isinstance(rt, ReadTable)
        assert rt.additivity == 1
        assert rt.keep_status is True


class TestSafetyRuleGrammar:
    """Unit tests for the safety-rule sub-grammar (P/NK/FREQ/WGT/ZERO/MAN/REQ)."""

    def _parse_rule(self, line: str):
        import tempfile, os
        from pytauargus.batch import Tokenizer
        # Build a minimal batch with a single table + one safety-rule line.
        body = (
            '<OPENMICRODATA> "x.asc"\n'
            '<OPENMETADATA> "x.rda"\n'
            '<SPECIFYTABLE> "A"|"R"|\n'
            f'<SAFETYRULE>       {line}\n'
            '<READMICRODATA>\n'
        )
        with tempfile.NamedTemporaryFile("w", suffix=".arb", delete=False) as f:
            f.write(body)
            path = f.name
        try:
            return [c for c in parse_batch(path) if isinstance(c, SafetyRule)]
        finally:
            os.unlink(path)

    def test_p_rule(self):
        rules = self._parse_rule("P(25,100,1)")
        assert [ (r.kind, r.args) for r in rules ] == [("P", ["25", "100", "1"])]

    def test_p_rule_two_args(self):
        rules = self._parse_rule("P(5,1)")
        assert [ (r.kind, r.args) for r in rules ] == [("P", ["5", "1"])]

    def test_multiple_rules_pipe(self):
        rules = self._parse_rule("P(25,100,1)|NK(2,75)|FREQ(1,30)")
        assert [ (r.kind, r.args) for r in rules ] == [
            ("P", ["25", "100", "1"]),
            ("NK", ["2", "75"]),
            ("FREQ", ["1", "30"]),
        ]

    def test_wgt_rule(self):
        rules = self._parse_rule("WGT(1)")
        assert [ (r.kind, r.args) for r in rules ] == [("WGT", ["1"])]


class TestErrorHandling:
    def test_unknown_keyword(self):
        import tempfile, os
        body = '<BADOPT> 1\n'
        with tempfile.NamedTemporaryFile("w", suffix=".arb", delete=False) as f:
            f.write(body)
            path = f.name
        try:
            with pytest.raises(BatchError):
                parse_batch(path)
        finally:
            os.unlink(path)

    def test_readmicrodata_out_of_order(self):
        import tempfile, os
        # READMICRODATA before any table/safety -> status != STATUS_SAFETY
        body = '<READMICRODATA>\n'
        with tempfile.NamedTemporaryFile("w", suffix=".arb", delete=False) as f:
            f.write(body)
            path = f.name
        try:
            with pytest.raises(BatchError):
                parse_batch(path)
        finally:
            os.unlink(path)
