"""Data contracts for the template-based-document-generation skill (v3).

Standard library only. Python 3.10+. No network, no subprocess, no third-party imports.

This module is the single source of truth for:
  * the documents exchanged between phases (manifest, plan, values, report) and their strict
    validation (unknown keys are errors),
  * canonical serialisation and hashing, so a plan binds to the exact manifest it was written for,
  * value resolution from arbitrary JSON input and formatting under a locale block,
  * the compile step: plan decisions + operations + values -> a normalised set of edits per part.
    The filler applies that set and the verifier independently checks the output against it.
"""
from __future__ import annotations

import dataclasses
import functools
import hashlib
import json
import re
import types
import typing
from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, InvalidOperation, localcontext
from typing import Any

# --------------------------------------------------------------------------------------
# Versions, identifiers, vocabularies
# --------------------------------------------------------------------------------------

SKILL_VERSION = "3.7.1"
CONTRACT_VERSION = "3"

SCHEMA_MANIFEST = "fill-word-template/manifest/v3"
SCHEMA_PLAN = "fill-word-template/plan/v3"
SCHEMA_VALUES = "fill-word-template/values/v3"
SCHEMA_REPORT = "fill-word-template/report/v3"
SCHEMA_POLICY = "fill-word-template/policy/v3"
SCHEMA_PROFILE = "fill-word-template/profile/v3"

IDENTIFIER_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]*$"
IDENTIFIER_RE = re.compile(IDENTIFIER_PATTERN)
SHA256_PATTERN = r"^[0-9a-f]{64}$"
PART_NAME_PATTERN = r"^[A-Za-z0-9_.\[\]/-]+$"
PARAGRAPH_ID_PATTERN = r"^[A-Za-z0-9_.\[\]/-]+#p[0-9]+$"
CANDIDATE_ID_PATTERN = r"^[fibc]:[A-Za-z0-9_.\[\]/-]+#p[0-9]+#[0-9]+-[0-9]+$"
JOB_ID_PATTERN = r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{6}$"
UTC_TIMESTAMP_PATTERN = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"

CANDIDATE_KINDS = ("field", "instruction", "blank", "control")
CONFIDENCES = ("high", "medium", "low")
DECISIONS = ("field", "literal", "remove_text", "remove_paragraph", "keep")
VALUE_TYPES = ("string", "integer", "decimal", "date", "boolean")
ABSENCE_POLICIES = ("required", "sentinel", "empty")
OPERATIONS = ("delete_paragraph", "delete_range", "delete_row", "delete_break", "repeat_row", "insert_paragraph_after")
FINDING_SEVERITIES = ("block", "report", "allow")
CHECK_OUTCOMES = ("passed", "failed", "not_performed")
RESULTS = ("ok", "needs_review", "failed")
CONTAINERS = ("body", "cell", "textbox", "footnote", "endnote", "header", "footer", "other")

STRING_CASES = ("none", "upper", "lower", "title")
THOUSANDS_SEPARATORS = ("", ",", ".", " ", "'", "\u00a0", "\u202f")
DECIMAL_SEPARATORS = (".", ",")
ROUNDING_MODES = ("half_even", "half_up")

MAX_INTEGER_DIGITS = 30
ASCII_INTEGER_RE = re.compile(r"^-?[0-9]{1,30}$")
INTEGER_MAGNITUDE_LIMIT = 10 ** MAX_INTEGER_DIGITS
DECIMAL_STRING_RE = re.compile(r"^-?[0-9]{1,30}(\.[0-9]{1,20})?$")
ISO_DATE_RE = re.compile(
    r"^([0-9]{4}-[0-9]{2}-[0-9]{2})"
    # An optional time suffix is dropped, but it must be a real clock time: silently discarding
    # "T99:99" would accept a value whose sender clearly meant something else.
    r"(?:[T ](?:[01][0-9]|2[0-3]):[0-5][0-9](?::(?:[0-5][0-9]|60))?(?:\.[0-9]+)?"
    r"(?:Z|[+-](?:[01][0-9]|2[0-3]):?[0-5][0-9])?)?$"
)
# A source path: dotted with [n] indexes, or an RFC 6901 pointer. Empty segments are typos, not paths.
_PATH_BODY_RE = re.compile(r"^(?:[^.\[\]]+|\[[0-9]+\])(?:\.[^.\[\]]+|\[[0-9]+\])*$")
DECIMAL_CONTEXT_PRECISION = 64
DATE_TOKEN_RE = re.compile(r"YYYY|YY|MMMM|MMM|MM|M|DD|D")

FORMAT_KEYS: dict[str, dict[str, tuple[type, ...]]] = {
    "string": {"max_length": (int,), "trim": (bool,), "case": (str,), "join": (str,)},
    "integer": {"thousands_separator": (str,), "min": (int,), "max": (int,)},
    "decimal": {"precision": (int,), "decimal_separator": (str,), "thousands_separator": (str,),
                "rounding": (str,), "min": (str,), "max": (str,)},
    "date": {"pattern": (str,)},
    "boolean": {"true_text": (str,), "false_text": (str,)},
}

DEFAULT_LOCALE: dict[str, Any] = {
    "months": ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"],
    "months_short": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "true_text": "Yes",
    "false_text": "No",
    "decimal_separator": ".",
    "thousands_separator": "",
    "date_pattern": "YYYY-MM-DD",
}


def _m(**kw: Any) -> dict[str, Any]:
    """Field metadata: constraints consumed by the validator."""
    return dict(kw)


# --------------------------------------------------------------------------------------
# Manifest (output of `run_job.py inspect`)
# --------------------------------------------------------------------------------------

@dataclass
class TemplateInfo:
    source_name: str
    sha256: str = dc_field(metadata=_m(pattern=SHA256_PATTERN))
    size_bytes: int = dc_field(metadata=_m(minimum=0))


@dataclass
class PartDigest:
    name: str = dc_field(metadata=_m(pattern=PART_NAME_PATTERN))
    sha256: str = dc_field(metadata=_m(pattern=SHA256_PATTERN))
    size_bytes: int = dc_field(metadata=_m(minimum=0))
    in_scope: bool = False


@dataclass
class ParagraphInfo:
    """One w:p in a part in scope. `index` counts every w:p in document order, nested ones included."""
    id: str = dc_field(metadata=_m(pattern=PARAGRAPH_ID_PATTERN))
    part: str = dc_field(metadata=_m(pattern=PART_NAME_PATTERN))
    index: int = dc_field(metadata=_m(minimum=0))
    text_sha256: str = dc_field(metadata=_m(pattern=SHA256_PATTERN))
    text: str = ""
    truncated: bool = False
    break_count: int = 0      # line and page breaks in the whole paragraph, not only in the stored preview
    style: str | None = None
    container: str = dc_field(default="body", metadata=_m(enum=CONTAINERS))
    container_id: str = ""
    block_first: int = 0
    block_last: int = 0
    row_id: str | None = None
    flags: list[str] = dc_field(default_factory=list)


@dataclass
class RowInfo:
    id: str
    part: str
    first_index: int
    last_index: int
    row_ordinal: int
    row_count: int
    table_id: str


@dataclass
class Candidate:
    id: str = dc_field(metadata=_m(pattern=CANDIDATE_ID_PATTERN))
    kind: str = dc_field(metadata=_m(enum=CANDIDATE_KINDS))
    part: str = dc_field(metadata=_m(pattern=PART_NAME_PATTERN))
    paragraph_index: int = dc_field(metadata=_m(minimum=0))
    char_start: int = dc_field(metadata=_m(minimum=0))
    char_end: int = dc_field(metadata=_m(minimum=0))
    text: str = ""
    label: str = ""
    name_guess: str | None = None
    pattern: str = ""
    confidence: str = dc_field(default="medium", metadata=_m(enum=CONFIDENCES))
    decision_required: bool = True
    eligible: bool = True
    ineligibility_reason: str | None = None
    mixed_formatting: bool = False
    context_before: str = ""
    context_after: str = ""
    control: dict[str, str] | None = None


@dataclass
class Finding:
    code: str
    severity: str = dc_field(metadata=_m(enum=FINDING_SEVERITIES))
    part: str | None = None
    detail: str = dc_field(default="", metadata=_m(maxLength=400))


@dataclass
class InspectionCoverage:
    parts_scanned: list[str] = dc_field(default_factory=list)
    parts_skipped: list[str] = dc_field(default_factory=list)
    notes: list[str] = dc_field(default_factory=list)


@dataclass
class Manifest:
    schema: str = dc_field(metadata=_m(const=SCHEMA_MANIFEST))
    skill_version: str
    contract_version: str = dc_field(metadata=_m(const=CONTRACT_VERSION))
    job_id: str = dc_field(metadata=_m(pattern=JOB_ID_PATTERN))
    created_utc: str = dc_field(metadata=_m(pattern=UTC_TIMESTAMP_PATTERN))
    policy_sha256: str = dc_field(metadata=_m(pattern=SHA256_PATTERN))
    template: TemplateInfo
    profile: dict[str, Any] = dc_field(default_factory=dict)
    blocked: bool = False
    parts_in_scope: list[str] = dc_field(default_factory=list)
    parts: list[PartDigest] = dc_field(default_factory=list)
    paragraphs: list[ParagraphInfo] = dc_field(default_factory=list)
    rows: list[RowInfo] = dc_field(default_factory=list)
    candidates: list[Candidate] = dc_field(default_factory=list)
    findings: list[Finding] = dc_field(default_factory=list)
    coverage: InspectionCoverage = dc_field(default_factory=InspectionCoverage)


# --------------------------------------------------------------------------------------
# Plan (prepared by the model or a person from the manifest)
# --------------------------------------------------------------------------------------

@dataclass
class Decision:
    candidate_id: str = dc_field(metadata=_m(pattern=CANDIDATE_ID_PATTERN))
    decision: str | None = dc_field(default=None, metadata=_m(enum=DECISIONS))
    field: str | None = dc_field(default=None, metadata=_m(pattern=IDENTIFIER_PATTERN, maxLength=64))
    reason: str | None = dc_field(default=None, metadata=_m(maxLength=400))


@dataclass
class FieldSpec:
    name: str = dc_field(metadata=_m(pattern=IDENTIFIER_PATTERN, maxLength=64))
    type: str = dc_field(default="string", metadata=_m(enum=VALUE_TYPES))
    format: dict[str, Any] = dc_field(default_factory=dict)
    absence_policy: str = dc_field(default="required", metadata=_m(enum=ABSENCE_POLICIES))
    absence_text: str | None = dc_field(default=None, metadata=_m(maxLength=200))
    source: str | None = dc_field(default=None, metadata=_m(maxLength=400))
    literal: Any = None
    repeat: str | None = dc_field(default=None, metadata=_m(maxLength=64))
    notes: str | None = dc_field(default=None, metadata=_m(maxLength=1000))


@dataclass
class Operation:
    op: str = dc_field(metadata=_m(enum=OPERATIONS))
    id: str | None = dc_field(default=None, metadata=_m(maxLength=64))
    paragraph: str | None = dc_field(default=None, metadata=_m(pattern=PARAGRAPH_ID_PATTERN))
    from_paragraph: str | None = dc_field(default=None, metadata=_m(pattern=PARAGRAPH_ID_PATTERN))
    to_paragraph: str | None = dc_field(default=None, metadata=_m(pattern=PARAGRAPH_ID_PATTERN))
    source: str | None = dc_field(default=None, metadata=_m(maxLength=400))
    text: str | None = None
    field: str | None = dc_field(default=None, metadata=_m(pattern=IDENTIFIER_PATTERN, maxLength=64))
    occurrence: int | None = dc_field(default=None, metadata=_m(minimum=1))
    reason: str | None = dc_field(default=None, metadata=_m(maxLength=400))


@dataclass
class ReviewFlag:
    target: str = dc_field(metadata=_m(maxLength=200))
    reason: str = dc_field(metadata=_m(maxLength=400))


@dataclass
class Plan:
    # `schema` and `contract_version` are stamped automatically and never need to be written by hand.
    # They exist so a file left over from an older package is refused with a clear message instead of
    # being half-understood. Supplying a wrong one is still an error.
    template_sha256: str = dc_field(metadata=_m(pattern=SHA256_PATTERN))
    manifest_sha256: str = dc_field(metadata=_m(pattern=SHA256_PATTERN))
    schema: str = dc_field(default=SCHEMA_PLAN, metadata=_m(const=SCHEMA_PLAN))
    contract_version: str = dc_field(default=CONTRACT_VERSION, metadata=_m(const=CONTRACT_VERSION))
    locale: dict[str, Any] = dc_field(default_factory=dict)
    decisions: list[Decision] = dc_field(default_factory=list)
    fields: list[FieldSpec] = dc_field(default_factory=list)
    operations: list[Operation] = dc_field(default_factory=list)
    review_flags: list[ReviewFlag] = dc_field(default_factory=list)
    instructions_used: list[str] = dc_field(default_factory=list)
    allow_large_deletion: bool = False
    prepared_by: str | None = dc_field(default=None, metadata=_m(maxLength=200))
    notes: str | None = dc_field(default=None, metadata=_m(maxLength=2000))


# --------------------------------------------------------------------------------------
# Values (arbitrary JSON input)
# --------------------------------------------------------------------------------------

@dataclass
class Values:
    # Only `data` matters here; the schema marker is stamped automatically.
    data: Any = None
    schema: str = dc_field(default=SCHEMA_VALUES, metadata=_m(const=SCHEMA_VALUES))
    provenance: str | None = dc_field(default=None, metadata=_m(maxLength=400))


# --------------------------------------------------------------------------------------
# Report (output of `run_job.py execute`)
# --------------------------------------------------------------------------------------

@dataclass
class Check:
    id: str = dc_field(metadata=_m(pattern=r"^[a-z0-9_.-]+$"))
    outcome: str = dc_field(metadata=_m(enum=CHECK_OUTCOMES))
    detail: str = dc_field(default="", metadata=_m(maxLength=800))


@dataclass
class ReviewItem:
    code: str = dc_field(metadata=_m(pattern=r"^[a-z0-9_]+$"))
    detail: str = dc_field(default="", metadata=_m(maxLength=800))
    target: str | None = None


@dataclass
class Change:
    op: str
    part: str
    paragraph: str | None = None
    before: str | None = None
    after: str | None = None
    detail: str | None = None


@dataclass
class OutputInfo:
    filename: str
    sha256: str = dc_field(metadata=_m(pattern=SHA256_PATTERN))
    size_bytes: int = dc_field(metadata=_m(minimum=0))


@dataclass
class Report:
    schema: str = dc_field(metadata=_m(const=SCHEMA_REPORT))
    skill_version: str
    contract_version: str = dc_field(metadata=_m(const=CONTRACT_VERSION))
    job_id: str = dc_field(metadata=_m(pattern=JOB_ID_PATTERN))
    created_utc: str = dc_field(metadata=_m(pattern=UTC_TIMESTAMP_PATTERN))
    template_sha256: str = dc_field(metadata=_m(pattern=SHA256_PATTERN))
    policy_sha256: str = dc_field(metadata=_m(pattern=SHA256_PATTERN))
    result: str = dc_field(metadata=_m(enum=RESULTS))
    manifest_sha256: str | None = dc_field(default=None, metadata=_m(pattern=SHA256_PATTERN))
    plan_sha256: str | None = dc_field(default=None, metadata=_m(pattern=SHA256_PATTERN))
    values_sha256: str | None = dc_field(default=None, metadata=_m(pattern=SHA256_PATTERN))
    checks: list[Check] = dc_field(default_factory=list)
    review: list[ReviewItem] = dc_field(default_factory=list)
    changes: list[Change] = dc_field(default_factory=list)
    output: OutputInfo | None = None
    notes: list[str] = dc_field(default_factory=list)


# --------------------------------------------------------------------------------------
# Serialisation and hashing
# --------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=256)
def _hints(cls: type) -> dict[str, Any]:
    return typing.get_type_hints(cls)


@functools.lru_cache(maxsize=256)
def _fields(cls: type) -> tuple:
    return dataclasses.fields(cls)


def to_dict(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_dict(getattr(obj, f.name)) for f in _fields(type(obj))}
    if isinstance(obj, list):
        return [to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): to_dict(v) for k, v in obj.items()}
    return obj


def canonical_bytes(data: Any, cls: type | None = None) -> bytes:
    """Deterministic JSON bytes: the fully materialised document (defaults included), sorted keys."""
    if isinstance(data, dict):
        if cls is None:
            raise TypeError("canonical_bytes(dict) needs the document class so defaults are materialised")
        data = from_dict(data, cls)
    return json.dumps(to_dict(data), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pretty_json(data: Any) -> str:
    return json.dumps(to_dict(data), sort_keys=True, indent=2, ensure_ascii=False) + "\n"


# Keys the plan draft keeps even at their default, because they are the work the reader has to do.
DRAFT_KEEP: dict[str, set[str]] = {"Decision": {"decision", "field"}, "FieldSpec": {"type", "source"}}


def sparse_dict(obj: Any) -> Any:
    """`to_dict` without the keys still sitting at their default.

    Only the plan draft is written this way. Nothing is lost: `from_dict` restores every default, so the
    file validates and hashes exactly as the full form does. It exists so the draft a model reads carries
    the decisions to make rather than a screenful of defaults.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        keep = DRAFT_KEEP.get(type(obj).__name__, set())
        out: dict[str, Any] = {}
        for f in _fields(type(obj)):
            value = getattr(obj, f.name)
            if f.name not in keep:
                if f.default is not dataclasses.MISSING and value == f.default:
                    continue
                if f.default_factory is not dataclasses.MISSING and value == f.default_factory():
                    continue
            out[f.name] = sparse_dict(value)
        return out
    if isinstance(obj, list):
        return [sparse_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): sparse_dict(v) for k, v in obj.items()}
    return obj


def sparse_json(data: Any) -> str:
    return json.dumps(sparse_dict(data), sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_document(data: Any, cls: type | None = None) -> str:
    return sha256_bytes(canonical_bytes(data, cls))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------------------
# Strict structural validation (unknown keys are errors)
# --------------------------------------------------------------------------------------

_NONE_TYPE = type(None)


def _unwrap_optional(tp: Any) -> tuple[Any, bool]:
    origin = typing.get_origin(tp)
    if origin is typing.Union or (hasattr(types, "UnionType") and origin is types.UnionType):
        args = [a for a in typing.get_args(tp) if a is not _NONE_TYPE]
        if len(args) == 1:
            return args[0], True
    return tp, False


def _check_constraints(value: Any, meta: dict[str, Any], path: str, errors: list[str]) -> None:
    if "const" in meta and value != meta["const"]:
        errors.append(f"{path}: must be {meta['const']!r}, got {value!r}")
    if "enum" in meta and value is not None and value not in meta["enum"]:
        errors.append(f"{path}: {value!r} is not one of {list(meta['enum'])}")
    if isinstance(value, str):
        if "pattern" in meta and not re.fullmatch(meta["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {meta['pattern']}")
        if "maxLength" in meta and len(value) > meta["maxLength"]:
            errors.append(f"{path}: longer than {meta['maxLength']} characters")
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in meta and value < meta["minimum"]:
            errors.append(f"{path}: below minimum {meta['minimum']}")


def _validate_value(value: Any, tp: Any, meta: dict[str, Any], path: str, errors: list[str]) -> None:
    tp, optional = _unwrap_optional(tp)
    if value is None:
        if optional or tp is Any:
            return
        errors.append(f"{path}: must not be null")
        return
    if tp is Any:
        return
    if dataclasses.is_dataclass(tp):
        validate_document(value, tp, path, errors)
        return
    origin = typing.get_origin(tp)
    if origin is list:
        if not isinstance(value, list):
            errors.append(f"{path}: expected a list")
            return
        (item_tp,) = typing.get_args(tp) or (Any,)
        for i, item in enumerate(value):
            _validate_value(item, item_tp, {}, f"{path}[{i}]", errors)
        return
    if origin is dict:
        if not isinstance(value, dict):
            errors.append(f"{path}: expected an object")
            return
        args = typing.get_args(tp)
        val_tp = args[1] if len(args) == 2 else Any
        for k, v in value.items():
            _validate_value(v, val_tp, {}, f"{path}.{k}", errors)
        return
    if tp is bool:
        if not isinstance(value, bool):
            errors.append(f"{path}: expected a boolean")
        return
    if tp is int:
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"{path}: expected an integer")
            return
    elif tp is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{path}: expected a number")
            return
    elif tp is str:
        if not isinstance(value, str):
            errors.append(f"{path}: expected a string")
            return
    else:
        errors.append(f"{path}: unsupported type in contract definition: {tp!r}")
        return
    _check_constraints(value, meta, path, errors)


def validate_document(data: Any, cls: type, path: str = "$", errors: list[str] | None = None) -> list[str]:
    """Strictly validate a JSON-like dict against a dataclass contract. Returns a list of errors."""
    if errors is None:
        errors = []
    if not isinstance(data, dict):
        errors.append(f"{path}: expected an object for {cls.__name__}")
        return errors
    hints = _hints(cls)
    fields = {f.name: f for f in _fields(cls)}
    for key in data:
        if key not in fields:
            errors.append(f"{path}.{key}: unknown key")
    for name, f in fields.items():
        required = f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
        if name not in data:
            if required:
                errors.append(f"{path}.{name}: required")
            continue
        _validate_value(data[name], hints[name], dict(f.metadata), f"{path}.{name}", errors)
    return errors


def from_dict(data: dict[str, Any], cls: type) -> Any:
    hints = _hints(cls)
    kwargs: dict[str, Any] = {}
    for f in _fields(cls):
        if f.name in data:
            kwargs[f.name] = _coerce(data[f.name], hints[f.name])
    return cls(**kwargs)


def _coerce(value: Any, tp: Any) -> Any:
    tp, _ = _unwrap_optional(tp)
    if value is None:
        return None
    if dataclasses.is_dataclass(tp):
        return from_dict(value, tp)
    origin = typing.get_origin(tp)
    if origin is list:
        (item_tp,) = typing.get_args(tp) or (Any,)
        return [_coerce(v, item_tp) for v in value]
    return value


# --------------------------------------------------------------------------------------
# Policy and profile
# --------------------------------------------------------------------------------------

def parse_policy(raw: bytes) -> tuple[dict[str, Any], str, list[str]]:
    errors: list[str] = []
    try:
        policy = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        return {}, sha256_bytes(raw), [f"policy is not valid UTF-8 JSON: {exc.__class__.__name__}"]
    if not isinstance(policy, dict):
        return {}, sha256_bytes(raw), [f"policy schema must be {SCHEMA_POLICY}", "policy must be a JSON object"]
    if policy.get("schema") != SCHEMA_POLICY:
        errors.append(f"policy schema must be {SCHEMA_POLICY}")
    for section in ("constructs", "limits", "delivery"):
        if not isinstance(policy.get(section), dict):
            errors.append(f"policy.{section}: required object")
    for key, val in (policy.get("limits") or {}).items():
        if isinstance(val, bool) or not isinstance(val, (int, float)) or val < 0:
            errors.append(f"policy.limits.{key}: must be a non-negative number")
    return policy, sha256_bytes(raw), errors


def load_policy(path: str) -> tuple[dict[str, Any], str, list[str]]:
    with open(path, "rb") as fh:
        return parse_policy(fh.read())


def nested_quantifier(regex: str) -> bool:
    """True when a quantified group itself contains a quantifier, as in `(a+)+`.

    That shape backtracks exponentially on a near miss, so one paragraph can hang an inspection. Length
    and back-reference limits do not prevent it. Character classes are stripped first, because a
    quantifier inside a class is bounded and harmless.
    """
    stack: list[int] = []
    i = 0
    while i < len(regex):
        ch = regex[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "[":                                  # skip a character class, including a leading ']'
            i += 2 if regex[i + 1:i + 2] == "]" else 1
            while i < len(regex) and regex[i] != "]":
                i += 2 if regex[i] == "\\" else 1
            i += 1
            continue
        if ch == "(":
            stack.append(i)
        elif ch == ")" and stack:
            start = stack.pop()
            if regex[i + 1:i + 2] in ("*", "+", "{"):
                body = re.sub(r"\\.|\[[^\]]*\]", "", regex[start + 1:i])
                # A group's own type marker is not a quantifier: (?:...) and friends start with '?'.
                body = re.sub(r"^\?(P<[^>]*>|P=[^)]*|<[=!]|[:=!>#imsxaLu-]*)", "", body)
                # '?' belongs here: (a?){40}a{40} backtracks exponentially just as (a+)+ does.
                if any(q in body for q in "*+?{"):
                    return True
        i += 1
    return False


def _well_formed_patterns(entries: Any, label: str, errors: list[str]) -> list[dict]:
    """Shape-check pattern entries *before* they are merged, so a malformed one cannot raise."""
    if entries is None:
        return []
    if not isinstance(entries, list):
        errors.append(f"{label}: must be a list")
        return []
    out: list[dict] = []
    for i, p in enumerate(entries):
        if not isinstance(p, dict) or not isinstance(p.get("name"), str) or not p["name"] or not isinstance(p.get("regex"), str):
            errors.append(f"{label}[{i}]: each entry needs a name and a regex")
            continue
        out.append(p)
    return out


def _merge_patterns(base: list[dict], extra: list[dict], disabled: set[str]) -> list[dict]:
    by_name: dict[str, dict] = {p["name"]: dict(p) for p in base}
    base_order = [p["name"] for p in base]
    # Overrides come ahead of the defaults, because they are the more specific convention, but they keep
    # the order they were declared in. Inserting each at the front one at a time reversed them, so a
    # generic pattern written last could outrank the specific one written first and claim its text.
    new_order = [p["name"] for p in extra if p["name"] not in by_name]
    for p in extra:
        by_name[p["name"]] = dict(p)
    order = new_order + [n for n in base_order if n not in new_order]
    return [by_name[n] for n in order if n not in disabled]


def parse_profile(default_raw: bytes, override_raw: bytes | None) -> tuple[dict[str, Any], list[str]]:
    """Merge an optional per-job profile over the default and validate the result."""
    errors: list[str] = []
    try:
        profile = json.loads(default_raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        return {}, [f"default profile is not valid UTF-8 JSON: {exc.__class__.__name__}"]
    override: dict[str, Any] = {}
    if override_raw is not None:
        try:
            override = json.loads(override_raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            return {}, [f"profile is not valid UTF-8 JSON: {exc.__class__.__name__}"]
        if not isinstance(override, dict):
            return {}, ["profile must be a JSON object"]
        if override.get("schema", SCHEMA_PROFILE) != SCHEMA_PROFILE:
            errors.append(f"profile schema must be {SCHEMA_PROFILE}")
    raw_disabled = override.get("disable_patterns", [])
    if not isinstance(raw_disabled, list) or not all(isinstance(x, str) for x in raw_disabled):
        errors.append("profile.disable_patterns: must be a list of pattern names")
        raw_disabled = []
    disabled = set(raw_disabled)
    for key in ("field_patterns", "instruction_patterns"):
        base = _well_formed_patterns(profile.get(key), f"profile.{key}", errors)
        extra = _well_formed_patterns(override.get(key), f"profile override {key}", errors)
        profile[key] = _merge_patterns(base, extra, disabled)
    for key in ("parts_in_scope", "instruction_formatting", "blank_cells"):
        if key in override:
            profile[key] = override[key]
    locale = dict(DEFAULT_LOCALE)
    for source in (profile.get("locale"), override.get("locale")):
        if source is None:
            continue
        if not isinstance(source, dict):
            errors.append("profile.locale: must be an object")
            continue
        locale.update(source)
    profile["locale"] = locale
    profile.pop("description", None)
    profile.pop("disable_patterns", None)
    if override.get("name"):
        profile["name"] = str(override["name"])[:120]
    if not isinstance(profile.get("parts_in_scope"), list) or not all(isinstance(x, str) for x in profile["parts_in_scope"]):
        errors.append("profile.parts_in_scope: must be a list of glob patterns")
    for key in ("field_patterns", "instruction_patterns"):
        for p in profile.get(key, []):
            if not isinstance(p, dict) or not isinstance(p.get("name"), str) or not isinstance(p.get("regex"), str):
                errors.append(f"profile.{key}: each entry needs a name and a regex")
                continue
            if p.get("confidence", "medium") not in CONFIDENCES:
                errors.append(f"profile.{key}.{p['name']}: confidence must be high, medium or low")
            if len(p["regex"]) > 1000 or re.search(r"\\[1-9]|\(\?P=", p["regex"]):
                errors.append(f"profile.{key}.{p['name']}: regex too long or uses back-references")
                continue
            if nested_quantifier(p["regex"]):
                errors.append(f"profile.{key}.{p['name']}: a quantified group contains a quantifier, which can backtrack "
                              f"exponentially; rewrite it without the nested repetition")
                continue
            try:
                re.compile(p["regex"])
            except re.error as exc:
                errors.append(f"profile.{key}.{p['name']}: invalid regex ({exc})")
    errors += validate_locale(locale, "profile.locale")
    return profile, errors


def validate_locale(locale: dict[str, Any], path: str = "locale") -> list[str]:
    errors: list[str] = []
    for key in ("months", "months_short"):
        val = locale.get(key)
        if not isinstance(val, list) or len(val) != 12 or not all(isinstance(x, str) and x for x in val):
            errors.append(f"{path}.{key}: must be a list of 12 non-empty strings")
    for key in ("true_text", "false_text", "date_pattern"):
        if not isinstance(locale.get(key), str):
            errors.append(f"{path}.{key}: must be a string")
    if locale.get("decimal_separator") not in DECIMAL_SEPARATORS:
        errors.append(f"{path}.decimal_separator: must be one of {list(DECIMAL_SEPARATORS)}")
    if locale.get("thousands_separator") not in THOUSANDS_SEPARATORS:
        errors.append(f"{path}.thousands_separator: not a permitted separator")
    for key in locale:
        if key not in DEFAULT_LOCALE:
            errors.append(f"{path}.{key}: unknown locale key")
    return errors


def effective_locale(profile_locale: dict[str, Any], plan_locale: dict[str, Any]) -> dict[str, Any]:
    out = dict(DEFAULT_LOCALE)
    out.update(profile_locale or {})
    out.update(plan_locale or {})
    return out


# --------------------------------------------------------------------------------------
# Paths into arbitrary JSON
# --------------------------------------------------------------------------------------

_PATH_SEGMENT_RE = re.compile(r"\[(\d+)\]|([^.\[\]]+)")


def path_segments(path: str) -> list[str]:
    if path in ("", ".", "$"):
        return []
    if path.startswith("/"):
        return [s.replace("~1", "/").replace("~0", "~") for s in path[1:].split("/")]
    if path.startswith("$."):
        path = path[2:]
    return [a if a else b for a, b in _PATH_SEGMENT_RE.findall(path)]


def resolve_path(data: Any, path: str) -> tuple[bool, Any]:
    """(found, value). A missing key or index is `found=False`; a present null is `found=True, None`."""
    cur = data
    for seg in path_segments(path):
        if isinstance(cur, dict):
            if seg not in cur:
                return False, None
            cur = cur[seg]
        elif isinstance(cur, list):
            if not seg.isdigit() or int(seg) >= len(cur):
                return False, None
            cur = cur[int(seg)]
        else:
            return False, None
    return True, cur


def path_errors(path: str) -> list[str]:
    """Validate a source path's shape. `client..name` is a typo that would otherwise resolve silently."""
    if path in ("", ".", "$"):
        return []
    if path.startswith("/"):
        return [] if all(seg for seg in path[1:].split("/")) else ["empty segment in the JSON pointer"]
    body = path[2:] if path.startswith("$.") else path
    if not body:
        return []
    return [] if _PATH_BODY_RE.fullmatch(body) else ["not a valid path: use client.name, items[0].qty or /client/name"]


Path = tuple[str, ...]


def path_key(path: str) -> Path:
    """A path as its segments. Identity is per segment, never the rendered string: a literal key
    "client.name" and a nested client -> name render identically but are different data."""
    return tuple(path_segments(path))


def show_path(key: Path) -> str:
    out = ""
    for seg in key:
        out += f"[{seg}]" if seg.isdigit() else (("." if out else "") + seg)
    return out or "(the whole input)"


def _path_consumed(leaf: Path, consumed: set[Path], containers: set[Path] | None = None) -> bool:
    """A leaf counts as used when a field read it, or read an object containing it.

    `containers` are paths a repeat iterated over. The list itself is used, but its items' keys are still
    accounted for one by one, so a key inside an item that no field maps is still reported as unused.
    """
    if () in consumed or leaf in consumed or (containers and leaf in containers):
        return True
    return any(c and leaf[: len(c)] == c for c in consumed)


def normalize_path(path: str) -> str:
    out = ""
    for seg in path_segments(path):
        out += f"[{seg}]" if seg.isdigit() else (("." if out else "") + seg)
    return out


def leaf_paths(data: Any, prefix: Path = (), out: list[Path] | None = None, limit: int = 100_000) -> list[Path]:
    """Every leaf of the input, as segment tuples. The limit bounds runaway recursion, not reporting:
    what is shown is capped separately, so a large input cannot quietly hide unused values."""
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if isinstance(data, dict):
        if not data and prefix:
            out.append(prefix)
        for k, v in data.items():
            leaf_paths(v, prefix + (str(k),), out, limit)
    elif isinstance(data, list):
        if not data and prefix:
            out.append(prefix)
        for i, v in enumerate(data):
            leaf_paths(v, prefix + (str(i),), out, limit)
    else:
        out.append(prefix)
    return out


# --------------------------------------------------------------------------------------
# Value formatting
# --------------------------------------------------------------------------------------

@dataclass
class Rendered:
    ok: bool
    text: str | None
    used_sentinel: bool = False
    used_empty: bool = False
    errors: list[str] = dc_field(default_factory=list)


def _group_thousands(digits: str, sep: str) -> str:
    if not sep:
        return digits
    out = []
    while len(digits) > 3:
        out.insert(0, digits[-3:])
        digits = digits[:-3]
    out.insert(0, digits)
    return sep.join(out)


def _format_string(value: Any, fmt: dict[str, Any], locale: dict[str, Any], errors: list[str]) -> str | None:
    if isinstance(value, list):
        if not all(isinstance(x, (str, int, float, bool)) or x is None for x in value):
            errors.append("a list value must contain only scalars")
            return None
        def one(x: Any) -> str:
            if x is None:
                return ""
            if isinstance(x, bool):
                return str(x).lower()
            # Line endings are normalised per element, not only on a scalar value, or a CRLF inside a
            # list item reaches the document as a control character and is rejected.
            return str(x).replace("\r\n", "\n").replace("\r", "\n")
        value = str(fmt.get("join", "\n")).join(one(x) for x in value)
    if isinstance(value, bool):
        value = locale["true_text"] if value else locale["false_text"]
    elif isinstance(value, (int, float)):
        value = repr(value) if isinstance(value, float) else str(value)
    if not isinstance(value, str):
        errors.append("expected text (object values cannot be rendered)")
        return None
    text = value.strip() if fmt.get("trim", True) else value
    case = fmt.get("case", "none")
    if case == "upper":
        text = text.upper()
    elif case == "lower":
        text = text.lower()
    elif case == "title":
        text = text.title()
    if "max_length" in fmt and isinstance(fmt["max_length"], int) and len(text) > fmt["max_length"]:
        errors.append("longer than the configured max_length")
        return None
    return text


def _format_integer(value: Any, fmt: dict[str, Any], locale: dict[str, Any], errors: list[str]) -> str | None:
    if isinstance(value, bool):
        errors.append("expected an integer, got a boolean")
        return None
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")) or not value.is_integer():
            errors.append("expected a whole number")
            return None
        value = int(value)
    if isinstance(value, int):
        n = value
        if n >= INTEGER_MAGNITUDE_LIMIT or n <= -INTEGER_MAGNITUDE_LIMIT:
            errors.append(f"integer exceeds {MAX_INTEGER_DIGITS} digits")
            return None
    elif isinstance(value, str):
        if not ASCII_INTEGER_RE.fullmatch(value.strip()):
            errors.append(f"expected 1-{MAX_INTEGER_DIGITS} ASCII digits with an optional leading '-'")
            return None
        digits = value.strip().lstrip("-")
        if digits.startswith("0") and digits != "0":
            errors.append("leading zeros would be lost; declare this field as string")
            return None
        n = int(value.strip())
    else:
        errors.append("expected an integer or a string of ASCII digits")
        return None
    if "min" in fmt and isinstance(fmt["min"], int) and n < fmt["min"]:
        errors.append("below the configured min")
        return None
    if "max" in fmt and isinstance(fmt["max"], int) and n > fmt["max"]:
        errors.append("above the configured max")
        return None
    sep = fmt.get("thousands_separator", locale["thousands_separator"])
    return ("-" if n < 0 else "") + _group_thousands(str(abs(n)), sep)


def _format_decimal(value: Any, fmt: dict[str, Any], locale: dict[str, Any], errors: list[str]) -> str | None:
    if isinstance(value, bool):
        errors.append("expected a number, got a boolean")
        return None
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            errors.append("not a finite number")
            return None
        value = repr(value)
    elif isinstance(value, int):
        value = str(value)
    if not isinstance(value, str):
        errors.append("expected a number or a numeric string")
        return None
    value = value.strip()
    if not DECIMAL_STRING_RE.fullmatch(value) and not re.fullmatch(r"-?[0-9]+(\.[0-9]+)?[eE][-+]?[0-9]+", value):
        errors.append("not a plain decimal: -?digits[.digits], at most 30 integer and 20 fraction digits")
        return None
    precision = fmt.get("precision", 2)
    if not isinstance(precision, int) or isinstance(precision, bool) or not (0 <= precision <= 12):
        errors.append("format.precision must be an integer between 0 and 12")
        return None
    rounding = ROUND_HALF_UP if fmt.get("rounding", "half_even") == "half_up" else ROUND_HALF_EVEN
    try:
        with localcontext() as ctx:
            ctx.prec = DECIMAL_CONTEXT_PRECISION
            ctx.traps[InvalidOperation] = True
            d = Decimal(value)
            for bound, worse in (("min", lambda a, b: a < b), ("max", lambda a, b: a > b)):
                if bound in fmt:
                    if not (isinstance(fmt[bound], str) and DECIMAL_STRING_RE.fullmatch(fmt[bound])):
                        errors.append(f"format.{bound} is not a plain decimal string")
                        return None
                    if worse(d, Decimal(fmt[bound])):
                        errors.append(f"outside the configured {bound}")
                        return None
            q = d.quantize(Decimal(1).scaleb(-precision), rounding=rounding)
            sign = "-" if q < 0 else ""
            digits = f"{abs(q):f}"
    except (InvalidOperation, ValueError) as exc:
        errors.append(f"decimal out of the supported range: {exc.__class__.__name__}")
        return None
    whole, _, frac = digits.partition(".")
    whole = _group_thousands(whole, fmt.get("thousands_separator", locale["thousands_separator"]))
    dec_sep = fmt.get("decimal_separator", locale["decimal_separator"])
    return sign + whole + (dec_sep + frac if precision > 0 else "")


def format_date(d: date, pattern: str, locale: dict[str, Any]) -> str:
    def token(mt: re.Match) -> str:
        t = mt.group(0)
        if t == "YYYY":
            return f"{d.year:04d}"
        if t == "YY":
            return f"{d.year % 100:02d}"
        if t == "MMMM":
            return locale["months"][d.month - 1]
        if t == "MMM":
            return locale["months_short"][d.month - 1]
        if t == "MM":
            return f"{d.month:02d}"
        if t == "M":
            return str(d.month)
        if t == "DD":
            return f"{d.day:02d}"
        return str(d.day)
    return DATE_TOKEN_RE.sub(token, pattern)


def _format_date(value: Any, fmt: dict[str, Any], locale: dict[str, Any], errors: list[str]) -> str | None:
    mt = ISO_DATE_RE.fullmatch(value.strip()) if isinstance(value, str) else None
    if mt is None:
        errors.append("dates must be ISO 8601 (YYYY-MM-DD, optionally followed by a time)")
        return None
    try:
        d = date.fromisoformat(mt.group(1))
    except ValueError:
        errors.append("not a valid calendar date")
        return None
    return format_date(d, fmt.get("pattern", locale["date_pattern"]), locale)


def _format_boolean(value: Any, fmt: dict[str, Any], locale: dict[str, Any], errors: list[str]) -> str | None:
    if isinstance(value, str) and value.strip().lower() in ("true", "false", "yes", "no", "y", "n", "1", "0"):
        value = value.strip().lower() in ("true", "yes", "y", "1")
    if not isinstance(value, bool):
        errors.append("expected true or false")
        return None
    text = fmt.get("true_text", locale["true_text"]) if value else fmt.get("false_text", locale["false_text"])
    if not isinstance(text, str):
        errors.append("format.true_text/false_text must be strings")
        return None
    return text


_FORMATTERS = {"string": _format_string, "integer": _format_integer, "decimal": _format_decimal,
               "date": _format_date, "boolean": _format_boolean}


def check_rendered_text(text: str, max_chars: int) -> list[str]:
    """Only printable characters, newline and tab may reach the document."""
    errors: list[str] = []
    if len(text) > max_chars:
        errors.append(f"rendered text longer than {max_chars} characters")
    for ch in text:
        cp = ord(ch)
        if ch in ("\n", "\t"):
            continue
        if cp < 0x20 or 0x7F <= cp <= 0x9F:
            errors.append(f"control character U+{cp:04X} is not permitted")
            break
        if 0xD800 <= cp <= 0xDFFF or cp in (0xFFFE, 0xFFFF):
            errors.append("character not permitted in XML 1.0")
            break
    return errors


def _absence(spec: FieldSpec, what: str, max_chars: int) -> Rendered:
    if spec.absence_policy == "required":
        return Rendered(False, None, errors=[f"required but the value is {what}"])
    if spec.absence_policy == "sentinel":
        text = spec.absence_text or ""
        errs = check_rendered_text(text, max_chars)
        if not text.strip():
            errs.append("absence_text is blank")
        return Rendered(not errs, text if not errs else None, used_sentinel=True, errors=errs)
    return Rendered(True, "", used_empty=True)


def format_value(spec: FieldSpec, found: bool, raw: Any, locale: dict[str, Any], limits: dict[str, Any] | None = None) -> Rendered:
    """Render one value. Missing, null and blank inputs go through the field's absence policy;
    everything else is formatted by type. Nothing is coerced silently across types."""
    limits = limits or {}
    max_chars = int(limits.get("max_value_chars", 10000))
    if not found:
        return _absence(spec, "missing from the input", max_chars)
    if raw is None:
        return _absence(spec, "null", max_chars)
    if isinstance(raw, str) and raw.strip() == "":
        return _absence(spec, "empty", max_chars)
    if isinstance(raw, list) and not raw:
        return _absence(spec, "an empty list", max_chars)
    errors: list[str] = []
    if isinstance(raw, str):
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    try:
        text = _FORMATTERS[spec.type](raw, spec.format, locale, errors)
    except (TypeError, AttributeError, IndexError, KeyError, ValueError, ArithmeticError) as exc:
        # Backstop only. Invalid format and locale settings are rejected by validate_field_spec and
        # validate_locale before anything is rendered; a formatter must never take the run down.
        return Rendered(False, None, errors=[f"could not be formatted ({type(exc).__name__}); check the field's format and the locale"])
    if text is None:
        return Rendered(False, None, errors=errors)
    errors += check_rendered_text(text, max_chars)
    if errors:
        return Rendered(False, None, errors=errors)
    if text == "":
        return _absence(spec, "empty after formatting", max_chars)
    return Rendered(True, text)


def validate_field_spec(spec: FieldSpec, limits: dict[str, Any], path: str, errors: list[str]) -> None:
    allowed = FORMAT_KEYS.get(spec.type)
    if allowed is None:
        errors.append(f"{path}.type: unknown type")
        return
    fmt: dict[str, Any] = {}
    for key, val in spec.format.items():
        if key not in allowed:
            errors.append(f"{path}.format.{key}: not a format key for type {spec.type}")
        elif isinstance(val, bool) and bool not in allowed[key] or not isinstance(val, allowed[key]):
            errors.append(f"{path}.format.{key}: wrong type")
        else:
            fmt[key] = val
    if spec.type == "string":
        if "case" in fmt and fmt["case"] not in STRING_CASES:
            errors.append(f"{path}.format.case: must be one of {list(STRING_CASES)}")
        if "max_length" in fmt and not (1 <= fmt["max_length"] <= int(limits.get("max_value_chars", 10000))):
            errors.append(f"{path}.format.max_length: out of range")
    if spec.type in ("integer", "decimal") and fmt.get("thousands_separator") not in (None, *THOUSANDS_SEPARATORS):
        errors.append(f"{path}.format.thousands_separator: not a permitted separator")
    if spec.type == "integer" and "min" in fmt and "max" in fmt and fmt["min"] > fmt["max"]:
        errors.append(f"{path}.format: min is greater than max")
    if spec.type == "decimal":
        if fmt.get("decimal_separator") not in (None, *DECIMAL_SEPARATORS):
            errors.append(f"{path}.format.decimal_separator: must be '.' or ','")
        if fmt.get("rounding") not in (None, *ROUNDING_MODES):
            errors.append(f"{path}.format.rounding: must be half_even or half_up")
        if "precision" in fmt and not (0 <= fmt["precision"] <= 12):
            errors.append(f"{path}.format.precision: must be between 0 and 12")
        for bound in ("min", "max"):
            if bound in fmt and not DECIMAL_STRING_RE.fullmatch(fmt[bound]):
                errors.append(f"{path}.format.{bound}: not a plain decimal string")
    if spec.type == "date" and "pattern" in fmt and not DATE_TOKEN_RE.search(fmt["pattern"]):
        errors.append(f"{path}.format.pattern: contains no date token (YYYY, MM, D ...)")
    if spec.absence_policy == "sentinel" and not (spec.absence_text or "").strip():
        errors.append(f"{path}.absence_text: required when absence_policy is sentinel")
    if spec.absence_policy != "sentinel" and spec.absence_text:
        errors.append(f"{path}.absence_text: only allowed with absence_policy sentinel")
    if spec.source is not None and spec.literal is not None:
        errors.append(f"{path}: give either source or literal, not both")
    if spec.source is None and spec.literal is None:
        errors.append(f"{path}: needs a source path into the input data or a literal")
    if spec.source is not None:
        errors += [f"{path}.source: {e}" for e in path_errors(spec.source)]


# --------------------------------------------------------------------------------------
# Compile: plan + manifest + values -> normalised edits per part
# --------------------------------------------------------------------------------------

@dataclass
class Replacement:
    start: int
    end: int
    text: str
    candidate_id: str | None = None
    control: bool = False


@dataclass
class RowRepeat:
    anchor: int                                     # paragraph index that identifies the row
    first: int
    last: int
    copies: list[dict[int, list[Replacement]]]     # per copy: replacements by paragraph index
    op_id: str = ""


@dataclass
class CompiledPart:
    replacements: dict[int, list[Replacement]] = dc_field(default_factory=dict)
    deleted: set[int] = dc_field(default_factory=set)              # every paragraph index that disappears
    delete_paragraphs: list[int] = dc_field(default_factory=list)
    delete_ranges: list[tuple[int, int]] = dc_field(default_factory=list)   # block_first(A) .. block_last(B)
    delete_rows: list[int] = dc_field(default_factory=list)                 # anchor paragraph index
    delete_breaks: list[tuple[int, int]] = dc_field(default_factory=list)   # (paragraph index, 1-based break)
    repeats: list[RowRepeat] = dc_field(default_factory=list)
    inserts: dict[int, list[str]] = dc_field(default_factory=dict)

    def touched(self) -> set[int]:
        out = set(self.replacements) | self.deleted | set(self.inserts) | {i for i, _ in self.delete_breaks}
        for rep in self.repeats:
            out |= set(range(rep.first, rep.last + 1))
        return out


@dataclass
class Compiled:
    parts: dict[str, CompiledPart] = dc_field(default_factory=dict)
    errors: list[str] = dc_field(default_factory=list)
    review: list[ReviewItem] = dc_field(default_factory=list)
    field_texts: dict[str, str] = dc_field(default_factory=dict)
    consumed_paths: set[tuple[str, ...]] = dc_field(default_factory=set)
    container_paths: set[tuple[str, ...]] = dc_field(default_factory=set)
    stats: dict[str, int] = dc_field(default_factory=dict)

    def is_empty(self) -> bool:
        return not any(p.replacements or p.deleted or p.repeats or p.inserts or p.delete_breaks for p in self.parts.values())


def _clip(text: str, n: int) -> str:
    text = text.replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= n else text[: n - 1] + "\u2026"


def compile_plan(plan: Plan, manifest: Manifest, values: Values, policy: dict[str, Any]) -> Compiled:
    """Turn the plan into edits. Every problem becomes an entry in `errors`; nothing raises."""
    limits = policy.get("limits", {})
    out = Compiled()
    errors = out.errors
    review = out.review
    locale = effective_locale(manifest.profile.get("locale", {}), plan.locale)
    locale_errors = validate_locale(locale, "$.locale")
    errors += locale_errors

    if plan.template_sha256 != manifest.template.sha256:
        errors.append("$.template_sha256: does not match the manifest's template")
    if plan.manifest_sha256 != sha256_document(manifest):
        errors.append("$.manifest_sha256: does not match the job's manifest; re-derive the plan from the current manifest")

    paragraphs = {p.id: p for p in manifest.paragraphs}
    by_part_index = {(p.part, p.index): p for p in manifest.paragraphs}
    rows = {r.id: r for r in manifest.rows}
    candidates = {c.id: c for c in manifest.candidates}
    cparts: dict[str, CompiledPart] = {}

    def cpart(part: str) -> CompiledPart:
        return cparts.setdefault(part, CompiledPart())

    def para(pid: str | None, path: str) -> ParagraphInfo | None:
        if pid is None:
            errors.append(f"{path}: paragraph id required")
            return None
        p = paragraphs.get(pid)
        if p is None:
            errors.append(f"{path}: unknown paragraph {pid}")
        return p

    # ---- fields ------------------------------------------------------------------------
    specs: dict[str, FieldSpec] = {}
    bad_specs: set[str] = set()
    for i, spec in enumerate(plan.fields):
        before = len(errors)
        if spec.name in specs:
            errors.append(f"$.fields[{i}]: duplicate field name {spec.name!r}")
        specs[spec.name] = spec
        validate_field_spec(spec, limits, f"$.fields[{i}]", errors)
        if len(errors) > before:
            bad_specs.add(spec.name)     # never rendered: a value formatted under invalid settings is meaningless
    op_ids = {op.id for op in plan.operations if op.id}
    for spec in plan.fields:
        if spec.repeat is not None and spec.repeat not in op_ids:
            errors.append(f"$.fields.{spec.name}.repeat: no repeat_row operation with id {spec.repeat!r}")

    rendered_cache: dict[str, Rendered] = {}

    def render(spec: FieldSpec, data: Any, item_prefix: Path | None) -> Rendered:
        if spec.name in bad_specs or locale_errors:
            return Rendered(False, None)      # the configuration error is already reported; do not format
        if spec.literal is not None:
            found, raw = True, spec.literal
        else:
            found, raw = resolve_path(data, spec.source or "")
            base = path_key(spec.source or "")
            out.consumed_paths.add((item_prefix + base) if item_prefix is not None else base)
        return format_value(spec, found, raw, locale, limits)

    def render_global(name: str) -> Rendered | None:
        spec = specs.get(name)
        if spec is None:
            return None
        if name not in rendered_cache:
            r = render(spec, values.data, None)
            rendered_cache[name] = r
            if r.ok:
                out.field_texts[name] = r.text or ""
                if spec.literal is not None:
                    review.append(ReviewItem("literal_value", f"{name}: value comes from the plan, not from the input data", name))
                if r.used_sentinel:
                    review.append(ReviewItem("sentinel_used", f"{name}: absence text inserted", name))
                elif r.used_empty:
                    review.append(ReviewItem("empty_used", f"{name}: rendered empty; the placeholder disappears", name))
            elif r.errors:
                errors.append(f"$.fields.{name}: {r.errors[0]}")
        return rendered_cache[name]

    def render_paragraphs(spec: FieldSpec, path: str) -> list[str] | None:
        """One rendered string per paragraph. A list value becomes one paragraph per item, so a
        multi-paragraph answer is inserted at an anchor without the plan knowing how many there are."""
        if spec.name in bad_specs or locale_errors:
            return None
        if spec.literal is not None:
            found, raw = True, spec.literal
            review.append(ReviewItem("literal_value", f"{spec.name}: value comes from the plan, not from the input data", spec.name))
        else:
            found, raw = resolve_path(values.data, spec.source or "")
            out.consumed_paths.add(path_key(spec.source or ""))
        items = raw if isinstance(raw, list) and raw else [raw]
        texts: list[str] = []
        for n, item in enumerate(items):
            r = format_value(spec, found, item, locale, limits)
            if not r.ok:
                if r.errors:
                    errors.append(f"{path}: {r.errors[0]}" + (f" (paragraph {n + 1})" if len(items) > 1 else ""))
                return None
            if r.used_sentinel:
                review.append(ReviewItem("sentinel_used", f"{spec.name}: absence text inserted", spec.name))
            elif r.used_empty:
                review.append(ReviewItem("empty_used", f"{spec.name}: rendered empty", spec.name))
            texts.append(r.text or "")
        return texts

    # ---- operations: deletions, rows, inserts -----------------------------------------
    repeats_by_op: dict[str, tuple[Operation, RowInfo, list[Any]]] = {}
    for i, op in enumerate(plan.operations):
        path = f"$.operations[{i}]"
        if op.op == "delete_paragraph":
            p = para(op.paragraph, path)
            if p is None:
                continue
            if "section_break" in p.flags:
                errors.append(f"{path}: {p.id} carries a section break and cannot be deleted")
                continue
            cp = cpart(p.part)
            cp.delete_paragraphs.append(p.index)
            cp.deleted.add(p.index)
        elif op.op == "delete_range":
            a, b = para(op.from_paragraph, path + ".from_paragraph"), para(op.to_paragraph, path + ".to_paragraph")
            if a is None or b is None:
                continue
            if a.part != b.part or a.container_id != b.container_id:
                errors.append(f"{path}: from_paragraph and to_paragraph must lie in the same container (both body-level, or both in the same cell)")
                continue
            first, last = a.block_first, b.block_last
            if first > last:
                errors.append(f"{path}: from_paragraph comes after to_paragraph")
                continue
            span = [q for (part, idx), q in by_part_index.items() if part == a.part and first <= idx <= last]
            if any("section_break" in q.flags for q in span):
                errors.append(f"{path}: the range contains a section break and cannot be deleted")
                continue
            cp = cpart(a.part)
            cp.delete_ranges.append((first, last))
            cp.deleted.update(range(first, last + 1))
        elif op.op == "delete_break":
            p = para(op.paragraph, path)
            if p is None:
                continue
            n = 1 if op.occurrence is None else op.occurrence
            # Counted over the whole paragraph. The stored text is a bounded preview, so a break past
            # that boundary is still a break.
            if p.break_count < n:
                errors.append(f"{path}: {p.id} has no break number {n}; it has {p.break_count}")
                continue
            cp = cpart(p.part)
            cp.delete_breaks.append((p.index, n))
        elif op.op in ("delete_row", "repeat_row"):
            p = para(op.paragraph, path)
            if p is None:
                continue
            row = rows.get(p.row_id or "")
            if row is None:
                errors.append(f"{path}: {p.id} is not inside a table row")
                continue
            if op.op == "delete_row":
                if row.row_count < 2:
                    errors.append(f"{path}: the table has only one row; use delete_range to remove the whole table")
                    continue
                cp = cpart(p.part)
                cp.delete_rows.append(p.index)
                cp.deleted.update(range(row.first_index, row.last_index + 1))
            else:
                if not op.id:
                    errors.append(f"{path}: repeat_row needs an id so fields can refer to it")
                    continue
                if op.id in repeats_by_op:
                    errors.append(f"{path}: duplicate operation id {op.id!r}")
                    continue
                bad_path = path_errors(op.source or "")
                if bad_path:
                    errors.append(f"{path}.source: {bad_path[0]}")
                    continue
                found, items = resolve_path(values.data, op.source or "")
                if not found or not isinstance(items, list):
                    errors.append(f"{path}.source: does not resolve to a list in the input data")
                    continue
                if len(items) > int(limits.get("max_repeat_items", 500)):
                    errors.append(f"{path}: {len(items)} items exceeds max_repeat_items")
                    continue
                out.container_paths.add(path_key(op.source or ""))
                repeats_by_op[op.id] = (op, row, items)
        elif op.op == "insert_paragraph_after":
            p = para(op.paragraph, path)
            if p is None:
                continue
            if (op.text is None) == (op.field is None):
                errors.append(f"{path}: give either text or field")
                continue
            if op.text is not None:
                text = op.text.replace("\r\n", "\n")
                errs = check_rendered_text(text, int(limits.get("max_value_chars", 10000)))
                if errs:
                    errors.append(f"{path}.text: {errs[0]}")
                    continue
                review.append(ReviewItem("inserted_text", f"{p.id}: paragraph inserted with text from the plan", p.id))
                texts = [text]
            else:
                if op.field not in specs:
                    errors.append(f"{path}.field: unknown field {op.field!r}")
                    continue
                texts = render_paragraphs(specs[op.field], f"{path}.field")
                if texts is None:
                    continue
            cpart(p.part).inserts.setdefault(p.index, []).extend(texts)
        else:
            errors.append(f"{path}.op: unknown operation")

    # ---- decisions ----------------------------------------------------------------------
    decisions: dict[str, Decision] = {}
    for i, d in enumerate(plan.decisions):
        if d.candidate_id not in candidates:
            errors.append(f"$.decisions[{i}]: unknown candidate {d.candidate_id}")
            continue
        if d.candidate_id in decisions:
            errors.append(f"$.decisions[{i}]: duplicate decision for {d.candidate_id}")
        decisions[d.candidate_id] = d

    def in_repeat(c: Candidate) -> str | None:
        for op_id, (op, row, _items) in repeats_by_op.items():
            if row.part == c.part and row.first_index <= c.paragraph_index <= row.last_index:
                return op_id
        return None

    row_field_candidates: dict[str, list[tuple[Candidate, FieldSpec | None]]] = {k: [] for k in repeats_by_op}
    for c in manifest.candidates:
        cp = cparts.get(c.part)
        if cp is not None and c.paragraph_index in cp.deleted:
            continue                                    # the paragraph goes; the candidate is moot
        d = decisions.get(c.id)
        rep = in_repeat(c)
        if not c.eligible and (d is None or d.decision in (None, "literal", "keep")):
            review.append(ReviewItem("unfillable", f"{c.id}: {_clip(c.text, 60)!r} stays in the document; {c.ineligibility_reason}", c.id))
            continue
        if d is None or d.decision is None:
            if c.decision_required and c.eligible:
                errors.append(f"$.decisions: no decision for {c.kind} candidate {c.id} ({_clip(c.text, 40)!r})")
            continue
        if d.decision == "literal":
            if c.kind == "field" and c.confidence == "high":
                review.append(ReviewItem("literal_high_confidence", f"{c.id}: {_clip(c.text, 60)!r} left as literal text", c.id))
            continue
        if d.decision == "keep":
            review.append(ReviewItem("kept", f"{c.id}: {c.kind} {_clip(c.text, 60)!r} deliberately kept", c.id))
            continue
        if not c.eligible:
            errors.append(f"$.decisions: {c.id} cannot be {d.decision}: {c.ineligibility_reason}")
            continue
        if d.decision == "remove_paragraph":
            if rep is not None:
                errors.append(f"$.decisions: {c.id}: remove_paragraph is not allowed inside a repeated row; use remove_text")
                continue
            p = by_part_index[(c.part, c.paragraph_index)]
            if "section_break" in p.flags:
                errors.append(f"$.decisions: {c.id}: its paragraph carries a section break and cannot be removed")
                continue
            cpx = cpart(c.part)
            if c.paragraph_index not in cpx.deleted:
                cpx.delete_paragraphs.append(c.paragraph_index)
                cpx.deleted.add(c.paragraph_index)
            continue
        if d.decision == "remove_text":
            s, e = c.char_start, c.char_end
            if c.context_after[:1] == " ":
                e += 1
            elif c.context_before[-1:] == " ":
                s -= 1
            if rep is not None:
                # Applied in every copy of the row: recorded with the widened span and no field.
                row_field_candidates[rep].append((dataclasses.replace(c, char_start=s, char_end=e), None))
            else:
                cpart(c.part).replacements.setdefault(c.paragraph_index, []).append(Replacement(s, e, "", c.id, c.control is not None))
            continue
        # decision == field
        spec = specs.get(d.field or "")
        if spec is None:
            errors.append(f"$.decisions: {c.id}: field {d.field!r} is not declared in $.fields")
            continue
        if spec.repeat is not None and spec.repeat != rep:
            errors.append(f"$.decisions: {c.id}: field {spec.name!r} belongs to repeat {spec.repeat!r} but the candidate is not in that row")
            continue
        if c.mixed_formatting:
            review.append(ReviewItem("mixed_formatting", f"{c.id}: the placeholder spans runs with different formatting; the first run's formatting applies", c.id))
        if rep is not None:
            row_field_candidates[rep].append((c, spec))
            continue
        r = render_global(spec.name)
        if r is None or not r.ok:
            continue
        cpart(c.part).replacements.setdefault(c.paragraph_index, []).append(Replacement(c.char_start, c.char_end, r.text or "", c.id, c.control is not None))

    # ---- repeated rows -------------------------------------------------------------------
    for op_id, (op, row, items) in repeats_by_op.items():
        prefix = path_key(op.source or "")
        copies: list[dict[int, list[Replacement]]] = []
        for n, item in enumerate(items):
            copy: dict[int, list[Replacement]] = {}
            for c, spec in row_field_candidates[op_id]:
                if spec is None:
                    text = ""
                elif spec.repeat == op_id:
                    r = render(spec, item, prefix + (str(n),))
                    if not r.ok:
                        if r.errors:
                            errors.append(f"$.fields.{spec.name} (row {n}): {r.errors[0]}")
                        continue
                    if r.used_sentinel:
                        review.append(ReviewItem("sentinel_used", f"{spec.name} (row {n}): absence text inserted", spec.name))
                    elif r.used_empty:
                        review.append(ReviewItem("empty_used", f"{spec.name} (row {n}): rendered empty; the placeholder disappears", spec.name))
                    text = r.text or ""
                else:
                    rg = render_global(spec.name)
                    if rg is None or not rg.ok:
                        continue
                    text = rg.text or ""
                copy.setdefault(c.paragraph_index, []).append(Replacement(c.char_start, c.char_end, text, c.id, c.control is not None))
            copies.append(copy)
        cpart(row.part).repeats.append(RowRepeat(anchor=paragraphs[op.paragraph or ""].index, first=row.first_index, last=row.last_index, copies=copies, op_id=op_id))
        if not items:
            review.append(ReviewItem("row_removed", f"{op_id}: the input list is empty, so the template row is removed", op_id))

    # ---- conflicts and bounds --------------------------------------------------------------
    total_deleted = inserted = 0
    for part, cp in cparts.items():
        for idx, repls in cp.replacements.items():
            if idx in cp.deleted:
                errors.append(f"{part}#p{idx}: has a replacement and is also deleted")
            repls.sort(key=lambda r: r.start)
            for x, y in zip(repls, repls[1:]):
                if y.start < x.end:
                    errors.append(f"{part}#p{idx}: overlapping replacements ({x.candidate_id} and {y.candidate_id}); decide one of them literal")
                    break
        for idx, _n in cp.delete_breaks:
            if idx in cp.deleted:
                errors.append(f"{part}#p{idx}: its break is removed and the paragraph is also deleted")
            if idx in cp.replacements:
                errors.append(f"{part}#p{idx}: a break cannot be removed from a paragraph that is also being filled")
        if len(set(cp.delete_breaks)) != len(cp.delete_breaks):
            errors.append(f"{part}: the same break is removed twice")
        for idx in cp.inserts:
            if idx in cp.deleted:
                errors.append(f"{part}#p{idx}: cannot insert after a deleted paragraph")
            inserted += len(cp.inserts[idx])
        spans = [(r.first, r.last) for r in cp.repeats]
        for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
            if a2 <= b1 and a1 <= b2:
                errors.append(f"{part}: two repeat_row operations address overlapping rows")
        for rep in cp.repeats:
            if any(rep.first <= i <= rep.last for i in cp.deleted):
                errors.append(f"{part}: a repeated row overlaps a deleted region")
            if any(rep.first <= i <= rep.last for i in cp.replacements):
                errors.append(f"{part}: a repeated row also has a direct replacement; row candidates must use repeat-scoped fields")
        # A repeat with no items removes its template row, so it counts as a deletion.
        # Removals are judged against what would survive, not against the template. Two delete_row
        # operations each see a two-row table and each look safe; together they leave a table with no
        # rows at all, which is not a valid table. An empty repeat removes its row the same way.
        emptied: dict[str, int] = {}
        for row in manifest.rows:
            if row.part != part:
                continue
            gone = row.first_index in cp.delete_rows or any(
                rep.first == row.first_index and not rep.copies for rep in cp.repeats)
            if gone:
                emptied[row.table_id] = emptied.get(row.table_id, 0) + 1
        for table_id, removed in sorted(emptied.items()):
            total = sum(1 for r in manifest.rows if r.table_id == table_id)
            if removed >= total:
                errors.append(f"{table_id}: all {total} row(s) would be removed, leaving a table with none; "
                              f"delete the whole table with delete_range instead")
        total_deleted += len(cp.deleted) + sum(rep.last - rep.first + 1 for rep in cp.repeats if not rep.copies)
    n_paragraphs = max(1, len(manifest.paragraphs))
    fraction = total_deleted / n_paragraphs
    if fraction > float(limits.get("max_deleted_fraction", 0.5)):
        if plan.allow_large_deletion:
            review.append(ReviewItem("large_deletion", f"{total_deleted} of {n_paragraphs} paragraphs deleted (allowed by the plan)"))
        else:
            errors.append(f"$.operations: {total_deleted} of {n_paragraphs} paragraphs would be deleted; set allow_large_deletion to confirm")
    if inserted > int(limits.get("max_inserted_paragraphs", 200)):
        errors.append(f"$.operations: {inserted} inserted paragraphs exceeds max_inserted_paragraphs")

    # ---- review: flags, unused input, findings --------------------------------------------
    for flag in plan.review_flags:
        review.append(ReviewItem("review_flag", f"{flag.target}: {flag.reason}", flag.target))
    for f in manifest.findings:
        if f.severity == "report":
            review.append(ReviewItem("template_finding", f"{f.code}: {f.detail}"[:200], f.part))
    if isinstance(values.data, (dict, list)):
        unused = [p for p in leaf_paths(values.data) if not _path_consumed(p, out.consumed_paths, out.container_paths)]
        if unused:
            cap = int(limits.get("max_unused_paths_listed", 25))
            shown = ", ".join(show_path(u) for u in unused[:cap])
            review.append(ReviewItem("unused_input", f"{len(unused)} input value(s) not used by any field: "
                                     + shown + (f" ... and {len(unused) - cap} more" if len(unused) > cap else "")))
    out.parts = cparts
    out.stats = {"deleted_paragraphs": total_deleted, "inserted_paragraphs": inserted,
                 "repeated_rows": sum(len(cp.repeats) for cp in cparts.values()),
                 "replacements": sum(len(v) for cp in cparts.values() for v in cp.replacements.values())}
    return out


# --------------------------------------------------------------------------------------
# Result derivation
# --------------------------------------------------------------------------------------

def derive_result(checks: list[Check], review: list[ReviewItem]) -> str:
    if not checks or any(c.outcome != "passed" for c in checks):
        return "failed"
    return "needs_review" if review else "ok"
