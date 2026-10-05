"""High-level Tau-Argus engine driving the native C++ bindings.

Usage:
    from tauargus.engine import Engine, parse_rda, run_batch
    eng = Engine()
    eng.run_batch("data/TestRecode.arb")

Or drive the native engine manually:
    eng = Engine()
    meta = parse_rda("data/tau_testW.rda")
    eng.open_microdata("data/tau_testW.asc", meta)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from ._tauargus import TauArgus, HiTaSCtrl, RounderCtrl
from .batch import (
    BatchError,
    Command,
    OpenMicrodata,
    OpenTableData,
    OpenMetadata,
    SpecifyTable,
    SafetyRule,
    ReadMicrodata,
    ReadTable,
    Apriory,
    Cover,
    Suppress,
    WriteTable,
    Recode,
    Solver,
    GoInteractive,
    Logbook,
    VersionInfo,
    Anco,
    Clear,
    Tokenizer,
    parse_batch,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# Variable dataclass (parsed from .rda)
# ===========================================================================
@dataclass
class Variable:
    name: str
    index: int = 0
    b_pos: int = 1
    var_len: int = 0
    n_decimals: int = 0
    in_table: bool = False
    missing: List[str] = field(default_factory=lambda: ["", ""])
    tot_code: str = ""
    # type (mirrors Java Type enum)
    type: str = "CAT_RESP"  # CATEGORICAL, RESPONSE, CAT_RESP, WEIGHT, HOLDING,
                            # REQUEST, SHADOW, COST, FREQUENCY, TOP_N,
                            # LOWER_PROTECTION_LEVEL, UPPER_PROTECTION_LEVEL,
                            # STATUS, RECORD_KEY
    # categorical fields
    has_distance_function: bool = False
    distance_function: List[int] = field(default_factory=lambda: [0] * 5)
    code_list_file: str = ""
    hierarchical: int = 0  # 0=NONE, 1=LEVELS, 2=FILE
    hier_levels: List[int] = field(default_factory=list)
    hier_levels_sum: int = 0
    hier_file_name: str = ""
    leading_string: str = "."
    # CKM / record-key
    p_table_file: str = ""
    p_table_file_cont: str = ""
    p_table_file_sep: str = ""
    ckm_type: str = "N"
    ckm_top_k: int = 1
    ckm_scaling: str = ""
    ckm_sigma0: float = -1
    ckm_sigma1: float = -1
    ckm_xstar: float = -1
    ckm_q: float = -1
    ckm_epsilon: List[float] = field(default_factory=list)
    ckm_separation: bool = False
    ckm_zeros: bool = False
    ckm_parity: bool = False
    # request
    request_code: List[str] = field(default_factory=lambda: ["", ""])
    # misc
    recoded: bool = False
    truncatable: bool = False

    @property
    def is_categorical(self) -> bool:
        return self.type in ("CATEGORICAL", "CAT_RESP")

    @property
    def is_response(self) -> bool:
        return self.type in ("RESPONSE", "CAT_RESP")

    @property
    def is_numeric(self) -> bool:
        return self.type in (
            "CATEGORICAL", "CAT_RESP", "RESPONSE", "WEIGHT",
            "SHADOW", "COST", "FREQUENCY", "TOP_N",
            "LOWER_PROTECTION_LEVEL", "UPPER_PROTECTION_LEVEL",
            "RECORD_KEY",
        )

    @property
    def is_weight(self) -> bool:
        return self.type == "WEIGHT"

    @property
    def is_holding(self) -> bool:
        return self.type == "HOLDING"

    @property
    def is_request(self) -> bool:
        return self.type == "REQUEST"

    @property
    def is_record_key(self) -> bool:
        return self.type == "RECORD_KEY"

    def n_missings(self) -> int:
        n = 0
        while n < 2 and self.missing[n]:
            n += 1
        return n

    def get_total_code(self) -> str:
        return self.tot_code if self.tot_code else "Total"


@dataclass
class Metadata:
    variables: List[Variable] = field(default_factory=list)
    data_file: str = ""
    meta_file: str = ""
    field_separator: str = ";"
    is_table: bool = False
    safe_status: str = "S"
    unsafe_status: str = "U"
    protect_status: str = "P"

    def find(self, name: str) -> Optional[Variable]:
        for v in self.variables:
            if v.name.lower() == name.lower():
                return v
        return None

    def index_of(self, name: str) -> int:
        for i, v in enumerate(self.variables):
            if v.name.lower() == name.lower():
                return i
        return -1

    def contains(self, vtype: str) -> bool:
        return any(v.type == vtype for v in self.variables)


# ===========================================================================
# .rda parser
# ===========================================================================
def parse_rda(path: Union[str, Path]) -> Metadata:
    """Parse a legacy Tau-Argus ``.rda`` metadata file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    tok = Tokenizer(text)
    meta = Metadata(meta_file=str(path))
    variable: Optional[Variable] = None
    ckmspecified = False

    while tok.next_line() is not None:
        token = tok.next_token()
        if token == "":
            continue

        if token.startswith("<"):
            if token == "<SEPARATOR>" and tok.line_number == 1:
                meta.field_separator = tok.next_token()
                continue
            if token == "<SPSS>" and tok.line_number == 1:
                continue

            if variable is None:
                raise BatchError("A variable should be declared before giving its properties")

            # -- variable property tags --------------------------------------
            if token in ("<RECODEABLE>", "<RECODABLE>"):
                if variable.type == "RESPONSE":
                    variable.type = "CAT_RESP"
                else:
                    variable.type = "CATEGORICAL"
            elif token == "<TOTCODE>":
                variable.tot_code = tok.next_token()
            elif token == "<DISTANCE>":
                variable.has_distance_function = True
                for i in range(5):
                    t = tok.next_token()
                    if t == "":
                        variable.distance_function[i] = 1 if i == 0 else variable.distance_function[i - 1]
                    else:
                        variable.distance_function[i] = int(t)
            elif token == "<CODELIST>":
                variable.code_list_file = tok.next_token()
            elif token == "<HIERARCHICAL>":
                variable.hierarchical = 2  # HIER_FILE
            elif token == "<HIERLEVELS>":
                variable.hierarchical = 1  # HIER_LEVELS
                x = 0
                while True:
                    t = tok.next_token()
                    if t == "":
                        break
                    n = int(t)
                    variable.hier_levels.append(n)
                    x += n
                variable.hier_levels_sum = x
            elif token == "<HIERLEADSTRING>":
                variable.leading_string = tok.next_token()
            elif token == "<HIERCODELIST>":
                variable.hier_file_name = tok.next_token()
            elif token == "<NUMERIC>":
                hs = tok.next_token()
                if hs == "":
                    if variable.type == "CATEGORICAL":
                        variable.type = "CAT_RESP"
                    else:
                        variable.type = "RESPONSE"
                elif hs == "<SHADOW>":
                    variable.type = "SHADOW"
                elif hs in ("<COST>", "<COSTVAR>"):
                    variable.type = "COST"
                elif hs == "<LOWERPL>":
                    variable.type = "LOWER_PROTECTION_LEVEL"
                elif hs == "<UPPERPL>":
                    variable.type = "UPPER_PROTECTION_LEVEL"
            elif token == "<WEIGHT>":
                variable.type = "WEIGHT"
            elif token == "<HOLDING>":
                variable.type = "HOLDING"
            elif token == "<REQUEST>":
                variable.type = "REQUEST"
                variable.request_code = [tok.next_token(), tok.next_token()]
            elif token == "<DECIMALS>":
                variable.n_decimals = int(tok.next_token())
            elif token == "<TRUNCABLE>":
                variable.truncatable = True
            elif token == "<RECORDKEY>":
                variable.type = "RECORD_KEY"
            elif token in ("<PFILE_FREQ>", "<PFILE>"):
                variable.p_table_file = tok.next_token()
            elif token == "<PFILE_CONT>":
                variable.p_table_file_cont = tok.next_token()
            elif token == "<PFILE_SEP>":
                variable.p_table_file_sep = tok.next_token()
            elif token == "<CKM>":
                if not variable.is_response:
                    raise BatchError("<CKM> tag only allowed for numeric variables.")
                hs = tok.next_field("(").upper()
                ckmspecified = True
                if hs == "N":
                    ckmspecified = False
                elif hs in ("M", "D", "V"):
                    variable.ckm_type = hs
                elif hs == "T":
                    variable.ckm_type = hs
                    variable.ckm_top_k = int(tok.next_field(")"))
                else:
                    raise BatchError(f"Unknown type <CKM> {hs} for variable {variable.name}")
                if ckmspecified:
                    variable.ckm_epsilon = [1.0] * variable.ckm_top_k
            elif token == "<INCLUDEZEROS>":
                if not ckmspecified:
                    raise BatchError("<INCLUDEZEROS> only allowed after <CKM>.")
                variable.ckm_zeros = tok.next_token() == "Y"
            elif token == "<PARITY>":
                if not ckmspecified:
                    raise BatchError("<PARITY> only allowed after <CKM>.")
                variable.ckm_parity = tok.next_token() == "Y"
            elif token == "<SEPARATION>":
                if not ckmspecified:
                    raise BatchError("<SEPARATION> only allowed after <CKM>.")
                variable.ckm_separation = tok.next_token() == "Y"
            elif token == "<SCALING>":
                if not ckmspecified:
                    raise BatchError("<SCALING> only allowed after <CKM>.")
                hs = tok.next_field("(").upper()
                variable.ckm_scaling = hs
                if hs == "F":
                    variable.ckm_sigma0 = float(tok.next_field(","))
                    variable.ckm_sigma1 = float(tok.next_field(","))
                    variable.ckm_xstar = float(tok.next_field(","))
                    t = variable.ckm_top_k
                    if t >= 2:
                        variable.ckm_q = float(tok.next_field(","))
                        for i in range(2, t):
                            variable.ckm_epsilon[i - 1] = float(tok.next_field(","))
                        variable.ckm_epsilon[t - 1] = float(tok.next_field(")"))
                    else:
                        variable.ckm_q = float(tok.next_field(")"))
                elif hs == "N":
                    t = variable.ckm_top_k
                    if t >= 2:
                        variable.ckm_sigma1 = float(tok.next_field(","))
                        for i in range(2, t):
                            variable.ckm_epsilon[i - 1] = float(tok.next_field(","))
                        variable.ckm_epsilon[t - 1] = float(tok.next_field(")"))
                    else:
                        variable.ckm_sigma1 = float(tok.next_field(")"))
                else:
                    raise BatchError(f"Unknown type <SCALING> {hs} for variable {variable.name}")
            else:
                raise BatchError(f"Unknown keyword ({token}) in line {tok.line_number}")
        else:
            # -- new variable declaration ------------------------------------
            variable = Variable(name=token, index=len(meta.variables))
            meta.variables.append(variable)
            ckmspecified = False
            variable.b_pos = int(tok.next_token())
            variable.var_len = int(tok.next_token())
            variable.missing = [
                _normalise_missing(tok.next_token(), variable.var_len),
                _normalise_missing(tok.next_token(), variable.var_len),
            ]

    tok.close()
    return meta


def parse_rda_table(path: Union[str, Path]) -> Metadata:
    """Parse a tabular (pre-aggregated) ``.rda`` metadata file.

    Mirrors ``Metadata.readTableMetadata``. Variable declarations carry no
    ``bPos``/``varLen`` (only name + two missing values); ``<NUMERIC>`` may be
    followed by a subtype (``<SHADOW>``/``<COSTVAR>``/``<LOWERPL>``/
    ``<UPPERPL>``), and top-level ``<SAFE>``/``<UNSAFE>``/``<PROTECT>`` tags
    set the status characters.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    tok = Tokenizer(text)
    meta = Metadata(meta_file=str(path), is_table=True)
    meta.field_separator = ";"
    variable: Optional[Variable] = None

    while tok.next_line() is not None:
        token = tok.next_token()
        if token == "":
            continue

        if token.startswith("<"):
            if token == "<SEPARATOR>":
                meta.field_separator = _unquote(tok.next_token())
                continue
            if token == "<SAFE>":
                meta.safe_status = _unquote(tok.next_token())
                continue
            if token == "<UNSAFE>":
                meta.unsafe_status = _unquote(tok.next_token())
                continue
            if token == "<PROTECT>":
                meta.protect_status = _unquote(tok.next_token())
                continue

            if variable is None:
                raise BatchError("A variable should be declared before giving its properties")

            if token in ("<RECODEABLE>", "<RECODABLE>"):
                variable.type = "CATEGORICAL"
                variable.in_table = True
            elif token == "<TOTCODE>":
                variable.tot_code = _unquote(tok.next_token())
            elif token == "<DISTANCE>":
                variable.has_distance_function = True
                for i in range(5):
                    t = tok.next_token()
                    if t == "":
                        variable.distance_function[i] = 1 if i == 0 else variable.distance_function[i - 1]
                    else:
                        variable.distance_function[i] = int(t)
            elif token == "<CODELIST>":
                variable.code_list_file = _unquote(tok.next_token())
            elif token == "<HIERARCHICAL>":
                variable.hierarchical = 2
            elif token == "<HIERLEVELS>":
                variable.hierarchical = 1
                x = 0
                while True:
                    t = tok.next_token()
                    if t == "":
                        break
                    n = int(t)
                    variable.hier_levels.append(n)
                    x += n
                variable.hier_levels_sum = x
            elif token == "<HIERLEADSTRING>":
                variable.leading_string = _unquote(tok.next_token())
            elif token == "<HIERCODELIST>":
                variable.hier_file_name = _unquote(tok.next_token())
            elif token == "<NUMERIC>":
                sub = tok.next_token()
                if sub == "":
                    variable.type = "RESPONSE"
                elif sub == "<SHADOW>":
                    variable.type = "SHADOW"
                elif sub in ("<COST>", "<COSTVAR>"):
                    variable.type = "COST"
                elif sub == "<LOWERPL>":
                    variable.type = "LOWER_PROTECTION_LEVEL"
                elif sub == "<UPPERPL>":
                    variable.type = "UPPER_PROTECTION_LEVEL"
            elif token == "<FREQUENCY>":
                variable.type = "FREQUENCY"
            elif token == "<MAXSCORE>":
                variable.type = "TOP_N"
            elif token == "<STATUS>":
                variable.type = "STATUS"
            elif token == "<DECIMALS>":
                variable.n_decimals = int(tok.next_token())
            else:
                raise BatchError(f"Unknown keyword ({token}) in line {tok.line_number}")
        else:
            # -- new variable declaration (no bPos/varLen) --------------------
            variable = Variable(name=token, index=len(meta.variables))
            meta.variables.append(variable)
            variable.missing = [
                _normalise_missing(tok.next_token(), 0),
                _normalise_missing(tok.next_token(), 0),
            ]

    tok.close()
    return meta


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s


def _normalise_missing(missing: str, var_len: int) -> str:
    if missing.strip() == "":
        return ""
    if var_len and len(missing) > var_len:
        raise BatchError(f"Missing value ({missing}) too long")
    return missing.rjust(var_len) if var_len else missing


# ===========================================================================
# Safety rule aggregation (per-table)
# ===========================================================================
@dataclass
class SafetyRuleSet:
    """Aggregated safety rules for a single table (maps to native SetTableSafety)."""
    dom_rule: bool = False
    dom_n: List[int] = field(default_factory=list)
    dom_k: List[int] = field(default_factory=list)
    pq_rule: bool = False
    pq_p: List[int] = field(default_factory=list)
    pq_q: List[int] = field(default_factory=list)
    pq_n: List[int] = field(default_factory=list)
    min_freq: List[int] = field(default_factory=list)
    freq_marge: List[int] = field(default_factory=list)
    peep_rule: bool = False
    peep_percentage: List[int] = field(default_factory=list)
    peep_marge: List[int] = field(default_factory=list)
    peep_min_freq: List[int] = field(default_factory=list)
    apply_peep: bool = False
    apply_weight: bool = False
    weight_on_safety: bool = False
    apply_holding: bool = False
    zero_rule: bool = False
    zero_range: float = 0.0
    empty_as_ns: bool = False
    ns_range: int = 10
    manual_perc: int = 0

    @staticmethod
    def from_rules(rules: List[SafetyRule]) -> "SafetyRuleSet":
        """Build a SafetyRuleSet from the parsed batch SafetyRule objects."""
        s = SafetyRuleSet()
        n_pq = 0
        n_dom = 0
        n_freq = 0
        n_req = 0

        for rule in rules:
            args = [int(a) for a in rule.args]
            if rule.kind == "P":
                if n_pq >= 4:
                    raise BatchError("More than 4 P rules specified.")
                if len(args) == 2:
                    s.pq_p.append(args[0])
                    s.pq_q.append(100)
                    s.pq_n.append(args[1])
                elif len(args) == 3:
                    s.pq_p.append(args[0])
                    s.pq_q.append(args[1])
                    s.pq_n.append(args[2])
                else:
                    raise BatchError("P rule needs 2 or 3 parameters.")
                s.pq_rule = True
                if n_pq >= 2 and s.pq_p[n_pq] > 0:
                    s.apply_holding = True
                n_pq += 1
            elif rule.kind == "NK":
                if n_dom >= 4:
                    raise BatchError("More than 4 NK rules specified.")
                if len(args) != 2:
                    raise BatchError("NK rule needs 2 parameters.")
                s.dom_n.append(args[0])
                s.dom_k.append(args[1])
                s.dom_rule = True
                if n_dom >= 2:
                    s.apply_holding = True
                n_dom += 1
            elif rule.kind == "FREQ":
                if n_freq >= 2:
                    raise BatchError("More than 2 frequency rules specified.")
                if len(args) != 2:
                    raise BatchError("FREQ rule needs 2 parameters.")
                s.min_freq.append(args[0])
                s.freq_marge.append(args[1])
                if n_freq >= 1 and s.min_freq[n_freq] > 0:
                    s.apply_holding = True
                n_freq += 1
            elif rule.kind == "ZERO":
                if len(args) != 1:
                    raise BatchError("ZERO rule needs 1 parameter.")
                s.zero_range = float(args[0])
                s.zero_rule = True
            elif rule.kind == "WGT":
                if len(args) != 1:
                    raise BatchError("WGT needs 1 parameter.")
                k = args[0]
                if k < 0 or k > 3:
                    raise BatchError("WGT value should be 0-3.")
                s.apply_weight = k != 0
                s.weight_on_safety = k >= 2
            elif rule.kind == "MIS":
                # missingIsSafe — handled at set_table level, not safety
                pass
            elif rule.kind == "MAN":
                if len(args) != 1:
                    raise BatchError("MAN needs 1 parameter.")
                s.manual_perc = args[0]
            elif rule.kind == "REQ":
                if n_req >= 2:
                    raise BatchError("More than 2 request rules specified.")
                if len(args) != 4:
                    raise BatchError("REQ rule needs 4 parameters.")
                s.peep_percentage.extend([args[0], args[1]])
                s.peep_marge.append(args[3])
                s.peep_min_freq.append(args[2])
                if args[0] > 0 or args[2] > 0:
                    s.apply_peep = True
                if n_req >= 0 and args[0] > 0:
                    s.apply_holding = True
                n_req += 1
            else:
                raise BatchError(f"Unknown safety rule kind: {rule.kind}")

        return s


# ===========================================================================
# Engine
# ===========================================================================
class Engine:
    """High-level driver for the native Tau-Argus engine."""

    def __init__(self) -> None:
        self._tau = TauArgus()
        self._hitas = HiTaSCtrl()
        self._rounder = RounderCtrl()
        self._metadata: Optional[Metadata] = None
        self._data_file: str = ""
        self._tables: List[tuple] = []  # (SpecifyTable, SafetyRuleSet)
        self._safety_rules_buf: List[List[SafetyRule]] = []
        self._n_tables: int = 0
        self._work_dir: Path = Path.cwd()

    # -- property accessors --------------------------------------------------
    @property
    def version(self) -> str:
        return self._tau.version()

    @property
    def metadata(self) -> Optional[Metadata]:
        return self._metadata

    # -- microdata flow ------------------------------------------------------
    def open_microdata(self, data_file: str, meta: Metadata) -> None:
        """Set up native engine for a fixed-width microdata file.

        Does not reset registered tables (``_tables``); call this after the
        table/safety commands have been buffered during a batch run.
        """
        self._data_file = data_file
        self._metadata = meta
        meta.data_file = data_file

        self._tau.clean_all()
        self._tau.set_in_file_info(True, "")
        self._tau.set_number_var(len(meta.variables))

        for var in meta.variables:
            self._set_variable(var)

        # Explore the data file to build code lists
        ok, err, line, nvar = self._tau.explore_file(data_file)
        if not ok:
            raise BatchError(f"ExploreFile failed: {self._tau.error_string(err)} line {line}")

    def _set_variable(self, var: Variable) -> None:
        n_miss = var.n_missings()
        self._tau.set_variable(
            index=var.index,
            b_pos=var.b_pos,
            n_pos=var.var_len,
            n_dec=var.n_decimals,
            n_missing=n_miss,
            missing1=var.missing[0] if n_miss >= 1 else "",
            missing2=var.missing[1] if n_miss >= 2 else "",
            total_code=var.get_total_code(),
            is_peeper=var.is_request,
            peeper_code1=var.request_code[0] if var.is_request else "",
            peeper_code2=var.request_code[1] if var.is_request else "",
            is_categorical=var.is_categorical,
            is_numeric=var.is_numeric,
            is_weight=var.is_weight,
            is_hierarchical=var.hierarchical != 0,
            is_holding=var.is_holding,
            is_record_key=var.is_record_key,
        )
        if var.hierarchical == 2:  # HIER_FILE
            hier_path = self._resolve_path(var.hier_file_name)
            self._tau.set_hierarchical_codelist(var.index, str(hier_path), var.leading_string)
        elif var.hierarchical == 1:  # HIER_LEVELS
            # Trim trailing zero levels (Java counts up to the last non-zero).
            levels = var.hier_levels
            n_levels = 0
            for j, d in enumerate(levels):
                if d != 0:
                    n_levels = j + 1
            ok = self._tau.set_hierarchical_digits(var.index, levels[:n_levels])
            if not ok:
                raise BatchError(
                    f"SetHierarchicalDigits failed for variable {var.name} "
                    f"levels={levels[:n_levels]} var_len={var.var_len}"
                )

    def _resolve_path(self, filename: str) -> Path:
        """Resolve a file path relative to the data file's directory."""
        p = Path(filename)
        if p.is_file():
            return p
        if self._data_file:
            data_dir = Path(self._data_file).parent
            p2 = data_dir / p.name
            if p2.is_file():
                return p2
        raise BatchError(f"File not found: {filename}")

    def specify_table(self, spec: SpecifyTable) -> None:
        """Register a table specification (safety rules are buffered separately)."""
        self._tables.append(spec)
        self._safety_rules_buf.append([])

    def _finalize_tables(self) -> None:
        """Call native SetTable + SetTableSafety for each registered table."""
        self._n_tables = len(self._tables)
        self._tau.set_number_tab(self._n_tables)
        for i, (spec, srs) in enumerate(self._tables):
            self._call_set_table(i, spec)
            self._call_set_table_safety(i, srs)

    def _call_set_table(self, idx: int, spec: SpecifyTable) -> None:
        if not self._metadata:
            raise BatchError("No metadata.")
        exp_indices = [self._metadata.index_of(n) for n in spec.exp_vars]
        resp_idx = self._metadata.index_of(spec.resp_var)
        resp_var = self._metadata.variables[resp_idx]
        is_freq = resp_var.type == "FREQUENCY"
        # Shadow: native rejects -1 for a non-frequency table, so default to the
        # response variable (Java: indexOfShadowVariable() falls back to resp).
        shadow_idx = -1 if is_freq else (
            self._metadata.index_of(spec.shadow_var) if spec.shadow_var else resp_idx
        )
        cost_idx = -1
        if spec.cost_var and spec.cost_var not in ("-1", "-2", "-3"):
            cost_idx = self._metadata.index_of(spec.cost_var)

        req_idx = self._metadata.index_of("REQUEST")

        ok = self._tau.set_table(
            index=idx,
            explanatory_vars=exp_indices,
            is_frequency=is_freq,
            response_var=resp_idx,
            shadow_var=shadow_idx,
            cost_var=cost_idx,
            cellkey_var=self._metadata.index_of("RECORD_KEY"),
            ckm_type=resp_var.ckm_type,
            ckm_topk=resp_var.ckm_top_k,
            lam=spec.lam,
            max_scaled_cost=20000.0,
            peep_var=req_idx,
            missing_as_safe=False,
        )
        if not ok:
            raise BatchError(f"SetTable failed for table {idx + 1}")

    def _call_set_table_safety(self, idx: int, srs: SafetyRuleSet) -> None:
        # Pad freq arrays to at least 2 entries (native expects >= 2)
        min_freq = list(srs.min_freq)
        freq_marge = list(srs.freq_marge)
        while len(min_freq) < 2:
            min_freq.append(0)
        while len(freq_marge) < 2:
            freq_marge.append(0)
        # fix min_freq 0 → 1 (as Java does)
        min_freq = [m if m > 0 else 1 for m in min_freq]
        # if freq_marge[0] < freq_marge[1] and min_freq[1] > 0: freq_marge[0] = freq_marge[1]
        if len(freq_marge) >= 2 and freq_marge[0] < freq_marge[1] and len(min_freq) >= 2 and min_freq[1] > 0:
            freq_marge[0] = freq_marge[1]

        ok = self._tau.set_table_safety(
            index=idx,
            dominance_rule=srs.dom_rule,
            dominance_number=srs.dom_n,
            dominance_k=srs.dom_k,
            pq_rule=srs.pq_rule,
            pq_p=srs.pq_p,
            pq_q=srs.pq_q,
            pq_n=srs.pq_n,
            min_freq=min_freq,
            peep_percentage=srs.peep_percentage,
            peep_marge=srs.peep_marge,
            peep_min_freq=srs.peep_min_freq,
            apply_peep=srs.apply_peep,
            apply_weight=srs.apply_weight,
            weight_on_safety_rule=srs.weight_on_safety,
            apply_holding=srs.apply_holding,
            apply_zero_rule=srs.zero_rule,
            empty_as_non_structural=False,
            ns_empty_safety_range=10,
            zero_safety_range=srs.zero_range,
            manual_safety_perc=srs.manual_perc,
            cell_holding_freq_safety_perc=freq_marge,
        )
        if not ok:
            raise BatchError(f"SetTableSafety failed for table {idx + 1}")

    def read_microdata(self) -> None:
        """Trigger table computation from microdata."""
        self._finalize_tables()
        ok, err, tab = self._tau.compute_tables()
        if not ok:
            raise BatchError(f"ComputeTables failed: {self._tau.error_string(err)} table {tab}")
        logger.info("Computed %d tables.", self._n_tables)

    # -- table-input (tabular data) flow ------------------------------------
    def open_table_data(self, data_file: str, meta: Metadata) -> None:
        self._data_file = data_file
        self._metadata = meta
        meta.data_file = data_file
        self._tables = []
        self._tau.clean_all()
        self._tau.set_in_file_info(False, meta.field_separator)
        self._tau.set_number_var(len(meta.variables))
        for var in meta.variables:
            var.index = 0
            self._set_variable(var)

    def read_table(self, additivity: int = 0, keep_status: bool = False) -> None:
        """Read tabular data (after SetInTable calls)."""
        self._finalize_tables()
        # CompletedTable is called per-table in the tabular flow;
        # for the batch path the Java code calls it after all cells are set.
        for i in range(self._n_tables):
            ok, err = self._tau.completed_table(
                index=i, file="", compute_totals=(additivity != 0),
                calculated_totals_as_safe=False, for_cover_table=False,
            )
            if not ok:
                raise BatchError(f"CompletedTable failed for table {i + 1}: {self._tau.error_string(err)}")

    # -- suppress ------------------------------------------------------------
    def suppress(self, cmd: Suppress) -> None:
        """Run suppression on the given table."""
        tab = cmd.tab_no - 1
        kind = cmd.kind.upper()

        if kind == "MOD":
            self._suppress_mod(tab, cmd)
        elif kind == "OPT":
            self._suppress_opt(tab, cmd)
        elif kind == "RND":
            self._suppress_rnd(tab, cmd)
        elif kind == "CKM":
            self._suppress_ckm(tab, cmd)
        else:
            raise BatchError(f"Suppress method '{kind}' not supported in headless mode "
                             f"(GH/NET/CTA require external executables).")

    def _suppress_mod(self, tab: int, cmd: Suppress) -> None:
        from .batch import Tokenizer as _T
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmp:
            param_file = os.path.join(tmp, "params.hsp")
            files_file = os.path.join(tmp, "files.hsp")
            tau_temp = tmp
            # PrepareHITAS writes parameter files
            self._tau.prepare_hitas(tab, param_file, files_file, tau_temp)
            # Run HiTAS
            ok = self._hitas.a_hitas(
                param_file=param_file,
                max_time=cmd.mod_max_time,
                singleton=cmd.mod_singleton,
                singleton_multi=cmd.mod_singleton_multi,
                min_freq=cmd.mod_min_freq,
                msc=cmd.mod_msc,
                lower_marg=cmd.mod_lower_marg,
                upper_marg=cmd.mod_upper_marg,
            )
            if not ok:
                raise BatchError("AHiTaS failed")
            # Read back
            ok2, n = self._tau.set_secondary_hitas(tab)
            logger.info("MOD suppress: %d cells set secondary.", n)

    def _suppress_opt(self, tab: int, cmd: Suppress) -> None:
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmp:
            jj_file = os.path.join(tmp, "opt.jj")
            self._tau.write_jj_format(tab, jj_file, 0.0, 0.0, False, False, False)
            ok = self._hitas.full_jj(
                jj_file=jj_file,
                max_time=cmd.opt_max_time,
            )
            if not ok:
                raise BatchError("FullJJ failed")
            code, n = self._tau.set_secondary_jjformat(tab, jj_file, False)
            logger.info("OPT suppress: %d cells set secondary.", n)

    def _suppress_rnd(self, tab: int, cmd: Suppress) -> None:
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmp:
            jj_file = os.path.join(tmp, "rnd.jj")
            self._tau.write_jj_format(tab, jj_file, 0.0, 0.0, False, False, True)
            ok = self._rounder.do_round(
                jj_file=jj_file,
                base=cmd.rnd_base,
                step=cmd.rnd_step,
                max_time=cmd.rnd_time,
                n_partitions=cmd.rnd_partitions,
                stop_rule=cmd.rnd_stop_rule,
                unit_cost=cmd.rnd_unit_cost,
            )
            if not ok:
                raise BatchError("DoRound failed")
            self._tau.set_rounded_response(jj_file, tab)
            logger.info("RND suppress: table %d rounded.", tab + 1)

    def _suppress_ckm(self, tab: int, cmd: Suppress) -> None:
        if cmd.ckm_p_table:
            ok, mn, mx = self._tau.set_cell_key_values_freq(tab, cmd.ckm_p_table)
            logger.info("CKM freq: min=%d max=%d", mn, mx)
        elif cmd.ckm_p_table_cont:
            if not self._metadata:
                raise BatchError("No metadata for CKM.")
            resp = self._metadata.variables[0]  # simplified
            self._tau.set_cell_key_values_cont(
                tab, cmd.ckm_p_table_cont, cmd.ckm_p_table_sep,
                resp.ckm_type, resp.ckm_top_k, resp.ckm_zeros, resp.ckm_parity,
                resp.ckm_separation, 0.0, resp.ckm_scaling,
                resp.ckm_sigma0, resp.ckm_sigma1, resp.ckm_xstar, resp.ckm_q,
                resp.ckm_epsilon, cmd.ckm_mu_c,
            )
            logger.info("CKM cont: table %d processed.", tab + 1)

    # -- recode ---------------------------------------------------------------
    def recode(self, cmd: Recode) -> None:
        """Apply a recode to a variable (by name, from the current table context).

        Mirrors ``batch.batchRecode``:
        - a single digit 1..9 → hierarchical truncation to that level;
        - a ``<TREERECODE>`` file → deactivate the listed parent codes;
        - any other file → classic ``DoRecode`` (``dest : src`` spec).
        """
        if not self._metadata:
            raise BatchError("No metadata loaded.")
        var = self._metadata.find(cmd.var_name)
        if var is None:
            raise BatchError(f"Variable '{cmd.var_name}' not found.")
        var_idx = var.index

        recode_src = cmd.recode_file
        # 1) digit truncation level (1..9)
        if len(recode_src) == 1 and "1" <= recode_src <= "9":
            if var.hierarchical == 0:
                raise BatchError(
                    "Truncation is only possible for hierarchical variables")
            self._recode_truncate(var_idx, int(recode_src))
            var.recoded = True
            logger.info("Recode: variable %s truncated to level %s.",
                        var.name, recode_src)
            return

        # 2) file-based recode
        recode_path = self._resolve_path(recode_src)
        first_line = recode_path.read_text(
            encoding="utf-8", errors="replace").splitlines()[0].strip() \
            if recode_path.exists() else ""
        if first_line == "<TREERECODE>":
            self._recode_tree(var_idx, recode_path)
            var.recoded = True
            logger.info("Recode: variable %s tree-recoded (%s).",
                        var.name, recode_src)
            return

        # 3) classic DoRecode (dest : src spec)
        recode_info = _parse_recode_file(recode_path)
        ok, et, el, ep, warn = self._tau.do_recode(
            var_idx, recode_info.data, recode_info.n_missing,
            recode_info.missing1, recode_info.missing2,
        )
        if not ok:
            raise BatchError(f"Recode failed for {var.name}: "
                             f"{self._tau.error_string(et)} line {el} pos {ep} {warn}")
        var.recoded = True
        self._tau.apply_recode()
        logger.info("Recode: variable %s recoded (%s).", var.name, warn or "no warnings")

    def _recode_truncate(self, var_idx: int, max_level: int) -> None:
        """Deactivate every node at ``max_level`` that has children, then recode."""
        self._tau.undo_recode(var_idx)
        n_codes, _ = self._tau.get_var_number_of_codes(var_idx)
        closed = 0
        for i in range(n_codes):
            ok, _, _, _, level, n_child, _ = self._tau.get_var_code_properties(var_idx, i)
            if ok and level == max_level and n_child > 0:
                self._tau.set_var_code_active(var_idx, i, False)
                closed += 1
        if closed > 0:
            if not self._tau.do_active_recode(var_idx):
                self._tau.undo_recode(var_idx)
                raise BatchError("There was a problem recoding this variable")
            self._tau.apply_recode()
        logger.info("Recode: %d nodes closed.", closed)

    def _recode_tree(self, var_idx: int, path: Path) -> None:
        """Deactivate the parent codes listed in a <TREERECODE> file, then recode."""
        self._tau.undo_recode(var_idx)
        # Build code-string -> code-index lookup.
        n_codes, _ = self._tau.get_var_number_of_codes(var_idx)
        index_by_code: Dict[str, int] = {}
        for i in range(n_codes):
            ok, _, cs, _, _ = self._tau.get_var_code(var_idx, i)
            if ok:
                index_by_code[cs] = i
        closed = 0
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            code = line.strip()
            if not code or code == "<TREERECODE>":
                continue
            ci = index_by_code.get(code)
            if ci is None:
                raise BatchError(f"Code ({code}) not found")
            self._tau.set_var_code_active(var_idx, ci, False)
            closed += 1
        if closed > 0:
            if not self._tau.do_active_recode(var_idx):
                self._tau.undo_recode(var_idx)
                raise BatchError("There was a problem recoding this variable")
            self._tau.apply_recode()
        logger.info("Recode: %d tree nodes closed.", closed)

    # -- write ----------------------------------------------------------------
    def write_table(self, cmd: WriteTable) -> None:
        """Write a table to file."""
        tab = cmd.tab_no - 1
        fpath = self._work_dir / cmd.file if cmd.file else self._work_dir / f"table_{tab + 1}.tab"

        if cmd.output_type == 1:  # CSV
            self._tau.write_csv(tab, str(fpath), True, [], 1)
        elif cmd.output_type in (2, 3, 4, 5, 6, 7):
            # CellRecords (SBS, code value, etc.)
            self._tau.write_cell_records(tab, str(fpath), True, False,
                                         False, "", False, True, 1)
        else:
            raise BatchError(f"Unknown output type {cmd.output_type}")
        logger.info("Wrote table %d to %s", tab + 1, fpath)

    # -- batch execution ------------------------------------------------------
    def run_batch(self, arb_path: Union[str, Path]) -> None:
        """Parse and execute a legacy .arb batch file."""
        arb_path = Path(arb_path)
        # Resolve file paths relative to the .arb file's directory
        self._work_dir = arb_path.parent
        commands = parse_batch(arb_path)

        # Reset state
        self._tables = []
        self._safety_rules_buf = []

        for cmd in commands:
            self._execute(cmd)
        return self

    def _execute(self, cmd: Command) -> None:
        if isinstance(cmd, OpenMicrodata):
            self._data_file = self._resolve_arb_path(cmd.file)
            logger.info("Open microdata: %s", cmd.file)
        elif isinstance(cmd, OpenTableData):
            self._data_file = self._resolve_arb_path(cmd.file)
            logger.info("Open table data: %s", cmd.file)
        elif isinstance(cmd, OpenMetadata):
            meta_path = self._resolve_arb_path(cmd.file)
            self._metadata = parse_rda(meta_path)
            logger.info("Loaded metadata: %d variables.", len(self._metadata.variables))
            # Set variable indices
            for i, v in enumerate(self._metadata.variables):
                v.index = i
        elif isinstance(cmd, SpecifyTable):
            self._tables.append((cmd, SafetyRuleSet()))
            self._safety_rules_buf.append([])
            logger.info("Table %d: %s | %s", len(self._tables),
                        cmd.exp_vars, cmd.resp_var)
        elif isinstance(cmd, SafetyRule):
            if self._safety_rules_buf:
                self._safety_rules_buf[-1].append(cmd)
        elif isinstance(cmd, ReadMicrodata):
            self._apply_safety_rules()
            self.open_microdata(self._data_file, self._metadata)
            self.read_microdata()
        elif isinstance(cmd, ReadTable):
            self._apply_safety_rules()
            self.read_table(cmd.additivity, cmd.keep_status)
        elif isinstance(cmd, Recode):
            self.recode(cmd)
        elif isinstance(cmd, Suppress):
            self.suppress(cmd)
        elif isinstance(cmd, WriteTable):
            self.write_table(cmd)
        elif isinstance(cmd, (GoInteractive, Logbook, VersionInfo, Anco)):
            logger.info("Skipping %s (no-op in headless mode).", type(cmd).__name__)
        elif isinstance(cmd, Clear):
            self._tables = []
            self._safety_rules_buf = []
            self._metadata = None
            logger.info("Cleared state.")
        elif isinstance(cmd, Solver):
            logger.info("Solver %s: all backends use HiGHS (license ignored).", cmd.name)
        elif isinstance(cmd, (Apriory, Cover)):
            logger.warning("%s not yet implemented.", type(cmd).__name__)

    def _resolve_arb_path(self, filename: str) -> str:
        """Resolve a file path relative to the .arb file's directory."""
        p = Path(filename)
        if p.is_file():
            return str(p)
        resolved = self._work_dir / filename
        if resolved.is_file():
            return str(resolved)
        return filename  # let the caller raise

    def _apply_safety_rules(self) -> None:
        """Aggregate buffered safety rules into each table's SafetyRuleSet."""
        if self._safety_rules_buf:
            for i, rules in enumerate(self._safety_rules_buf):
                if self._tables and i < len(self._tables):
                    self._tables[i] = (self._tables[i][0], SafetyRuleSet.from_rules(rules))


# ===========================================================================
# Recode file parser
# ===========================================================================
@dataclass
class RecodeInfo:
    data: str
    missing1: str
    missing2: str
    code_list: str
    n_missing: int = 0


def _parse_recode_file(path: Union[str, Path]) -> RecodeInfo:
    """Parse a .grc recode file (port of Variable.readRecodeFile)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    tok = Tokenizer(text)
    recode_data = ""
    missing1 = ""
    missing2 = ""
    code_list = ""

    while tok.next_line() is not None:
        hs = tok.get_line()
        token = tok.next_token()
        if token == "<MISSING>":
            missing1 = tok.next_token()
            if missing1 == "":
                raise BatchError("No missing values found after <MISSING>")
            token = tok.next_token()
            if token == ",":
                token = tok.next_token()
            missing2 = token
        elif token == "<CODELIST>":
            code_list = tok.next_token()
        elif token != "":
            recode_data = recode_data + hs + "\n"

    n_missing = 0
    if missing1:
        n_missing = 1
    if missing2:
        n_missing = 2

    return RecodeInfo(data=recode_data.replace("\n", "\r\n"),
                      missing1=missing1, missing2=missing2,
                      code_list=code_list, n_missing=n_missing)


# ===========================================================================
# Convenience: one-shot batch run
# ===========================================================================
def run_batch(arb_path: Union[str, Path]) -> "Engine":
    """Parse and execute a .arb batch file in a fresh Engine.

    Returns the configured ``Engine`` (with tables computed) for inspection.
    """
    return Engine().run_batch(arb_path)
