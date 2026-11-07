#!/usr/bin/env python3
"""closeout_core - shared rules for the engagement-closeout-knowledge-harvest engines.

One byte-identical copy ships in the scripts/ folder of asset-identify, lesson-cluster,
sanitize-check and knowledge-record. It holds the strict loader, the input contract validator, the
embedded-instruction screen (through the vendored shared steering_guard.py), the three deterministic
stages, the knowledge-record skeleton and the whole-document replay every later stage runs.
Section numbers cite references/reuse-asset-rubric.md, lesson-taxonomy.md and
confidentiality-sanitisation-rules.md. No network, no model calls, no side effects beyond --out.
"""
import bisect
import functools
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import steering_guard as sg  # noqa: E402  vendored byte for byte from shared/steering-guard

SCREENING_LABEL = f"steering_guard {sg.__version__} (shared, vendored) with the closeout hook profile"

CONTRACT = "ps.engagement-closeout-knowledge-harvest.v1"
ENGINE_VERSIONS = {
    "asset_identify": "asset_identify/1.0.5",
    "lesson_cluster": "lesson_cluster/1.0.5",
    "sanitize_check": "sanitize_check/1.0.5",
}

WITHHELD = "[withheld: embedded instruction held for review - see screening_holds]"
DRAFT_LABEL = "DRAFT - HUMAN REVIEW REQUIRED"
MAX_INPUT_BYTES = 5_000_000
MAX_DEPTH = 64
# Screening is linear in the number of records and list items (#8.1); these ceilings only keep one
# run inside the runner's time budget (confidentiality-sanitisation-rules.md #8.1, README).
MAX_RECORDS = 1000
MAX_TOTAL_RECORDS = 2500
MAX_LIST_ITEMS = 200

# Plugin vocabulary passes to the shared detector only through its documented hooks
# (confidentiality-sanitisation-rules.md #8.1). Closeout text never legitimately carries an e-mail
# address or URL, so any contact detail is treated as steering.
GUARD_HOOKS = {
    "extra_verdict_words": (
        "release candidate", "release ready", "cleared for reuse", "approved for reuse",
        "approved for external use", "sanitised", "sanitized", "publishable", "no redaction needed",
        "client approved", "internal reuse candidate", "satisfied", "met", "external use", "safe to publish",
        "safe to reuse", "publication ready", "cleared", "already reviewed",
        # QA round 2 closeout vocabulary (#8.1): "redaction complete" closes detector gap line 2;
        # "published" closes "mark/treat this record as published".
        "published", "redaction complete", "confidentiality cleared", "cleared for external use",
        "approved for publication",
    ),
    "extra_rule_nouns": (
        "confidentiality terms", "confidentiality rules", "sanitisation rules", "sanitization rules",
        "aggregation rule", "aggregation review", "redaction", "practice review", "client terms",
        "govern step", "sanitisation gate", "sanitisation check", "sanitization check", "confidentiality check",
        "redaction check", "client approval", "written approval",
        "knowledge base", "external use", "client consent", "consent requirement", "publication rule",
    ),
    "contact_is_steering": True,
}

# reuse-asset-rubric.md
GENERALISABILITY_WEIGHT = 0.35   # #1.1
EFFORT_WEIGHT = 0.25             # #2.1
SHELF_LIFE_WEIGHT = 0.20         # #3.1
DEPENDENCY_WEIGHT = 0.20         # #4.1
SHORTLIST_SCORE = 70             # #5.1
RETAIN_SCORE = 50                # #5.2
SCORING_CONFIDENCE_FLOOR = 0.70  # #5.1

# lesson-taxonomy.md
CLUSTER_KEYWORDS = {
    "delivery-governance": ["governance", "sign-off", "signoff", "decision", "escalation", "scope", "steerco", "owner"],
    "adoption-change": ["training", "adoption", "champion", "communications", "readiness", "change"],
    "data-integration": ["data", "migration", "integration", "environment", "api", "cutover", "defect"],
    "commercial-staffing": ["staffing", "budget", "contract", "margin", "partner", "resourcing"],
}
CATEGORY_CITATIONS = {
    "delivery-governance": "lesson-taxonomy.md #1.1",
    "adoption-change": "lesson-taxonomy.md #1.2",
    "data-integration": "lesson-taxonomy.md #1.3",
    "commercial-staffing": "lesson-taxonomy.md #1.4",
    "unclassified": "lesson-taxonomy.md #1.5",
}
HIGH_IMPACT_TERMS = ["blocker", "critical", "delayed", "rework", "executive", "go-live", "golive"]  # #2.1
MIN_CLUSTER_CONFIDENCE = 0.70  # #3.1

# confidentiality-sanitisation-rules.md
DIRECT_IDENTIFIER_MARKERS = {"client_name", "client_logo", "client_domain", "site_name", "project_codename"}  # #1.1
CLIENT_SPECIFIC_MARKERS = {"client_specific_configuration"}  # #1.3
NAMED_PERSON_MARKERS = {"named_individual", "named_person_blame"}  # #2.1, #2.2
COMMERCIAL_MARKERS = {"pricing", "contract_value", "revenue", "margin", "precise_headcount", "implementation_date"}  # #3.1
LICENSED_MARKERS = {"licensed_third_party_content", "vendor_screenshot", "benchmark_excerpt"}  # #4.1
PRODUCT_AGGREGATION_MARKERS = {"third_party_product", "named_vendor"}  # #4.2
AGGREGATION_TOKENS = {
    "sector", "region", "client_headcount", "go_live_date", "third_party_product", "named_vendor",
    "unique_architecture", "rare_operating_model", "distinctive_metric",
    "generic_operating_model", "generic_training_pattern",
}  # #5.3
KNOWN_MARKERS = (DIRECT_IDENTIFIER_MARKERS | CLIENT_SPECIFIC_MARKERS | NAMED_PERSON_MARKERS
                 | COMMERCIAL_MARKERS | LICENSED_MARKERS | PRODUCT_AGGREGATION_MARKERS)
AGGREGATION_MIN_TOKENS = 4  # #5.1
SANITISATION_CONFIDENCE_FLOOR = 0.80  # #6.1
DEFAULT_REVIEW_REQUIRED = True  # #6.2
BLAME_PATTERN = re.compile(r"\b(?:failed|fault|blamed|missed|caused)\b", re.IGNORECASE)  # #2.2
PERSON_NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:[-'][A-Z][a-z]+)?\s+[A-Z][a-z]+(?:[-'][A-Z][a-z]+)?\b")

RELEASE = "RELEASE_CANDIDATE_SANITISED"
# Clearance-state precedence, most restrictive first (#7.3). An asset takes the first state that applies.
PRECEDENCE = (
    "HOLD_EMBEDDED_INSTRUCTION",
    "HOLD_IDENTITY_UNSCREENABLE",
    "HOLD_TERMS_UNAVAILABLE",
    "HOLD_UNRECOGNISED_MARKER",
    "HOLD_PERSONAL_DATA_REWRITE",
    "HOLD_RIGHTS_UNKNOWN",
    "HOLD_REDACTION_REQUIRED",
    "HOLD_AGGREGATION_RISK",
    "HOLD_LOW_CONFIDENCE",
    "HOLD_NOT_SHORTLISTED",
    RELEASE,
)

# ---------------------------------------------------------------------------------------------
# Errors, canonical forms and the strict loader
# ---------------------------------------------------------------------------------------------


class InputError(Exception):
    """A clean input error. The message names a field path and the expected shape; it never
    repeats a supplied value, file name or unknown member name (D17)."""


def strip_cf(text):
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


def canon(text):
    """One canonical form for every comparison (A13): NFKC, no Cf characters, casefold, single spaces."""
    return " ".join(strip_cf(unicodedata.normalize("NFKC", strip_cf(text))).casefold().split())


def canon_id(text):
    """canon() with '-', '_', '.' and spaces folded away, for identifier comparisons (A13)."""
    return re.sub(r"[-_.\s]+", "", canon(text))


def words(text):
    return re.findall(r"[a-z0-9]+", canon(text))


ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
TOKEN_RE = re.compile(r"[a-z][a-z0-9_]{0,63}")
SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
SOURCE_RE = re.compile(r"(skill|connector):[a-z0-9][a-z0-9_.-]{0,63}")
TS_RE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
DATE_RE = re.compile(r"\d{4}-\d\d-\d\d")
STATUSES = ("complete", "draft", "missing", "superseded")

# Label forms the engines emit or that downstream Mobilization reserves (D25): cluster and hold
# IDs, the knowledge-record ID suffix, hold IDs, file paths and positions, and display fallbacks.
_RESERVED_RE = re.compile(
    r"(?:lc|sh)[-_. ]?\d+"
    r"|.*[-_. ]kr[-_. ]draft"
    r"|hold(?:-[a-z0-9]+){2,}"
    r"|(?:raw|upstream|expected|demo-data)/.*|rendered order of .*"
    r"|[\w.-]+\.(?:csv|md|json|txt)\b.*"
    r"|(?:rows?|lines?|clauses?) \d+(?:(?: ?[-,] ?| and )\d+)*(?:\.\w+)?"
    r"|[\w.]*\[\d+\][\w.\[\]]*(?: .*)?"
    r"|\(blank [\w ]+\)|this client or matter|released knowledge asset .+|lesson: .*|<member>"
)


def reserved_label(value):
    text = canon(value)
    return bool(text) and bool(_RESERVED_RE.fullmatch(text))


def _no_duplicate_members(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise InputError("a JSON object repeats a member name (name not repeated); duplicate members are malformed")
        seen.add(key)
    return dict(pairs)


def _refuse_constant(_):
    raise InputError("a JSON number is NaN or Infinity; only finite numbers are accepted")


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise InputError("a JSON number is out of range; only finite numbers are accepted")
    return value


_STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"', re.DOTALL)


def _depth_ok(text):
    depth = 0
    for match in re.finditer(r"[\[\]{}]", _STRING_RE.sub('""', text)):
        if match.group() in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                return False
        else:
            depth -= 1
    return True


def load_json(path, label="input"):
    """Strict JSON load (A7, A11, A14): UTF-8, size cap, depth cap, no duplicate members, finite numbers."""
    try:
        with open(path, "rb") as handle:
            data = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputError(f"{label} file could not be read") from None
    if len(data) > MAX_INPUT_BYTES:
        raise InputError(f"{label} is larger than {MAX_INPUT_BYTES} bytes")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError(f"{label} is not UTF-8 text") from None
    if not _depth_ok(text):
        raise InputError(f"{label} nests JSON deeper than {MAX_DEPTH} levels")
    try:
        return json.loads(text, object_pairs_hook=_no_duplicate_members,
                          parse_constant=_refuse_constant, parse_float=_finite_float)
    except InputError:
        raise
    except (ValueError, RecursionError):
        raise InputError(f"{label} is not valid JSON") from None


def read_text(path, label, limit=1_000_000):
    try:
        with open(path, "rb") as handle:
            data = handle.read(limit + 1)
    except OSError:
        raise InputError(f"{label} file could not be read") from None
    if len(data) > limit:
        raise InputError(f"{label} is larger than {limit} bytes")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError(f"{label} is not UTF-8 text") from None


def write_text(path, text):
    """Atomic LF write: the target appears only when the whole output is ready (G3)."""
    directory = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=directory, prefix=".closeout-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as output:
            output.write(text)
        os.replace(temp, path)
    except BaseException:
        if os.path.exists(temp):
            os.remove(temp)
        raise


def dump(doc):
    return json.dumps(doc, indent=2)


# ---------------------------------------------------------------------------------------------
# Field paths and value validators (D17: only contract vocabulary is ever named)
# ---------------------------------------------------------------------------------------------

CONTRACT_VOCAB = frozenset({
    "contract_version", "run_metadata", "generated_at", "demo_scenario", "engagement", "engagement_id",
    "title", "client_name", "client_descriptor", "sector", "region", "client_headcount", "go_live_date",
    "third_party_products", "confidence", "source", "citation", "artifacts", "artifact_id", "artifact_type",
    "required", "status", "owner", "candidate_assets", "asset_id", "asset_type", "description",
    "generalisability", "effort_to_recreate", "shelf_life_months", "client_dependency",
    "confidentiality_markers", "aggregation_tokens", "decision_log", "decision_id", "summary", "impact",
    "retrospective_inputs", "input_id", "text", "speaker_role", "named_people", "confidentiality_terms",
    "term_id", "escalations", "deliverable_index", "completeness_gap", "reusable_asset_shortlist",
    "reuse_score", "recommendation", "reuse_rationale", "clearance_state", "lesson_clusters", "cluster_id",
    "category", "priority_score", "review_candidate", "evidence_ids", "evidence_citations", "summary_seed",
    "sensitivity_signals", "evidence_id", "signal", "sanitisation_report", "overall_disposition", "findings",
    "target_type", "target_id", "disposition", "reason", "governance_note", "released_assets",
    "review_required", "held_assets", "lessons_for_draft", "rewrite_required", "drafting_guidance",
    "knowledge_record", "record_id", "engagement_context_guidance", "reusable_assets",
    "held_assets_summary", "lessons", "sanitisation_summary", "downstream_handoff", "consumer_template",
    "contract_fields", "handoff_note", "draft_label", "provenance", "engines", "input_escalations",
    "policies", "screening", "screening_holds", "hold_id", "path", "location", "family",
})


def seg(key):
    return key if key in CONTRACT_VOCAB else "<member>"


def _type_name(value):
    if isinstance(value, bool):
        return "true or false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return "a number"
    if isinstance(value, str):
        return "a string"
    if isinstance(value, list):
        return "an array"
    return "an object"


def need_object(value, path):
    if type(value) is not dict:
        raise InputError(f"{path} must be a JSON object, got {_type_name(value)} (value not repeated)")
    return value


def need_list(value, path):
    if type(value) is not list:
        raise InputError(f"{path} must be a JSON array, got {_type_name(value)} (value not repeated)")
    return value


def check_members(obj, path, required, optional=()):
    allowed = set(required) | set(optional)
    for key in obj:
        if key not in allowed:
            raise InputError(f"{path}.{seg(key)} is not a member the contract allows here (name not repeated)")
    for key in required:
        if key not in obj:
            raise InputError(f"{path}.{key} is required (an absent member is not an empty one)")


def timestamp_ok(value):
    if type(value) is not str or not TS_RE.fullmatch(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def date_ok(value):
    if type(value) is not str or not DATE_RE.fullmatch(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _check_text(value, path, ctx, name=False):
    if type(value) is not str:
        raise InputError(f"{path} must be a string, got {_type_name(value)} (value not repeated)")
    if value == WITHHELD and ctx["replay"]:
        if path not in ctx["prior"]:
            raise InputError(f"{path} carries the withheld placeholder without a screening hold for that path (confidentiality-sanitisation-rules.md #8.4)")
        ctx["bound"].add(path)
        return
    if not value.strip():
        raise InputError(f"{path} must not be blank")
    if name and reserved_label(value):
        raise InputError(f"{path} is in a label form the engines reserve (value not repeated)")


def _check_ident(value, path):
    if type(value) is not str:
        raise InputError(f"{path} must be an identifier string, got {_type_name(value)} (value not repeated)")
    if not ID_RE.fullmatch(value):
        raise InputError(f"{path} must be 1-64 ASCII letters, digits, '.', '_' or '-' starting with a letter or digit (value not repeated)")
    if reserved_label(value):
        raise InputError(f"{path} is in a label form the engines reserve (value not repeated)")
    if id_hits(value):
        raise InputError(f"{path} reads as an instruction to the reviewer or tool (value not repeated)")
    if not id_shape_ok(value):
        raise InputError(f"{path} reads as a phrase, not an identifier (value not repeated)")


def _check_token(value, path):
    if type(value) is not str or not TOKEN_RE.fullmatch(value):
        raise InputError(f"{path} must be a lowercase marker token (letters, digits, '_'; value not repeated)")
    if id_hits(value):
        raise InputError(f"{path} reads as an instruction to the reviewer or tool (value not repeated)")


def _check_value(kind, value, path, ctx):
    if kind == "text":
        _check_text(value, path, ctx)
    elif kind == "name":
        _check_text(value, path, ctx, name=True)
    elif kind == "id":
        _check_ident(value, path)
    elif kind == "bool":
        if type(value) is not bool:
            raise InputError(f"{path} must be true or false, got {_type_name(value)} (value not repeated)")
    elif kind == "score5":
        if type(value) is not int or not 0 <= value <= 5:
            raise InputError(f"{path} must be a whole number from 0 to 5 (value not repeated)")
    elif kind == "months":
        if type(value) is not int or not 0 <= value <= 600:
            raise InputError(f"{path} must be a whole number of months from 0 to 600 (value not repeated)")
    elif kind == "headcount":
        if value is not None and (type(value) is not int or value < 0):
            raise InputError(f"{path} must be a non-negative whole number or null (value not repeated)")
    elif kind == "num01":
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise InputError(f"{path} must be a number from 0 to 1 (value not repeated)")
    elif kind == "source":
        if type(value) is not str or not SOURCE_RE.fullmatch(value):
            raise InputError(f"{path} must be skill:<name> or connector:<name>; engine: sources are reserved for the engines (value not repeated)")
        if id_hits(value):
            raise InputError(f"{path} reads as an instruction to the reviewer or tool (value not repeated)")
    elif kind == "status":
        if type(value) is not str or value not in STATUSES:
            raise InputError(f"{path} must be one of complete, draft, missing or superseded (value not repeated)")
    elif kind == "date":
        if not date_ok(value):
            raise InputError(f"{path} must be a calendar date YYYY-MM-DD (value not repeated)")
    elif kind in ("names", "texts", "tokens"):
        need_list(value, path)
        if kind != "tokens" and len(value) > MAX_LIST_ITEMS:
            raise InputError(f"{path} has more than {MAX_LIST_ITEMS} items, above the screening ceiling (#8.1); "
                             f"nothing was screened (values not repeated)")
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"
            if kind == "tokens":
                _check_token(item, item_path)
            else:
                _check_text(item, item_path, ctx, name=(kind == "names"))
    else:  # pragma: no cover - programming error
        raise AssertionError(kind)


# The input contract the first stage enforces (A1, A2, A5a, A15). (member, kind, required)
RECORD_SPECS = {
    "engagement": (
        ("engagement_id", "id", True), ("title", "name", True), ("client_name", "name", True),
        ("client_descriptor", "text", True), ("sector", "text", False), ("region", "text", False),
        ("client_headcount", "headcount", False), ("go_live_date", "date", False),
        ("third_party_products", "texts", False), ("confidence", "num01", True),
        ("source", "source", True), ("citation", "text", True),
    ),
    "artifacts": (
        ("artifact_id", "id", True), ("title", "name", True), ("artifact_type", "text", True),
        ("required", "bool", True), ("status", "status", True), ("owner", "name", True),
        ("confidence", "num01", True), ("source", "source", True), ("citation", "text", True),
    ),
    "candidate_assets": (
        ("asset_id", "id", True), ("title", "name", True), ("asset_type", "text", True),
        ("description", "text", True), ("generalisability", "score5", True),
        ("effort_to_recreate", "score5", True), ("shelf_life_months", "months", True),
        ("client_dependency", "score5", True), ("confidentiality_markers", "tokens", True),
        ("aggregation_tokens", "tokens", True), ("confidence", "num01", True),
        ("source", "source", True), ("citation", "text", True),
    ),
    "decision_log": (
        ("decision_id", "id", True), ("summary", "text", True), ("impact", "text", True),
        ("confidence", "num01", True), ("source", "source", True), ("citation", "text", True),
    ),
    "retrospective_inputs": (
        ("input_id", "id", True), ("speaker_role", "name", True), ("text", "text", True),
        ("named_people", "names", True), ("confidence", "num01", True), ("source", "source", True),
        ("citation", "text", True),
    ),
    "confidentiality_terms": (
        ("term_id", "id", True), ("summary", "text", True), ("confidence", "num01", True),
        ("source", "source", True), ("citation", "text", True),
    ),
}
ID_FIELDS = {
    "engagement": "engagement_id", "artifacts": "artifact_id", "candidate_assets": "asset_id",
    "decision_log": "decision_id", "retrospective_inputs": "input_id", "confidentiality_terms": "term_id",
}
RAW_ARRAYS = ("artifacts", "candidate_assets", "decision_log", "retrospective_inputs", "confidentiality_terms")
RAW_REQUIRED = ("contract_version", "engagement") + RAW_ARRAYS
RAW_OPTIONAL = ("run_metadata", "escalations")
ENGINE_SECTIONS = (
    "deliverable_index", "reusable_asset_shortlist", "lesson_clusters", "sanitisation_report",
    "released_assets", "held_assets", "lessons_for_draft", "knowledge_record", "provenance", "screening_holds",
)
STAGE_KEYS = {
    1: set(RAW_REQUIRED) | {"run_metadata", "escalations", "deliverable_index", "reusable_asset_shortlist",
                            "provenance", "screening_holds"},
}
STAGE_KEYS[2] = STAGE_KEYS[1] | {"lesson_clusters"}
STAGE_KEYS[3] = STAGE_KEYS[2] | {"sanitisation_report", "released_assets", "held_assets", "lessons_for_draft",
                                 "knowledge_record"}
STAGE_NAMES = {1: "asset_identify", 2: "lesson_cluster", 3: "sanitize_check"}


def _check_contract_version(doc):
    need_object(doc, "input")
    if "contract_version" not in doc:
        raise InputError("contract_version is required")
    if doc["contract_version"] != CONTRACT:
        raise InputError(f"wrong contract version (expected {CONTRACT}; value not repeated)")


def validate_input(doc, generated_at=None, prior=None):
    """Validate the engagement input (or the raw sections an intermediate carries) and return
    (input, timestamp). prior maps a carried placeholder's path to its screening hold (replay)."""
    _check_contract_version(doc)
    for key in doc:
        if key in ENGINE_SECTIONS:
            raise InputError(f"{key} is engine-owned and may not be supplied in the engagement input")
    check_members(doc, "input", (), RAW_REQUIRED + RAW_OPTIONAL)
    ctx = {"replay": prior is not None, "prior": prior or {}, "bound": set()}
    for name in RAW_ARRAYS:
        if name not in doc or type(doc[name]) is not list:
            raise InputError(f"missing or invalid required array: {name} (absent, null or another type is not an empty list)")
        if len(doc[name]) > MAX_RECORDS:
            raise InputError(f"{name} has more than {MAX_RECORDS} records, above the screening ceiling (#8.1); "
                             f"nothing was screened (values not repeated)")
    # The upstream escalations are a screened top-level list too, so they count toward every ceiling.
    upstream = len(doc["escalations"]) if type(doc.get("escalations")) is list else 0
    if upstream > MAX_RECORDS:
        raise InputError(f"escalations has more than {MAX_RECORDS} items, above the screening ceiling (#8.1); "
                         f"nothing was screened (values not repeated)")
    if sum(len(doc[name]) for name in RAW_ARRAYS) + upstream > MAX_TOTAL_RECORDS:
        raise InputError(f"the input arrays and escalations hold more than {MAX_TOTAL_RECORDS} records together, "
                         f"above the screening ceiling (#8.1); nothing was screened (values not repeated)")
    if "engagement" not in doc or type(doc["engagement"]) is not dict:
        raise InputError("missing or invalid required object: engagement")

    timestamp = generated_at
    if generated_at is not None and not timestamp_ok(generated_at):
        raise InputError("--generated-at must be an ISO-8601 UTC timestamp YYYY-MM-DDTHH:MM:SSZ")
    run_metadata = {}
    if "run_metadata" in doc:
        run_metadata = need_object(doc["run_metadata"], "run_metadata")
        check_members(run_metadata, "run_metadata", (), ("generated_at", "demo_scenario"))
        if "generated_at" in run_metadata:
            if not timestamp_ok(run_metadata["generated_at"]):
                raise InputError("run_metadata.generated_at must be an ISO-8601 UTC timestamp YYYY-MM-DDTHH:MM:SSZ (value not repeated)")
            if timestamp is not None and timestamp != run_metadata["generated_at"]:
                raise InputError("--generated-at and run_metadata.generated_at disagree")
            timestamp = run_metadata["generated_at"]
        if "demo_scenario" in run_metadata:
            value = run_metadata["demo_scenario"]
            if type(value) is not str or not SLUG_RE.fullmatch(value) or id_hits(value):
                raise InputError("run_metadata.demo_scenario must be a lowercase slug (value not repeated)")
    if timestamp is None:
        raise InputError("run_metadata.generated_at is required (or pass --generated-at)")

    escalations, merged = [], set()
    if "escalations" in doc:
        need_list(doc["escalations"], "escalations")
        for index, item in enumerate(doc["escalations"]):
            _check_text(item, f"escalations[{index}]", ctx)
            if item == WITHHELD or item not in merged:  # identical upstream escalations merge once (A8)
                escalations.append(item)
                merged.add(item)

    def check_record(record, path, spec):
        need_object(record, path)
        check_members(record, path, [m for m, _, req in spec if req], [m for m, _, req in spec if not req])
        for member, kind, _ in spec:
            if member in record:
                _check_value(kind, record[member], f"{path}.{member}", ctx)

    check_record(doc["engagement"], "engagement", RECORD_SPECS["engagement"])
    evidence_ids = {}
    for name in RAW_ARRAYS:
        seen = {}
        for index, record in enumerate(doc[name]):
            path = f"{name}[{index}]"
            check_record(record, path, RECORD_SPECS[name])
            key = canon_id(record[ID_FIELDS[name]])
            if key in seen:
                raise InputError(f"{path}.{ID_FIELDS[name]} duplicates {name}[{seen[key]}] in canonical form (A12)")
            seen[key] = index
            if name in ("decision_log", "retrospective_inputs"):
                if key in evidence_ids:
                    raise InputError(f"{path}.{ID_FIELDS[name]} duplicates an evidence ID used in {evidence_ids[key]}")
                evidence_ids[key] = path
    if ctx["replay"] and set(ctx["prior"]) - ctx["bound"]:
        pass  # holds whose path is not a placeholder are refused by the whole-document comparison
    clean = {
        "contract_version": CONTRACT,
        "run_metadata": {"generated_at": timestamp},
        "engagement": json.loads(json.dumps(doc["engagement"])),
    }
    if "demo_scenario" in run_metadata:
        clean["run_metadata"]["demo_scenario"] = run_metadata["demo_scenario"]
    for name in RAW_ARRAYS:
        clean[name] = json.loads(json.dumps(doc[name]))
    clean["escalations"] = escalations
    return clean, timestamp


# ---------------------------------------------------------------------------------------------
# Embedded-instruction screen (D1-D3, D5, D11, D13, D15, D16, D18, D20-D22)
# ---------------------------------------------------------------------------------------------

_MARKER_RE = re.compile(r"[\[\u27e6\u3010\u3014][^\[\]\u27e6\u27e7\u3010\u3011\u3014\u3015]{0,60}?\bwithheld\b")
FAMILIES = tuple(sg.FAMILIES) + ("supplied_marker", "client_identity", "render_shape")
LOCATION_RE = re.compile(r"field|record|run|rendered|line \d+|lines \d+-\d+")
HOLD_REASONS = {
    "oversize": "field too long to screen; withheld for review (text not repeated)",
    "supplied_marker": "field carries a withheld-marker form the engines did not emit; withheld for review (text not repeated)",
    "client_identity": "field repeats the engagement client name, which is itself withheld; withheld for review (text not repeated)",
    "instruction": "embedded instruction or steering text; the field is withheld for review (text not repeated)",
    "render_shape": "value is not in a render-safe shape (a title is a short noun phrase; a citation is a source "
                    "path or document ID with an optional locator); withheld for review (text not repeated)",
}

# ---------------------------------------------------------------------------------------------
# Render policy (confidentiality-sanitisation-rules.md #8.6). A supplied title or citation reaches
# the governed record and the skeleton only in a positive allow-shape, so text the detector misses
# cannot render: anything else is withheld with a render_shape hold.
# ---------------------------------------------------------------------------------------------

TITLE_MAX_CHARS = 80
TITLE_MAX_WORDS = 10
CITATION_MAX_CHARS = 160
_TITLE_PUNCT = set(" -&/(),+'\u2019")
# Words that make a clause rather than a noun phrase: auxiliaries, modals, negation, pronouns,
# demonstratives, politeness and steering adverbs.
_TITLE_CLAUSE_WORDS = frozenset((
    "is am are was were be been being do does did has have had can could will would shall should must might "
    "not no never nothing nobody please kindly this these that those it its they them we us you your i me "
    "he she him said says say tell told so already now just straight again exactly anyone everyone someone"
).split())
# Imperative or verdict verbs that never head a reusable-asset noun phrase.
_TITLE_VERBS = frozenset((
    "approve approved approves publish published publishes waive waived waives bypass bypassed ignore ignored "
    "ignores disregard disregarded overlook overlooked skip skipped skips vouch vouched vetted cleared "
    "authorise authorised authorize authorized escalate reopen examine delete consider"
).split())
# Verbs that are also nouns ("Release plan", "Review checklist"): refused only as the first word
# followed by a determiner, pronoun or 'as/for/to/without' ("Release the asset", "Share as is").
_TITLE_LEAD_VERBS = frozenset((
    "release share send mark keep leave flag treat look go move use take make put let check review close file "
    "list accept allow forward grant permit sign remove drop add set give push post upload distribute circulate "
    "copy label rate classify record"
).split())
_TITLE_LEAD_FOLLOWERS = frozenset("the a an all every any each our their my his her as for to without".split())
_TITLE_PHRASES = ("fine to", "ok to", "okay to", "safe to", "good to go", "as is", "cleared for", "approved for",
                  "for external use", "no need", "no one", "they are", "as it is")
# A negation makes a clause only when a verb or clause material follows ("DoNotFlagThisAsset"), so an
# established name such as "DoNotDisturb" stays a noun phrase.
_NEGATIONS = ("donot", "doesnot", "didnot")
# Clause material (#8.6): the determiners, pronouns and object words that turn a verb into an
# instruction ("ReleaseThisRecord", "skipthisrecord", "PublishingThisRecordNow"). Strong verbs also
# take a preposition ("approveforexternaluse", "vouchedfor").
_DETERMINERS = frozenset((
    "the this these that those it its them all every any each our their my his her us me you your everything now"
).split())
_OBJECTS = frozenset("record records asset assets".split())
_PREPOSITIONS = ("for", "to", "as", "without")
# Inside a run of letters only these longer words count as material, so 'Markit' or 'closeout' is no clause.
_RUN_MATERIAL = ("the", "this", "these", "that", "those", "them", "their", "all", "every", "each", "any", "our",
                 "now", "record", "asset")
# Derivational and inflectional endings that turn a strong verb into a noun or modifier ('approver',
# 'publishing', 'considerations'): such a word is a clause only when clause material follows.
_DERIVED = frozenset("s es d ed ing ings r rs er ers ation ations able al als ment ments ance".split())
FUSED_MIN_CHARS = 5
LEAD_RUN_MIN_CHARS = 4
# A lead verb shorter than LEAD_RUN_MIN_CHARS ('use', 'set', 'go') fused at the start of a longer part
# is a clause only when the rest of the part, with any parts after it, begins with one or more
# determiners then a known object, whatever follows ('usethisrecord', 'ADDTHISRECORDPLAN'), or with a
# pronoun object (_object_start, the boundary rule): 'Gothenburg', 'Setallocations' and 'Usecase' stay
# names.
_SHORT_DETERMINERS = ("the", "this", "these", "that", "those", "all", "every", "each", "any", "our", "their",
                      "my", "your", "its")
_SHORT_OBJECTS = ("record", "records", "asset", "assets", "entry", "entries", "item", "items", "section",
                  "sections", "file", "files", "document", "documents", "page", "pages", "lesson", "lessons")
_SHORT_PRONOUNS = ("it", "them", "everything")
# Steering words and verdict phrases are clause-shaped wherever they appear, run together or not.
_FUSED_WORDS = ("already", "exactly", "kindly", "please", "nothing", "nobody")
_FUSED_NEEDLES = tuple(sorted(set(_FUSED_WORDS) | {phrase.replace(" ", "") for phrase in _TITLE_PHRASES
                                                   if len(phrase.replace(" ", "")) >= FUSED_MIN_CHARS}))
# The internal word boundaries of each run-together verdict phrase ('safeto': 4), the case evidence
# a split phrase is read by ('xsafeToReuse').
_PHRASE_BOUNDARIES = {phrase.replace(" ", ""): tuple(len("".join(phrase.split()[:index]))
                                                     for index in range(1, len(phrase.split())))
                      for phrase in _TITLE_PHRASES if len(phrase.replace(" ", "")) >= FUSED_MIN_CHARS}
_TRIGGER_VERBS = tuple(sorted(_TITLE_VERBS | _TITLE_LEAD_VERBS))
# The comparison skeleton folds only these look-alike digits and symbols, inside runs that hold a letter.
_LOOKALIKE_DIGITS = {"0": "o", "3": "e", "4": "a", "5": "s", "7": "t"}
_CITE_LOCATOR = (r"(?:rows?|lines?|clauses?|sections?|pages?|pp?\.|slides?|paras?|paragraphs?|items?|tabs?|sheets?|"
                 r"cells?|tables?|figures?|fig\.|appendix|annex|schedule|\u00a7)")
_CITE_TOKEN = r"(?:\d[A-Za-z0-9.]{0,15}|[A-Za-z]{1,2}(?:[\d.][A-Za-z0-9.]{0,13})?)"
_CITE_VALUE = _CITE_TOKEN + r"(?:\s?[-\u2013]\s?" + _CITE_TOKEN + r")?"
_CITE_NAMED = r"(?:sheet|tab)\s[A-Za-z][A-Za-z0-9_]{0,31}"
_CITE_PART = (r"[A-Za-z0-9][A-Za-z0-9_./\\-]{0,119}(?:#[A-Za-z0-9][A-Za-z0-9_.-]{0,63})?"
              r"(?:,?\s(?:" + _CITE_NAMED + r"|" + _CITE_LOCATOR + r"\s?" + _CITE_VALUE
              + r"(?:,\s?" + _CITE_VALUE + r")*))*")
CITATION_RE = re.compile(_CITE_PART + r"(?:;\s?" + _CITE_PART + r")*")
_CITE_SOURCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./\\-]*")
_CITE_WORDS = re.compile(r"#([A-Za-z0-9][A-Za-z0-9_.-]*)|\b(?:sheet|tab)\s([A-Za-z][A-Za-z0-9_]*)")
_TITLE_PATH = re.compile(r"(?:engagement|artifacts\[\d+\]|candidate_assets\[\d+\])\.title")
_CITATION_PATH = re.compile(r"(?:engagement|[a-z_]+\[\d+\])\.citation")


def has_cf(value):
    """True when the value carries a Unicode format (Cf) character such as a zero-width space."""
    return any(unicodedata.category(char) == "Cf" for char in value)


# A lone 4 (no digit beside it) next to a letter: a look-alike 'a' or shorthand for 'for'.
_LONE_FOUR = re.compile(r"(?<!\d)(?:(?<=[^\W\d_])4(?!\d)|4(?=[^\W\d_]))")


def comparison_skeletons(value):
    """The comparison copies of a value (#8.6), never rendered: NFKD with combining marks (Mn) dropped,
    '@' read as 'a' and '$' as 's', and inside a letter-and-digit run that holds a letter the look-alike
    digits 0, 3, 4, 5 and 7 read as o, e, a, s and t, and 1 as i in one copy and l in the other. A folded
    character takes the case of the nearest letter, so case boundaries survive. A lone 4 beside a
    letter may also be shorthand for 'for' ('NoNeedleRoadmap4Share'), so such a value also gets an
    unfolded copy."""
    base = "".join(ch for ch in unicodedata.normalize("NFKD", value) if unicodedata.category(ch) != "Mn")
    base = base.replace("@", "a").replace("$", "s")
    forms = [base] if _LONE_FOUR.search(base) else []
    for one in ("i", "l"):
        def fold(match, one=one):
            run = match.group(0)
            if not any(ch.isalpha() for ch in run):
                return run
            out = []
            for index, ch in enumerate(run):
                letter = one if ch == "1" else _LOOKALIKE_DIGITS.get(ch)
                if letter is None:
                    out.append(ch)
                    continue
                near = [c for c in out if c.isalpha()][-1:] or [c for c in run[index + 1:] if c.isalpha()][:1]
                out.append(letter.upper() if near and near[0].isupper() else letter)
            return "".join(out)
        forms.append(re.sub(r"[^\W_]+", fold, base))
    return tuple(dict.fromkeys(forms))


def _case_parts(run):
    """Split one letter-and-digit run at case and digit boundaries: 'PublishThisRecord' gives
    Publish, This, Record; 'APIGateway' gives API, Gateway; 'Section4' gives Section, 4."""
    parts, start = [], 0
    for index in range(1, len(run)):
        prev, char = run[index - 1], run[index]
        following = run[index + 1] if index + 1 < len(run) else ""
        if (char.isdigit() != prev.isdigit() or (char.isupper() and prev.islower())
                or (char.isupper() and prev.isupper() and following.islower())):
            parts.append(run[start:index])
            start = index
    parts.append(run[start:])
    return parts


def _starts_clause(text):
    return text.startswith(_RUN_MATERIAL) or any(
        text == verb or (len(verb) >= LEAD_RUN_MIN_CHARS and text.startswith(verb)) for verb in _TRIGGER_VERBS)


def _object_run(rest, later):
    """True when rest (the letters after a split verb that ends inside a part), read on through the parts after
    it, is clause material in full: determiners then an object, or a pronoun object, optionally
    followed by 'now', ending at a part boundary."""
    later = list(later[:4])
    tail = rest + "".join(later)
    ends, position = {len(rest)}, len(rest)
    for part in later:
        position += len(part)
        ends.add(position)

    def finishes(index):
        return index in ends or (tail.startswith("now", index) and index + 3 in ends)

    if any(tail.startswith(word) and finishes(len(word)) for word in _SHORT_PRONOUNS):
        return True
    reached, frontier = set(), [0]
    while frontier:
        index = frontier.pop()
        for word in _SHORT_DETERMINERS:
            if tail.startswith(word, index) and index + len(word) not in reached:
                reached.add(index + len(word))
                frontier.append(index + len(word))
    return any(tail.startswith(word, index) and finishes(index + len(word))
               for index in reached for word in _SHORT_OBJECTS)


def _verb_hit(verb, rest, following, at_start, later=()):
    """One occurrence of a trigger verb in the collapsed form. rest: the letters after it in the same
    part; following: the next part; later: the parts after it, starting with following; at_start: it
    begins at a part boundary."""
    if verb in _TITLE_VERBS:
        if at_start and not rest:
            return True  # a whole part or whole parts: 'Publish', 'Pub|Lish', 'APPROVE'
        if at_start and len(verb) >= FUSED_MIN_CHARS and rest not in _DERIVED:
            return True  # run together with more text: 'publishthisrecord', 'PUBLISHKNOWLEDGEBASE'
        material = _RUN_MATERIAL + _PREPOSITIONS
        whole = _DETERMINERS | _OBJECTS | set(_PREPOSITIONS)
        if rest.startswith(material) or any(
                rest.startswith(end) and rest[len(end):].startswith(material) for end in _DERIVED):
            return True
        # Ending its part, it is a clause before a whole determiner, object or preposition, or before a
        # part that begins with determiners then a known object ('ItempublishTHISRECORDTOTHEBASE').
        return (not rest or rest in _DERIVED) and (following in whole or _object_start(later))
    if at_start and not rest:
        # 'ReleaseThisRecord', 'ReleaseTHISRECORDNOW', not 'Release readiness' or 'Review Allocations'.
        return following in _DETERMINERS or _object_start(later)
    if len(verb) < LEAD_RUN_MIN_CHARS:
        # Fused at a part boundary only before determiners then a known object, whatever follows, or a
        # pronoun ending at a part end ('usethisrecord', 'ADDTHISRECORDPLAN', 'useit'; not 'Gothenburg',
        # 'Setallocations' or 'Additions'); inside a longer part a short verb is a coincidence
        # ('warehouse', 'output').
        return at_start and _object_start([rest] + list(later))
    return rest.startswith(_RUN_MATERIAL) or (not rest and (following in _DETERMINERS or _object_start(later)))


def spells_clause(value, separators, tokens=True):
    """The canonical token check for every rendered title, ID, citation path segment, anchor and
    sheet or tab name, and for their record-level join (#8.6). True when the value spells a clause:
    - it carries a format (Cf) character, which is refused, never stripped;
    - in either comparison skeleton (comparison_skeletons): a separator token is a clause word (an
      upper-case acronym excepted) or ends in n't (when tokens is set); the parts, split at every
      other non-alphanumeric character and at case boundaries, spell a verdict phrase in order; the
      collapsed form (parts run together) contains a steering word or a verdict phrase of
      FUSED_MIN_CHARS letters or more; a negation is followed by a verb or clause material; or an
      imperative or verdict verb sits where it reads as a verb (_verb_hit)."""
    if has_cf(value) or _shorthand_hit(value):
        return True
    return any(_spells_clause(form, separators, tokens) for form in comparison_skeletons(value))


# Digit shorthand inside a verdict phrase (#8.6): a lone '2' read as 'to', a lone '4' as 'for'
# ('safe2reuse', 'good2go', 'cleared4release'). Only verdict phrases are read this way, so 'B2B',
# 'P2P', 'go2market', 'v2' and 'Q4-2026' stay identifiers.
_SHORTHAND = {"2": ("\x01", "to"), "4": ("\x02", "for")}
_SHORTHAND_RE = re.compile(r"(?<![0-9])[24](?![0-9])")
_SHORTHAND_PHRASES = tuple((words[:index], word, words[index + 1:])
                           for words in (phrase.split() for phrase in _TITLE_PHRASES)
                           for index, word in enumerate(words) if word in ("to", "for") and len(words) > 1)
# A '.' is a path boundary for the shorthand only before a file extension that ends a path segment
# (a known extension, or one with a digit: '.md', '.xlsx', '.mp4') or between digits ('v1.2.3', '2.4');
# anywhere else it joins like '-' or '_' ('DOC-7#safe.2.reuse', 'raw/fine.2.ship').
_KNOWN_EXTENSIONS = frozenset((
    "md markdown txt text rtf pdf xps oxps doc docx docm dot dotx odt xls xlsx xlsm xlsb xlt xltx csv tsv ods "
    "ppt pptx pptm pps ppsx pot potx odp vsd vsdx mpp one onepkg msg eml ics vcf json xml yaml yml toml ini cfg "
    "conf log html htm xhtml mht mhtml css png jpg jpeg gif bmp svg tif tiff webp heic mov avi wmv wav "
    "zip rar gz tgz tar bz2 xz py ts tsx js jsx sql sh ps1 bat cmd cs java ipynb r rmd tex bib epub pbix pbit "
    "pbip twb twbx sav sas dwg dxf bak tmp url lnk key pages numbers mp3 mp4 m4a 7z"
).split())
_PATH_END = re.compile(r"[/\\#;,\s]|$")
# One extension rule (_extension_kind) decides every extension site: the '.' boundary of _path_dots,
# the file-name stem of the title-file join (_strip_final_extension) and the tokens dropped for phrase
# reading (_drop_extensions). A known extension counts whatever its length ('.markdown', '.numbers',
# '.onepkg'); an unknown one only with a digit and at most five characters ('.v2'); any other suffix
# is a word ('raw/to.go'). Only known extensions are dropped for phrase reading, since a digit-bearing
# token may itself be shorthand ('raw/good.2go.md').
_EXTENSION_TOKEN = re.compile(r"\.([A-Za-z0-9]+)(?![A-Za-z0-9])")


def _extension_kind(token):
    """'known', 'digit' or None for token, the letters and digits after a '.'."""
    if token.casefold() in _KNOWN_EXTENSIONS:
        return "known"
    if len(token) <= 5 and any(c.isdigit() for c in token):
        return "digit"
    return None


def _is_extension(token):
    """True when token (the letters and digits after a '.') is a file extension (_extension_kind)."""
    return _extension_kind(token) is not None


def _strip_final_extension(name):
    """name without a final '.ext' that is a file extension (_is_extension): 'shThisRecord.markdown'
    gives 'shThisRecord', 'to.go' stays 'to.go'."""
    match = re.search(r"\.([A-Za-z0-9]+)$", name)
    return name[:match.start()] if match and _is_extension(match.group(1)) else name


def _letter_parts(segment):
    """The casefolded parts of a stretch of a comparison skeleton, split at separators and case and
    digit boundaries."""
    return [part.casefold() for run in re.findall(r"[^\W_]+", segment) for part in _case_parts(run)]


def _covers(parts, words, from_end):
    """True when words, run together, are exactly the first (or last) whole parts, with no part
    boundary inside a word ('SAFe' is not 'safe')."""
    target = "".join(words)
    taken, length = [], 0
    for part in (reversed(parts) if from_end else parts):
        if length >= len(target):
            break
        taken.append(part)
        length += len(part)
    if from_end:
        taken.reverse()
    if "".join(taken) != target:
        return False
    cuts, position = set(), 0
    for part in taken[:-1]:
        position += len(part)
        cuts.add(position)
    bounds, position = set(), 0
    for word in words[:-1]:
        position += len(word)
        bounds.add(position)
    return cuts <= bounds


def _path_dots(value):
    """The value with every '.' that is not a real path boundary (a final file extension, _is_extension,
    or a '.' between digits) read as '-'."""
    out = []
    for index, char in enumerate(value):
        if char == ".":
            before, after = value[index - 1:index], value[index + 1:index + 2]
            extension = re.match(r"[A-Za-z0-9]+", value[index + 1:])
            final = extension and _PATH_END.match(value, index + 1 + extension.end())
            real = (before.isdigit() and after.isdigit()) or (final and _is_extension(extension.group(0)))
            if not real:
                char = "-"
        out.append(char)
    return "".join(out)


def _drop_extensions(value):
    """The value with every known file-extension token removed, wherever it stands ('raw/safe.md#reuse'
    reads 'raw/safe#reuse'; 'raw/safe.md.2.reuse' reads 'raw/safe.2.reuse'), so the phrase is read
    across it."""
    return _EXTENSION_TOKEN.sub(lambda match: "" if _extension_kind(match.group(1)) == "known" else match.group(0),
                                value)


def _shorthand_hit(value):
    """True when a lone '2' or '4' stands for the 'to' or 'for' of a verdict phrase: the phrase words
    before it are whole parts ending at the digit, and the words after it are whole parts starting
    there. Known extension tokens (_drop_extensions) and the path and anchor separators '/', '\\' and
    '#' are transparent ('raw/safe2.md#reuse', 'raw/fine.2.pptx#ship'); only a dotted version or a
    final extension that is not known but carries a digit bounds the reading (_path_dots: 'raw/Safe2.md',
    'DOC-7#section.2.1'). A phrase ending in 'to' ('safe to') needs a word after the digit."""
    if not _SHORTHAND_RE.search(value):
        return False
    plain = re.sub(r"[/\\#]", "-", _drop_extensions(value))
    marked = _SHORTHAND_RE.sub(lambda match: _SHORTHAND[match.group(0)][0], _path_dots(plain))
    markers = {mark: word for mark, word in _SHORTHAND.values()}
    for form in comparison_skeletons(marked):
        pieces = re.split("([\x01\x02])", form)
        for index in range(1, len(pieces), 2):
            # A dotted version or a remaining real extension bounds the reading ('section.2.1').
            left = _letter_parts(pieces[index - 1].split(".")[-1])
            right = _letter_parts(pieces[index + 1].split(".")[0])
            for before, word, after in _SHORTHAND_PHRASES:
                if word != markers[pieces[index]] or not right or not right[0][:1].isalpha():
                    continue
                if before and not _covers(left, before, True):
                    continue
                if after and not _covers(right, after, False):
                    continue
                return True
    return False


# Ordinary words that may run on from a word of a verdict phrase inside one capitalised part (#8.6):
# 'Safe|Toolkit', 'No|Needles', 'They|Areas'. A case-evidenced phrase that ends inside a capitalised
# part beginning inside it is held unless that whole part is one of these words or a simple inflection
# of one (_ordinary_word); anything else that runs on is held ('SafeToreuse', 'SafeToarchive',
# 'TheyAreclear'). The list holds the words of the ordinary-word and realistic-name sets that begin
# with a phrase word after its first (to, go, for, external, use, need, one, are, it, is) and are in
# Webster's Second International (public domain), with a few modern compounds (toolkit, tooltip,
# username, onedrive); a word that is clause material or runs on into it (todo, forall, forgive,
# golive, isset) is left out.
_ORDINARY_RUN_ONS = frozenset("""
    area arena externally externals forbid forbidden force forcefully forcibly forcing ford fore forecast
    forego foreground foreign forest forever forge forger forgery forget forgetting forgot forgotten fork
    form formal formalization formally format formerly formula formulae formulate forth fortnightly
    fortuitous fortunately fortune forty forum forwarding forwardly forwards goal god goes going golden gone
    gong goods goodwill gopher gory got gotham gothic gotten govern governance government island iso isolate
    isolation isomorphic issuance issue issuer issuing italian italic item iterable iterate iteration
    iterative iteratively itself needing needle needlessly needlework needs onedrive oneself onetime today
    toe together toggle token tokenization tokenize tokenizer tolerable tolerance tolerant tolerantly
    tolerate tom tomato tomorrow ton tone tong tongue too tool toolbar toolbox toolchain toolkit toolset
    tooltip tooth top topic topmost topological topology topped topping tore torn toronto tort tortious
    tortoise tortuous torture toss tot total totality totally touch touchline touchy tour tournament tout
    toward tower used useful usefulness useless uselessly user userbase userguide username
""".split())
_INFLECTIONS = (("s", ""), ("es", ""), ("ies", "y"), ("d", ""), ("ed", ""), ("ing", ""), ("ing", "e"), ("er", ""),
                ("ers", ""))


# Clause material after a verdict phrase (#8.6): an allowlisted run-on is no exemption when the
# letters after the phrase word begin one of these ('They|Are|as|Clear' in 'TheyAreasClear'), or when
# the next whole part is one ('NoNeedsToReview', 'SafeToolsThisRecord').
_REST_MATERIAL = tuple(sorted(
    set(_PREPOSITIONS) | set(_RUN_MATERIAL) | set(_SHORT_DETERMINERS) | set(_SHORT_PRONOUNS) | set(_SHORT_OBJECTS)
    | {"is", "are", "be", "do", "no", "not", "so"}
    | {word for word in _TITLE_CLAUSE_WORDS | _TITLE_VERBS | set(_FUSED_WORDS) if len(word) >= 4}
    | {word for phrase in _TITLE_PHRASES for word in phrase.split() if len(word) >= 4}
    | {"clear", "ready", "reuse", "ship", "proceed", "release", "publish"}))
_NEXT_MATERIAL = frozenset(
    set(_PREPOSITIONS) | _DETERMINERS | set(_SHORT_DETERMINERS) | set(_SHORT_PRONOUNS) | _OBJECTS
    | set(_SHORT_OBJECTS) | _TITLE_CLAUSE_WORDS | _TITLE_VERBS | set(_FUSED_WORDS)
    | {word for phrase in _TITLE_PHRASES for word in phrase.split()}
    | {"safe", "fine", "okay", "ok", "good", "clear", "cleared", "ready", "approved", "reuse", "ship", "proceed"})


# Words a lower-case run-together part is read through after an allowlisted run-on ('Thisrecord',
# 'thisrecordnow'): clause material without the one- and two-letter pronouns that begin ordinary words
# ('Theme', 'Usher').
_RUN_AFTER_WORDS = frozenset(
    (_NEXT_MATERIAL | set(_SHORT_OBJECTS) | {verb for verb in _TRIGGER_VERBS if len(verb) >= LEAD_RUN_MIN_CHARS})
    - {"i", "me", "us", "we", "he", "my", "a"})


def _run_reads_clause(part):
    """True when part, a run of lower-case letters, reads end to end as words of _RUN_AFTER_WORDS that
    reach a determiner or 'now' (_RUN_MATERIAL) within its first three words, with a word after it or a
    verb before it ('thisrecord', 'thisreview', 'forthisrecord', 'reusethis'; 'foreach' is none), so an
    ordinary word that only splits into short words ('areas', 'assay', 'allowlist') is no clause."""
    size = len(part)
    tail = [False] * (size + 1)
    tail[size] = True
    for index in range(size - 1, -1, -1):
        tail[index] = any(tail[index + len(word)] for word in _RUN_AFTER_WORDS if part.startswith(word, index))

    def lead(index, budget, verbal):
        for word in _RUN_AFTER_WORDS:
            if not part.startswith(word, index):
                continue
            end = index + len(word)
            if word in _RUN_MATERIAL and tail[end] and (end < size or verbal):
                return True
            if budget and lead(end, budget - 1, verbal or word in _TRIGGER_VERBS or word in _SHORTHAND_VERBS):
                return True
        return False

    return lead(0, 2, False)


# Verbs a lone 2 or 4 ('to', 'for') turns into a clause after an allowlisted run-on, with the trigger verbs.
_SHORTHAND_VERBS = frozenset("go golive reuse ship proceed use deploy launch merge export".split())


# Clause material read later in the same token after an allowlisted run-on, once a verb has been read
# there ('SafeTools2ReleaseRoadmapNow', 'SafeToolsReviewRoadmapNow'): determiners, pronoun objects and
# 'now', without the short pronouns that end ordinary names ('MoveIT').
_LATER_MATERIAL = frozenset(_DETERMINERS - {"it", "its", "us", "me", "my", "his", "her", "you", "your"})
# Verbs that a later lone 2 or 4 does not turn into a clause on its own: they end product names
# ('Teams2Go', 'Ready2Use').
_LATER_SHORTHAND_NAMES = frozenset(("go", "use"))
_RUN_VERBS = tuple(sorted({verb for verb in _TRIGGER_VERBS if len(verb) >= LEAD_RUN_MIN_CHARS} | _SHORTHAND_VERBS))
# Verbs a later lone 2 or 4 turns into a clause: every trigger, lead and shorthand verb but go and use.
_LATER_SHORTHAND_VERBS = frozenset(set(_TRIGGER_VERBS) | _SHORTHAND_VERBS) - _LATER_SHORTHAND_NAMES
# Words a number follows as an ordinal, not as 'to' or 'for' ('Phase2Review', 'Sprint4Release').
_SEQUENCE_NOUNS = frozenset((
    "phase phases wave waves sprint sprints stage stages step steps round rounds part parts tier tiers level "
    "levels version versions release releases chapter chapters module modules week weeks day days month months "
    "year years quarter batch batches cohort cohorts iteration iterations milestone milestones gen generation "
    "track tracks pillar pillars section sections lot lots increment pi q v r h fy wk"
).split())
# Product and ordinary compounds whose last part is a clause word ('ServiceNow', 'CatchAll'): that part
# is no later clause material.
_MATERIAL_COMPOUNDS = (
    ("service", "now"), ("pay", "now"), ("buy", "now"), ("book", "now"), ("shop", "now"), ("news", "now"),
    ("catch", "all"), ("carry", "all"), ("hold", "all"), ("cure", "all"), ("over", "all"), ("know", "all"),
    ("free", "for", "all"), ("end", "all"), ("be", "all"))


def _after_is_clause(parts, reach=None):
    """True when the parts after an allowlisted run-on hold clause material (#8.6). Digit runs are
    separators ('SafeTools2026Roadmap'). The first word part, and the word after a verb that is also a
    noun read after a lone 2 or 4 ('SafeTools2Release this record'), are clause material when they are a
    clause word, determiner, pronoun, object, preposition, strong verb or verdict word (_NEXT_MATERIAL:
    'SafeTools_ThisRecord'), or a lower-case run of such words ('SafeToolsThisrecord'). The scan then
    reads every later part of the same token (the first reach parts), not only the first: a lone 2 or 4
    read as 'to' or 'for' before a verb is a clause ('SafeTools2Reuse', 'SafeToolsPlan2Reuse'; after
    the first word not before go or use, 'SafeToolsTeams2Go'), and once a verb has been read
    (_TRIGGER_VERBS, a shorthand verb) a later determiner, pronoun object or 'now' (_LATER_MATERIAL), or
    a lower-case run of clause words, completes the clause ('SafeTools2ReleaseRoadmapNow',
    'SafeToolsReviewRoadmapNow'). After the first word a lone 2 or 4 before any trigger, lead or
    shorthand verb but go and use is a clause ('SafeToolsPlan2Release', 'NoNeedleRoadmap4Share'), unless
    it follows a sequence noun as an ordinal ('SafeToolsPhase2Review'). A determiner or 'now' that ends a
    known compound is no material ('SafeToolsReviewServiceNowMigration'). 'SafeTools2Release',
    'SafeTools2026Roadmap' and 'SafeToolsServiceNowMigration' render."""
    reach = len(parts) if reach is None else reach
    tokens = []
    for index, part in enumerate(parts):
        # A look-alike digit folded inside a number ('2026' read '2o26') stays part of the number.
        folded = (len(part) == 1 and 0 < index < len(parts) - 1 and parts[index - 1].isdigit()
                  and parts[index + 1].isdigit())
        if (part.isdigit() or folded) and tokens and tokens[-1][0] == "number":
            tokens[-1] = ("number", tokens[-1][1] + part, tokens[-1][2])
        else:
            tokens.append(("number" if part.isdigit() else "word", part, index))
    shorthand, pending, first, verb, words = False, True, True, False, []
    for kind, part, origin in tokens:
        if kind == "number":
            # A number after a sequence noun is an ordinal ('Phase2Review'), not 'to' or 'for'.
            shorthand = part in ("2", "4") and not (words and words[-1] in _SEQUENCE_NOUNS)
            words = []
            continue
        if not pending and origin >= reach:
            break
        if shorthand and (part in _TITLE_VERBS or part in _SHORTHAND_VERBS) and first:
            return True
        # Later in the token any verb counts ('SafeToolsPlan2Release'); first, a lead verb is a noun
        # until clause material follows ('SafeTools2ReleaseNotes').
        if shorthand and not first and part in _LATER_SHORTHAND_VERBS:
            return True
        words.append(part)
        # A verb that is also a noun after a version number ('SafeTools2Release', 'SafeTools2FilePlan')
        # needs clause material after it.
        noun_verb = shorthand and part in _TITLE_LEAD_VERBS
        if pending and not noun_verb and (part in _NEXT_MATERIAL or _run_reads_clause(part)):
            return True
        if origin < reach and _run_reads_clause(part) and (verb or part.startswith(_RUN_VERBS)):
            return True
        if origin < reach and verb and part in _LATER_MATERIAL and not any(
                tuple(words[-len(compound):]) == compound for compound in _MATERIAL_COMPOUNDS):
            return True
        pending = noun_verb
        verb = verb or part in _TRIGGER_VERBS or part in _SHORTHAND_VERBS
        shorthand, first = False, False
    return False


def _rest_is_clause(rest):
    """True when the letters after a verdict phrase's last word, inside the run-on word, begin clause
    material ('as' in 'Areas', 'all' in a 'Goallrecords'-style run)."""
    return bool(rest) and (rest.startswith(_REST_MATERIAL) or _starts_clause(rest))


def _ordinary_word(word):
    """True when word is in _ORDINARY_RUN_ONS or is a plural, -ed, -ing or -er form of one."""
    return word in _ORDINARY_RUN_ONS or any(
        word.endswith(suffix) and word[:-len(suffix)] + stem in _ORDINARY_RUN_ONS for suffix, stem in _INFLECTIONS)


def _needle_hit(collapsed, starts, boundary=None, case_starts=(), continuing=(), breaks=()):
    """A steering word or verdict phrase in the collapsed form. Inside one part (a run-together word,
    'pleaseapprove') it counts anywhere. Across parts it counts when it starts at a part start and ends
    at a part end ('Plea-se', not 'Roadmap lease'). Inside one value a verdict phrase also counts when a
    case transition inside a letter run (case_starts) falls on one of its own word boundaries, wherever
    its ends fall ('xsafeToReuse', 'ItemnoONENEEDS'): the transition is the evidence of a phrase. A space
    is no such evidence ('Safe Tomorrow plan'). A phrase that ends inside a capitalised word that
    begins inside the phrase and runs on in lower case (continuing) is held unless that whole word is
    an ordinary word (_ordinary_word: 'Safe|Toolkit', 'No|Needle', 'Safe|Tomorrow') whose letters after
    the phrase word begin no clause material (_rest_is_clause: 'They|Are|as' in 'TheyAreasClear') and
    whose following parts, to the end of its token (up to a break: whitespace or a path break), hold
    no clause material (_after_is_clause: 'NoNeedsToReview', 'SafeToolsThisrecord', 'SafeTools2Reuse',
    'SafeToolsReviewRoadmapNow'); anything else is held
    ('SafeToreuse', 'SafeToarchive', 'TheyAreclear'; 'Xgood|to|Go' counts as before). A word
    inside the phrase always runs on into the phrase's next word, so only the phrase's end is read
    this way.
    With a boundary (a join of two values), only an
    occurrence that straddles it counts, and only by its ends."""
    ends = (set(starts) - {0}) | {len(collapsed)}

    def runs_on(start, end):
        """True when the phrase ends inside a capitalised word that began inside it and that whole
        word is an ordinary word."""
        if end not in continuing:
            return False
        first = max(begin for begin in starts if begin < end)
        if first <= start:
            return False
        stop = min([begin for begin in starts if begin > end] + [len(collapsed)])
        if not _ordinary_word(collapsed[first:stop]) or _rest_is_clause(collapsed[end:stop]):
            return False
        bounds = sorted(begin for begin in starts if begin >= stop) + [len(collapsed)]
        pieces = [(a, collapsed[a:b]) for a, b in zip(bounds, bounds[1:]) if b > a]
        # The rest of the run-on's token: up to the next whitespace or path break (breaks).
        limit = min([begin for begin in breaks if begin >= stop] + [len(collapsed)])
        return not _after_is_clause([piece for _, piece in pieces], sum(1 for a, _ in pieces if a < limit))
    for needle in _FUSED_NEEDLES:
        start = collapsed.find(needle)
        while start >= 0:
            end = start + len(needle)
            first = max(begin for begin in starts if begin <= start)
            inside = not any(first < begin < end for begin in starts)
            straddles = boundary is None or start < boundary < end
            splits = _PHRASE_BOUNDARIES.get(needle, ())
            # The phrase may not end inside a capitalised word that begins inside it ('Safe|To|olkit').
            evidenced = (boundary is None and any(start + offset in case_starts for offset in splits)
                         and not runs_on(start, end))
            if straddles and ((inside and boundary is None) or evidenced or (start in starts and end in ends)):
                return True
            start = collapsed.find(needle, start + 1)
    return False


# The noun 'to-do' ('to-do', 'to_do', 'todo', 'ToDo', 'to-dos', 'TODOs') is one token: across the
# components of a citation part ('docs/status-okay.md#to-dos') and in the separator-token test, where
# its 'do' is no auxiliary ('DOC-7#to-do', 'raw/notes.md#to-do-list'). A verdict phrase written inside
# one component is still read word by word ('DOC-7#okay-to-do', 'DOC-7#OkayToDo'). 'to-be' is not a
# noun here: 'safe to be shared' is a clause. Only '-', '_' or nothing join the two words; a '.' keeps
# its token boundary ('raw/okay.md#to.do' is read word by word).
_TODO_NOUN = re.compile(r"(?<![A-Za-z0-9])(?:to|To|TO)[-_]?(?:do|Do|DO)(?:s|es|S|ES)?(?![a-z0-9])")


def _spells_clause(text, separators, tokens):
    if tokens:
        for token in re.split(separators, _TODO_NOUN.sub("todo", text)):
            bare = token.strip("(),'\u2019")
            low = bare.casefold().replace("\u2019", "'")
            acronym = len(bare) >= 2 and bare.isupper()
            if low.endswith("n't") or (not acronym and low in _TITLE_CLAUSE_WORDS):
                return True
    parts, case_starts, continuing, breaks, position, previous = [], set(), set(), set(), 0, 0
    for match in re.finditer(r"[^\W_]+", text):
        run = match.group(0)
        # Whitespace, a slash, backslash, '#', ',' or ';' ends a token for the run-on remainder scan.
        if position and re.search(r"[\s/\\#,;]", text[previous:match.start()]):
            breaks.add(position)
        previous = match.end()
        for index, part in enumerate(_case_parts(run)):
            if index:
                case_starts.add(position)
            if any(char.isupper() for char in part):
                # Lower-case letters that continue a capitalised word: no token ends before them.
                continuing.update(position + offset for offset, char in enumerate(part) if offset and char.islower())
            parts.append(part.casefold())
            position += len(part)
    joined = f" {' '.join(parts)} "
    if any(f" {phrase} " in joined for phrase in _TITLE_PHRASES):
        return True
    collapsed, starts = "".join(parts), {}
    position = 0
    for index, part in enumerate(parts):
        starts[position] = index
        position += len(part)
    if _needle_hit(collapsed, starts, case_starts=case_starts, continuing=continuing, breaks=breaks):
        return True

    def after(end):
        """(letters after end in the same part, the next whole part, the parts from there on)."""
        if end in starts:
            return "", parts[starts[end]], parts[starts[end]:]
        if end >= len(collapsed):
            return "", "", []
        first = max(start for start in starts if start < end)
        index = starts[first]
        return parts[index][end - first:], parts[index + 1] if index + 1 < len(parts) else "", parts[index + 1:]

    for negation in _NEGATIONS:
        start = collapsed.find(negation)
        while start >= 0:
            rest, following, _ = after(start + len(negation))
            if _starts_clause(rest) if rest else (following in _DETERMINERS | _OBJECTS or _starts_clause(following)):
                return True
            start = collapsed.find(negation, start + 1)
    for verb in _TRIGGER_VERBS:
        start = collapsed.find(verb)
        while start >= 0:
            rest, following, later = after(start + len(verb))
            if _verb_hit(verb, rest, following, start in starts, later):
                return True
            start = collapsed.find(verb, start + 1)
    return False


def title_shape_ok(value, spelled=True):
    """A short noun phrase: letters, digits and light punctuation only, no format character and
    nothing the canonical token check reads as a clause (#8.6). The value is checked as supplied
    (NFKC only), never as a stripped copy. spelled=False checks the shape without the spelling."""
    if has_cf(value):
        return False
    text = unicodedata.normalize("NFKC", value).strip()
    if not text or len(text) > TITLE_MAX_CHARS or not any(c.isalpha() for c in text):
        return False
    for index, char in enumerate(text):
        if char.isalnum() or char in _TITLE_PUNCT:
            continue
        if char == "." and 0 < index < len(text) - 1 and text[index - 1].isdigit() and text[index + 1].isdigit():
            continue
        return False
    tokens = text.split()
    if len(tokens) > TITLE_MAX_WORDS or (spelled and spells_clause(text, r"\s+")):
        return False
    if not spelled:
        return True
    lowered = [token.strip("(),'\u2019").casefold() for token in tokens]
    return not (lowered[0] in _TITLE_LEAD_VERBS and len(lowered) > 1 and lowered[1] in _TITLE_LEAD_FOLLOWERS)


def citation_shape_ok(value, spelled=True):
    """A source path or document ID (no spaces; it carries a '.', '/', '\\' or a digit) with an optional
    #anchor and row, line, clause, section, page or named-sheet locators, ';'-separated. No path,
    anchor or sheet name may spell a clause under the canonical token check, as an identifier may
    not. Joins read only boundaries that are contiguous in rendering order, with the token-anchored
    boundary recogniser (#8.6): each source, anchor and sheet name with the next in order
    ('DOC-Publi#shThisRecord', anchor to the next source), and for adjacent ';' parts the source with
    the next source and the last anchor or sheet name with the next part's first
    ('DOC-1#Publi; DOC-2#shThisRecord')."""
    text = value.strip()
    if has_cf(value) or not text or len(text) > CITATION_MAX_CHARS or not CITATION_RE.fullmatch(text):
        return False
    parts = []
    for part in text.split(";"):
        source = _CITE_SOURCE.match(part.strip())
        if not source or not any(c in "./\\" or c.isdigit() for c in source.group(0)):
            return False
        if spelled and spells_clause(source.group(0), r"[-_./\\]+"):
            return False
        names = [anchor or sheet for anchor, sheet in _CITE_WORDS.findall(part)]
        if spelled and part_phrase_spells(source.group(0), names):
            return False
        parts.append((source.group(0), names))
    if not spelled:
        return True
    if not all(id_shape_ok(name) for _, names in parts for name in names):
        return False
    if sequence_spells_clause([word for source, names in parts for word in [source] + names]):
        return False
    for (source, names), (next_source, next_names) in zip(parts, parts[1:]):
        if boundary_spells_clause(source, " ".join([next_source] + next_names[:3])):
            return False
        if names and next_names and boundary_spells_clause(names[-1], " ".join(next_names[:4])):
            return False
    return True


def part_phrase_spells(source, names):
    """One citation part read as a single run of words for verdict phrases and digit shorthand (#8.6):
    its source with known extension tokens dropped (_drop_extensions), then its anchors and sheet names,
    with '/', '\\', '#' and the sheet keyword transparent ('raw/safe.md#to-reuse', 'raw/good-to.md#go',
    'raw/safe.md sheet ToReuse', 'raw/safe2.md#reuse'). Only verdict phrases, run-together verdict
    phrases and steering words that start and end at part boundaries, and digit shorthand are read
    here; verbs are read per identifier and across boundaries by the recogniser of (8)."""
    view = _TODO_NOUN.sub("todo", "-".join([re.sub(r"[/\\#]", "-", _drop_extensions(source))] + list(names)))
    if _shorthand_hit(view):
        return True
    for form in comparison_skeletons(view):
        parts = _letter_parts(form)
        joined = f" {' '.join(parts)} "
        if any(f" {phrase} " in joined for phrase in _TITLE_PHRASES):
            return True
        starts, position = {}, 0
        for index, part in enumerate(parts):
            starts[position] = index
            position += len(part)
        if parts and _needle_hit("".join(parts), starts):
            return True
    return False


def id_shape_ok(value):
    """An identifier renders as itself, so it may not spell a clause: the canonical token check with
    '-', '_' and '.' as separators (#8.6). Upper-case acronym segments pass the clause-word test."""
    return not spells_clause(value, r"[-_.]+")


def _object_start(parts):
    """True when parts (what follows a whole verb at a boundary, or a short lead verb at a part start)
    begin with clause material: one or more determiners then a known object, or a pronoun object.
    Anything may follow the object ('thisrecordpublic', 'ADDTHISRECORDPLAN'). A pronoun shorter than
    FUSED_MIN_CHARS must end at a part end ('it', not 'items' or 'Addition'; 'Them', not 'Themes');
    'everything' may run on ('ADDEVERYTHINGPLAN')."""
    tail = "".join(parts)
    ends, position = set(), 0
    for part in parts:
        position += len(part)
        ends.add(position)
    if any(tail.startswith(word) and (len(word) >= FUSED_MIN_CHARS or len(word) in ends
                                      or (tail.startswith("now", len(word)) and len(word) + 3 in ends))
           for word in _SHORT_PRONOUNS):
        return True
    reached, frontier = set(), [0]
    while frontier:
        index = frontier.pop()
        for word in _SHORT_DETERMINERS:
            if tail.startswith(word, index) and index + len(word) not in reached:
                reached.add(index + len(word))
                frontier.append(index + len(word))
    return any(tail.startswith(word, index) for index in reached for word in _SHORT_OBJECTS)


def _boundary_clause(left, right):
    """The token-anchored recogniser for one touching boundary (left's tail meets right's head), on
    comparison skeletons. Each value already passed the canonical check alone, so only what crosses
    the boundary is read:
    - a verdict phrase whose whole tokens fall on both sides ('Safe' + 'to-deploy');
    - a steering word, verdict phrase or trigger verb split across the boundary, counted only when its
      left piece starts at a token start and its right piece ends at a token end ('Publi' +
      'shInstructions', 'Sk' + 'ipValidation'; not 'Roadmap' + 'lease-accounting', where 'p' starts no
      token, nor 'Sk' + 'ipad-guide'), or, in a run-together right token, when the rest of that token
      is clause material in full ('Publi' + 'shthisrecord'). A split verb is itself the signal: it
      holds when any token follows it, or when it is an imperative or verdict verb;
    - a whole verb that ends left, followed by determiners and a known object, or a pronoun object,
      with anything after ('Set' + 'thisrecordpublic'); a lead verb that is also a noun ('review',
      'record', 'set') counts only when it also starts left, since the last word of a longer noun
      phrase is its head noun ('Go-live readiness review' + 'all-records' renders);
    - a negation that ends left before a verb or clause material."""
    def split(text):
        return [part.casefold() for run in re.findall(r"[^\W_]+", text) for part in _case_parts(run)]

    head, tail = split(left), split(right)
    if not head or not tail:
        return False
    parts = head + tail
    collapsed, boundary = "".join(parts), len("".join(head))
    starts, position = {}, 0
    for index, part in enumerate(parts):
        starts[position] = index
        position += len(part)
    ends = (set(starts) - {0}) | {len(collapsed)}
    for phrase in _TITLE_PHRASES:
        words = phrase.split()
        for index in range(len(parts) - len(words) + 1):
            if parts[index:index + len(words)] == words and index < len(head) < index + len(words):
                return True
    if _needle_hit(collapsed, starts, boundary):
        return True

    def rest_of(end):
        """(letters after end in its part, the parts after that part)."""
        if end in starts:
            return "", parts[starts[end]:]
        first = max(begin for begin in starts if begin < end)
        return parts[starts[first]][end - first:], parts[starts[first] + 1:]

    for verb in _TRIGGER_VERBS:
        start = collapsed.find(verb)
        while start >= 0:
            end = start + len(verb)
            if start in starts and start < boundary < end:
                if end in ends:
                    if end < len(collapsed) or verb in _TITLE_VERBS:
                        return True
                else:
                    rest, later = rest_of(end)
                    if _object_run(rest, later):
                        return True
            elif start in starts and end == boundary and (start == 0 or verb in _TITLE_VERBS):
                if _object_start(tail):
                    return True
            start = collapsed.find(verb, start + 1)
    for negation in _NEGATIONS:
        start = collapsed.find(negation)
        while start >= 0:
            if start in starts and start + len(negation) == boundary and (
                    tail[0] in _DETERMINERS | _OBJECTS or _starts_clause(tail[0])):
                return True
            start = collapsed.find(negation, start + 1)
    return False


def boundary_spells_clause(left, right):
    """True when left followed directly by right spells a clause across their touching ends (#8.6).
    right may carry the rendered words that follow it, space-separated."""
    if has_cf(left) or has_cf(right):
        return True
    return any(_boundary_clause(one, two)
               for one in comparison_skeletons(left) for two in comparison_skeletons(right))


def sequence_spells_clause(words):
    """The boundaries of a rendered sequence of identifier words (#8.6): each word meets the next,
    with up to three further words as the clause material that may follow."""
    return any(boundary_spells_clause(words[index], " ".join(words[index + 1:index + 5]))
               for index in range(len(words) - 1))


def joined_spells_clause(title, citation):
    """A record's title and citation render together, so a clause split between them is refused (#8.6).
    The token-anchored boundary recogniser reads the title before the citation's first word and after
    its last, and, because a directory prefix such as raw/ is conventional, next to each source file
    name and each anchor and sheet name of every ';' part, in either order. So 'Publi' with
    'DOC-1#shThisRecord' or 'raw/shThisRecordNow.md' is refused, and 'Go-live readiness review' with
    '...#all-sites' or 'Roadmap' with 'DOC-1#lease-accounting' is not."""
    pieces = [word for source, names in _citation_parts(citation) for word in [source] + names]
    if not pieces:
        return False
    joins = [(title, " ".join(pieces[:4])), (pieces[-1], title)]
    for source, names in _citation_parts(citation):
        stem = _strip_final_extension(re.split(r"[/\\]", source)[-1])
        if stem:
            joins += [(title, " ".join([stem] + names[:3])), (stem, title)]
        joins += [(title, " ".join(names[index:index + 4])) for index in range(len(names))]
        joins += [(name, title) for name in names]
    return any(boundary_spells_clause(left, right) for left, right in joins)


def _citation_parts(citation):
    """(source, [anchors and sheet names]) for each ';' part, in rendering order."""
    found = []
    for part in citation.split(";"):
        source = _CITE_SOURCE.match(part.strip())
        if source:
            found.append((source.group(0), [anchor or sheet for anchor, sheet in _CITE_WORDS.findall(part)]))
    return found


def neighbour_spells_clause(first, first_is_title, second, second_is_title):
    """Neighbour records of one list render one after the other, so a clause split between a value of
    one and a value of the next is refused (#8.6), read as adjacent ';' parts are: two titles meet at
    their ends; a title and a citation join as a record's title and citation do; two citations join
    the first's last part with the second's first part ('DOC-1#Publi' then 'DOC-2#shThisRecord')."""
    if first_is_title and second_is_title:
        return boundary_spells_clause(first, second)
    if first_is_title or second_is_title:
        return joined_spells_clause(*((first, second) if first_is_title else (second, first)))
    ahead, behind = _citation_parts(first), _citation_parts(second)
    if not ahead or not behind:
        return False
    (source, names), (next_source, next_names) = ahead[-1], behind[0]
    words = [word for part, more in behind for word in [part] + more]
    return (boundary_spells_clause(([source] + names)[-1], " ".join(words[:4]))
            or boundary_spells_clause(source, " ".join([next_source] + next_names[:3]))
            or bool(names and next_names and boundary_spells_clause(names[-1], " ".join(next_names[:4]))))


def shape_hits(path, value):
    """The render-policy screen for one supplied value: ("render_shape",) or ()."""
    if _TITLE_PATH.fullmatch(path):
        return () if title_shape_ok(value) else ("render_shape",)
    if _CITATION_PATH.fullmatch(path):
        return () if citation_shape_ok(value) else ("render_shape",)
    return ()


def marker_shaped(text):
    return bool(_MARKER_RE.search(canon(text)))


# Marker syntax (#8.4): a bracketed span that names a hold, flag or redaction ('[withheld: ...]',
# '[FLAGGED]', '(redacted)'), or an unclosed bracket that opens with one. The text around it is kept.
_OPENERS = "[\uff3b\u27e6\u3010\u3014\u3016\u3018\u301a(\uff08{\uff5b<\uff1c\u27e8\u3008\u300a"
_CLOSERS = "]\uff3d\u27e7\u3011\u3015\u3017\u3019\u301b)\uff09}\uff5d>\uff1e\u27e9\u3009\u300b"
_MARKER_BRACKET = re.compile(f"[{re.escape(_OPENERS + _CLOSERS)}]")
_MARKER_CLOSED = re.compile(f"[{re.escape(_OPENERS)}]([^{re.escape(_OPENERS + _CLOSERS)}]{{0,200}})[{re.escape(_CLOSERS)}]")
_MARKER_OPEN_HEAD = re.compile(f"[{re.escape(_OPENERS)}]\\s*([^\\s{re.escape(_OPENERS + _CLOSERS)}]{{1,40}})")
_MARKER_CLOSE_TAIL = re.compile(f"([^\\s{re.escape(_OPENERS + _CLOSERS)}]{{1,40}})\\s*[{re.escape(_CLOSERS)}]")
_MARKER_WORDS = re.compile(r"\b(?:withh[eo]ld\w*|flag(?:ged|s)?|redact\w*|removed|held|holds?|omitted|placeholder"
                           r"|mask(?:ed)?|saniti[sz]ed|scrubbed|hidden|deleted|censored|blocked|screen(?:ed|ing)\w*)\b")


@functools.lru_cache(maxsize=None)
def unmarked(text):
    """text with marker syntax removed and the words around it kept, so a marker placed inside an
    instruction ('Whoever [withheld: ...] reviews this next') cannot break it (#8.1, #8.4). The text
    itself when it carries none. Read alongside the text as supplied, never in place of it."""
    if not isinstance(text, str) or not _MARKER_BRACKET.search(text):
        return text

    def drop(match):
        return " " if _MARKER_WORDS.search(canon(match.group(1))) else match.group(0)

    plain = strip_cf(text)
    stripped = _MARKER_CLOSE_TAIL.sub(drop, _MARKER_OPEN_HEAD.sub(drop, _MARKER_CLOSED.sub(drop, plain)))
    return text if stripped == plain else " ".join(stripped.split())


def _families(hits):
    found = []
    for hit in hits:
        if hit.family not in found:
            found.append(hit.family)
    return found


@functools.lru_cache(maxsize=None)
def scan_families(text):
    """The single detector call site: the hit families of sg.scan on one text. Each distinct text is
    scanned once per process, so a value screened as a field is not scanned again when it joins a
    record, a pair or a run, and a re-run of the chain (#8.2) re-reads the cache."""
    return tuple(_families(sg.scan(text, **GUARD_HOOKS)))


@functools.lru_cache(maxsize=None)
def text_hits(text):
    """One line of supplied text: a tuple of hit families."""
    if len(text) > sg.MAX_TOTAL_CHARS:
        return ("oversize",)
    found = ["supplied_marker"] if marker_shaped(text) else []
    for family in scan_families(text):
        if family not in found:
            found.append(family)
    if not found and unmarked(text) != text:
        return text_hits(unmarked(text))
    return tuple(found)


@functools.lru_cache(maxsize=None)
def fields_hits(values):
    """Bounded join of related values (D13, D18, D22): a tuple of hit families, exactly as
    sg.scan_fields reports it. Each value's own scan comes from the cache, so only the two joins
    (' ; ' and, with 'Label:' prefixes removed, a plain space) are new scans."""
    if sum(len(value) for value in values) > sg.MAX_TOTAL_CHARS:
        return ("oversize",)
    values = [value for value in values if isinstance(value, str) and value.strip()]
    found = []
    for value in values:
        found.extend(family for family in scan_families(value) if family not in found)
    if found or len(values) < 2:
        return tuple(found)
    for joined in (" ; ".join(values), " ".join(sg._LABEL.sub("", value).strip() for value in values)):
        if len(joined) > sg.MAX_TOTAL_CHARS:
            return ("oversize",)
        families = [family for family in scan_families(joined) if family != "mixed_script"]
        if "oversize" in families:
            return ("oversize",)
        if families:
            return ("split",)
    content = tuple(value for value in values if has_content(value))
    if len(content) != len(values):
        return fields_hits(content)
    plain = tuple(unmarked(value) for value in values)
    if plain != tuple(values):
        return fields_hits(plain)
    return ()


# Split partners (#8.1): sg.split_partners scans up to four joins of the values it is given, so a long
# sequence is read in overlapping windows of SPLIT_WINDOW present values, SPLIT_STEP apart. Any
# SPLIT_WINDOW - SPLIT_STEP + 1 consecutive values share a window.
SPLIT_WINDOW = 8
SPLIT_STEP = 5


# A filler value (no letter or digit: '.', '-', '\u2026', '|') carries no instruction text; it is left out of
# the split-partner windows and kept as it is, so it neither pads the parts of a split into different
# windows nor breaks their adjacency.
_CONTENT = re.compile(r"[^\W_]")


def has_content(value):
    return isinstance(value, str) and bool(_CONTENT.search(value))


@functools.lru_cache(maxsize=None)
def split_hits(values, focus=None):
    """The values of an ordered sequence (str, or None for a value that is absent or already withheld)
    that carry part of an instruction split across value boundaries, read by sg.split_partners: every
    value a boundary-crossing hit overlaps, including a value that trips on its own and its clean
    partners. Every index sg.split_partners returns is kept; no neighbour is exempted (owner decision,
    over-withholding is the accepted failure). None, blank and filler values are skipped without
    breaking adjacency. Returns ((index, family), ...) with family 'split', or 'oversize' for every
    value of a window whose join is too long to screen (sg.split_partners returns every index then, and
    the record is held as oversize). focus: sorted indices (held values); only the windows that span
    one are read, so a long sequence costs in proportion to what is held. The windows keep one grid
    either way."""
    present = [index for index, value in enumerate(values) if has_content(value)]
    if len(present) < 2:
        return ()
    last = max(len(present) - SPLIT_WINDOW, 0)
    starts = list(range(0, last + 1, SPLIT_STEP))
    if starts[-1] < last:
        starts.append(last)
    found = {}
    for start in starts:
        window = present[start:start + SPLIT_WINDOW]
        if focus is not None:
            at = bisect.bisect_left(focus, window[0])
            if at == len(focus) or focus[at] > window[-1]:
                continue
        parts = [values[index] for index in window]
        joined = " ; ".join(parts)
        if len(joined) > sg.MAX_TOTAL_CHARS or (not joined.isascii()
                                                and sg._nfkc_len_bound(joined) > sg.MAX_TOTAL_CHARS):
            found.update((index, "oversize") for index in window)
            continue
        for position in sg.split_partners(parts, **GUARD_HOOKS):
            found.setdefault(window[position], "split")
    return tuple(sorted(found.items()))


# A complete sentence: it ends in a full stop, question or exclamation mark, before any closing quote.
_COMPLETE = re.compile(r"[.!?\u3002][\"'\u2019\u201d)\]]*\s*$")


# A trailing item reference ('raw/decision-log.csv row 3', 'lines 8-10', 'clause 2', a bare number).
_TRAILING_ANCHOR = re.compile(
    r"(?:\b(?:rows?|lines?|items?|entry|entries|steps?|clauses?|sections?|paras?|paragraphs?|pages?|pp?|nos?"
    r"|sheet|tab|slides?)\.?\s*)?#?\d+(?:\s*[-\u2013,]\s*\d+)*[.!?;:)\u3002]*\s*$", re.IGNORECASE)


@functools.lru_cache(maxsize=None)
def source_shaped(value):
    """A value that is only a source reference: a citation-shaped path or document ID with its
    locators (#8.6), or a bare item reference ('row 3', 'lines 8-10'). It carries no clause, so the
    split-partner views may read the values around it without it (it is still read in the full view)."""
    return bool(value.strip()) and (citation_shape_ok(value) or not _TRAILING_ANCHOR.sub("", value).strip())


def id_hits(value):
    """IDs, tokens and sources are scanned with '-', '_', '.' and ':' read as spaces, then each
    ':'-separated segment on its own so a 'scheme:' prefix cannot shield an instruction (D13)."""
    found = text_hits(re.sub(r"[-_.:]+", " ", value))
    segments = value.split(":")
    for segment in segments if not found and len(segments) > 1 else ():
        found = text_hits(re.sub(r"[-_.]+", " ", segment).strip())
        if found:
            break
    return found


_LINE_SPLIT = re.compile(r"\r\n|[\n\r\u2028\u2029\x85\x0b\x0c]")


def field_hits(text):
    """Screen one field line by line, then adjacent line pairs (D11). Returns (families, location)."""
    if len(text) > sg.MAX_TOTAL_CHARS:
        return ("oversize",), "field"
    lines = _LINE_SPLIT.split(text)
    single = len([line for line in lines if line.strip()]) <= 1
    for number, line in enumerate(lines, start=1):
        found = text_hits(line)
        if found:
            return found, "field" if single else f"line {number}"
    for number in range(1, len(lines)):
        pair = (lines[number - 1], lines[number])
        if pair[0].strip() and pair[1].strip():
            found = fields_hits(pair)
            if found:
                return found, f"lines {number}-{number + 1}"
    return (), ""


def strip_placeholders(text):
    return text.replace(WITHHELD, " ")


_STOP_TOKENS = {"the", "client", "group", "company", "services", "service", "global", "national",
                "international", "holdings", "limited", "ltd", "inc", "corp", "corporation", "and", "of"}


def identity_terms(client_name):
    """The canonical client name and its distinctive first word (>= 4 letters, not a generic word)."""
    if client_name == WITHHELD:
        return ()
    terms = [canon(client_name)]
    first = words(client_name)[:1]
    if first and len(first[0]) >= 4 and first[0] not in _STOP_TOKENS:
        terms.append(first[0])
    return tuple(t for t in terms if t)


def contains_identity(text, terms):
    body = canon(strip_placeholders(text))
    tokens = set(words(body))
    for term in terms:
        if " " in term or not term.isalnum():
            if term in body:
                return True
        elif term in tokens:
            return True
    return False


CLIENT_TOKEN = "[client]"


def redact_identity(text, terms):
    """Replace the engagement client name in a value the engine echoes with CLIENT_TOKEN (#1.1).
    If a form of the name survives the replacement, the whole value is replaced (fails closed)."""
    if not terms or text == WITHHELD or not contains_identity(text, terms):
        return text
    out = unicodedata.normalize("NFKC", strip_cf(text))
    for term in sorted(terms, key=len, reverse=True):
        pattern = r"\s+".join(re.escape(part) for part in term.split())
        if term.isalnum():
            pattern = rf"(?<![a-z0-9]){pattern}(?![a-z0-9])"
        out = re.sub(pattern, CLIENT_TOKEN, out, flags=re.IGNORECASE)
    return CLIENT_TOKEN if contains_identity(out, terms) else out


def _layout(doc):
    """Every screened free-text slot in a fixed order, the records whose fields render together and
    the runs of adjacent values. A slot is (path, container, key)."""
    slots, records, runs = [], [], []

    def record_slots(record, path, spec):
        members = []
        for member, kind, _ in spec:
            if member not in record:
                continue
            if kind in ("text", "name"):
                members.append((f"{path}.{member}", record, member))
            elif kind in ("texts", "names"):
                items = [(f"{path}.{member}[{i}]", record[member], i) for i in range(len(record[member]))]
                members.extend(items)
                if len(items) > 1:
                    runs.append(items)
        slots.extend(members)
        records.append(members)
        return members

    record_slots(doc["engagement"], "engagement", RECORD_SPECS["engagement"])
    for name in RAW_ARRAYS:
        previous = None
        for index, record in enumerate(doc[name]):
            members = record_slots(record, f"{name}[{index}]", RECORD_SPECS[name])
            if previous is not None:
                runs.append(("pair", previous, members))
            previous = members
    escalation_slots = [(f"escalations[{i}]", doc["escalations"], i) for i in range(len(doc["escalations"]))]
    slots.extend(escalation_slots)
    if len(escalation_slots) > 1:
        runs.append(escalation_slots)
    return slots, records, runs


RUN_BLOCK = 16


def _is_item(member):
    """A slot that is one item of a list (named_people, third_party_products, escalations)."""
    return type(member[2]) is int


def screen(doc, prior=None, forced=None):
    """Screen every supplied free-text value of a validated input. Returns (screened copy, holds).
    prior: carried holds keyed by path (a carried placeholder keeps its hold); forced: paths the
    rendered-document screen withholds (#8.2)."""
    prior = prior or {}
    forced = forced or {}
    doc = json.loads(json.dumps(doc))
    slots, records, runs = _layout(doc)
    order = {path: index for index, (path, _, _) in enumerate(slots)}
    held = {}
    for path, box, key in slots:
        value = box[key]
        if path in forced:
            held[path] = forced[path]
        elif path in prior and value == WITHHELD:
            held[path] = prior[path]
        else:
            found, location = field_hits(value)
            if not found:
                found, location = shape_hits(path, value), "field"
            if found:
                held[path] = (found, location)
    for members in records:
        named = {key: (path, box) for path, box, key in members}
        if "title" in named and "citation" in named:
            (title_path, title_box), (citation_path, citation_box) = named["title"], named["citation"]
            title, citation = title_box["title"], citation_box["citation"]
            # A half held only for spelling a clause, though identifier-shaped, still joins, so the
            # other half is withheld too; a half held for any other reason stays out of the join.
            spelled_only = (("render_shape",), "field")
            joinable = ((title_path not in held or (held[title_path] == spelled_only
                                                    and title_shape_ok(title, spelled=False)))
                        and (citation_path not in held or (held[citation_path] == spelled_only
                                                           and citation_shape_ok(citation, spelled=False))))
            if (joinable and (title_path not in held or citation_path not in held)
                    and joined_spells_clause(title, citation)):
                for path in (title_path, citation_path):
                    held.setdefault(path, (("render_shape",), "record"))
    # Neighbour records of one list: each rendered title or citation of a record meets each of the next
    # record's, read by the token-anchored recogniser as adjacent ';' parts are ('DOC-1#Publi' then
    # 'DOC-2#shThisRecord'); both values are withheld with a render_shape hold.
    for run in runs:
        if not (run and run[0] == "pair"):
            continue
        rendered = [[(path, box[key]) for path, box, key in side
                     if (_TITLE_PATH.fullmatch(path) or _CITATION_PATH.fullmatch(path)) and path not in held]
                    for side in run[1:]]
        for first_path, first in rendered[0]:
            for second_path, second in rendered[1]:
                if first_path in held or second_path in held:
                    continue
                if neighbour_spells_clause(first, bool(_TITLE_PATH.fullmatch(first_path)),
                                           second, bool(_TITLE_PATH.fullmatch(second_path))):
                    for path in (first_path, second_path):
                        held[path] = (("render_shape",), "run")
    terms = identity_terms(doc["engagement"]["client_name"])  # harvested before any redaction (A16)

    def live(members):
        return [m for m in members if m[0] not in held]

    def withhold(members, found, location):
        # Filler (no letter or digit) carries no instruction material and is kept as supplied.
        for path, box, key in members:
            if path not in held and has_content(box[key]):
                held[path] = (found, location)

    def text_of(member, live_only):
        path, box, key = member
        value = box[key]
        return None if value == WITHHELD or (live_only and path in held) else value

    def withhold_partners(members, location, focused=False, clean=False):
        # A held value no longer joins the screen below, so the clean half of an instruction split
        # across it and its neighbours is found here (#8.1): the full sequence, held text included, and
        # the live values alone (the sequence a replay sees once every held value is a placeholder),
        # each as supplied and with marker syntax removed (#8.4). focused: read only the windows that
        # span a held value. clean: read every window even when nothing is held.
        held_at = tuple(index for index, member in enumerate(members) if member[0] in held)
        if not (held_at or clean):
            return
        focus = held_at if focused and not clean else None
        full = tuple(text_of(member, False) for member in members)
        live_values = tuple(text_of(member, True) for member in members)
        sequences = (full, live_values, tuple(map(unmarked, full)), tuple(map(unmarked, live_values)))
        for values in dict.fromkeys(sequences):
            for index, family in split_hits(values, focus):
                if members[index][0] not in held:
                    held[members[index][0]] = ((family,), location)

    def withhold_pair_partners(pairs, location):
        # The pairs the join screen below reads, where exactly one value is held (D18, D22).
        for pair in pairs:
            if (pair[0][0] in held) != (pair[1][0] in held):
                full = tuple(text_of(member, False) for member in pair)
                for values in dict.fromkeys((full, tuple(map(unmarked, full)))):
                    for index, family in split_hits(values):
                        if pair[index][0] not in held:
                            held[pair[index][0]] = ((family,), location)

    def views(members):
        # Ordinary values can stand between the parts of a split instruction: the sequence is also read
        # without source references (citations, IDs, item references), then also without complete
        # sentences, so the parts meet. A held value always stays.
        found = [members]
        for keep in (lambda value: not source_shaped(value),
                     lambda value: not (source_shaped(value) or _COMPLETE.search(value))):
            view = [m for m in members if m[0] in held or keep(m[1][m[2]])]
            if len(view) < len(found[-1]):
                found.append(view)
        return found

    def record_pairs(members):
        return [(first, second) for first in members for second in members if first is not second and not (
            _is_item(first) and _is_item(second) and not (
                first[1] is second[1] and abs(first[2] - second[2]) == 1))]

    def neighbour_pairs(ahead, behind):
        return [(first, second) for first in ahead for second in behind if not (
            _is_item(first) and _is_item(second) and not (first[2] == len(first[1]) - 1 and second[2] == 0))]

    # Consecutive records of one array, in input order and field by field (one field across the
    # records), so the parts of an instruction split over three or more records meet (#8.1). A column
    # is read without source references and complete sentences: a complete sentence of the previous
    # record is not the start of the next record's field.
    chains = []
    for members in records:
        name = members[0][0].split("[", 1)[0].split(".", 1)[0] if members else ""
        if chains and chains[-1][0] == name:
            chains[-1][1].append(members)
        else:
            chains.append((name, [members]))
    sequences = []
    for _, chain in chains:
        rows = [member for members in chain for member in members]
        sequences.append((rows, "run" if len(chain) > 1 else "record", False))
        if len(chain) > 1:
            columns = {}
            for member in rows:
                columns.setdefault(re.sub(r"\[\d+\]", "", member[0]), []).append(member)
            sequences.extend((column, "run", True) for column in columns.values() if len(column) > 1)

    while True:
        before = len(held)
        for members in records:
            if len(members) > 1 and any(member[0] in held for member in members):
                withhold_partners(members, "record")
                withhold_pair_partners(record_pairs(members), "record")
        for run in runs:
            if run and run[0] == "pair":
                if any(member[0] in held for member in run[1] + run[2]):
                    withhold_partners(run[1] + run[2], "run")
                    withhold_pair_partners(neighbour_pairs(run[1], run[2]), "run")
            else:
                for number, view in enumerate(views(run)):
                    withhold_partners(view, "run", focused=number > 0)
        for sequence, location, column in sequences:
            if any(member[0] in held for member in sequence):
                found_views = views(sequence)
                for view in found_views[-1:] if column else found_views:
                    withhold_partners(view, location, focused=True)
        for members in records:
            current = live(members)
            if len(current) > 1:
                found = fields_hits(tuple(box[key] for _, box, key in current))
                if found:
                    withhold(current, found, "record")
                    continue
                # Fields of one record can render next to each other in any layout (a title beside
                # its description), so every pair of live fields is also screened as a join (D22).
                # Two list items are paired only as neighbours in one list (wider item windows are the
                # run windows below), which keeps the screen linear in the list's length.
                for i in range(len(current)):
                    for j in range(i + 1, len(current)):
                        pair = (current[i], current[j])
                        if _is_item(pair[0]) and _is_item(pair[1]) and not (
                                pair[0][1] is pair[1][1] and abs(pair[0][2] - pair[1][2]) == 1):
                            continue
                        if all(m[0] not in held for m in pair):
                            found = fields_hits(tuple(box[key] for _, box, key in pair))
                            if found:
                                withhold(pair, found, "record")
        for run in runs:
            if run and run[0] == "pair":
                current = live(run[1]) + live(run[2])
                if live(run[1]) and live(run[2]):
                    found = fields_hits(tuple(box[key] for _, box, key in current))
                    if found:
                        withhold(current, found, "run")
                        continue
                    # Any field of one entry can render next to any field of the next (D18); list items
                    # meet across the boundary only as the last item of one and the first of the next.
                    for first in run[1]:
                        for second in run[2]:
                            if _is_item(first) and _is_item(second) and not (
                                    first[2] == len(first[1]) - 1 and second[2] == 0):
                                continue
                            if first[0] not in held and second[0] not in held:
                                found = fields_hits((first[1][first[2]], second[1][second[2]]))
                                if found:
                                    withhold((first, second), found, "run")
                continue
            current = [member for member in live(run) if has_content(member[1][member[2]])]
            # Neighbours (2 and 3 items) and overlapping blocks of RUN_BLOCK items; a run that short
            # is one block, so the whole run is joined as before without growing past a block. Filler
            # is skipped, so it neither pads a block nor separates neighbours.
            step = RUN_BLOCK - 3
            blocks = [current[i:i + RUN_BLOCK] for i in range(0, max(len(current) - 3, 1), step)]
            windows = blocks + [current[i:i + size] for size in (2, 3) for i in range(len(current) - size + 1)]
            for window in windows:
                if len(window) > 1 and all(m[0] not in held for m in window):
                    found = fields_hits(tuple(box[key] for _, box, key in window))
                    if found:
                        withhold(window, found, "run")
        # Parts that are each clean, after the joins above (which read two records, or a few items, at
        # most): every list run is read whole through split_partners, so filler entries between the
        # parts neither pad nor break them, and so are the fragments of each array's records (no
        # source references, no complete sentences), so a split over three or more records is found.
        for run in runs:
            if run and run[0] != "pair":
                withhold_partners(run, "run", clean=True)
        for sequence, location, _ in sequences:
            if location == "run":
                withhold_partners(views(sequence)[-1], location, clean=True)
        if "engagement.client_name" in held and terms:
            for member in slots:
                if member[0] not in held and contains_identity(member[1][member[2]], terms):
                    held[member[0]] = (("client_identity",), "field")
        if len(held) == before:
            break
    for path, box, key in slots:
        if path in held:
            box[key] = WITHHELD
    holds = []
    for number, path in enumerate(sorted(held, key=order.__getitem__), start=1):
        found, location = held[path]
        holds.append(make_hold(number, path, found, location))
    return doc, holds


def make_hold(number, path, found, location):
    found = tuple(found)
    if "oversize" in found:
        reason, citation = HOLD_REASONS["oversize"], "confidentiality-sanitisation-rules.md #8.1"
    elif "supplied_marker" in found:
        reason, citation = HOLD_REASONS["supplied_marker"], "confidentiality-sanitisation-rules.md #8.4"
    elif "client_identity" in found:
        reason, citation = HOLD_REASONS["client_identity"], "confidentiality-sanitisation-rules.md #8.3"
    elif found == ("render_shape",):
        reason, citation = HOLD_REASONS["render_shape"], "confidentiality-sanitisation-rules.md #8.6"
    else:
        reason, citation = HOLD_REASONS["instruction"], "confidentiality-sanitisation-rules.md #8.1"
    if location == "rendered" and found != ("render_shape",):
        citation = "confidentiality-sanitisation-rules.md #8.2"
    return {
        "hold_id": f"SH-{number:03d}",
        "path": path,
        "location": location,
        "family": "+".join(sorted(found)),
        "reason": reason,
        "source": "engine:sanitize_check" if location == "rendered" else "engine:asset_identify",
        "citation": citation,
    }


def parse_holds(value):
    """Carried screening holds keyed by path. Only the family and location of a withheld value are
    carried (its text is gone); everything else is re-derived and compared."""
    need_list(value, "screening_holds")
    prior = {}
    for index, hold in enumerate(value):
        path = f"screening_holds[{index}]"
        need_object(hold, path)
        check_members(hold, path, ("hold_id", "path", "location", "family", "reason", "source", "citation"))
        for member in ("hold_id", "path", "location", "family", "reason", "source", "citation"):
            if type(hold[member]) is not str:
                raise InputError(f"{path}.{member} must be a string (value not repeated)")
        if not LOCATION_RE.fullmatch(hold["location"]):
            raise InputError(f"{path}.location is not a screening location (value not repeated)")
        families = tuple(hold["family"].split("+"))
        if not all(f in FAMILIES for f in families):
            raise InputError(f"{path}.family is not a detector family (value not repeated)")
        if hold["path"] in prior:
            raise InputError(f"{path}.path repeats another hold's path")
        prior[hold["path"]] = (families, hold["location"])
    return prior


# ---------------------------------------------------------------------------------------------
# Stage 1 - asset_identify (reuse-asset-rubric.md)
# ---------------------------------------------------------------------------------------------


def shelf_score(months):
    if months >= 18:
        return 100
    if months >= 12:
        return 80
    if months >= 6:
        return 50
    return 20


def asset_score(asset):
    general = asset["generalisability"] / 5 * 100
    effort = asset["effort_to_recreate"] / 5 * 100
    shelf = shelf_score(asset["shelf_life_months"])
    dependency = (5 - asset["client_dependency"]) / 5 * 100
    return round(general * GENERALISABILITY_WEIGHT + effort * EFFORT_WEIGHT
                 + shelf * SHELF_LIFE_WEIGHT + dependency * DEPENDENCY_WEIGHT, 1)


def recommendation(score, confidence):
    if score >= SHORTLIST_SCORE and confidence >= SCORING_CONFIDENCE_FLOOR:
        return "shortlist"
    if score >= RETAIN_SCORE:
        return "retain_for_internal_reference"
    return "archive_with_engagement"


def _merge(items, extra):
    out = list(items)
    for item in extra:
        if item == WITHHELD or item not in out:
            out.append(item)
    return out


def _composed(text, fallback):
    """Text composed from several supplied values is screened as composed (D22)."""
    if WITHHELD in text or text_hits(text):
        return fallback
    return text


def stage_asset_identify(s, holds, timestamp):
    deliverable_index, gaps = [], []
    for artifact in s["artifacts"]:
        complete = artifact["status"] == "complete"
        gap = artifact["required"] is True and not complete
        if gap:
            rule = " - closeout gap (reuse-asset-rubric.md #6.1)"
            gaps.append(_composed(
                f"{artifact['artifact_id']}: required deliverable '{artifact['title']}' is {artifact['status']}{rule}",
                f"{artifact['artifact_id']}: required deliverable is {artifact['status']}{rule}",
            ))
        deliverable_index.append({
            "artifact_id": artifact["artifact_id"],
            "title": artifact["title"],
            "artifact_type": artifact["artifact_type"],
            "required": artifact["required"],
            "status": artifact["status"],
            "completeness_gap": gap,
            "owner": artifact["owner"],
            "confidence": min(float(artifact["confidence"]), 0.99),
            "source": "engine:asset_identify",
            "citation": f"{artifact['citation']}; reuse-asset-rubric.md #6.1",
        })
    shortlist = []
    for asset in s["candidate_assets"]:
        score = asset_score(asset)
        confidence = min(float(asset["confidence"]), 0.94)
        shortlist.append({
            "asset_id": asset["asset_id"],
            "title": asset["title"],
            "asset_type": asset["asset_type"],
            "description": asset["description"],
            "reuse_score": score,
            "recommendation": recommendation(score, confidence),
            "reuse_rationale": (
                f"generalisability {asset['generalisability']}/5; "
                f"effort_to_recreate {asset['effort_to_recreate']}/5; "
                f"shelf_life {asset['shelf_life_months']} months; "
                f"client_dependency {asset['client_dependency']}/5"
            ),
            "confidentiality_markers": list(asset["confidentiality_markers"]),
            "aggregation_tokens": list(asset["aggregation_tokens"]),
            "confidence": confidence,
            "source": "engine:asset_identify",
            "citation": f"{asset['citation']}; reuse-asset-rubric.md #1.1,#2.1,#3.1,#4.1,#5.1",
        })
    screening = []
    if holds:
        screening.append(
            f"screening: {len(holds)} field(s) withheld for embedded-instruction review - see screening_holds "
            "(confidentiality-sanitisation-rules.md #8.1)"
        )
    doc = {key: s[key] for key in ("contract_version", "run_metadata", "engagement") + RAW_ARRAYS}
    doc["escalations"] = _merge(s["escalations"], gaps + screening)
    doc["deliverable_index"] = deliverable_index
    doc["reusable_asset_shortlist"] = shortlist
    doc["provenance"] = {
        "engines": [ENGINE_VERSIONS["asset_identify"]],
        "generated_at": timestamp,
        "demo_scenario": s["run_metadata"].get("demo_scenario", ""),
        "input_escalations": list(s["escalations"]),
        "policies": ["reuse-asset-rubric.md #1-#6", "confidentiality-sanitisation-rules.md #8.1"],
        "screening": SCREENING_LABEL,
    }
    doc["screening_holds"] = holds
    return doc


# ---------------------------------------------------------------------------------------------
# Stage 2 - lesson_cluster (lesson-taxonomy.md)
# ---------------------------------------------------------------------------------------------


def category_for(text):
    """(category, keyword hits). No match, or a tie between categories, stays unclassified (#1.5, A4)."""
    low = text.lower()
    counts = {category: sum(1 for word in kw if word in low) for category, kw in CLUSTER_KEYWORDS.items()}
    best = max(counts.values())
    if best == 0 or list(counts.values()).count(best) > 1:
        return ("unclassified", 0)
    return (next(c for c, n in counts.items() if n == best), best)


def decision_withheld(item):
    return WITHHELD in (item["summary"], item["impact"], item["citation"])


def retro_withheld(item):
    return WITHHELD in (item["text"], item["speaker_role"], item["citation"])


def evidence_items(doc):
    """Decision and retrospective evidence; withheld text is marked and never read (D19)."""
    items = []
    for item in doc["decision_log"]:
        withheld = decision_withheld(item)
        items.append({
            "id": item["decision_id"], "kind": "decision",
            "text": "" if withheld else item["summary"] + " " + item["impact"],
            "withheld": withheld, "confidence": item["confidence"], "citation": item["citation"],
            "named_people": [],
        })
    for item in doc["retrospective_inputs"]:
        withheld = retro_withheld(item)
        items.append({
            "id": item["input_id"], "kind": "retrospective",
            "text": "" if withheld else item["text"],
            "withheld": withheld, "confidence": item["confidence"], "citation": item["citation"],
            "named_people": list(item["named_people"]),
        })
    return items


def stage_lesson_cluster(doc):
    grouped = {}
    for ev in evidence_items(doc):
        category, hits = ("unclassified", 0) if ev["withheld"] else category_for(ev["text"])
        grouped.setdefault(category, []).append((ev, hits))
    clusters = []
    for category in sorted(grouped):
        members = [m[0] for m in grouped[category]]
        blob = " ".join(m["text"] for m in members).lower()
        impact_hits = sum(1 for term in HIGH_IMPACT_TERMS if term in blob)
        priority = min(100, 45 + 10 * impact_hits + 5 * len(members))
        keyword_hits = sum(h for _, h in grouped[category])
        confidence = round(min(0.95, 0.62 + 0.06 * keyword_hits + 0.03 * len(members)), 2)
        signals = []
        for ev in members:
            if ev["withheld"]:
                signals.append({"evidence_id": ev["id"], "signal": "embedded_instruction",
                                "citation": "confidentiality-sanitisation-rules.md #8.1"})
            if ev["named_people"]:
                signals.append({"evidence_id": ev["id"], "signal": "named_person",
                                "citation": "confidentiality-sanitisation-rules.md #2.1"})
            if ev["named_people"] and BLAME_PATTERN.search(ev["text"]):
                signals.append({"evidence_id": ev["id"], "signal": "named_person_blame",
                                "citation": "confidentiality-sanitisation-rules.md #2.2"})
        first = members[0]
        seed = (f"Evidence {first['id']}: source text withheld for embedded-instruction review."
                if first["withheld"] else _composed(first["text"][:220], f"Evidence {first['id']}: seed not repeated."))
        clusters.append({
            "category": category,
            "priority_score": priority,
            "review_candidate": confidence < MIN_CLUSTER_CONFIDENCE,
            "evidence_ids": [ev["id"] for ev in members],
            "evidence_citations": list(dict.fromkeys(ev["citation"] for ev in members)),
            "summary_seed": seed,
            "sensitivity_signals": signals,
            "confidence": confidence,
            "source": "engine:lesson_cluster",
            "citation": f"{CATEGORY_CITATIONS[category]}; lesson-taxonomy.md #2.1,#2.2,#3.1",
        })
    clusters.sort(key=lambda c: (-c["priority_score"], c["category"]))
    for index, cluster in enumerate(clusters, start=1):
        cluster["cluster_id"] = f"LC-{index:03d}"
    out = {key: value for key, value in doc.items() if key != "screening_holds"}
    out["provenance"] = dict(doc["provenance"])
    out["provenance"]["engines"] = doc["provenance"]["engines"] + [ENGINE_VERSIONS["lesson_cluster"]]
    out["provenance"]["policies"] = doc["provenance"]["policies"] + ["lesson-taxonomy.md #1-#4"]
    out["lesson_clusters"] = clusters
    out["screening_holds"] = doc["screening_holds"]
    return out


# ---------------------------------------------------------------------------------------------
# Stage 3 - sanitize_check (confidentiality-sanitisation-rules.md)
# ---------------------------------------------------------------------------------------------

LESSON_HELD_REASON = "lesson evidence must be rewritten at role and process level before reuse (source text not repeated)"
CONTEXT_GUIDANCE = (
    "Draft a generalized engagement context only from approved release-candidate "
    "metadata. Do not copy client names, client descriptors, sector-and-region "
    "combinations, precise scale, dates, products or other raw engagement fields."
)
HANDOFF_NOTE = (
    "Credential & Case Study Assembly may consume only release-candidate fields and inherits no "
    "permission to publish, identify the client, use logos or waive client terms."
)
HANDOFF_FIELDS = [
    "knowledge_record.reusable_assets",
    "knowledge_record.held_assets_summary",
    "knowledge_record.lessons",
    "sanitisation_report.findings",
    "released_assets[].clearance_state",
]


def finding(target_type, target_id, disposition, state, reason, citation, confidence):
    return {
        "target_type": target_type, "target_id": target_id, "disposition": disposition,
        "clearance_state": state, "reason": reason, "confidence": confidence,
        "source": "engine:sanitize_check", "citation": citation,
    }


def _asset_withheld(raw_asset):
    return any(raw_asset[m] == WITHHELD for m in ("title", "asset_type", "description", "citation"))


def stage_sanitize_check(doc):
    engagement = doc["engagement"]
    terms = identity_terms(engagement["client_name"])
    identity_unscreenable = engagement["client_name"] == WITHHELD
    terms_unavailable = not doc["confidentiality_terms"]
    raw_assets = {a["asset_id"]: a for a in doc["candidate_assets"]}
    findings, released, held, candidates = [], [], [], []
    escalations = list(doc["escalations"])
    own_finding = {}

    for asset in doc["reusable_asset_shortlist"]:
        raw_asset = raw_assets[asset["asset_id"]]
        markers = set(asset["confidentiality_markers"]) | set(asset["aggregation_tokens"])
        confidence = min(float(asset["confidence"]), 0.93)
        states, reasons, citations = [], [], []

        def hold(state, reason, citation):
            states.append(state)
            reasons.append(reason)
            citations.append(citation)

        if asset["recommendation"] != "shortlist":
            hold("HOLD_NOT_SHORTLISTED", "reuse score did not reach shortlist band",
                 "confidentiality-sanitisation-rules.md #6.2; reuse-asset-rubric.md #5.2,#5.3")
        else:
            candidates.append(asset)
            citations.append("confidentiality-sanitisation-rules.md #6.2,#7.1")
        if confidence < SANITISATION_CONFIDENCE_FLOOR:
            hold("HOLD_LOW_CONFIDENCE", f"confidence {confidence} below {SANITISATION_CONFIDENCE_FLOOR}",
                 "confidentiality-sanitisation-rules.md #6.1")
        if markers & DIRECT_IDENTIFIER_MARKERS:
            hold("HOLD_REDACTION_REQUIRED",
                 "direct client-identifying material present: " + ", ".join(sorted(markers & DIRECT_IDENTIFIER_MARKERS)),
                 "confidentiality-sanitisation-rules.md #1.1")
        if markers & CLIENT_SPECIFIC_MARKERS:
            hold("HOLD_REDACTION_REQUIRED",
                 "client-specific configuration requires removal before reuse: " + ", ".join(sorted(markers & CLIENT_SPECIFIC_MARKERS)),
                 "confidentiality-sanitisation-rules.md #1.3")
        asset_text = " ".join(raw_asset[m] for m in ("title", "asset_type", "description", "citation"))
        if terms and contains_identity(asset_text, terms):
            hold("HOLD_REDACTION_REQUIRED", "asset text contains the engagement client name (name not repeated)",
                 "confidentiality-sanitisation-rules.md #1.1")
        if markers & NAMED_PERSON_MARKERS:
            hold("HOLD_PERSONAL_DATA_REWRITE",
                 "named-person material requires removal and role-level rewrite: " + ", ".join(sorted(markers & NAMED_PERSON_MARKERS)),
                 "confidentiality-sanitisation-rules.md #2.1,#2.2")
        if markers & LICENSED_MARKERS:
            hold("HOLD_RIGHTS_UNKNOWN",
                 "third-party or licensed material requires rights evidence: " + ", ".join(sorted(markers & LICENSED_MARKERS)),
                 "confidentiality-sanitisation-rules.md #4.1")
        if markers & COMMERCIAL_MARKERS:
            hold("HOLD_REDACTION_REQUIRED",
                 "commercial figures require verified removal or banding before review: " + ", ".join(sorted(markers & COMMERCIAL_MARKERS)),
                 "confidentiality-sanitisation-rules.md #3.1")
        if markers & PRODUCT_AGGREGATION_MARKERS and not states:
            reasons.append("named product/vendor contributes to aggregation review")
            citations.append("confidentiality-sanitisation-rules.md #4.2")
        unknown = markers - KNOWN_MARKERS - AGGREGATION_TOKENS
        if unknown:
            hold("HOLD_UNRECOGNISED_MARKER",
                 f"{len(unknown)} unrecognised confidentiality marker(s) or aggregation token(s) (names not repeated)",
                 "confidentiality-sanitisation-rules.md #7.4")
            escalations.append(f"{asset['asset_id']}: unrecognised confidentiality marker or aggregation token - asset held "
                               "(confidentiality-sanitisation-rules.md #7.4)")
        if terms_unavailable:
            hold("HOLD_TERMS_UNAVAILABLE", "no confidentiality terms supplied; client terms cannot be checked",
                 "confidentiality-sanitisation-rules.md #7.5")
        if identity_unscreenable:
            hold("HOLD_IDENTITY_UNSCREENABLE", "engagement client name withheld; client identity cannot be screened",
                 "confidentiality-sanitisation-rules.md #8.3")
        if _asset_withheld(raw_asset):
            hold("HOLD_EMBEDDED_INSTRUCTION", "asset text withheld for embedded-instruction review (text not repeated)",
                 "confidentiality-sanitisation-rules.md #8.1")
        state = next(s for s in PRECEDENCE if s in states or s == RELEASE)
        disposition = "release_candidate" if state == RELEASE else "hold"
        if not reasons and disposition == "release_candidate":
            reasons.append("no individual hold marker detected; candidate still requires human review")
        rec = {
            "asset_id": asset["asset_id"],
            "title": redact_identity(asset["title"], terms),
            "title_withheld": asset["title"] == WITHHELD,
            "reuse_score": asset["reuse_score"],
            "clearance_state": state,
            "review_required": DEFAULT_REVIEW_REQUIRED,
            "reason": "; ".join(reasons),
            "confidence": confidence,
            "source": "engine:sanitize_check",
            "citation": "; ".join(dict.fromkeys(citations)) or "confidentiality-sanitisation-rules.md #6.2",
        }
        own = finding("asset", asset["asset_id"], disposition, state, rec["reason"], rec["citation"], confidence)
        own_finding[asset["asset_id"]] = own
        findings.append(own)
        (held if disposition == "hold" else released).append(rec)

    tokens, unknown_tokens, group = set(), set(), set()
    for asset in candidates:
        for token in asset["aggregation_tokens"]:
            (tokens if token in AGGREGATION_TOKENS else unknown_tokens).add(token)
            group.add(asset["asset_id"])
    if len(tokens) + len(unknown_tokens) >= AGGREGATION_MIN_TOKENS:
        listed = ", ".join(sorted(tokens)) + (f" and {len(unknown_tokens)} unrecognised" if unknown_tokens else "")
        reason = (f"aggregation risk: {len(tokens) + len(unknown_tokens)} identifying token categories across "
                  f"candidate assets ({listed})")
        citation = "confidentiality-sanitisation-rules.md #5.1,#5.2"
        escalations.append(reason + " - group HOLD (" + citation + ")")
        still = []
        for rec in released:
            if rec["asset_id"] in group:
                moved = dict(rec, clearance_state="HOLD_AGGREGATION_RISK", reason=reason, citation=citation)
                held.append(moved)
                own_finding[rec["asset_id"]].update(disposition="hold", clearance_state="HOLD_AGGREGATION_RISK",
                                                     reason=reason, citation=citation)  # A10
                findings.append(finding("asset_group", rec["asset_id"], "hold", "HOLD_AGGREGATION_RISK", reason,
                                        citation, rec["confidence"]))
            else:
                still.append(rec)
        released = still

    sensitive = set()
    for item in doc["retrospective_inputs"]:
        withheld = retro_withheld(item)
        text = "" if withheld else item["text"]
        named = list(item["named_people"])
        blame = bool(BLAME_PATTERN.search(text))
        if blame and not named:
            named = PERSON_NAME_PATTERN.findall(text)
        client_hit = bool(terms) and contains_identity(text, terms)
        confidence = min(item["confidence"], 0.91)
        state = guidance = None
        if withheld:
            state, guidance = "HOLD_EMBEDDED_INSTRUCTION", "Source text withheld for embedded-instruction review; do not draft from this evidence."
            citation = "confidentiality-sanitisation-rules.md #8.1,#6.2"
        elif blame:
            state, guidance = "HOLD_PERSONAL_DATA_REWRITE", "Rewrite at role/process level; remove named person and blame attribution."
            citation = "confidentiality-sanitisation-rules.md #2.1,#2.2,#6.2"
        elif named:
            state, guidance = "HOLD_PERSONAL_DATA_REWRITE", "Remove named person; use role-level description."
            citation = "confidentiality-sanitisation-rules.md #2.1,#6.2"
        elif client_hit:
            state, guidance = "HOLD_REDACTION_REQUIRED", "Remove the client identity; use a generalized description."
            citation = "confidentiality-sanitisation-rules.md #1.1,#6.2"
        elif identity_unscreenable:
            state, guidance = "HOLD_IDENTITY_UNSCREENABLE", "Client identity cannot be screened; hold for review."
            citation = "confidentiality-sanitisation-rules.md #8.3,#6.2"
        if state:
            sensitive.add(item["input_id"])
            findings.append(finding("lesson", item["input_id"], "rewrite", state, guidance, citation, confidence))
    for item in doc["decision_log"]:
        withheld = decision_withheld(item)
        text = "" if withheld else item["summary"] + " " + item["impact"]
        if withheld or (terms and contains_identity(text, terms)):
            sensitive.add(item["decision_id"])
            state = "HOLD_EMBEDDED_INSTRUCTION" if withheld else "HOLD_REDACTION_REQUIRED"
            citation = "confidentiality-sanitisation-rules.md #8.1,#6.2" if withheld else "confidentiality-sanitisation-rules.md #1.1,#6.2"
            guidance = ("Source text withheld for embedded-instruction review; do not draft from this evidence."
                        if withheld else "Remove the client identity; use a generalized description.")
            findings.append(finding("lesson", item["decision_id"], "rewrite", state, guidance, citation,
                                    min(item["confidence"], 0.91)))

    governed = []
    for cluster in doc["lesson_clusters"]:
        rewrite = bool(cluster["sensitivity_signals"] or sensitive.intersection(cluster["evidence_ids"])
                       or identity_unscreenable)
        if rewrite:
            guidance = ("Draft only at role and process level. Remove names, blame attribution, "
                        "client identifiers and source wording.")
            policy = "confidentiality-sanitisation-rules.md #2.1,#2.2,#6.2"
        else:
            guidance = ("Draft a generalized lesson from the category and evidence IDs only. "
                        "Do not quote, reconstruct or paraphrase source text.")
            policy = "confidentiality-sanitisation-rules.md #6.2"
        governed.append({
            "cluster_id": cluster["cluster_id"],
            "category": cluster["category"],
            "priority_score": cluster["priority_score"],
            "review_candidate": cluster["review_candidate"],
            "evidence_ids": list(cluster["evidence_ids"]),
            "evidence_citations": list(cluster["evidence_citations"]),
            "citation_withheld": WITHHELD in cluster["evidence_citations"],
            "rewrite_required": rewrite,
            "drafting_guidance": guidance,
            "confidence": min(float(cluster["confidence"]), 0.91),
            "source": "engine:sanitize_check",
            "citation": f"{policy}; {cluster['citation']}",
        })

    if terms_unavailable:
        findings.append(finding("register", "confidentiality_terms", "hold", "HOLD_TERMS_UNAVAILABLE",
                                "no confidentiality terms supplied; client terms cannot be checked",
                                "confidentiality-sanitisation-rules.md #7.5", 0.99))
        escalations.append("confidentiality_terms is empty - client terms cannot be checked; every asset held "
                           "(confidentiality-sanitisation-rules.md #7.5)")
    if identity_unscreenable:
        findings.append(finding("engagement", engagement["engagement_id"], "hold", "HOLD_IDENTITY_UNSCREENABLE",
                                "engagement client name withheld; client identity cannot be screened",
                                "confidentiality-sanitisation-rules.md #8.3", 0.99))
        escalations.append("engagement client name withheld - client identity cannot be screened; every asset held "
                           "(confidentiality-sanitisation-rules.md #8.3)")
    for hold in doc["screening_holds"]:
        state = "HOLD_IDENTITY_UNSCREENABLE" if hold["family"] == "client_identity" else "HOLD_EMBEDDED_INSTRUCTION"
        findings.append(finding("screening", hold["hold_id"], "hold", state, hold["reason"], hold["citation"], 0.95))

    escalations = _merge([], escalations)
    overall = ("HOLD" if held or escalations or any(f["disposition"] in ("hold", "rewrite") for f in findings)
               else RELEASE)
    rewrite_count = sum(1 for lesson in governed if lesson["rewrite_required"])
    summary = (f"{len(released)} release candidate asset(s), {len(held)} held asset(s), "
               f"{rewrite_count} lesson rewrite(s).")
    if doc["screening_holds"]:
        summary += f" {len(doc['screening_holds'])} field(s) withheld for embedded-instruction review."
    out = {key: value for key, value in doc.items() if key not in ("screening_holds", "lesson_clusters")}
    out["escalations"] = escalations
    out["provenance"] = dict(doc["provenance"])
    out["provenance"]["engines"] = doc["provenance"]["engines"] + [ENGINE_VERSIONS["sanitize_check"]]
    out["provenance"]["policies"] = doc["provenance"]["policies"] + ["confidentiality-sanitisation-rules.md #1-#8"]
    out["lesson_clusters"] = governed
    out["sanitisation_report"] = {
        "overall_disposition": overall,
        "findings": findings,
        "governance_note": "Release candidates require human practice review; the engine never clears publication or external use.",
        "source": "engine:sanitize_check",
        "citation": "confidentiality-sanitisation-rules.md #6.2,#7.1,#7.2",
    }
    out["released_assets"] = released
    out["held_assets"] = held
    out["lessons_for_draft"] = governed
    out["knowledge_record"] = {
        "record_id": f"{engagement['engagement_id']}-KR-DRAFT",
        "status": "draft_pending_practice_review",
        "title": "Engagement closeout knowledge record",
        "engagement_context_guidance": CONTEXT_GUIDANCE,
        "reusable_assets": released,
        "held_assets_summary": [{"asset_id": a["asset_id"], "clearance_state": a["clearance_state"],
                                 "reason": a["reason"], "citation": a["citation"]} for a in held],
        "lessons": governed,
        "sanitisation_summary": summary,
        "downstream_handoff": {
            "consumer_template": "credential-case-study-assembly",
            "contract_fields": list(HANDOFF_FIELDS),
            "handoff_note": HANDOFF_NOTE,
        },
        "clearance_state": "DRAFT_NOT_PUBLISHED",
        "confidence": 0.9 if overall != "HOLD" else 0.86,
        "source": "engine:sanitize_check",
        "citation": "confidentiality-sanitisation-rules.md #6.2; downstream handoff contract",
        "draft_label": DRAFT_LABEL,
    }
    out["screening_holds"] = doc["screening_holds"]
    return out


# ---------------------------------------------------------------------------------------------
# Knowledge-record skeleton (knowledge-record SKILL.md; #8.2, #8.5)
# ---------------------------------------------------------------------------------------------

CONTEXT_SLOT = "<<CONTEXT: generalized engagement context that follows engagement_context_guidance>>"
NO_CONTEXT_LINE = "No generalized context drafted: the client identity could not be screened (see Held or excluded material)."
TITLE_WITHHELD_MARK = "title_withheld"
CITATION_WITHHELD_MARK = "citation_withheld"


def lesson_slot(cluster_id):
    return f"<<LESSON {cluster_id}: role- and process-level lesson>>"


def _num(value):
    return json.dumps(value)


def withheld_evidence(doc):
    return {ev["id"] for ev in evidence_items(doc) if ev["withheld"]}


def skeleton(doc):
    """The deterministic knowledge-record skeleton as [(line, slot, contributor paths)]. A slot line
    is the only text the drafter writes; every other line is fixed by the governed payload."""
    kr = doc["knowledge_record"]
    report = doc["sanitisation_report"]
    unscreenable = doc["engagement"]["client_name"] == WITHHELD
    asset_index = {a["asset_id"]: i for i, a in enumerate(doc["candidate_assets"])}
    cite_paths = {}
    for i, item in enumerate(doc["decision_log"]):
        cite_paths[item["decision_id"]] = f"decision_log[{i}].citation"
    for i, item in enumerate(doc["retrospective_inputs"]):
        cite_paths[item["input_id"]] = f"retrospective_inputs[{i}].citation"
    withheld = withheld_evidence(doc)
    lines = []

    def add(text, slot=None, contributors=()):
        lines.append((text, slot, tuple(contributors)))

    add(DRAFT_LABEL)
    add("")
    add(f"# {kr['title']} ({kr['record_id']})")
    add("")
    add("## Generalized engagement context")
    if unscreenable:
        add(NO_CONTEXT_LINE)
    else:
        add(CONTEXT_SLOT, slot="CONTEXT")
    add("")
    add("## Released reusable assets")
    if kr["reusable_assets"]:
        add("| Asset ID | Title | Reuse score | Clearance state | Rule citation |")
        add("|---|---|---|---|---|")
        for asset in kr["reusable_assets"]:
            title = TITLE_WITHHELD_MARK if asset["title"] == WITHHELD else asset["title"]
            add(f"| {asset['asset_id']} | {title} | {_num(asset['reuse_score'])} | "
                f"{asset['clearance_state']} | {asset['citation']} |",
                contributors=[f"candidate_assets[{asset_index[asset['asset_id']]}].title"])
    else:
        add("No reusable assets released by Govern.")
    add("")
    add("## Governed lesson themes")
    if not kr["lessons"]:
        add("No lesson themes clustered.")
    for lesson in kr["lessons"]:
        citations = [CITATION_WITHHELD_MARK if c == WITHHELD else c for c in lesson["evidence_citations"]]
        tail = (f" - evidence {', '.join(lesson['evidence_ids'])}; "
                f"{'; '.join(citations)}")
        head = f"- {lesson['cluster_id']} ({lesson['category']}): "
        contributors = [cite_paths[e] for e in lesson["evidence_ids"]]
        if unscreenable:
            add(head + "No lesson text: the client identity could not be screened" + tail, contributors=contributors)
        elif withheld.intersection(lesson["evidence_ids"]):
            add(head + "No lesson text: evidence withheld for embedded-instruction review" + tail,
                contributors=contributors)
        else:
            add(head + lesson_slot(lesson["cluster_id"]) + tail, slot=lesson["cluster_id"], contributors=contributors)
    add("")
    add("## Held or excluded material")
    rows = [(a["asset_id"], a["clearance_state"], a["reason"], a["citation"]) for a in kr["held_assets_summary"]]
    rows += [(f["target_id"], f["clearance_state"], LESSON_HELD_REASON, f["citation"])
             for f in report["findings"] if f["target_type"] == "lesson"]
    rows += [(f["target_id"], f["clearance_state"], f["reason"], f["citation"])
             for f in report["findings"] if f["target_type"] in ("screening", "register", "engagement")]
    if rows:
        add("| Asset, lesson or hold ID | Clearance state | Reason | Rule citation |")
        add("|---|---|---|---|")
        for row in rows:
            add("| " + " | ".join(row) + " |")
    else:
        add("No assets or lessons held by Govern.")
    add("")
    add("## Sanitisation summary")
    add(f"{kr['sanitisation_summary']} Overall disposition: {report['overall_disposition']}.")
    add("")
    add("## Credential handoff")
    add(f"Consumer: {kr['downstream_handoff']['consumer_template']}. Readable fields: "
        f"{', '.join(kr['downstream_handoff']['contract_fields'])}.")
    add(kr["downstream_handoff"]["handoff_note"])
    add("")
    add("## Required approvals")
    add("Practice review, legal review where flagged, and engagement-owner review. Nothing has been published.")
    return lines


def skeleton_text(doc):
    return "\n".join(line for line, _, _ in skeleton(doc)) + "\n"


def rendered_hits(doc, raw=None):
    """Screen the rendered skeleton line by line, as each line's contributing values joined, and in
    adjacent pairs (D22), and read rendered titles and citations with their neighbours in rendering
    order (#8.6). raw: the screened input the chain started from, whose withheld values still carry
    their text in a first run; a clean value that completes an instruction split across a withheld
    one on the same or the adjacent line is withheld too. Returns the supplied contributor paths to
    withhold: {path: (families, "rendered")}."""
    lines = skeleton(doc)
    held = {p for p, b, k in _layout(doc)[0] if b[k] == WITHHELD}
    out = {}

    def take(found, *entries):
        for _, _, contributors in entries:
            for path in contributors:
                if path not in held and path not in out:
                    out[path] = (found, "rendered")

    def body(entry):
        text, slot, _ = entry
        if slot == "CONTEXT":
            return ""
        if slot:
            text = text.replace(lesson_slot(slot), " ")
        return strip_placeholders(text)

    values = {p: b[k] for p, b, k in _layout(doc)[0]}
    texts = {p: b[k] for p, b, k in _layout(raw)[0]} if raw is not None else values

    def partners(*entries):
        # As screen() does for the input order (#8.1): the full sequence, withheld text included, and
        # the live values alone.
        paths = [path for _, _, contributors in entries for path in contributors if path in values]
        if not any(values[path] == WITHHELD for path in paths):
            return
        full = tuple(None if texts.get(path, WITHHELD) == WITHHELD else texts[path] for path in paths)
        live_values = tuple(None if values[path] == WITHHELD else values[path] for path in paths)
        for sequence in dict.fromkeys((full, live_values, tuple(map(unmarked, full)),
                                       tuple(map(unmarked, live_values)))):
            for index, family in split_hits(sequence):
                if paths[index] not in held and paths[index] not in out:
                    out[paths[index]] = ((family,), "rendered")

    for entry in lines:
        if entry[2]:
            partners(entry)
            found = text_hits(body(entry))
            if not found:
                # The values that land on one line are also screened as a run, so punctuation the
                # template puts between them cannot hide a split instruction.
                parts = tuple(values[p] for p in entry[2] if p in values and values[p] != WITHHELD)
                if len(parts) > 1:
                    found = fields_hits(parts)
            if found:
                take(found, entry)
    # Every contributor in rendering order, so the parts of an instruction split over three or more
    # lines meet: read around each withheld contributor, also without source references and then also
    # without complete sentences (as screen() reads records).
    order = list(dict.fromkeys(path for _, _, contributors in lines for path in contributors if path in values))
    if any(values[path] == WITHHELD for path in order):
        for keep in (lambda text: True, lambda text: not source_shaped(text),
                     lambda text: not (source_shaped(text) or _COMPLETE.search(text))):
            view = [path for path in order if values[path] == WITHHELD or keep(texts.get(path, values[path]))]
            focus = tuple(index for index, path in enumerate(view) if values[path] == WITHHELD)
            full = tuple(None if texts.get(path, WITHHELD) == WITHHELD else texts[path] for path in view)
            live_values = tuple(None if values[path] == WITHHELD else values[path] for path in view)
            for sequence in dict.fromkeys((full, live_values, tuple(map(unmarked, full)),
                                           tuple(map(unmarked, live_values)))):
                for index, family in split_hits(sequence, focus):
                    if view[index] not in held and view[index] not in out:
                        out[view[index]] = ((family,), "rendered")
    for first, second in zip(lines, lines[1:]):
        if first[2] and second[2]:
            partners(first, second)
        if (first[2] or second[2]) and body(first).strip() and body(second).strip():
            found = fields_hits((body(first), body(second)))
            if found:
                take(found, first, second)
    out.update(rendered_neighbour_hits(doc, values, held | set(out)))
    return out


def rendered_neighbour_hits(doc, values, gone):
    """Neighbours in rendering order (#8.6). Input order is screened in screen(); once assets are held
    and evidence is clustered, the released-asset table and the lesson citations render values side by
    side that were not neighbours in the input. Titles of released assets are read in table order: a
    title withheld here moves its asset to the held table, so the scan keeps the live titles on a stack
    and reads the newly touching pair at once ('Publi', a withheld 'Sk' + 'ipThisRecord', then
    'shThisRecord'). Lesson evidence citations are read in line order, across lessons. gone: paths
    already withheld or about to be. Returns {path: (("render_shape",), "rendered")}; derive() re-runs
    the chain with them until nothing new is found."""
    out = {}
    kr = doc["knowledge_record"]
    asset_index = {a["asset_id"]: i for i, a in enumerate(doc["candidate_assets"])}

    def mark(*paths):
        for path in paths:
            if path not in gone:
                out[path] = (("render_shape",), "rendered")

    live = []
    for asset in kr["reusable_assets"]:
        path = f"candidate_assets[{asset_index[asset['asset_id']]}].title"
        if asset["title"] == WITHHELD or path in gone:
            continue
        if live and neighbour_spells_clause(live[-1][1], True, asset["title"], True):
            mark(live.pop()[0], path)
        else:
            live.append((path, asset["title"]))
    cite_paths = {item["decision_id"]: f"decision_log[{i}].citation" for i, item in enumerate(doc["decision_log"])}
    cite_paths.update({item["input_id"]: f"retrospective_inputs[{i}].citation"
                       for i, item in enumerate(doc["retrospective_inputs"])})
    previous = None
    for lesson in kr["lessons"]:
        for value in lesson["evidence_citations"]:
            paths = [cite_paths[e] for e in lesson["evidence_ids"] if values.get(cite_paths[e]) == value]
            if value == WITHHELD or not paths or any(path in gone or path in out for path in paths):
                previous = None
            elif previous and neighbour_spells_clause(previous[1], False, value, False):
                mark(*previous[0], *paths)
                previous = None
            else:
                previous = (paths, value)
    return out


# ---------------------------------------------------------------------------------------------
# The chain, its replay and the command-line wrapper (A19, A22, A23, B1a, B5, D21)
# ---------------------------------------------------------------------------------------------


def derive(raw, timestamp, prior=None, upto=3):
    """Run the deterministic chain on a validated input up to stage `upto`. Stage 3 also screens the
    rendered skeleton and re-runs the chain until no rendered value is left to withhold (#8.2)."""
    forced = {}
    while True:
        screened, holds = screen(raw, prior, forced)
        doc = stage_asset_identify(screened, holds, timestamp)
        if upto >= 2:
            doc = stage_lesson_cluster(doc)
        if upto >= 3:
            doc = stage_sanitize_check(doc)
            extra = rendered_hits(doc, raw)
            if extra:
                forced.update(extra)
                continue
        return doc


def reconstruct(doc, stage):
    """Validate an intermediate's shape and rebuild the screened input it carries."""
    _check_contract_version(doc)
    expected = STAGE_KEYS[stage]
    missing = sorted(expected - set(doc))
    if missing:
        raise InputError(f"input is not {STAGE_NAMES[stage]} output: {missing[0]} is required")
    extra = [key for key in doc if key not in expected]
    if extra:
        raise InputError(f"input is not {STAGE_NAMES[stage]} output: {seg(extra[0])} is not a member here (name not repeated)")
    provenance = need_object(doc["provenance"], "provenance")
    if "input_escalations" not in provenance:
        raise InputError("provenance.input_escalations is required")
    if not timestamp_ok(provenance.get("generated_at")):
        raise InputError("provenance.generated_at must be an ISO-8601 UTC timestamp YYYY-MM-DDTHH:MM:SSZ (value not repeated)")
    prior = parse_holds(doc["screening_holds"])
    raw = {key: doc[key] for key in RAW_REQUIRED}
    raw["run_metadata"] = doc["run_metadata"]
    raw["escalations"] = provenance["input_escalations"]
    clean, timestamp = validate_input(raw, prior=prior)
    if timestamp != provenance["generated_at"]:
        raise InputError("provenance.generated_at disagrees with run_metadata.generated_at")
    return clean, timestamp, prior


def first_difference(expected, supplied):
    for key in expected:
        if json.dumps(expected[key], sort_keys=True) != json.dumps(supplied.get(key), sort_keys=True):
            return key
    return None


def verify(doc, stage):
    """Re-derive the whole intermediate from the input it carries and require exact equality of
    every member, provenance and holds included. Returns (input, timestamp, prior)."""
    raw, timestamp, prior = reconstruct(doc, stage)
    expected = derive(raw, timestamp, prior, upto=stage)
    if json.dumps(expected, sort_keys=True) != json.dumps(doc, sort_keys=True):
        section = first_difference(expected, doc) or "document"
        raise InputError(f"{section} does not re-derive from the screened input it carries; "
                         f"the {STAGE_NAMES[stage]} output was edited or is from another engine version")
    return raw, timestamp, prior


def run(engine, argv, body):
    """Run an engine body; an InputError prints one value-free line and exits 2 with nothing written."""
    try:
        return body(argv)
    except InputError as error:
        print(f"{engine}: input error: {error}; nothing written", file=sys.stderr)
        return 2
