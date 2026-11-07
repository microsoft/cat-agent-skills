"""assertion_rules - shared assertion-support rules and input schemas.

Canonical copy: the assertion-map skill's scripts/assertion_rules.py. The gate-check and review-packet skills
ship byte-identical copies in their own scripts/ (verified by the test data's check_shared_copies.py), so each skill
runs on its own and gate_check can recompute exactly what assertion_map emits and never has to trust a
self-declared source tag (quality-gate-criteria.md #8.4).

Type rule: a field of the wrong JSON type is a clean InputError; values are never coerced, so a string
"false" is never read as a boolean and a page label "iv" is never read as a page number.

Contract rule: every engine calls validate_contract at entry, which checks the whole payload against the
skill's own copy of contracts/ps.deliverable-review-quality-gate.v1.json (required fields, JSON types, closed
enums, ranges and provenance prefixes). A violation is an InputError raised before any output is written."""
import argparse
import copy
import functools
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

import steering_guard as sg  # vendored shared detector; never edit (tests/check_shared_copies.py pins its SHA-256)

AM_ENGINE = "engine:assertion_map"
AM_ENGINE_VERSION = "1.0.9"
AM_LEDGER_TAG = f"assertion_map/{AM_ENGINE_VERSION}"
CONTRACT_VERSION = "ps.deliverable-review-quality-gate.v1"
# The engines in run order; provenance.engines names them as `<engine>/<version>` (record_engine).
ENGINE_NAMES = ("assertion_map", "gate_check", "severity_rank")
CONTRACT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "contracts", "ps.deliverable-review-quality-gate.v1.json")
# Top-level sections each engine needs beyond the contract's own required list (contract descriptions say which).
STAGE_REQUIRED = {
    "assertion_map": ("criteria", "evidence_set"),
    "gate_check": ("assertion_mappings",),
    "severity_rank": ("assertion_mappings", "gate_results", "findings", "escalations"),
}
EVIDENCE_CONFIDENCE_FLOOR = 0.70  # severity-rules.md #2.2
QUANTIFIED_CONFIDENCE_FLOOR = 0.80  # severity-rules.md #2.3; quality-gate-criteria.md #1.2
FORWARD_LOOKING_CONFIDENCE_FLOOR = 0.55  # quality-gate-criteria.md #1.3
RECOMMENDATION_CONFIDENCE_FLOOR = 0.65  # quality-gate-criteria.md #1.4
MIN_RECOMMENDATION_SAMPLE_SIZE = 30  # quality-gate-criteria.md #1.4
MAX_INPUT_DEPTH = 64  # nesting deeper than any contract shape is rejected before any recursive processing
# Closed evidence-type vocabulary (contract evidence_set[].type). A missing or unrecognised type never supports an assertion.
EVIDENCE_TYPES = {
    "analysis_model", "financial_model", "system_export", "signed_client_data", "licensed_content_register",
    "internal_benchmark", "statement_of_work", "disclaimer_extract", "interview_summary", "workshop_note", "stakeholder_verbal",
}
# Per-class allowlists: support must come from a listed type (quality-gate-criteria.md #1.1-#1.4).
TRACEABLE_QUANTIFIED_TYPES = {"analysis_model", "financial_model", "system_export", "signed_client_data"}  # quality-gate-criteria.md #1.2
FACTUAL_SUPPORT_TYPES = {  # quality-gate-criteria.md #1.1: documented sources stronger than stakeholder recollection
    "analysis_model", "financial_model", "system_export", "signed_client_data", "licensed_content_register",
    "internal_benchmark", "statement_of_work", "disclaimer_extract",
}
FORWARD_LOOKING_SUPPORT_TYPES = EVIDENCE_TYPES - {"stakeholder_verbal"}  # quality-gate-criteria.md #1.3
RECOMMENDATION_SUPPORT_TYPES = EVIDENCE_TYPES - {"stakeholder_verbal", "disclaimer_extract", "licensed_content_register"}  # quality-gate-criteria.md #1.4
SUPPORT_TYPES_BY_CLASS = {
    "quantified": TRACEABLE_QUANTIFIED_TYPES,
    "factual": FACTUAL_SUPPORT_TYPES,
    "forward_looking": FORWARD_LOOKING_SUPPORT_TYPES,
    "recommendation": RECOMMENDATION_SUPPORT_TYPES,
}
RELEVANCE_BY_CLASS = {
    "quantified": {"analysis_model": 4, "financial_model": 4, "system_export": 4, "signed_client_data": 4, "stakeholder_verbal": 1},
    "factual": {"licensed_content_register": 4, "system_export": 4, "signed_client_data": 4, "analysis_model": 3, "financial_model": 3},
    "forward_looking": {"analysis_model": 4, "financial_model": 4, "workshop_note": 3, "interview_summary": 3},
    "recommendation": {"analysis_model": 4, "financial_model": 4, "signed_client_data": 4, "system_export": 4, "interview_summary": 3, "workshop_note": 2, "statement_of_work": 1},
}
# Recognised evidence provenance (quality-gate-criteria.md #1.5): deliverable-ingest records every evidence item as
# `connector:<slug>` or as extracted by an ingest skill. Any other value, including a self-declared tag, cannot
# establish support for any assertion class.
EVIDENCE_SOURCE_CONNECTOR_PREFIX = "connector:"
EVIDENCE_SOURCE_SKILLS = {"skill:deliverable-ingest", "skill:criteria-retrieve"}
CONNECTOR_SLUG_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-_.")
ASSERTION_BOOLEANS = ("hedging_present", "limitation_present", "stated_basis", "scope_aligned")
ASSERTION_COUNTS = ("sample_size", "population_size")
PAGE_LABEL_HINT = "record the physical page number and keep printed labels such as roman numerals in location.label"
# Positions (location.page, location.paragraph) count from 1; counts (sample_size, population_size, finding_count)
# from 0 (quality-gate-criteria.md #8.12).
MIN_POSITION = 1
# The largest integer every JSON reader holds exactly (an IEEE double's 2^53 - 1). A larger integer is refused at
# load, so no engine or tool ever converts one to float (OverflowError) or prints one (Python's digit limit).
MAX_JSON_INTEGER = 2 ** 53 - 1
_MAX_JSON_INTEGER_DIGITS = len(str(MAX_JSON_INTEGER))


class InputError(ValueError):
    """Raised for malformed or unsafe engine input."""


def check_depth(value, label="input", max_depth=MAX_INPUT_DEPTH):
    """Reject nesting deeper than max_depth iteratively, so hostile input can never reach a RecursionError."""
    stack = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        if isinstance(item, (dict, list)):
            if depth > max_depth:
                raise InputError(f"{label} is nested more than {max_depth} levels deep; the review contract never nests that deeply")
            children = item.values() if isinstance(item, dict) else item
            stack.extend((child, depth + 1) for child in children)
    return value


def is_number(value):
    """A finite JSON number. NaN and +/-Infinity are not JSON numbers and never pass a range check."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return isinstance(value, int) or math.isfinite(value)


def _reject_constant(name):
    raise InputError(f"input JSON contains {name}, which is not a valid JSON number")


def _parse_int(text):
    """JSON integers are bounded to +/-MAX_JSON_INTEGER (quality-gate-criteria.md #8.12). The digit count is checked
    before conversion, so an integer of thousands of digits never reaches int() and the value is never echoed."""
    if len(text.lstrip("-")) > _MAX_JSON_INTEGER_DIGITS or abs(int(text)) > MAX_JSON_INTEGER:
        raise InputError(f"input JSON contains an integer of {len(text.lstrip('-'))} digits outside +/-{MAX_JSON_INTEGER}; "
                         "no contract number needs one, so the input is malformed")
    return int(text)


def _parse_float(text):
    """A JSON number written with a fraction or exponent must be finite: 1e400 overflows to infinity, which is not a
    JSON number (quality-gate-criteria.md #8.12)."""
    value = float(text)
    if not math.isfinite(value):
        raise InputError("input JSON contains a number too large to represent (it overflows to infinity), which is not a valid JSON number")
    return value


def is_position(value):
    """A location page or paragraph: an integer of 1 or more (quality-gate-criteria.md #8.12)."""
    return is_integer(value) and value >= MIN_POSITION


def describe(value):
    """A content-free description of an untrusted value for error messages: its JSON type and size, never its text
    (quality-gate-criteria.md #8.9), so a rejected value can never echo embedded instructions to stderr."""
    def plural(count, noun):
        return f"{count} {noun}{'' if count == 1 else 's'}"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "a boolean"
    if isinstance(value, int):
        return "an integer"
    if isinstance(value, float):
        return "a number"
    if isinstance(value, str):
        return f"a {'' if value.strip() else 'blank '}string of {plural(len(value), 'character')}"
    if isinstance(value, list):
        return f"an array of {plural(len(value), 'item')}"
    if isinstance(value, dict):
        return f"an object with {plural(len(value), 'field')}"
    return f"a {type(value).__name__} value"


_CONTRACT_FIELD_NAMES = []


def contract_field_names():
    """Every member name the shipped contract declares (any `properties` block, at any depth): the only member names a
    message, finding or G8 path repeats (quality-gate-criteria.md #8.9). Any other name is supplied text, however
    plain it looks (`atlas_credit_id` can name another client). Empty if the contract cannot be loaded, so every name is
    then a placeholder."""
    if not _CONTRACT_FIELD_NAMES:
        names = set()
        try:
            stack = [contract_schema()]
        except InputError:
            stack = []
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if isinstance(node.get("properties"), dict):
                    names.update(node["properties"])
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
        _CONTRACT_FIELD_NAMES.append(frozenset(names))
    return _CONTRACT_FIELD_NAMES[0]


def path_key(key):
    """A member name in an error path: a contract field name as is; any other name is shown as <field>, so a supplied
    member name is never echoed (quality-gate-criteria.md #8.9)."""
    return key if isinstance(key, str) and key in contract_field_names() else "<field>"


def labelled_members(mapping):
    """(label, key, child) per member of `mapping` for a G8 screen path: a contract field name as is, any other name as
    `<field N>`, the Nth member of that object the contract does not declare. N ignores contract sections, so it is the
    same at every stage, whichever sections a stage adds or removes, and a path names one member without repeating
    supplied text (quality-gate-criteria.md #8.9)."""
    names, undeclared = contract_field_names(), 0
    for key, child in mapping.items():
        if isinstance(key, str) and key in names:
            yield key, key, child
        else:
            undeclared += 1
            yield f"<field {undeclared}>", key, child


def format_path(parts):
    text = "$"
    for part in parts:
        text += f"[{part}]" if isinstance(part, int) else f".{path_key(part)}"
    return text


class _DuplicateFields(dict):
    """A JSON object with two member names that are equal exactly or after normalisation; rejected after loading."""


class _OverlongFieldName(dict):
    """A JSON object with a member name longer than MAX_FIELD_NAME_CHARS; rejected after loading."""


MAX_FIELD_NAME_CHARS = 512  # far above any contract field name or withheld marker (quality-gate-criteria.md #8.10)
MAX_ID_CHARS = 512  # far above any contract ID, engine finding ID or withheld marker (quality-gate-criteria.md #8.11)

# Letters that render like Latin letters, folded before comparing names and identifiers (finding-ID spoofing #8.4,
# recipient classification #2.5, duplicate IDs and member names #8.10-#8.11). Embedded-instruction screening uses
# steering_guard's own fold. Upper/lower case partners are added automatically.
_CONFUSABLE_BASE = {
    # Cyrillic
    "А": "A", "В": "B", "Е": "E", "І": "I", "Ј": "J", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P",
    "С": "C", "Т": "T", "Х": "X", "У": "Y", "Ѕ": "S", "Ԁ": "D", "Ԛ": "Q", "Ԝ": "W",
    "а": "a", "в": "b", "е": "e", "і": "i", "ј": "j", "к": "k", "м": "m", "н": "h", "о": "o", "р": "p",
    "с": "c", "т": "t", "х": "x", "у": "y", "ѕ": "s", "ԁ": "d", "һ": "h", "ӏ": "l", "ԛ": "q", "ԝ": "w",
    # Greek
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O",
    "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X", "Ϲ": "C",
    "α": "a", "β": "b", "ε": "e", "η": "n", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t",
    "υ": "u", "χ": "x", "ω": "w", "ϲ": "c", "ϳ": "j",
    # Armenian
    "Օ": "O", "օ": "o", "Ս": "U", "ս": "u", "ո": "n", "հ": "h", "ց": "g", "զ": "q", "ա": "w", "Լ": "L",
    "Տ": "S", "ı": "i",
    # Cherokee (capitals; small forms are added below through str.lower)
    "Ꭰ": "D", "Ꭱ": "R", "Ꭲ": "T", "Ꭵ": "I", "Ꭹ": "Y", "Ꭺ": "A", "Ꭻ": "J", "Ꭼ": "E", "Ꮃ": "W", "Ꮇ": "M",
    "Ꮋ": "H", "Ꮍ": "Y", "Ꮐ": "G", "Ꮒ": "H", "Ꮓ": "Z", "Ꮏ": "B", "Ꮢ": "R", "Ꮤ": "W", "Ꮥ": "S", "Ꮩ": "V",
    "Ꮪ": "S", "Ꮮ": "L", "Ꮯ": "C", "Ꮲ": "P", "Ꮶ": "K", "Ᏼ": "B",
    # Lisu
    "ꓮ": "A", "ꓐ": "B", "ꓚ": "C", "ꓓ": "D", "ꓰ": "E", "ꓝ": "F", "ꓖ": "G", "ꓧ": "H", "ꓲ": "I", "ꓙ": "J",
    "ꓗ": "K", "ꓡ": "L", "ꓟ": "M", "ꓠ": "N", "ꓳ": "O", "ꓑ": "P", "ꓣ": "R", "ꓢ": "S", "ꓔ": "T", "ꓴ": "U",
    "ꓦ": "V", "ꓪ": "W", "ꓫ": "X", "ꓬ": "Y", "ꓜ": "Z",
    # Latin small capitals and IPA look-alikes (Latin script, so only folding catches them)
    "ᴀ": "a", "ʙ": "b", "ᴄ": "c", "ᴅ": "d", "ᴇ": "e", "ꜰ": "f", "ɢ": "g", "ʜ": "h", "ɪ": "i", "ᴊ": "j",
    "ᴋ": "k", "ʟ": "l", "ᴍ": "m", "ɴ": "n", "ᴏ": "o", "ᴘ": "p", "ʀ": "r", "ꜱ": "s", "ᴛ": "t", "ᴜ": "u",
    "ᴠ": "v", "ᴡ": "w", "ʏ": "y", "ᴢ": "z", "ɑ": "a", "ɡ": "g", "ɩ": "i", "ʋ": "u",
}


def _with_case_partners(base):
    table = dict(base)
    for source, target in base.items():
        for variant in (source.lower(), source.upper()):
            if len(variant) == 1 and variant != source and variant not in table and not variant.isascii():
                table[variant] = target.lower() if variant == source.lower() else target.upper()
    return table


CONFUSABLE_MAP = _with_case_partners(_CONFUSABLE_BASE)
CONFUSABLES = str.maketrans(CONFUSABLE_MAP)
_ID_SEPARATOR_RUN = re.compile(r"[\s\-_./\\]+")


@functools.lru_cache(maxsize=8192)
def canonical_name(value):
    """The one comparison form for names and free-text labels (quality-gate-criteria.md #8.11): the look-alike map
    above, then the detector's fold (NFKC, format-character (Cf) stripping, confusables, diacritics, casefold,
    whitespace collapsing). Applied at every length; there is no length-gated fast path. Compare only; outputs keep
    the original value."""
    return sg.normalize(str(value).translate(CONFUSABLES))


@functools.lru_cache(maxsize=8192)
def canonical_id(value):
    """canonical_name plus separator folding: every run of whitespace, -, _, ., / or \\ is one space, so `A-001`,
    `a_001` and `A .001` compare equal. Used for every ID and member-name comparison, at every length."""
    return _ID_SEPARATOR_RUN.sub(" ", canonical_name(value)).strip()


def key_of(value):
    """The join key of a stated ID or key: canonical_id, or None when the value is not a string or is blank after the
    fold (for example "", "-", "_" or a zero-width character). None never equals anything: a missing, null or blank key
    names nothing, so it cannot match another missing key in a join, ownership check or reconciliation
    (quality-gate-criteria.md #8.17)."""
    if not isinstance(value, str):
        return None
    return canonical_id(value) or None


def keys_match(left, right):
    """True only when both sides state a key and the keys are equal after the canonical fold (#8.11, #8.17)."""
    key = key_of(left)
    return key is not None and key == key_of(right)


def field_name_key(name):
    """Comparison form of a member name (canonical_id). Names longer than MAX_FIELD_NAME_CHARS are refused at load."""
    return canonical_id(name)


ENGINE_ID_PREFIXES = {"am": AM_ENGINE, "gc": "engine:gate_check", "sr": "engine:severity_rank"}


def engine_id_owner(finding_id):
    """The engine tag whose finding-ID prefix (AM-, GC-, SR-) finding_id carries after the canonical fold, so `gc_G8-x`,
    `ＧＣ-x` or a G and C split by a zero-width character is still engine-owned (quality-gate-criteria.md #8.4); None otherwise. Callers pass the raw
    ID, before any withholding, so a flagged ID keeps its owner."""
    if not isinstance(finding_id, str):
        return None
    head = re.match(r"[^\W_]+", canonical_id(finding_id))
    return ENGINE_ID_PREFIXES.get(head.group(0)) if head else None


AM_SPOOF_ID = "AM-G8-engine-id-spoof"
AM_SPOOF_ESCALATION = ("G8: a finding supplied with the review input reused a finding ID that assertion_map recomputes without "
                       "matching the recomputation and was replaced by the recomputed finding - hold for reviewing partner/QRM "
                       "(quality-gate-criteria.md #8.4)")


def am_spoof_finding():
    """The G8 release blocker assertion_map emits when a supplied finding collides with one it recomputes (#8.4). Fixed
    text, so gate_check and severity_rank can verify it exactly and a re-run reproduces it."""
    return {"finding_id": AM_SPOOF_ID, "gate_id": "G8", "severity": "release_blocker",
            "title": "Supplied finding reused an assertion_map finding ID",
            "detail": "A finding supplied with the review input used a finding ID that assertion_map recomputes from the assertions and evidence index but did not match the recomputation; it was replaced by the recomputed finding. Engine findings cannot be replaced, removed or downgraded by input data.",
            "location": {"section": "Upstream findings", "page": None, "paragraph": None, "label": "findings[] supplied with the review input"},
            "criteria_section": "quality-gate-criteria.md #8.4", "confidence": 0.99, "source": AM_ENGINE,
            "citation": "quality-gate-criteria.md #8.1, #8.4; severity-rules.md #1.1"}


def is_am_spoof_id(finding_id):
    return isinstance(finding_id, str) and canonical_id(finding_id) == canonical_id(AM_SPOOF_ID)


def merge_recomputed_findings(supplied, raw_supplied, recomputed, holds=()):
    """Combine supplied findings with the AM- findings assertion_map recomputes (quality-gate-criteria.md #8.4).

    IDs are compared in canonical form (canonical_id). A supplied finding whose raw ID is assertion_map-owned and
    collides with a recomputed finding (or with the AM spoof hold or a foreign-entry hold in `holds`) stands only when
    it is exactly that finding; any other copy is dropped, so the genuine finding replaces it and the ID is never
    duplicated. Every other supplied finding passes through for gate_check to screen. Missing recomputed findings and
    `holds` are appended in order, so a re-run on assertion_map's own output reproduces it. `raw_supplied[i]` is
    findings[i] before withholding, so a flagged ID keeps its owner. Returns (findings, number of supplied findings
    dropped as spoofed)."""
    reserved = {canonical_id(item["finding_id"]): item for item in list(recomputed) + list(holds)}
    reserved[canonical_id(AM_SPOOF_ID)] = am_spoof_finding()
    kept, spoofed = [], 0
    for index, item in enumerate(supplied):
        raw = raw_supplied[index] if index < len(raw_supplied) and isinstance(raw_supplied[index], dict) else item
        raw_id = raw.get("finding_id") if isinstance(raw, dict) else None
        key = canonical_id(raw_id) if isinstance(raw_id, str) else None
        if key in reserved and engine_id_owner(raw_id) == AM_ENGINE and item != reserved[key]:
            spoofed += 1
            continue
        kept.append(item)
    present = {canonical_id(item["finding_id"]) for item in kept if isinstance(item, dict) and isinstance(item.get("finding_id"), str)}
    for item in list(recomputed) + list(holds):
        if canonical_id(item["finding_id"]) not in present:
            kept.append(item)
            present.add(canonical_id(item["finding_id"]))
    if spoofed and canonical_id(AM_SPOOF_ID) not in present:
        kept.append(am_spoof_finding())
    return kept, spoofed


def canonical_tag(source):
    """Comparison form of a `prefix:slug` source tag: canonical_id on each side of the first colon (after NFKC, so a
    fullwidth colon counts), so `Engine :gate_check`, `ENGINE:gate-check` and a tag split by a zero-width character all
    read as `engine:gate check` (quality-gate-criteria.md #8.4, #8.11). None for a non-string."""
    if not isinstance(source, str):
        return None
    prefix, separator, slug = canonical_name(source).partition(":")
    return f"{canonical_id(prefix)}:{canonical_id(slug)}" if separator else canonical_id(prefix)


def is_engine_tag(source):
    """True when a source claims to be an engine (`engine:<anything>` in canonical form)."""
    tag = canonical_tag(source)
    return tag is not None and tag.startswith("engine:")


def is_id_field(parts):
    """True when the path ends at an ID: a member named *_id, or an entry of a member named *_ids."""
    if parts and isinstance(parts[-1], str):
        return canonical_id(parts[-1]).endswith(" id")
    return len(parts) > 1 and isinstance(parts[-1], int) and isinstance(parts[-2], str) and canonical_id(parts[-2]).endswith(" ids")


def _object_pairs(pairs):
    if any(len(key) > MAX_FIELD_NAME_CHARS for key, _ in pairs):
        return _OverlongFieldName(pairs)
    seen, duplicate = set(), False
    for key, _ in pairs:
        folded = field_name_key(key)
        duplicate = duplicate or folded in seen
        seen.add(folded)
    return _DuplicateFields(pairs) if duplicate else dict(pairs)


def _check_loaded(value):
    """Reject objects with duplicate member names (a later value would overwrite an earlier one, quality-gate-criteria.md
    #8.10), identifiers longer than MAX_ID_CHARS (#8.11: no ID needs that length, so none is ever compared at it), and
    lone UTF-16 surrogates (for example "\\ud800": not Unicode text, cannot be written as UTF-8)."""
    stack = [(value, ())]
    while stack:
        item, parts = stack.pop()
        if isinstance(item, _OverlongFieldName):
            raise InputError(f"{format_path(parts)} has a field name longer than {MAX_FIELD_NAME_CHARS} characters; no contract field needs one, so the input is malformed")
        if isinstance(item, _DuplicateFields):
            raise InputError(f"{format_path(parts)} has duplicate field names (equal exactly or after Unicode, case and separator folding), so a later value could overwrite an earlier one; the input is malformed")
        if isinstance(item, dict):
            for key, child in item.items():
                _check_encodable_text(key, lambda parts=parts: f"{format_path(parts)} (a field name)")
                stack.append((child, parts + (key,)))
        elif isinstance(item, list):
            stack.extend((child, parts + (index,)) for index, child in enumerate(item))
        elif isinstance(item, str):
            _check_encodable_text(item, lambda parts=parts: format_path(parts))
            if len(item) > MAX_ID_CHARS and is_id_field(parts):
                raise InputError(f"{format_path(parts)} is an identifier longer than {MAX_ID_CHARS} characters; no contract ID needs one, so the input is malformed")


# Every identifier in the review input is a bounded token (quality-gate-criteria.md #8.11): a member named *_id or an
# entry of a member named *_ids, at any depth. IDs are rendered beside prose in the review packet (an assertion ID before
# its text, evidence IDs before a citation), so an ID that could hold words or punctuation could complete a sentence
# there. ID_TOKEN fits every documented ID convention (A-001, EV-B2, PR-A1, DELIV-ASTER-ORION-V0.8, fig-4-benchmark).
ID_TOKEN = re.compile(r"[A-Za-z0-9._-]{1,80}")
ID_TOKEN_RULE = "1 to 80 ASCII letters, digits, '.', '_' or '-', with no spaces or other characters"


def _id_values(value, parts=()):
    """(path parts, value) for every ID value in `value`, in document order: the value of a member named *_id and each
    and each entry of a member named *_ids (is_id_field), whatever its type, plus (path parts, value) for a *_ids member
    whose value is not an array. An ID value is never walked into, so text nested under an identifier member cannot
    pass as a container. A null *_id member names nothing (key_of) and is not yielded; a null *_ids entry is. The
    contract types each declared ID."""
    if parts and is_id_field(parts):
        if value is not None or isinstance(parts[-1], int):
            yield parts, value
    elif parts and isinstance(parts[-1], str) and canonical_id(parts[-1]).endswith(" ids") and not isinstance(value, list):
        if value is not None:
            yield parts, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _id_values(child, parts + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _id_values(child, parts + (index,))


# The label forms the engines write for records they name themselves (quality-gate-criteria.md #8.11): the positional
# slugs of a register entry, assertion or required-language item with no usable ID, or of another party's record
# (brand-check-2, licensed-content-1, prior-finding-3, assertion-4, scope-assertion-4, language-2, with claim_finding_id's
# -2, -3 suffixes), severity_rank's withheld-finding-N, and gate_check's bare "assertion" fallback. Compared in
# canonical_id form, so case, surrounding whitespace and separator variants (Brand_Check.1) are the same label.
POSITIONAL_LABEL = re.compile(r"(?:brand check|licensed content|prior finding|scope assertion|assertion|language|withheld finding)(?: [0-9]+)+|assertion")
RESERVED_LABEL_RULE = ("the engines reserve the AM-, GC- and SR- finding-ID namespace and the positional labels they write for records "
                       "they name themselves (brand-check-N, licensed-content-N, prior-finding-N, assertion-N, scope-assertion-N, "
                       "language-N, withheld-finding-N, in any case or separator spelling); give the record its own identifier")


def reserved_label(value, engine_namespace=True):
    """True when value is, after canonical_id folding, a label the engines write themselves (quality-gate-criteria.md
    #8.11): a positional label (POSITIONAL_LABEL) or, when engine_namespace, an ID in the AM-, GC- or SR- finding
    namespace (engine_id_owner, #8.4). Such a value can never be accepted as an input ID or match key: it would be
    indistinguishable from the engines' own label for another record in every output. The one shared check for the
    engines and the raw-pack parser. A non-string is not a label (the shape checks refuse it)."""
    if not isinstance(value, str):
        return False
    key = canonical_id(value)
    return bool(POSITIONAL_LABEL.fullmatch(key)) or (engine_namespace and engine_id_owner(value) is not None)


# Finding IDs in these sections are engine-owned when they carry an engine prefix: recomputation, the #8.4 spoof hold
# and --verify govern them, and a re-run legitimately carries the engines' own findings. Only the positional labels are
# refused there.
ENGINE_FINDING_SECTIONS = ("findings", "ranked_findings")
# The deliverable key lists that are identifier-like match keys: a required_language entry is written into a finding ID
# (GC-G2-missing-<key>) and title. client_aliases are client names, not identifiers, and are never written into an ID.
RESERVED_CHECKED_KEY_LISTS = ("required_language", "present_language", "present_disclaimer_types")


def require_unreserved(value, path, engine_namespace=True):
    if reserved_label(value, engine_namespace):
        raise InputError(f"{path} is in a label form the engines write themselves: {RESERVED_LABEL_RULE} (quality-gate-criteria.md #8.11)")


def validate_id_shapes(payload):
    """Refuse the review input when any ID is not an ID_TOKEN string (quality-gate-criteria.md #8.11): a number,
    boolean, object or array under a *_id member, a *_ids member that is not an array, and a *_ids entry that is not a
    string are refused like a malformed string, whether or not the contract declares the member, never passed on to a
    later check. Every ID and every entry of an identifier-like key list (RESERVED_CHECKED_KEY_LISTS) must also not be
    in a label form the engines write themselves (reserved_label); a finding's own finding_id may carry an engine prefix
    (ENGINE_FINDING_SECTIONS). The message names the field path, the type and the rule, never the value (#8.9)."""
    for parts, value in _id_values(payload):
        if is_id_field(parts) and isinstance(value, str):
            if not ID_TOKEN.fullmatch(value):
                raise InputError(f"{format_path(parts)} is not an identifier: IDs are {ID_TOKEN_RULE} (quality-gate-criteria.md #8.11)")
            engine_finding = len(parts) == 3 and parts[0] in ENGINE_FINDING_SECTIONS and parts[2] == "finding_id"
            require_unreserved(value, format_path(parts), engine_namespace=not engine_finding)
        elif is_id_field(parts):
            raise InputError(f"{format_path(parts)} is not an identifier: IDs are strings of {ID_TOKEN_RULE}, got {describe(value)} (quality-gate-criteria.md #8.11)")
        else:
            raise InputError(f"{format_path(parts)} must be an array of identifier strings, got {describe(value)} (quality-gate-criteria.md #8.11)")
    deliverable = payload.get("deliverable") if isinstance(payload, dict) else None
    for field in RESERVED_CHECKED_KEY_LISTS:
        entries = deliverable.get(field) if isinstance(deliverable, dict) else None
        for index, entry in enumerate(entries if isinstance(entries, list) else []):
            require_unreserved(entry, format_path(("deliverable", field, index)))


def _check_encodable_text(text, path):
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InputError(f"{path()} contains a lone surrogate code point, which is not valid Unicode text") from exc


def unique_entries(entries):
    """The entries in order without repeats (strings or objects), so re-running an engine on its own output never
    duplicates an escalation or finding it already carries."""
    seen, kept = set(), []
    for entry in entries:
        key = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            kept.append(entry)
    return kept


# RFC 3339 date-time (the contract's "format": "date-time"), ASCII digits only: 2026-10-01T00:00:00Z or with an offset.
TIMESTAMP = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.[0-9]{1,9})?(?:Z|[+-]([0-9]{2}):([0-9]{2}))")


def is_timestamp(value):
    """True when value is an RFC 3339 date-time with a real calendar date and time and a Z or +/-HH:MM offset
    (quality-gate-criteria.md #8.14). Dates alone, free text and impossible dates such as month 13 are not."""
    match = TIMESTAMP.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return False
    try:
        datetime(*(int(part) for part in match.group(1, 2, 3, 4, 5, 6)))
    except ValueError:
        return False
    return match.group(7) is None or (int(match.group(7)) < 24 and int(match.group(8)) < 60)


def validate_generated_at(value):
    """The --generated-at flag, checked exactly as the contract checks provenance.generated_at."""
    if value is not None and not is_timestamp(value):
        raise InputError("--generated-at must be an ISO-8601 (RFC 3339) date-time such as 2026-10-01T00:00:00Z")
    return value


def engine_ledger_name(entry):
    """The engine (ENGINE_NAMES) a provenance.engines entry names, compared in canonical form (canonical_id), else
    None: `gate_check/1.0.4`, `Gate-Check/9.9` and `gate check` all name gate_check, so a renamed or re-versioned
    engine entry is still recognised as engine-owned (quality-gate-criteria.md #8.21)."""
    if not isinstance(entry, str):
        return None
    folded = canonical_id(entry)
    return next((name for name in ENGINE_NAMES if folded == canonical_id(name) or folded.startswith(canonical_id(name) + " ")), None)


def record_engine(payload, tag, generated_at=None, prior=()):
    """Append the engine/version tag to provenance.engines unless this engine was the last to run (idempotent re-run),
    and stamp generated_at: the --generated-at value, else the value already present, else the current UTC time. The
    review packet renders both, so no engine output ever lacks them (quality-gate-criteria.md #8.14).

    The engine-owned entries already in the ledger (engine_ledger_name) must be exactly `prior`, the exact tags of the
    stages that run before this one, in run order, optionally followed by this engine's own tag (a re-run on its own
    output), and must end the ledger. A missing, renamed, re-versioned, reordered, repeated or extra engine entry is
    an input error, never repaired (quality-gate-criteria.md #8.21)."""
    provenance = payload.setdefault("provenance", {})
    if not isinstance(provenance, dict):
        raise InputError("provenance must be an object when present")
    engines = provenance.setdefault("engines", [])
    if not isinstance(engines, list):
        raise InputError("provenance.engines must be an array when present")
    first = next((index for index, entry in enumerate(engines) if engine_ledger_name(entry)), len(engines))
    owned = engines[first:]
    if any(engine_ledger_name(entry) is None for entry in owned) or owned not in (list(prior), list(prior) + [tag]):
        raise InputError(f"provenance.engines must end with exactly the {len(prior)} entr{'y' if len(prior) == 1 else 'ies'} of the engines "
                         f"that produced this input, in run order; an engine entry is missing, renamed, reordered, repeated or extra. "
                         f"Re-run the chain from the review input; the engine ledger cannot be edited (quality-gate-criteria.md #8.21)")
    if engines[-1:] != [tag]:
        engines.append(tag)
    if generated_at:
        provenance["generated_at"] = generated_at
    elif not (isinstance(provenance.get("generated_at"), str) and provenance["generated_at"].strip()):
        provenance["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return provenance


# --- Whole-document re-derivation (quality-gate-criteria.md #8.21; checklist A23) ----------------------------------
# Every top-level section of the contract. gate_check and severity_rank re-derive the whole upstream document from the
# review input and compare every member, these and any other, in canonical JSON form; the names are used only to say
# which section differs. tests/run_tests.py fails when the contract gains a section or provenance member that is
# neither listed here nor in NOT_ENGINE_OWNED.
COMPARED_SECTIONS = ("contract_version", "engagement_id", "scenario_id", "deliverable", "criteria", "assertions", "evidence_set",
                     "prior_findings", "assertion_mappings", "gate_results", "findings", "ranked_findings", "release_readiness",
                     "escalations", "provenance")
# Members no engine derives from the review input, each with the reason it is safe to leave out of the comparison.
NOT_ENGINE_OWNED = {
    ("provenance", "generated_at"): (
        "The run timestamp. It comes from the operator's --generated-at flag (else the value already present, else the "
        "clock), never from review data, and every stage overwrites it. Re-derivation reuses the carried value as its own "
        "stamp, so it is reproduced by construction; the contract still requires an RFC 3339 date-time (#8.14). It decides "
        "no finding, severity, rank, count, escalation or status and is rendered only as the packet's generation time."),
}


def require_review_input(payload):
    """assertion_map's entry checks on the review input (the root every later stage re-derives from)."""
    if not isinstance(payload, dict):
        raise InputError("input must be a JSON object")
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise InputError(f"expected contract {CONTRACT_VERSION}, got {describe(payload.get('contract_version'))}")
    for key in ("deliverable", "criteria"):
        if not isinstance(payload.get(key), dict):
            raise InputError(f"missing required object: {key}")
    for key in ("assertions", "evidence_set"):
        if key not in payload:
            raise InputError(f"missing required array: {key}")
        if not isinstance(payload[key], list):
            raise InputError(f"{key} must be an array")
    criteria_sections = payload["criteria"].get("criteria_sections")
    if criteria_sections is None:
        raise InputError("missing required criteria list: criteria.criteria_sections")
    if not isinstance(criteria_sections, list):
        raise InputError("criteria.criteria_sections must be an array")
    for index, section in enumerate(criteria_sections):
        if not isinstance(section, str) or not section.strip():
            raise InputError(f"criteria.criteria_sections[{index}] must be a non-blank string, got {describe(section)}")
    for key in ("findings", "escalations"):
        if key in payload and not isinstance(payload[key], list):
            raise InputError(f"{key} must be an array")


def assertion_map_stage(payload, generated_at=None):
    """assertion_map's whole derivation, in place, with no file I/O: validate the review input, withhold flagged text,
    map every assertion, merge recomputed AM- findings, add escalations and stamp provenance. assertion_map.py runs it,
    and gate_check and severity_rank run it again on the review input to re-derive the mapped document (#8.21).
    Returns (payload, mappings)."""
    require_review_input(payload)
    # Every section is checked against the contract before any reader touches it (quality-gate-criteria.md #8.16).
    validate_contract(payload, "assertion_map")
    # IDs are tokens, never prose (quality-gate-criteria.md #8.11); checked on the raw input before any screening.
    validate_id_shapes(payload)
    # Names and locations are never in a label form the engines write themselves (D25, #8.11).
    validate_reserved_names(payload)
    evidence_index(payload["evidence_set"])
    validate_assertions(payload["assertions"])
    # Ownership of a supplied finding ID is read before withholding (quality-gate-criteria.md #8.4).
    raw_findings = copy.deepcopy(payload.get("findings", []))
    # Flagged text is withheld before mapping, so no mapping, finding or later stage repeats it
    # (quality-gate-criteria.md #8.7); gate_check raises the G8 hold for every marker.
    withhold_untrusted(payload, raw_input=True)
    # A record of another engagement or deliverable is replaced by its fixed, positional stand-in before anything reads
    # it, so none of its supplied fields reaches any output (quality-gate-criteria.md #8.15).
    sanitise_foreign_records(payload)
    # A reviewer finding or escalation object of another engagement, deliverable or client is replaced by assertion_map's
    # fixed, positional hold, and any other member naming one is refused (quality-gate-criteria.md #8.15).
    foreign_holds = quarantine_foreign_upstream(payload, raw_findings)
    require_no_foreign_subject(payload)
    evidence_by_id = evidence_index(payload["evidence_set"])
    escalations = list(payload.get("escalations", []))
    mappings, recomputed = [], []
    for assertion in payload["assertions"]:
        mapping, finding, escalation = map_assertion(assertion, evidence_by_id, review_subject(payload))
        mappings.append(mapping)
        if finding:
            recomputed.append(finding)
            # Appended once: re-running assertion_map on its own output reproduces it.
            if escalation not in escalations:
                escalations.append(escalation)
    # A supplied finding colliding with a recomputed one (canonical ID) is replaced by the genuine finding and held
    # as a spoof under G8, never duplicated (quality-gate-criteria.md #8.4).
    findings, spoofed = merge_recomputed_findings(list(payload.get("findings", [])), raw_findings, recomputed, foreign_holds)
    if spoofed and AM_SPOOF_ESCALATION not in escalations:
        escalations.append(AM_SPOOF_ESCALATION)
    payload["assertion_mappings"], payload["findings"], payload["escalations"] = mappings, findings, escalations
    record_engine(payload, AM_LEDGER_TAG, generated_at)
    return payload, mappings


def carried_stamp(carried):
    """The carried provenance.generated_at when it is a valid date-time, else None: the run stamp re-derivation uses
    (NOT_ENGINE_OWNED), so it is reproduced and every other member must re-derive exactly."""
    provenance = carried.get("provenance") if isinstance(carried, dict) else None
    stamp = provenance.get("generated_at") if isinstance(provenance, dict) else None
    return stamp if is_timestamp(stamp) else None


def _canonical_json(value):
    """Exact comparison form: key order ignored, JSON types kept (true is not 1, 1 is not 1.0)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _without_allowed(document):
    document = copy.deepcopy(document)
    if isinstance(document, dict):
        for section, member in NOT_ENGINE_OWNED:
            if isinstance(document.get(section), dict):
                document[section].pop(member, None)
    return document


def differing_members(carried, derived):
    """The top-level members of `carried` that differ from `derived` outside NOT_ENGINE_OWNED: missing, extra or
    changed, compared in canonical JSON form. A non-object `carried` differs as a whole."""
    carried, derived = _without_allowed(carried), _without_allowed(derived)
    if not isinstance(carried, dict):
        return [None]
    keys = list(dict.fromkeys(list(derived) + list(carried)))
    return [key for key in keys if key not in carried or key not in derived or _canonical_json(carried[key]) != _canonical_json(derived[key])]


# What each authenticating stage calls the document it re-derives, and how to recover (require_rederived).
REDERIVED = {
    "gate_check": ("the mapped input (--mapped)", "re-run assertion_map on the review input, then gate_check"),
    "severity_rank": ("the gate-check input (--gates)", "re-run assertion_map and gate_check on the review input, then severity_rank"),
    "verify": ("the ranked output (--verify)", "render nothing from it; re-run assertion_map, gate_check and severity_rank on the review input"),
}


def require_rederived(carried, candidates, stage):
    """Refuse `carried` unless it equals one of the re-derived `candidates` (the first is the expected upstream
    document; a later one is this stage's own output, so a re-run on it reproduces it) in every member outside
    NOT_ENGINE_OWNED (quality-gate-criteria.md #8.21). `candidates` yields documents lazily. The message names the
    contract sections (COMPARED_SECTIONS) that differ from the first candidate and counts any other member, whose name
    is input; it never quotes a value, ID or path (#8.9)."""
    first = None
    for derived in candidates:
        differing = differing_members(carried, derived)
        if not differing:
            return
        if first is None:
            first = differing
    first = first or [None]
    mismatched = [key for key in COMPARED_SECTIONS if key in first]
    count = len(first) - len(mismatched)
    shown = ", ".join(mismatched + ([f"{count} other member(s)"] if count else []))
    raise InputError(f"{REDERIVED[stage][0]} does not match its re-derivation from the review input (--input) in: {shown}. Every "
                     f"engine-owned field, provenance included, must be exactly what the engines derive; {REDERIVED[stage][1]} "
                     f"(quality-gate-criteria.md #8.21)")


def os_reason(exc):
    """An OS error without its file name: the exception type and the OS reason text only. str(exc) repeats the path,
    and a file name is untrusted input (quality-gate-criteria.md #8.9)."""
    reason = getattr(exc, "strerror", None)
    return f"{type(exc).__name__}: {reason}" if isinstance(reason, str) and reason else type(exc).__name__


def load_json_file(path, label="input JSON"):
    """Load engine input. Strict JSON only: NaN/Infinity constants, numbers that overflow to infinity, integers outside
    +/-MAX_JSON_INTEGER, lone surrogates, duplicate member names and over-deep nesting are input errors, so no engine
    ever processes or writes a value that is not valid JSON. Errors name the input by the fixed, trusted `label`
    (for example "review input"), never by its path or file name (#8.9)."""
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle, parse_constant=_reject_constant, parse_int=_parse_int, parse_float=_parse_float,
                                object_pairs_hook=_object_pairs)
    except OSError as exc:
        raise InputError(f"could not read the {label} ({os_reason(exc)})") from None
    except UnicodeDecodeError as exc:
        raise InputError(f"the {label} is not valid UTF-8 (first bad byte at offset {exc.start})") from None
    except json.JSONDecodeError as exc:
        raise InputError(f"the {label} is not valid JSON ({exc.msg} at line {exc.lineno}, column {exc.colno})") from None
    except RecursionError as exc:
        raise InputError(f"the {label} is nested too deeply to process safely") from exc
    check_depth(payload)
    _check_loaded(payload)
    return payload


def write_json_atomic(path, payload, label="output"):
    """Serialise the whole output first, then write it to a temporary file beside the target and os.replace it into
    place. On any error the output path is neither created nor truncated. Errors name the output by the fixed `label`,
    never by its path or file name (#8.9)."""
    try:
        data = (json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except ValueError as exc:  # includes UnicodeEncodeError and non-finite numbers
        raise InputError(f"the {label} could not be serialised as valid JSON ({type(exc).__name__}), so nothing was written") from None
    target = os.path.abspath(path)
    try:
        handle, temp = tempfile.mkstemp(dir=os.path.dirname(target), prefix=f".{os.path.basename(target)}.", suffix=".tmp")
    except OSError as exc:
        raise InputError(f"could not write the {label} ({os_reason(exc)})") from None
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        if os.name != "nt":
            os.chmod(temp, 0o644)
        os.replace(temp, target)
    except BaseException as exc:
        try:
            os.remove(temp)
        except OSError:
            pass
        if isinstance(exc, OSError):
            raise InputError(f"could not write the {label} ({os_reason(exc)})") from None
        raise


class EngineArgumentParser(argparse.ArgumentParser):
    """argparse that never repeats a command-line value, such as a file name, in an error (#8.9). Only argparse's own
    content-free messages (a missing required flag, a flag with no value) pass; anything else, such as an unrecognised
    argument or an ambiguous abbreviation, is reported without the text that was typed. `prog` is the engine's fixed
    script name, never sys.argv[0]."""

    SAFE_ERROR = re.compile(r"the following arguments are required: --[a-z-]+(?:, --[a-z-]+)*|argument --[a-z-]+: expected one argument"
                            r"|argument --[a-z-]+: not allowed with argument --[a-z-]+")

    def error(self, message):
        if not self.SAFE_ERROR.fullmatch(message):
            message = "unrecognised or malformed command-line arguments (the values are not repeated; see --help)"
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")


def is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def require_text(container, key, label, required=True, allow_blank=False):
    """Return container[key] when it is a string; absent optional fields return None."""
    if key not in container or container[key] is None:
        if required:
            raise InputError(f"{label} missing required field: {key}")
        return None
    value = container[key]
    if not isinstance(value, str):
        raise InputError(f"{label}.{key} must be a string, got {describe(value)}")
    if not allow_blank and not value.strip():
        raise InputError(f"{label}.{key} must not be blank")
    return value


def require_boolean(container, key, label, required=True):
    """Booleans must be JSON true/false; "false", 0 and null are input errors, never coerced."""
    if key not in container:
        if required:
            raise InputError(f"{label} missing required boolean: {key}")
        return None
    value = container[key]
    if not isinstance(value, bool):
        raise InputError(f"{label}.{key} must be true or false, got {describe(value)}; omit optional flags instead of sending null or text")
    return value


def require_confidence(container, label, required=False):
    if "confidence" not in container:
        if required:
            raise InputError(f"{label} missing required field: confidence")
        return None
    value = container["confidence"]
    if not is_number(value) or not 0 <= value <= 1:
        raise InputError(f"{label}.confidence must be a number from 0 to 1, got {describe(value)}")
    return value


def validate_location(location, label, required=True):
    if location is None and not required:
        return None
    if not isinstance(location, dict):
        raise InputError(f"{label}.location must be an object")
    for key in ("section", "label"):
        if key in location and location[key] is not None and not isinstance(location[key], str):
            raise InputError(f"{label}.location.{key} must be a string, got {describe(location[key])}")
    for key in ("page", "paragraph"):
        value = location.get(key)
        if value is not None and not is_position(value):
            raise InputError(f"{label}: location.{key} must be an integer of {MIN_POSITION} or more, or null, got "
                             f"{describe(value) if not is_integer(value) else 'an integer below ' + str(MIN_POSITION)}; {PAGE_LABEL_HINT}")
    return location


def validate_assertion(assertion, index):
    if not isinstance(assertion, dict):
        raise InputError(f"assertions[{index}] must be an object")
    label = f"assertions[{index}]"
    require_text(assertion, "assertion_id", label)
    if is_am_spoof_id(f"AM-{assertion['assertion_id']}"):
        raise InputError(f"{label}.assertion_id is reserved: its assertion_map finding ID would be the engine's own spoof hold ({AM_SPOOF_ID}); choose another assertion ID")
    if FOREIGN_HOLD_KEY.fullmatch(canonical_id(f"AM-{assertion['assertion_id']}")):
        raise InputError(f"{label}.assertion_id is reserved: its assertion_map finding ID would be one of the engine's own foreign-entry holds (AM-G8-foreign-...); choose another assertion ID")
    require_text(assertion, "class", label)
    require_text(assertion, "text", label, allow_blank=True)
    require_text(assertion, "citation", label, allow_blank=True)
    # Required provenance (contract: engine:/skill:/connector: prefix); the prefix itself is checked by validate_contract.
    require_text(assertion, "source", label)
    if "location" not in assertion:
        raise InputError(f"{label} missing required field: location")
    validate_location(assertion["location"], label)
    for key in ASSERTION_BOOLEANS:
        # scope_aligned is required for every class: G3 (quality-gate-criteria.md #3.1) applies to all claims and
        # recommendations, so an omitted flag is never read as "aligned".
        require_boolean(assertion, key, label, required=key == "scope_aligned")
    if assertion["class"] == "recommendation" and "sample_size" not in assertion:
        raise InputError(f"{label} missing required field for a recommendation: sample_size (use null only when the recommendation is not sample-based)")
    for key in ASSERTION_COUNTS:
        value = assertion.get(key)
        if value is not None and (not is_integer(value) or value < 0):
            raise InputError(f"{label}.{key} must be a non-negative integer or null, got {describe(value)}")
    require_confidence(assertion, label)
    evidence_ids = assertion.get("evidence_ids")
    if evidence_ids is not None:
        if not isinstance(evidence_ids, list):
            raise InputError(f"{label}.evidence_ids must be an array when present")
        for position, evidence_id in enumerate(evidence_ids):
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                raise InputError(f"{label}.evidence_ids[{position}] must be a non-blank string, got {describe(evidence_id)}")


def validate_assertions(assertions):
    if not isinstance(assertions, list):
        raise InputError("assertions must be an array")
    for index, assertion in enumerate(assertions):
        validate_assertion(assertion, index)
    require_unique_ids(assertions, "assertions", "assertion_id")


def evidence_index(evidence_set):
    """Evidence items keyed by canonical_id(evidence_id), so a reference spelled `ev_001` finds `EV-001`; the items
    keep their original IDs. Duplicate IDs (exact or after the fold) are refused (quality-gate-criteria.md #8.11)."""
    if not isinstance(evidence_set, list):
        raise InputError("evidence_set must be an array")
    for index, item in enumerate(evidence_set):
        if not isinstance(item, dict):
            raise InputError(f"evidence_set[{index}] must be an object with evidence_id")
        label = f"evidence_set[{index}]"
        require_text(item, "evidence_id", label)
        for key in ("type", "title", "citation", "source"):
            require_text(item, key, label, required=False, allow_blank=True)
        require_confidence(item, label)
    require_unique_ids(evidence_set, "evidence_set", "evidence_id")
    return {canonical_id(item["evidence_id"]): item for item in evidence_set}


def evidence_for(evidence_by_id, evidence_id):
    """The evidence item an assertion's evidence_ids entry names, compared in canonical form; None when absent."""
    key = key_of(evidence_id)
    return evidence_by_id.get(key) if key is not None else None


# The subject a record can name (#8.15), by the engine's constant member name: the engagement, the deliverable and the
# client. A member names one when its name, in canonical form with separators removed (field_name_key), is the subject
# word followed by one of SUBJECT_SUFFIXES, so `engagement_id`, `Engagement-ID`, `engagementRef`, `client_name` and
# `client` all count. `client` with no suffix or `name` is compared with the review's client_name and client_aliases;
# any other client suffix (an ID, reference, code or number) has nothing in the review to compare with, so it is never
# verified and always counts as foreign.
SUBJECT_FIELDS = ("engagement_id", "deliverable_id", "client")
SUBJECT_WORDS = (("engagement", "engagement_id"), ("deliverable", "deliverable_id"), ("client", "client"))
SUBJECT_SUFFIXES = ("", "id", "ids", "ref", "reference", "code", "number", "no", "key", "name")
CLIENT_NAME_SUFFIXES = ("", "name")


def subject_member(name):
    """(the SUBJECT_FIELDS constant, compared by name) when member `name` names a subject, else None. `compared` is
    False for a client member that states an identifier rather than a name (nothing to compare it with)."""
    if not isinstance(name, str):
        return None
    compact = field_name_key(name).replace(" ", "")
    for word, constant in SUBJECT_WORDS:
        if compact.startswith(word) and compact[len(word):] in SUBJECT_SUFFIXES:
            return constant, constant != "client" or compact[len(word):] in CLIENT_NAME_SUFFIXES
    return None


def review_subject(payload):
    """The subject every linked record must share: the review's engagement_id, deliverable.deliverable_id and client
    (deliverable.client_name and every client_aliases entry), as given (quality-gate-criteria.md #8.15)."""
    payload = payload if isinstance(payload, dict) else {}
    deliverable = payload.get("deliverable") if isinstance(payload.get("deliverable"), dict) else {}
    aliases = deliverable.get("client_aliases") if isinstance(deliverable.get("client_aliases"), list) else []
    clients = [name for name in [deliverable.get("client_name")] + aliases if isinstance(name, str)]
    return {"engagement_id": payload.get("engagement_id"), "deliverable_id": deliverable.get("deliverable_id"), "client": clients}


def _subject_matches(value, own):
    """True when a stated subject value equals the review's own (`own` is a string, or a list of client names). A
    non-string, blank or withheld value on either side never matches (#8.13, #8.17)."""
    if not isinstance(value, str) or contains_withheld(value):
        return False
    owned = own if isinstance(own, list) else [own]
    return any(isinstance(item, str) and not contains_withheld(item) and keys_match(value, item) for item in owned)


def _subject_members(value, depth=0):
    """(constant, compared, member value) for every member of `value` that names a subject, at any depth (a location or
    any other nested object of the record counts as the record's own)."""
    if depth > MAX_INPUT_DEPTH:
        return
    if isinstance(value, dict):
        for key, child in value.items():
            named = subject_member(key)
            if named is not None:
                yield named[0], named[1], child
            elif isinstance(child, (dict, list)):
                yield from _subject_members(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from _subject_members(child, depth + 1)


def foreign_subject(record, subject):
    """The subjects (SUBJECT_FIELDS constants, in that order) on which a record names another engagement, deliverable
    or client than the review (#8.15); [] when it shares the subject. Every member that names a subject (subject_member)
    counts, at any depth of the record and in any spelling. An absent or null member names no subject, so the record is
    the review's own. Values are compared by keys_match (#8.11): a value blank after the fold on either side states no
    subject to compare, so it never matches and counts as foreign (#8.17); a non-string value (an object, array, number
    or boolean) states no comparable subject and counts as foreign. A value that is withheld on either side cannot be
    verified, and every copy of one flagged text carries the same marker, so a withheld value never matches: it counts
    as foreign and holds (#8.13). A client identifier (not a name) has nothing to compare with and counts as foreign."""
    if not isinstance(record, dict) or not isinstance(subject, dict):
        return []
    found = set()
    for constant, compared, value in _subject_members(record):
        if value is None:
            continue
        if not compared or not _subject_matches(value, subject.get(constant)):
            found.add(constant)
    return [key for key in SUBJECT_FIELDS if key in found]


# Engine text a foreign record's stand-in carries. Neither is an identifier token (#8.11), so no review-input ID can
# equal one, and FOREIGN_SUBJECT never matches the review's own subject, so the stand-in stays foreign at every stage.
FOREIGN_SUBJECT = "[another engagement or deliverable]"


def foreign_record_id(path):
    """The stand-in ID of the foreign record at `path` (for example `deliverable.brand_checks[0]`): positional only."""
    return f"[record of another engagement or deliverable: {path}]"


# The label forms the engines write in names and locations for records they name themselves (D25, #8.11), compared in
# canonical_id form (case, surrounding whitespace and -, _, . separators folded): a record path (brand_checks[0],
# deliverable.brand_checks[0], $.findings[2]), a positional record label with its path (Brand check 1
# (deliverable.brand_checks[0]), Reviewer finding 1 (findings[0])), and the foreign-record stand-ins (FOREIGN_SUBJECT,
# foreign_record_id). None is an identifier token, so ID_TOKEN already refuses them as IDs; reserved_name refuses them,
# and the reserved ID labels (reserved_label), in the review input's name and location fields.
_LABEL_PATH = r"(?:\$ ?)?[a-z][a-z0-9 ]*\[[0-9]+\](?:\[[0-9]+\]|[a-z0-9 ]+)*"
ENGINE_LABEL_FORM = re.compile(
    _LABEL_PATH + r"|[a-z][a-z ]* [0-9]+ \(" + _LABEL_PATH + r"\)"
    + "|" + re.escape(canonical_id(FOREIGN_SUBJECT)) + "|" + re.escape(canonical_id(foreign_record_id("")).rstrip("]").rstrip()) + r" .*\]")
RESERVED_NAME_RULE = ("a name, title or location may not be a label the engines write themselves: a record path (brand_checks[N], "
                      "<section>[N]), a positional record label (Brand check N (<path>)), a foreign-record stand-in, or a reserved "
                      "ID label (an AM-, GC- or SR- finding ID, brand-check-N, language-N, assertion and the like), in any case "
                      "or separator spelling")
# Name fields of the deliverable (D25): a string, or each entry of a list of strings.
RESERVED_NAME_FIELDS = ("client_name", "title", "client_aliases", "intended_recipients")
# Supplied records whose location names a section and paragraph label of this deliverable. An engine-owned finding in
# findings[] (engine_id_owner) carries the engines' own positional location and is verified by recomputation (#8.4).
LOCATED_RECORDS = (("assertions",), ("evidence_set",), ("deliverable", "brand_checks"), ("deliverable", "licensed_content"),
                   ("prior_findings",), ("findings",))


def reserved_name(value):
    """True when value is a label the engines write themselves (ENGINE_LABEL_FORM, or reserved_label), after
    canonical_id folding. The one shared check for name and location fields, in the engines and the raw-pack parser."""
    return isinstance(value, str) and (bool(ENGINE_LABEL_FORM.fullmatch(canonical_id(value))) or reserved_label(value))


def require_unreserved_name(value, path):
    if reserved_name(value):
        raise InputError(f"{path} is in a label form the engines write themselves: {RESERVED_NAME_RULE} (quality-gate-criteria.md #8.11)")


def validate_reserved_names(payload):
    """Refuse the review input when a name field (RESERVED_NAME_FIELDS) or a supplied record's location section or label
    (LOCATED_RECORDS) is in a label form the engines write themselves (reserved_name), so no supplied value can pass for
    the engines' own label of another record in any output (quality-gate-criteria.md #8.11). Checked on the raw input
    before any screening; the message names the field path and the rule, never the value (#8.9)."""
    deliverable = payload.get("deliverable") if isinstance(payload.get("deliverable"), dict) else {}
    for field in RESERVED_NAME_FIELDS:
        value = deliverable.get(field)
        for index, entry in (enumerate(value) if isinstance(value, list) else [(None, value)]):
            require_unreserved_name(entry, format_path(("deliverable", field) + (() if index is None else (index,))))
    for segments in LOCATED_RECORDS:
        records = payload
        for part in segments:
            records = records.get(part) if isinstance(records, dict) else None
        for index, record in enumerate(records if isinstance(records, list) else []):
            if not isinstance(record, dict) or not isinstance(record.get("location"), dict):
                continue
            if segments == ("findings",) and engine_id_owner(record.get("finding_id")) is not None:
                continue
            for member in ("section", "label"):
                require_unreserved_name(record["location"].get(member), format_path(segments + (index, "location", member)))


def _positional_location(path):
    return {"section": FOREIGN_SUBJECT, "page": None, "paragraph": None, "label": foreign_record_id(path)}


# Record lists whose entries may carry their own subject and are quarantined by a stand-in (#8.15): (path segments, ID
# member, the contract's required members with the fixed values a foreign record's stand-in takes; a callable takes the
# record's path). A foreign assertion keeps the contract's required members with fixed values that can never support it
# or clear a gate: no evidence, scope_aligned false, confidence 0, and map_assertion holds it (#8.15). findings[] and
# escalations[] entries are replaced by assertion_map's fixed hold instead (quarantine_foreign_upstream).
SUBJECT_RECORDS = (
    (("evidence_set",), "evidence_id", ()),
    (("deliverable", "brand_checks"), "check_id", (("legal_or_release_control", False),)),
    (("deliverable", "licensed_content"), "content_id", (("attribution_present", False),)),
    (("prior_findings",), "finding_id", (("claimed_closed", False), ("document_fix_present", False))),
    (("assertions",), "assertion_id", (("class", "factual"), ("text", FOREIGN_SUBJECT), ("location", _positional_location),
                                       ("evidence_ids", []), ("scope_aligned", False), ("confidence", 0.0),
                                       ("source", AM_ENGINE), ("citation", FOREIGN_SUBJECT))),
)


def _markers_only(value):
    """The engine markers a string carries, joined, with no supplied text; None when it carries none."""
    if not isinstance(value, str):
        return None
    markers = list(dict.fromkeys(marker_texts(value)))
    return " ".join(markers) if markers else None


def foreign_record_stand_in(item, subject, path, id_key, fixed):
    """The fixed stand-in of a record that names another engagement, deliverable or client (foreign_subject), else
    None. Only engine text survives: the ID becomes foreign_record_id(path) and each foreign subject FOREIGN_SUBJECT
    under the engine's constant member name (SUBJECT_FIELDS, never the supplied spelling), the contract's required
    members take `fixed` values, and every other member is dropped, nested objects included. Text the screen already
    withheld keeps only its engine marker, in its own member (a location keeps a fixed section and label), so its G8
    hold and #8.13 handling stand; an ID or subject that is exactly a marker stays that marker."""
    fields = foreign_subject(item, subject)
    if not fields:
        return None
    record_id = item.get(id_key)
    stand_in = {id_key: record_id if is_withheld(record_id) else foreign_record_id(path)}
    for constant in fields:
        stated = [value for key, value in item.items() if (subject_member(key) or (None,))[0] == constant]
        stand_in[constant] = next((_markers_only(value) for value in stated if _markers_only(value)), FOREIGN_SUBJECT)
    stand_in.update({key: copy.deepcopy(value(path) if callable(value) else value) for key, value in fixed})
    replaceable = {key for key, value in fixed if isinstance(value, str) or callable(value)}
    for key, value in item.items():
        if (key in stand_in and key not in replaceable) or subject_member(key) is not None:
            continue
        if contains_withheld(key):
            stand_in[key] = _markers_only(value) or FOREIGN_SUBJECT
        elif isinstance(value, str) and _markers_only(value):
            stand_in[key] = _markers_only(value)
        elif key == "location" and isinstance(value, dict):
            kept = {member: _markers_only(value.get(member)) for member in ("section", "label")}
            base = stand_in.get("location") if isinstance(stand_in.get("location"), dict) else {}
            if any(kept.values()):
                stand_in[key] = {"section": kept["section"] or FOREIGN_SUBJECT, "page": None, "paragraph": None,
                                 "label": kept["label"] or base.get("label") or FOREIGN_SUBJECT}
    return stand_in


def sanitise_foreign_records(payload):
    """Replace, in place, every linked record that names another engagement or deliverable (#8.15) by its fixed
    stand-in (foreign_record_stand_in), so none of its supplied ID, title, detail, citation, location or other field
    reaches any output, finding, escalation or the review packet; a shape-valid ID is not trusted once the record is
    foreign (quality-gate-criteria.md #8.15). An evidence_ids entry or best_evidence_id that named a replaced evidence
    item names its stand-in instead, so the assertion still resolves it as foreign. A stand-in is its own stand-in, so
    every stage that re-derives the document reproduces it exactly (#8.21). Returns the replaced paths."""
    subject = review_subject(payload)
    replaced, renamed = [], {}
    for segments, id_key, fixed in SUBJECT_RECORDS:
        records = payload
        for part in segments:
            records = records.get(part) if isinstance(records, dict) else None
        if not isinstance(records, list):
            continue
        for index, item in enumerate(records):
            path = f"{'.'.join(segments)}[{index}]"
            stand_in = foreign_record_stand_in(item, subject, path, id_key, fixed) if isinstance(item, dict) else None
            if stand_in is None or stand_in == item:
                continue
            if segments == ("evidence_set",) and key_of(item.get(id_key)) is not None and not contains_withheld(item.get(id_key)):
                renamed[key_of(item[id_key])] = stand_in[id_key]
            records[index] = stand_in
            replaced.append(path)
    if renamed:
        for section in EVIDENCE_REFERENCE_SECTIONS:
            for record in payload.get(section) or [] if isinstance(payload.get(section), list) else []:
                if not isinstance(record, dict):
                    continue
                if isinstance(record.get("evidence_ids"), list):
                    record["evidence_ids"] = [renamed.get(key_of(entry), entry) if not contains_withheld(entry) else entry
                                              for entry in record["evidence_ids"]]
                if key_of(record.get("best_evidence_id")) in renamed and not contains_withheld(record["best_evidence_id"]):
                    record["best_evidence_id"] = renamed[key_of(record["best_evidence_id"])]
    return replaced


# Upstream entries assertion_map replaces by a fixed hold when they name another engagement, deliverable or client
# (#8.15): kind -> (label, field path, location section). Only the kind and the position vary, so gate_check and
# severity_rank verify a hold exactly (am_foreign_hold_for) and a re-run reproduces it.
FOREIGN_HOLD_KINDS = {
    "finding": ("Reviewer finding", "findings", "Upstream findings"),
    "escalation": ("Escalation entry", "escalations", "Escalations"),
}
FOREIGN_HOLD_ID = re.compile(r"AM-G8-foreign-(finding|escalation)-([1-9][0-9]{0,8})")
FOREIGN_HOLD_KEY = re.compile(r"am g8 foreign (?:finding|escalation) [0-9]+")


def _foreign_where(kind, index):
    label, field, _ = FOREIGN_HOLD_KINDS[kind]
    return f"{label} {index + 1} ({field}[{index}])"


def am_foreign_hold(kind, index):
    """assertion_map's fixed G8 release blocker for the `kind` entry at `index` that names another engagement,
    deliverable or client (#8.15): positional only, with none of the entry's supplied fields."""
    where = _foreign_where(kind, index)
    return {"finding_id": f"AM-G8-foreign-{kind}-{index + 1}", "gate_id": "G8", "severity": "release_blocker",
            "title": f"{FOREIGN_HOLD_KINDS[kind][0]} belongs to another engagement or deliverable",
            "detail": f"{where}, supplied with the review input, names another engagement, deliverable or client than this review's (or one that cannot be verified), so it was replaced by this hold and none of its identifier, title, detail, location or other fields are shown; the reviewing partner/QRM must confirm or remove it before release.",
            "location": {"section": FOREIGN_HOLD_KINDS[kind][2], "page": None, "paragraph": None, "label": where},
            "criteria_section": "quality-gate-criteria.md #8.15", "confidence": 0.97, "source": AM_ENGINE,
            "citation": "quality-gate-criteria.md #8.15; severity-rules.md #1.1"}


def am_foreign_escalation(kind, index):
    where = _foreign_where(kind, index)
    return (f"G8: {where[0].lower()}{where[1:]} names another engagement, deliverable or client - release blocker; hold "
            "for reviewing partner/QRM (quality-gate-criteria.md #8.15)")


def am_foreign_hold_for(finding_id):
    """The fixed foreign-entry hold a finding ID names exactly (am_foreign_hold), else None."""
    match = FOREIGN_HOLD_ID.fullmatch(finding_id) if isinstance(finding_id, str) else None
    return am_foreign_hold(match.group(1), int(match.group(2)) - 1) if match else None


def quarantine_foreign_upstream(payload, raw_findings):
    """Replace, in place, every findings[] entry and every escalations[] object that names another engagement,
    deliverable or client (foreign_subject, any member at any depth) by assertion_map's fixed, positional hold, so none
    of its supplied ID, title, detail, location, citation or other field reaches any output, log or the review packet
    (quality-gate-criteria.md #8.15). A finding is replaced by its hold (am_foreign_hold) and its escalation is added;
    an escalation object is replaced by its fixed escalation (am_foreign_escalation). Returns every hold, for
    merge_recomputed_findings to reserve and, for an escalation, add. `raw_findings[i]` becomes the hold too, so
    ownership is read from the hold."""
    subject = review_subject(payload)
    findings = payload.get("findings") if isinstance(payload.get("findings"), list) else []
    escalations = payload.get("escalations") if isinstance(payload.get("escalations"), list) else []
    added = []
    for index, item in enumerate(findings):
        if isinstance(item, dict) and foreign_subject(item, subject):
            findings[index] = am_foreign_hold("finding", index)
            if index < len(raw_findings):
                raw_findings[index] = am_foreign_hold("finding", index)
            added.append(am_foreign_hold("finding", index))
            note = am_foreign_escalation("finding", index)
            if note not in escalations:
                escalations.append(note)
    for index, entry in enumerate(list(escalations)):
        if isinstance(entry, dict) and foreign_subject(entry, subject):
            escalations[index] = am_foreign_escalation("escalation", index)
            added.append(am_foreign_hold("escalation", index))
    return added


# Sections whose entries are quarantined above (SUBJECT_RECORDS, quarantine_foreign_upstream), and the members that
# define the review's own subject; require_no_foreign_subject checks every other member of the review input.
QUARANTINED_SECTIONS = {(): ("engagement_id", "deliverable", "evidence_set", "assertions", "prior_findings", "findings", "escalations"),
                        ("deliverable",): ("deliverable_id", "client_name", "client_aliases", "brand_checks", "licensed_content")}


def require_no_foreign_subject(payload):
    """Refuse the review input when a member outside the quarantined record lists names another engagement,
    deliverable or client (foreign_subject): the criteria object, provenance, a supplied derived section, the
    deliverable's other members, any top-level member or section outside the contract, at any depth. None of those is
    a record list whose entries may carry their own subject, so nothing can stand in for it; refusing at the first stage
    writes no output. The message names a contract section, or a fixed phrase, never the member or its value (#8.9,
    #8.15)."""
    subject = review_subject(payload)
    for scope, skipped in QUARANTINED_SECTIONS.items():
        container = payload.get(scope[0]) if scope else payload
        if not isinstance(container, dict):
            continue
        for key, value in container.items():
            if key in skipped or not foreign_subject({key: value}, subject):
                continue
            # The message names the engine's own constant for a contract section, never the supplied member name.
            where = ("deliverable" if scope else COMPARED_SECTIONS[COMPARED_SECTIONS.index(key)] if key in COMPARED_SECTIONS and isinstance(value, (dict, list))
                     else "a top-level member" if subject_member(key) is not None else "a section outside the contract")
            raise InputError(f"{where} names another engagement, deliverable or client than this review's, or one that "
                             "cannot be verified. Only the record lists of quality-gate-criteria.md #8.15 may carry their "
                             "own subject, and a foreign record there is quarantined; remove it from the review input "
                             "(quality-gate-criteria.md #8.15)")


_CONTRACT_SCHEMA = []
_JSON_TYPES = {
    "object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list), "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool), "null": lambda v: v is None, "number": is_number, "integer": is_integer,
}


def contract_schema():
    """The contract this skill ships (contracts/ next to scripts/), loaded once. A missing contract fails closed."""
    if not _CONTRACT_SCHEMA:
        try:
            with open(CONTRACT_PATH, encoding="utf-8") as handle:
                _CONTRACT_SCHEMA.append(json.load(handle))
        except OSError as exc:
            raise InputError(f"contract schema could not be loaded from the skill's contracts folder ({os_reason(exc)})") from None
        except ValueError as exc:
            raise InputError(f"contract schema in the skill's contracts folder is not valid JSON ({type(exc).__name__})") from None
    return _CONTRACT_SCHEMA[0]


_TYPE_PHRASES = {"object": "an object", "array": "an array", "string": "a string", "boolean": "true or false", "null": "null", "number": "a number", "integer": "an integer"}


def _type_phrase(types, node):
    """Plain-English expected type for a contract message, e.g. `an integer of 1 or more, or null`."""
    phrases = [f"an integer of {node['minimum']} or more" if name == "integer" and "minimum" in node else _TYPE_PHRASES[name] for name in types]
    if len(phrases) == 1:
        return phrases[0]
    joiner = ", or " if any(" or " in phrase for phrase in phrases) else " or "
    return joiner.join(phrases)


_ID_PATH = re.compile(r"_id$|_ids\[[0-9]+\]$")


def _is_position_path(path):
    return path.endswith((".location.page", ".location.paragraph"))


def _contract_errors(value, node, path, root):
    """Yield the first violation of `node` (a draft-07 subset: $ref, const, oneOf, type, enum, required, properties,
    items, minLength, pattern, minimum, maximum, and format: date-time checked by is_timestamp). x-unrecognised: hold marks an enum the gates judge themselves: any
    string or null passes here and the gate holds on an unrecognised value. x-normalise: provenance compares a source
    after normalise_provenance, as the evidence rule does."""
    if "$ref" in node:
        node = root["definitions"][node["$ref"].rsplit("/", 1)[-1]]
    if "const" in node and value != node["const"]:
        yield f"{path} must be the constant {node['const']}, got {describe(value)}"
        return
    if "oneOf" in node:
        if sum(1 for option in node["oneOf"] if next(_contract_errors(value, option, path, root), None) is None) != 1:
            yield f"{path} has the wrong shape (expected exactly one of {', '.join(str(option.get('type')) for option in node['oneOf'])}), got {describe(value)}"
        return
    types = node.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        if not any(_JSON_TYPES[name](value) for name in types):
            yield f"{path} must be {_type_phrase(types, node)}, got {describe(value)}" + (f"; {PAGE_LABEL_HINT}" if _is_position_path(path) else "")
            return
    if "enum" in node and value not in node["enum"]:
        if node.get("x-unrecognised") == "hold":
            if not (value is None or isinstance(value, str)):
                yield f"{path} must be a string or null, got {describe(value)}"
        else:
            yield f"{path} must be one of {', '.join(node['enum'])}, got {describe(value)}"
        return
    if isinstance(value, str):
        if node.get("format") == "date-time":
            # Checked before the withheld skip: a genuine timestamp never trips the screen, so a marker here is not one.
            if not is_timestamp(value):
                yield f"{path} must be an ISO-8601 (RFC 3339) date-time such as 2026-10-01T00:00:00Z, got {describe(value)}"
            return
        if is_withheld(value):
            # Withheld marker: the embedded-instruction screen replaced text that was validated raw before withholding.
            return
        if len(value.strip()) < node.get("minLength", 0):
            yield f"{path} must be a non-blank string"
        elif node.get("minLength") and _ID_PATH.search(path) and key_of(value) is None:
            # A blank key names nothing and must never equal another blank key in a join (#8.17).
            yield f"{path} is blank after Unicode, case and separator folding; IDs must state a value"
        elif "pattern" in node:
            candidate = normalise_provenance(value) if node.get("x-normalise") == "provenance" else value
            if not re.search(node["pattern"], candidate):
                yield f"{path} ({describe(value)}) does not match the contract format {node['pattern']}"
    elif is_number(value):
        if value < node.get("minimum", value) or value > node.get("maximum", value):
            if "maximum" not in node:
                yield f"{path} must be {node['minimum']} or more, got a number below that"
            else:
                yield f"{path} must be between {node.get('minimum')} and {node.get('maximum')}, got a number outside that range"
    elif isinstance(value, dict):
        for field in node.get("required", ()):
            if field not in value:
                yield f"{path} is missing required field {field}"
                return
        properties = node.get("properties", {})
        if properties:
            # A member that differs from a contract field only in case, Unicode form or separators would be ignored
            # by every exact lookup while looking like that field to a reader (quality-gate-criteria.md #8.11).
            canonical = {canonical_id(name): name for name in properties}
            for member in value:
                if member not in properties and canonical_id(member) in canonical:
                    yield f"{path}.{path_key(member)} is a variant spelling of the contract field {canonical[canonical_id(member)]}; use the exact field name"
                    return
        for field, child in properties.items():
            if field in value:
                yield from _contract_errors(value[field], child, f"{path}.{field}", root)
    elif isinstance(value, list) and "items" in node:
        for index, item in enumerate(value):
            yield from _contract_errors(item, node["items"], f"{path}[{index}]", root)


def validate_contract(payload, stage):
    """Check the whole payload against the contract at engine entry; raise InputError on the first violation."""
    schema = contract_schema()
    error = next(_contract_errors(payload, schema, "$", schema), None)
    if error is None:
        missing = [key for key in STAGE_REQUIRED[stage] if key not in payload]
        if missing:
            error = f"$ is missing {', '.join(missing)}, which {stage} requires (see the contract descriptions)"
    if error is not None:
        raise InputError(f"contract violation: {error}")
    validate_unique_ids(payload)
    return payload


# Every array an engine indexes or matches by ID (quality-gate-criteria.md #8.11). gate_results (one entry per gate) is
# checked by severity_rank's reconciliation; findings[] allows identical copies, which collapse (severity-rules.md #3.4).
ID_KEYED_ARRAYS = (
    (("assertions",), "assertion_id"),
    (("evidence_set",), "evidence_id"),
    (("assertion_mappings",), "assertion_id"),
    (("deliverable", "brand_checks"), "check_id"),
    (("deliverable", "licensed_content"), "content_id"),
    (("prior_findings",), "finding_id"),
    (("findings",), "finding_id"),
    (("ranked_findings",), "finding_id"),
)


def require_unique_ids(items, label, id_key, allow_identical=False, prefix="", skip=None):
    """Refuse two entries whose IDs are equal exactly or after the detector's fold (Unicode, case, separators), so a
    lookup keyed by ID can never let one entry overwrite or mask another. With allow_identical, entries that are equal
    in every field are not a conflict: nothing differs, so nothing can be hidden. The message names positions only."""
    positions = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get(id_key), str) or (skip and skip(item)):
            continue
        key = canonical_id(item[id_key])
        if key in positions:
            first = positions[key]
            if allow_identical and items[first] == item:
                continue
            raise InputError(f"{prefix}{label}[{index}].{id_key} duplicates {label}[{first}].{id_key} (equal exactly or after Unicode, case and separator folding); IDs must be unique so no entry can overwrite or mask another")
        positions[key] = index


# Lists of keys an engine matches entries against (quality-gate-criteria.md #8.11, #8.17). A repeat is refused like a
# repeated ID, so one key can never count twice or stand in for another: evidence_ids within each assertion and
# mapping, and these deliverable lists.
EVIDENCE_REFERENCE_SECTIONS = ("assertions", "assertion_mappings")
DELIVERABLE_KEY_LISTS = ("required_language", "present_language", "present_disclaimer_types", "client_aliases")


def require_unique_keys(values, label):
    """Refuse two entries of a key list that are equal exactly or after the canonical fold. Withheld markers are
    skipped: every copy of one flagged text carries the same marker, and the screen already holds it (#8.13)."""
    positions = {}
    for index, value in enumerate(values):
        if contains_withheld(value):
            continue
        key = key_of(value)
        if key is None:
            continue
        if key in positions:
            raise InputError(f"contract violation: {label}[{index}] duplicates {label}[{positions[key]}] (equal exactly or after Unicode, case and separator folding); each entry must be unique so none can count twice or mask another")
        positions[key] = index


def validate_unique_keys(payload):
    for field in EVIDENCE_REFERENCE_SECTIONS:
        items = payload.get(field)
        for index, item in enumerate(items if isinstance(items, list) else []):
            if isinstance(item, dict) and isinstance(item.get("evidence_ids"), list):
                require_unique_keys(item["evidence_ids"], f"{field}[{index}].evidence_ids")
    deliverable = payload.get("deliverable")
    for field in DELIVERABLE_KEY_LISTS:
        if isinstance(deliverable, dict) and isinstance(deliverable.get(field), list):
            require_unique_keys(deliverable[field], f"deliverable.{field}")


def validate_unique_ids(payload):
    validate_unique_keys(payload)
    for path, id_key in ID_KEYED_ARRAYS:
        items = payload
        for part in path:
            items = items.get(part) if isinstance(items, dict) else None
        if isinstance(items, list):
            # An engine-owned finding ID (AM-, GC-, SR-) is not refused for colliding: every stage recomputes engine
            # findings, keeps the genuine one and holds any other copy as a spoof (quality-gate-criteria.md #8.4).
            skip = (lambda item: engine_id_owner(item.get(id_key)) is not None) if path == ("findings",) else None
            require_unique_ids(items, ".".join(path), id_key, allow_identical=path == ("findings",), prefix="contract violation: ", skip=skip)


def contains_withheld(value):
    """True when value is a string carrying a withheld marker. Withheld text decides nothing
    (quality-gate-criteria.md #8.13): no rule reads it to match evidence, satisfy a requirement, identify the client,
    place a finding or set a severity. It produces the G8 hold and nothing else. This is the one predicate for both
    sides: every rule that sets text aside uses it, and instruction_hits raises a G8 hit for every string it is true of
    (an exact marker, a forged marker, or an embedded marker whose exact twin is itself a hit), so setting text aside
    can never lower a verdict without a G8 release blocker (#8.7)."""
    return isinstance(value, str) and WITHHELD_PATTERN.search(value) is not None


def marker_texts(value):
    """Every marker-shaped substring of value, in order."""
    return [match.group(0) for match in WITHHELD_PATTERN.finditer(value)] if isinstance(value, str) else []


def exact_markers(payload):
    """Every string in payload (member names included) that is exactly a withheld marker."""
    return {text for _, text in iter_strings(payload, "$") if is_withheld(text)}


def forged_marker(value, emitted):
    """True when value carries a marker-shaped substring the engines cannot have produced (quality-gate-criteria.md
    #8.7). In the raw review input (emitted is None) every marker, exact or embedded, is forged: only an engine
    withholds text. At a later stage an exact marker is accepted as an engine marker (and is itself a G8 hit), and a
    marker inside a longer string is genuine only when the same marker also stands alone in the payload (`emitted`, from
    exact_markers), as the engines' embedded replacement always leaves it. Anything else is tampering and a G8 hold."""
    if not contains_withheld(value):
        return False
    if emitted is None:
        return True
    return not is_withheld(value) and any(marker not in emitted for marker in marker_texts(value))


def is_withheld_reference(evidence_by_id, evidence_id):
    """True when an evidence_ids entry, or the evidence_id it resolves to, was withheld (#8.13). Every copy of one
    flagged text carries the same marker, so without this a withheld reference would still link to withheld evidence."""
    if contains_withheld(evidence_id):
        return True
    item = evidence_for(evidence_by_id, evidence_id)
    return item is not None and contains_withheld(item.get("evidence_id"))


def withheld_references(assertion, evidence_by_id):
    return [eid for eid in assertion.get("evidence_ids") or [] if is_withheld_reference(evidence_by_id, eid)]


def is_foreign_reference(evidence_by_id, evidence_id, subject):
    """True when an evidence_ids entry resolves to an evidence item that names another engagement or deliverable (#8.15)."""
    if is_withheld_reference(evidence_by_id, evidence_id):
        return False
    return bool(foreign_subject(evidence_for(evidence_by_id, evidence_id), subject))


def foreign_references(assertion, evidence_by_id, subject):
    return [eid for eid in assertion.get("evidence_ids") or [] if is_foreign_reference(evidence_by_id, eid, subject)]


def linked_evidence(assertion, evidence_by_id, subject=None):
    """The evidence items an assertion's references resolve to. A withheld reference never links (#8.13), and neither
    does evidence of another engagement or deliverable (#8.15); either makes the declared support unverifiable (classify)."""
    found = (evidence_for(evidence_by_id, eid) for eid in assertion.get("evidence_ids") or []
             if not is_withheld_reference(evidence_by_id, eid) and not is_foreign_reference(evidence_by_id, eid, subject))
    return [item for item in found if item is not None]


def evidence_relevance(assertion, evidence):
    by_type = RELEVANCE_BY_CLASS.get(assertion.get("class"), {})
    return by_type.get(evidence.get("type", "unknown"), 2)


def normalise_provenance(source):
    """Fold presentation differences a model-driven ingest may introduce: surrounding whitespace, case, and internal
    whitespace runs (to `-`), so `Connector:Engagement Workspace` reads as `connector:engagement-workspace`.
    Case adds no trust, because any lower-case slug is accepted. Returns None for a non-string."""
    if not isinstance(source, str):
        return None
    prefix, separator, slug = source.strip().partition(":")
    if not separator:
        return source.strip().lower()
    return f"{prefix.strip().lower()}:{'-'.join(slug.lower().split())}"


def recognised_provenance(evidence):
    """True only for ingest provenance after normalisation: `connector:<slug>` or an ingest skill tag (quality-gate-criteria.md #1.5)."""
    source = normalise_provenance(evidence.get("source"))
    if source is None:
        return False
    if source in EVIDENCE_SOURCE_SKILLS:
        return True
    slug = source[len(EVIDENCE_SOURCE_CONNECTOR_PREFIX):] if source.startswith(EVIDENCE_SOURCE_CONNECTOR_PREFIX) else ""
    return bool(slug) and slug[0].isalnum() and set(slug) <= CONNECTOR_SLUG_CHARS


def acceptable_support(assertion, evidence):
    return recognised_provenance(evidence) and evidence.get("type") in SUPPORT_TYPES_BY_CLASS.get(assertion.get("class"), ())


def evidence_type_label(ev_type):
    return ev_type if ev_type in EVIDENCE_TYPES else "a missing or unrecognised evidence type"


def best_evidence(assertion, linked_items):
    if not linked_items:
        return None
    return max(linked_items, key=lambda item: (acceptable_support(assertion, item), recognised_provenance(item), evidence_relevance(assertion, item), item.get("confidence", 0.0)))


def linked_evidence_citation(assertion, evidence_by_id, subject=None):
    citations = []
    for evidence_id in assertion.get("evidence_ids") or []:
        if is_withheld_reference(evidence_by_id, evidence_id):
            citations.append("withheld linked evidence reference (not used)")
            continue
        if is_foreign_reference(evidence_by_id, evidence_id, subject):
            citations.append("linked evidence of another engagement or deliverable (not used)")
            continue
        evidence = evidence_for(evidence_by_id, evidence_id)
        citations.append(evidence.get("citation", f"evidence {evidence_id}") if evidence else f"missing linked evidence {evidence_id}")
    return "; ".join(citations) if citations else "no linked evidence found"


def location_label(location):
    return f"p{location.get('page')}, {location.get('section')}, paragraph {location.get('paragraph')}"


def is_definitive_conclusion(assertion):
    if assertion.get("limitation_present") is True:
        return False
    text = assertion.get("text", "")
    # Withheld text is never read for keywords (#8.13); only the structured flags decide.
    text = "" if contains_withheld(text) or not isinstance(text, str) else text.lower()
    definitive_terms = (" should ", "we conclude", "will ", "all ", "full ", "estate-wide", "applies across", "national ")
    return (
        assertion.get("hedging_present") is not True
        or assertion.get("scope_aligned") is False
        or assertion.get("population_size") is not None
        or any(term in f" {text} " for term in definitive_terms)
    )


FOREIGN_SUPPORT_SECTION = "quality-gate-criteria.md #1.1; quality-gate-criteria.md #8.15"
FOREIGN_ASSERTION_SECTION = "quality-gate-criteria.md #8.15"
FOREIGN_ASSERTION_RATIONALE = ("The assertion names another engagement, deliverable or client than this review's (or one that "
                               "cannot be verified), so it was replaced by a positional stand-in, is not reviewed against "
                               "this deliverable's evidence and its text is not shown; hold for reviewing partner/QRM")


def foreign_rationale(foreign_ids):
    return (f"{len(foreign_ids)} linked evidence item(s) name another engagement or deliverable (engagement_id, "
            "deliverable_id or client differs from this review's, or cannot be verified), so they are not used and the declared "
            "support cannot be verified; hold for reviewing partner/QRM")


def classify(assertion, evidence, missing_ids=(), withheld_ids=(), foreign_ids=()):
    klass = assertion.get("class")
    if foreign_ids:
        # Evidence of another engagement or deliverable is never a basis for this review (quality-gate-criteria.md #8.15).
        confidence = 0.0 if evidence is None else min(float(assertion.get("confidence", 0.0)), float(evidence.get("confidence", 0.0)))
        return "unsupported", confidence, foreign_rationale(foreign_ids), FOREIGN_SUPPORT_SECTION
    if evidence is None:
        if not assertion.get("evidence_ids"):
            return "unsupported", 0.0, "No evidence IDs were linked to the assertion", "quality-gate-criteria.md #1.1"
        if withheld_ids:
            # A withheld reference is never matched (quality-gate-criteria.md #8.13), so the declared support cannot be verified.
            return "unsupported", 0.0, f"{len(withheld_ids)} linked evidence ID(s) were withheld by the embedded-instruction screen and no other linked evidence was found, so the declared support cannot be verified", "quality-gate-criteria.md #1.1; quality-gate-criteria.md #8.13"
        return "unsupported", 0.0, "No linked evidence item was found in the evidence index", "quality-gate-criteria.md #1.1"
    confidence = min(float(assertion.get("confidence", 0.0)), float(evidence.get("confidence", 0.0)))
    if missing_ids:
        # Declared support must exist: a dangling evidence reference is never ignored (quality-gate-criteria.md #1.1).
        return "unsupported", confidence, f"{len(missing_ids)} linked evidence ID(s) are not in the evidence index, so the declared support cannot be verified", "quality-gate-criteria.md #1.1"
    if withheld_ids:
        # Like a dangling reference, a withheld one is never ignored and never matched (#1.1, #8.13).
        return "unsupported", confidence, f"{len(withheld_ids)} linked evidence ID(s) were withheld by the embedded-instruction screen, so the declared support cannot be verified", "quality-gate-criteria.md #1.1; quality-gate-criteria.md #8.13"
    if not recognised_provenance(evidence):
        # A type or confidence the evidence item declares about itself proves nothing without ingest provenance.
        return "unsupported", confidence, "No linked evidence item has recognised provenance (connector:<slug>, skill:deliverable-ingest or skill:criteria-retrieve); missing, unrecognised or self-declared sources cannot establish support", "quality-gate-criteria.md #1.5"
    ev_type = evidence.get("type")
    if klass == "quantified":
        if ev_type not in TRACEABLE_QUANTIFIED_TYPES:
            return "unsupported", confidence, f"Quantified claim cites {evidence_type_label(ev_type)}, not traceable analysis or signed data", "quality-gate-criteria.md #1.2; severity-rules.md #2.3"
        if confidence < QUANTIFIED_CONFIDENCE_FLOOR:
            return "unsupported", confidence, f"Quantified support confidence {confidence:.2f} below {QUANTIFIED_CONFIDENCE_FLOOR:.2f}", "severity-rules.md #2.3"
        return "supported", confidence, "Quantified claim supported by traceable analytical evidence", "quality-gate-criteria.md #1.2"
    if klass == "factual":
        if ev_type not in FACTUAL_SUPPORT_TYPES or confidence < EVIDENCE_CONFIDENCE_FLOOR:
            return "unsupported", confidence, f"Factual claim support is {evidence_type_label(ev_type)} at confidence {confidence:.2f}; factual support must be a documented source type stronger than stakeholder recollection at or above {EVIDENCE_CONFIDENCE_FLOOR:.2f}", "quality-gate-criteria.md #1.1; severity-rules.md #2.2"
        return "supported", confidence, "Factual claim has cited evidence above the support floor", "quality-gate-criteria.md #1.1"
    if klass == "forward_looking":
        if assertion.get("hedging_present") is not True or assertion.get("limitation_present") is not True:
            return "limited", confidence, "Forward-looking statement lacks required hedging or limitation", "quality-gate-criteria.md #1.3"
        if ev_type not in FORWARD_LOOKING_SUPPORT_TYPES:
            return "limited", confidence, f"Forward-looking statement cites {evidence_type_label(ev_type)}, which is not accepted support", "quality-gate-criteria.md #1.3"
        if confidence < FORWARD_LOOKING_CONFIDENCE_FLOOR:
            return "limited", confidence, f"Forward-looking support confidence {confidence:.2f} below {FORWARD_LOOKING_CONFIDENCE_FLOOR:.2f}", "quality-gate-criteria.md #1.3"
        return "supported", confidence, "Forward-looking statement is hedged and limitation is stated", "quality-gate-criteria.md #1.3"
    if klass == "recommendation":
        sample_size = assertion.get("sample_size")
        if assertion.get("stated_basis") is not True:
            return "unsupported", confidence, "Recommendation has no stated basis", "quality-gate-criteria.md #1.4"
        if ev_type not in RECOMMENDATION_SUPPORT_TYPES:
            return "unsupported", confidence, f"Recommendation cites {evidence_type_label(ev_type)}, not evidence proportionate to a recommendation", "quality-gate-criteria.md #1.4"
        if sample_size is not None and sample_size < MIN_RECOMMENDATION_SAMPLE_SIZE and assertion.get("limitation_present") is not True:
            criteria = "quality-gate-criteria.md #1.4; quality-gate-criteria.md #3.2"
            rationale = f"Recommendation uses sample size {sample_size}, below {MIN_RECOMMENDATION_SAMPLE_SIZE}, without a limitation"
            if is_definitive_conclusion(assertion):
                criteria += "; severity-rules.md #1.1"
                rationale += " and is framed as a definitive conclusion"
            return "unsupported", confidence, rationale, criteria
        if confidence < RECOMMENDATION_CONFIDENCE_FLOOR:
            return "limited", confidence, f"Recommendation support confidence {confidence:.2f} below {RECOMMENDATION_CONFIDENCE_FLOOR:.2f}", "quality-gate-criteria.md #1.4"
        return "supported", confidence, "Recommendation has a stated basis and proportionate support", "quality-gate-criteria.md #1.4"
    return "unsupported", 0.0, f"Unknown assertion class {klass}", "severity-rules.md #2.1"


def map_assertion(assertion, evidence_by_id, subject=None):
    """Return (mapping, AM finding or None, escalation or None) exactly as assertion_map emits them. `subject` is
    review_subject(payload): linked evidence of another engagement or deliverable is not used and holds (#8.15)."""
    evidence = best_evidence(assertion, linked_evidence(assertion, evidence_by_id, subject))
    withheld_ids = withheld_references(assertion, evidence_by_id)
    foreign_ids = foreign_references(assertion, evidence_by_id, subject)
    missing_ids = [eid for eid in assertion.get("evidence_ids") or [] if evidence_for(evidence_by_id, eid) is None and not is_withheld_reference(evidence_by_id, eid)]
    status, support_score, rationale, criteria_section = classify(assertion, evidence, missing_ids, withheld_ids, foreign_ids)
    # An assertion of another engagement, deliverable or client (its stand-in, sanitise_foreign_records) is never
    # reviewed as this deliverable's claim: it is unsupported and holds the release (quality-gate-criteria.md #8.15).
    foreign_assertion = bool(foreign_subject(assertion, subject))
    if foreign_assertion:
        evidence, status, support_score = None, "unsupported", 0.0
        rationale, criteria_section = FOREIGN_ASSERTION_RATIONALE, FOREIGN_ASSERTION_SECTION
    mapping = {
        "assertion_id": assertion["assertion_id"], "class": assertion["class"], "text": assertion["text"],
        "location": assertion["location"], "evidence_ids": assertion.get("evidence_ids") or [],
        "best_evidence_id": evidence.get("evidence_id") if evidence else None, "support_status": status,
        "support_score": round(support_score, 2), "rationale": rationale, "criteria_section": criteria_section,
        "confidence": round(support_score, 2), "source": AM_ENGINE,
        "citation": f"{assertion['citation']}; {linked_evidence_citation(assertion, evidence_by_id, subject)}; {criteria_section}"
    }
    if status not in {"unsupported", "limited"}:
        return mapping, None, None
    severity = "release_blocker" if foreign_ids or foreign_assertion or (
        status == "unsupported"
        and (assertion["class"] == "quantified" or is_definitive_conclusion(assertion))
    ) else "must_fix" if status == "unsupported" else "advisory"
    finding = {"finding_id": f"AM-{assertion['assertion_id']}", "gate_id": "G1", "severity": severity,
        "title": f"{assertion['class'].replace('_', ' ').title()} assertion is {status}", "detail": rationale,
        "location": assertion["location"], "criteria_section": criteria_section, "confidence": round(support_score, 2),
        "source": AM_ENGINE, "citation": mapping["citation"]}
    escalation = f"{assertion['assertion_id']} at {location_label(assertion['location'])}: {status} - {rationale} ({criteria_section})"
    return mapping, finding, escalation


# ---------------------------------------------------------------------------------------------------------------
# Embedded-instruction screening and withholding shared by every stage (quality-gate-criteria.md #8.1-#8.7).
# G8 screening runs through the vendored shared detector. DRQG vocabulary reaches it only through the hooks. The
# contract carries no client or firm e-mail/web domains, so trusted_domains stays empty and any send/forward verb
# aimed at an address or URL holds.
STEERING_HOOKS = dict(
    extra_verdict_words=("release ready", "ready for issue", "ready for release", "cleared for release", "quality gate passed"),
    extra_rule_nouns=("disclaimer requirement", "citation rules", "reliance clause", "reliance language", "disclaimer", "qrm",
                      "quality gate", "gate criteria", "g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8"),
    trusted_domains=(),
)
# Rule override aimed at a numbered criteria section (an override verb whose object is "section 8", Cowork evaluation
# matrix 2026-10-22-1252 FX-04). The detector's rule nouns name no section, and a hook noun "section" would also match
# navigation ("skip to section 4") through the detector's filler words, so this rule only adds a hit, on the detector's
# own clause lead, when the section reference is the override verb's direct object. Matched on the detector's
# normalised text, so look-alike letters and format characters cannot hide it (quality-gate-criteria.md #8.5).
SECTION_OVERRIDE = re.compile(sg._LEAD + r"(?:ignore|disregard|bypass|override|overrule|set\saside|forget|circumvent|skip|"
                              r"waive|suspend|turn\soff|disable)\s(?:(?:the|this|that|these|those|all|any|our|your)\s)?"
                              r"(?:(?:qrm|criteria|criterion|quality\sgate|gate|review)\s)?(?:sections?\s?#?|§\s?|#)\d")
OVERSIZE = "oversize"
SPLIT = "split"
INSTRUCTION = "instruction"
# Untrusted sections scanned verbatim. Every other section (assertion_mappings, findings, escalations,
# provenance) is derived from them and is scanned only for text that is not a copy of a primary field.
PRIMARY_SECTIONS = ("deliverable", "criteria", "assertions", "evidence_set", "prior_findings")
UNSCANNED_KEYS = {"contract_version"}  # validated against the contract version before any scan
AGGREGATE_LABEL = "(combined ID, text, evidence IDs, citation, evidence titles, location section and label)"
RECORD_LABEL = "(combined fields)"
# Every other record whose free text travels to an output is screened with its fields joined, as an assertion is
# (quality-gate-criteria.md #8.5): (path segments, members in reading order), "[]" marking an array of records,
# "location" standing for the location's section and label, and a string-list member (client_aliases, required_language,
# criteria_sections and the like) read as one field, its entries joined in order. IDs, closed enums, numbers, booleans
# and `source` tags are left out (an assertion's own ID and evidence IDs are joined, because the review packet renders
# them beside its text, assertion_records). assertion_mappings are engine copies of the assertion record and
# are rebuilt from it; escalation notes (strings or {gate_id, note}) are screened as runs of adjacent entries
# (array_runs). tests/run_tests.py fails when the contract gains a string or string-list member of one of these records
# that is neither listed here nor in RECORD_EXCLUDED.
RECORD_MEMBERS = (
    (("deliverable",), ("title", "version", "type", "client_name", "client_aliases", "intended_recipients",
                        "confidentiality_marking", "present_disclaimer_types", "required_language", "present_language",
                        "citation")),
    (("deliverable", "brand_checks", "[]"), ("title", "detail", "location", "citation")),
    (("deliverable", "licensed_content", "[]"), ("title", "detail", "location", "citation")),
    (("criteria",), ("criteria_sections", "citation")),
    (("evidence_set", "[]"), ("title", "citation")),
    (("prior_findings", "[]"), ("detail", "location", "citation")),
    (("findings", "[]"), ("title", "detail", "location", "criteria_section", "citation")),
    (("ranked_findings", "[]"), ("title", "detail", "location", "criteria_section", "citation", "ranking_basis")),
    (("gate_results", "[]"), ("name", "citation")),
    (("release_readiness",), ("summary", "citation")),
)
# String members of those records that are not joined, with the reason: identifiers and provenance tags are screened
# on their own and read as labels, never as prose.
RECORD_EXCLUDED = {
    "deliverable_id": "identifier", "engagement_id": "identifier", "check_id": "identifier", "content_id": "identifier",
    "evidence_id": "identifier", "finding_id": "identifier", "criteria_set_id": "identifier", "source": "provenance tag",
}
# Withheld markers (quality-gate-criteria.md #8.7). Numbered per distinct withheld text, so two different withheld
# identifiers never collide and every copy of one text carries the same marker at every stage.
WITHHELD_WORDING = {
    INSTRUCTION: "flagged by the embedded-instruction screen",
    OVERSIZE: "too long to screen for embedded instructions",
    SPLIT: "flagged with neighbouring fields by the embedded-instruction screen",
}
# Marker numbers are 1 to 9 digits, so reading one back (int) is always bounded; a longer number is not a marker.
WITHHELD_PATTERN = re.compile(r"\[withheld ([1-9][0-9]{0,8})(?: \((oversize|split)\))?: [a-z -]+; see the G8 finding\]")
MAX_MARKER_NUMBER = 999_999_999


def withheld_marker(number, kind=INSTRUCTION):
    qualifier = "" if kind == INSTRUCTION else f" ({kind})"
    return f"[withheld {number}{qualifier}: {WITHHELD_WORDING[kind]}; see the G8 finding]"


def withheld_kind(value):
    """INSTRUCTION, OVERSIZE or SPLIT when value is exactly a withheld marker, otherwise None."""
    match = WITHHELD_PATTERN.fullmatch(value) if isinstance(value, str) else None
    return (match.group(2) or INSTRUCTION) if match else None


def is_withheld(value):
    return withheld_kind(value) is not None


def _section_override(value):
    """SECTION_OVERRIDE as a detector hit on value's normalised text, or [] (the span is in normalised characters)."""
    match = SECTION_OVERRIDE.search(sg.normalize(value))
    return [sg.Hit("rule_override", match.start(), match.end())] if match else []


@functools.lru_cache(maxsize=4096)
def _screen_cached(value):
    return tuple(sg.scan(value, **STEERING_HOOKS)) or tuple(_section_override(value))


def screen_text(value):
    """steering_guard hits for one untrusted string, with the DRQG hooks and SECTION_OVERRIDE (cached: keys and IDs
    repeat)."""
    return list(_screen_cached(value)) if isinstance(value, str) else []


@functools.lru_cache(maxsize=16384)
def _screen_fields_cached(items):
    found = tuple(sg.scan_fields(dict(items), **STEERING_HOOKS))
    values = [value for _, value in items if isinstance(value, str) and value.strip()]
    if found or not values:
        return found
    # SECTION_OVERRIDE the way scan_fields reads a record: each field, then the ' ; ' and label-stripped joins (a field
    # that trips is returned as-is, a join that trips is one 'split' hit). The detector already held an over-long join.
    for value in values:
        found += tuple(_section_override(value))
    if found or len(values) < 2:
        return found
    for joined in (" ; ".join(values), " ".join(sg._LABEL.sub("", value).strip() for value in values)):
        hits = _section_override(joined)
        if hits:
            return (sg.Hit("split", hits[0].start, hits[0].end),)
    return ()


def screen_fields(fields):
    """steering_guard hits for a multi-field record; a 'split' hit means only the joined fields trip (cached: every
    stage re-screens the same assertions)."""
    return list(_screen_fields_cached(tuple(fields.items())))


def screen_record(fields):
    """screen_fields for a record, all fields joined in reading order and, when that does not trip and there are more
    than two fields, each pair of fields joined too, so a note split across two fields with another field between them
    is still caught (quality-gate-criteria.md #8.5). Returns the first hits found."""
    found = screen_fields(fields)
    if found or len(fields) < 3:
        return found
    items = list(fields.items())
    for first in range(len(items)):
        for second in range(first + 1, len(items)):
            found = screen_fields(dict((items[first], items[second])))
            if found:
                return found
    return []


def hit_reason(found):
    """OVERSIZE when the text was too long to screen, which is a hold (quality-gate-criteria.md #8.6), else INSTRUCTION."""
    return OVERSIZE if any(hit.family == OVERSIZE for hit in found) else INSTRUCTION


def suspicious_instruction(value):
    """True when the text trips the shared detector or is too long to screen (an oversize result is a hold)."""
    return bool(screen_text(value))


def safe_token(value, fallback):
    """A value named in engine-composed text: only an identifier of the documented shape (ID_TOKEN, #8.11) that passes
    the screen; anything else is named by `fallback`, a fixed or positional label (quality-gate-criteria.md #8.9)."""
    text = str(value)
    return text if ID_TOKEN.fullmatch(text) and not suspicious_instruction(text) else fallback


KEY_SUFFIX = " (field name)"
PAIR_SUFFIX = " (adjacent entries)"


def iter_strings(value, path):
    """Yield (path, text) for every string in value, member names included: a name is untrusted text too
    (quality-gate-criteria.md #8.5). Nothing below the top level is skipped, whatever its key (metadata, provenance or a
    nested contract_version alike)."""
    if isinstance(value, dict):
        for label, key, child in labelled_members(value):
            child_path = f"{path}.{label}"
            yield child_path + KEY_SUFFIX, key
            yield from iter_strings(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_strings(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def iter_arrays(value, path):
    """Yield (path, list) for every array in value, at any depth."""
    if isinstance(value, dict):
        for label, key, child in labelled_members(value):
            yield from iter_arrays(child, f"{path}.{label}")
    elif isinstance(value, list):
        yield path, value
        for index, child in enumerate(value):
            yield from iter_arrays(child, f"{path}[{index}]")


def top_level_sections(payload):
    """Yield (key, path, child, derived) for each top-level member except the validated contract_version."""
    for label, key, child in labelled_members(payload):
        if key in UNSCANNED_KEYS:
            continue
        yield key, f"$.{label}", child, not (key in PRIMARY_SECTIONS or not isinstance(child, (dict, list)))


def scan_sections(payload):
    """(primary, derived): lists of (path, text) for every untrusted string and member name, primary sections and
    top-level scalars first."""
    primary, derived = [], []
    for key, path, child, is_derived in top_level_sections(payload):
        target = derived if is_derived else primary
        target.append((path + KEY_SUFFIX, key))
        target.extend(iter_strings(child, path))
    return primary, derived


ARRAY_WINDOW = 8
ESCALATIONS_PATH = "$.escalations"


def run_slots(list_path, items):
    """(container, key) per array entry, as array_runs reads it: the entry itself, except that a {gate_id, note}
    escalation is read as its note, so a note split across adjacent escalations of either form is one text."""
    if list_path == ESCALATIONS_PATH:
        return [(item, "note") if isinstance(item, dict) else (items, index) for index, item in enumerate(items)]
    return [(items, index) for index in range(len(items))]


def slot_value(container, key):
    """The value a (container, key) slot holds, or None when the object has no such member."""
    return container.get(key) if isinstance(container, dict) else container[key]


def _entries(slots, first, last):
    """(fields, refs) for slots[first..last]: fields maps 'entry N' to the text, refs to the (container, key)."""
    names = [f"entry {index}" for index in range(first, last + 1)]
    chosen = slots[first:last + 1]
    return dict(zip(names, (slot_value(container, key) for container, key in chosen))), dict(zip(names, chosen))


def _run_trips(slots, first, last):
    return screen_fields(_entries(slots, first, last)[0])


def array_runs(payload, breaks):
    """Yield (path, fields, refs, derived, found) for each run of adjacent array entries that trips only when joined, so
    prose split across any number of entries is screened as one text (quality-gate-criteria.md #8.5).

    Entries for which breaks(value) is true (non-strings, blanks, and text already flagged or withheld) split an array
    into runs; an escalation object is read as its note (run_slots). Each run is screened in sliding windows of up to
    ARRAY_WINDOW entries, and, when it is longer than that, joined whole, so the cost stays linear in the array. A
    tripping window is narrowed to the entries the note needs (dropping an end entry stops the hit); a whole-run hit
    that no window shows withholds the whole run."""
    for _, path, child, derived in top_level_sections(payload):
        for list_path, items in iter_arrays(child, path):
            slots = run_slots(list_path, items)
            values = [slot_value(container, key) for container, key in slots]
            start = 0
            while start < len(values):
                if breaks(values[start]):
                    start += 1
                    continue
                end = start
                while end + 1 < len(values) and not breaks(values[end + 1]):
                    end += 1
                yield from _run_hits(list_path, slots, start, end, derived)
                start = end + 1


def _run_hits(list_path, slots, start, end, derived):
    if end == start:
        return
    first, flagged = start, False
    while first < end:
        last = min(first + ARRAY_WINDOW - 1, end)
        if _run_trips(slots, first, last):
            low, high = first, last
            while high - low > 1 and _run_trips(slots, low + 1, high):
                low += 1
            while high - low > 1 and _run_trips(slots, low, high - 1):
                high -= 1
            fields, refs = _entries(slots, low, high)
            flagged = True
            yield f"{list_path}[{low}]+[{high}]{PAIR_SUFFIX}", fields, refs, derived, screen_fields(fields)
            first = high + 1
            continue
        if last == end:
            break
        first += 1
    if not flagged and end - start + 1 > ARRAY_WINDOW:
        fields, refs = _entries(slots, start, end)
        found = screen_fields(fields)
        if found:
            yield f"{list_path}[{start}]+[{end}]{PAIR_SUFFIX}", fields, refs, derived, found


# Instructions split across a value that trips on its own and a clean neighbour (sg.split_partners, steering_guard
# 1.1.5). Text flagged alone is withheld under its own hold and left out of the joined screens, so without this the
# clean half of an instruction-override sentence split across two values reached the outputs. A sequence is screened
# in windows of PARTNER_WINDOW present values starting every PARTNER_STEP values, and only windows that hold flagged
# text, so the cost stays linear in the sequence; a withheld marker ends a sequence.
PARTNER_WINDOW = ARRAY_WINDOW
PARTNER_STEP = ARRAY_WINDOW // 2


@functools.lru_cache(maxsize=16384)
def _partners_cached(values):
    return frozenset(sg.split_partners(values, **STEERING_HOOKS))


# Raw characters kept at each end of an over-long value when a join is too long to screen whole (split_partner_positions).
PARTNER_EDGE = 4 * sg.WINDOW_OVERLAP


def _too_long(values):
    joined = " ; ".join(values)  # the longest of split_partners' joins
    return len(joined) > sg.MAX_TOTAL_CHARS or (not joined.isascii() and sg._nfkc_len_bound(joined) > sg.MAX_TOTAL_CHARS)


def _edges(value):
    """(head, tail) of a value longer than two PARTNER_EDGEs, or None for a shorter one or one whose head or tail
    normalises to fewer than 2 * sg.WINDOW_OVERLAP characters (format characters are stripped), which stays whole."""
    if len(value) <= 2 * PARTNER_EDGE:
        return None
    head, tail = value[:PARTNER_EDGE], value[-PARTNER_EDGE:]
    if min(len(sg.normalize(head)), len(sg.normalize(tail))) < 2 * sg.WINDOW_OVERLAP:
        return None
    return head, tail


def split_partner_positions(values, flagged, groups=()):
    """(partners, oversize) for a sequence of values in reading order with text flagged on its own at the positions in
    `flagged`: partners is every position a split instruction overlaps (sg.split_partners), flagged ones included, and
    every one of them is withheld; a clean neighbour is never exempted (over-withholding is the accepted failure).
    Non-strings, blanks and punctuation- or symbol-only values (_wordless) are absent: they neither break adjacency nor
    pad a split apart across windows. A value carrying a withheld marker ends a sequence.
    `groups` lists the positions of each field of a record: a flagged value is also joined alone with the first and
    last value of every other field, so a field between the two halves (an assertion's evidence IDs between its text
    and citation) does not hide the split, as screen_record joins each pair of fields. oversize is the positions of a
    join too long to screen (sg.split_partners then returns every value of it), which is a hold (#8.6)."""
    partners, oversize, segments, segment = set(), set(), [], []
    for position, value in enumerate(values):
        if not (isinstance(value, str) and value.strip()) or _wordless(value):
            continue
        if contains_withheld(value):
            segments.append(segment)
            segment = []
            continue
        segment.append(position)
    segments.append(segment)

    def screen(positions):
        chosen = tuple(values[position] for position in positions)
        if not _too_long(chosen):
            partners.update(positions[index] for index in _partners_cached(chosen))
            return
        # Too long to join whole: a hit across a value boundary reaches at most sg.WINDOW_OVERLAP normalised characters
        # (plus the DRQG hook words) into a value, so an over-long value takes part only through its edges; its middle
        # is screened in full when the value is screened on its own, and a value that trips there is flagged. It is cut
        # into its head, which ends the joins before it, and its tail, which starts the joins after it. A value whose
        # edges normalise too short to cover that reach stays whole, and a join still too long to screen holds its
        # values as oversize (#8.6).
        pieces, current = [], []
        for position, value in zip(positions, chosen):
            edges = _edges(value)
            if edges is None:
                current.append((position, value))
                continue
            current.append((position, edges[0]))
            pieces.append(current)
            current = [(position, edges[1])]
        pieces.append(current)
        for piece in pieces:
            if len(piece) < 2:
                continue
            places, texts = [position for position, _ in piece], tuple(text for _, text in piece)
            found = {places[index] for index in _partners_cached(texts)}
            if _too_long(texts):
                oversize.update(found)
            partners.update(found)

    for segment in segments:
        if len(segment) < 2 or flagged.isdisjoint(segment):
            continue
        for start in dict.fromkeys(list(range(0, len(segment) - PARTNER_WINDOW, PARTNER_STEP)) + [max(len(segment) - PARTNER_WINDOW, 0)]):
            window = segment[start:start + PARTNER_WINDOW]
            if not flagged.isdisjoint(window):
                screen(window)
    usable = {position for segment in segments for position in segment}
    edges = [[position for position in group if position in usable] for group in groups]
    # A split across two fields joins the end of one to the start of the other, so only a flagged value at an edge of
    # its own field can be one half of it.
    own_edges = {group[index] for group in edges if group for index in (0, -1)}
    for position in sorted(flagged & usable):
        if groups and position not in own_edges:
            continue
        for group in edges:
            if group and position not in group:
                for other in dict.fromkeys((group[0], group[-1])):
                    screen(sorted((position, other)))
    return partners, oversize


def position_runs(positions):
    """Maximal runs (first, last) of consecutive integers in `positions`."""
    runs = []
    for position in sorted(positions):
        if runs and runs[-1][1] == position - 1:
            runs[-1][1] = position
        else:
            runs.append([position, position])
    return [tuple(run) for run in runs]


def run_path(list_path, first, last):
    """The hit path for array entries first..last, as _array_hits names a run."""
    return f"{list_path}[{first}]+[{last}]{PAIR_SUFFIX}" if last > first else f"{list_path}[{first}]"


def collect_scan_text(payload):
    """Yield (path, text, derived) for every untrusted string, primary sections first.

    Every string is yielded verbatim, including citation fields; nothing is stripped before screening
    (quality-gate-criteria.md #8.5). A derived string that is exactly equal to a primary string is a copy
    (for example assertion_mappings[].text) and is not yielded again."""
    primary, derived = scan_sections(payload)
    for path, text in primary:
        yield path, text, False
    copies = {text for _, text in primary}
    for path, text in derived:
        if text not in copies:
            yield path, text, True


def assertion_records(payload):
    """Yield (path, fields, refs) per assertion: fields maps the assertion ID, text, evidence IDs, citation, linked
    evidence titles and the location section and label (in reading order, non-blank strings only) to their values, and
    refs maps the same names to the (container, key) holding each value. The ID, text, evidence IDs and citation are
    the order the review packet renders a mapping in (quality-gate-criteria.md #8.22), so an ID that completes a
    sentence with the text is withheld here, before any finding ID or escalation is built from it. Only assertions with
    more than one such field are yielded."""
    evidence = {key_of(item["evidence_id"]): item for item in payload.get("evidence_set") or [] if isinstance(item, dict) and key_of(item.get("evidence_id")) is not None}
    for index, assertion in enumerate(payload.get("assertions") or []):
        if not isinstance(assertion, dict):
            continue
        refs = {"assertion id": (assertion, "assertion_id"), "text": (assertion, "text")}
        evidence_ids = assertion.get("evidence_ids") if isinstance(assertion.get("evidence_ids"), list) else []
        for position in range(len(evidence_ids)):
            refs[f"evidence id {position + 1}"] = (evidence_ids, position)
        refs["citation"] = (assertion, "citation")
        for position, evidence_id in enumerate(evidence_ids):
            # The same canonical lookup map_assertion uses, so every title that can support a claim is screened with it.
            linked = evidence_for(evidence, evidence_id)
            if isinstance(linked, dict):
                refs[f"evidence title {position + 1}"] = (linked, "title")
        location = assertion.get("location")
        if isinstance(location, dict):
            refs["location section"] = (location, "section")
            refs["location label"] = (location, "label")
        fields = _present(refs)
        if len(fields) > 1:
            yield f"$.assertions[{index}] {AGGREGATE_LABEL}", fields, refs


def _present(refs):
    """The non-blank string values refs points to, by name; refs keeps only those names."""
    fields = {}
    for name, (container, key) in list(refs.items()):
        value = slot_value(container, key)
        if isinstance(value, str) and value.strip():
            fields[name] = value
        else:
            del refs[name]
    return fields


def _records_at(value, segments, path):
    """Yield (path, record) for each object RECORD_MEMBERS' path segments reach from value."""
    if not segments:
        if isinstance(value, dict):
            yield path, value
        return
    head, rest = segments[0], segments[1:]
    if head == "[]":
        for index, item in enumerate(value if isinstance(value, list) else []):
            yield from _records_at(item, rest, f"{path}[{index}]")
    elif isinstance(value, dict):
        yield from _records_at(value.get(head), rest, f"{path}.{head}")


def record_refs(record, members, base):
    """refs for a record's joined members in reading order: name -> [(container, key, path)], location as section and
    label, a string-list member as one name holding each entry's slot."""
    refs = {}
    for member in members:
        value = record.get(member)
        if member == "location":
            if isinstance(value, dict):
                refs["location section"] = [(value, "section", f"{base}.location.section")]
                refs["location label"] = [(value, "label", f"{base}.location.label")]
        elif isinstance(value, list):
            refs[member.replace("_", " ")] = [(value, index, f"{base}.{member}[{index}]") for index in range(len(value))]
        else:
            refs[member.replace("_", " ")] = [(record, member, f"{base}.{member}")]
    return refs


def record_fields(refs, keep):
    """(fields, kept) for a record: fields maps each name to its non-blank string text that keep(value) accepts (a list
    member's accepted entries joined with ' ; ' in order), kept maps the same names to the slots that text came from."""
    fields, kept = {}, {}
    for name, slots in refs.items():
        chosen = [(slot, slot_value(slot[0], slot[1])) for slot in slots]
        chosen = [(slot, value) for slot, value in chosen if isinstance(value, str) and value.strip() and keep(value)]
        if chosen:
            fields[name] = " ; ".join(value for _, value in chosen)
            kept[name] = [slot for slot, _ in chosen]
    return fields, kept


def other_records(payload):
    """Yield (path, refs, derived) for every record other than an assertion (RECORD_MEMBERS), primary sections first, so
    steering split across a record's fields that no single field contains is caught (quality-gate-criteria.md #8.5)."""
    for segments, members in RECORD_MEMBERS:
        for base, record in _records_at(payload, segments, "$"):
            yield f"{base} {RECORD_LABEL}", record_refs(record, members, base), segments[0] not in PRIMARY_SECTIONS


def assertion_fields(payload):
    """Yield (path, fields) per assertion: text, citation, linked evidence titles and the location label in reading
    order. scan_fields screens them together so steering split across fields (quality-gate-criteria.md #8.5) that no
    single field contains is caught."""
    for path, fields, _ in assertion_records(payload):
        yield path, fields


def instruction_hits(payload):
    """(path, reason) for every untrusted string or member name that trips the detector or carries a withheld marker,
    then for each primary record (other_records), each assertion and each derived record whose fields trip only when
    joined, then for each run of adjacent array entries that trip only when joined (so one note is never counted twice).

    Text withheld at an earlier stage stays a hit: a primary instruction/oversize marker is a field hit, split markers
    across a record's fields are that record's combined hit, a split marker on any of an assertion's fields is that
    assertion's combined hit (unless a record already counted it), a run of split-marked array entries is one hit,
    any other split marker is a hit of its own, and a derived string that is exactly a marker (and not a copy of a
    primary string) is a hit. A derived string that merely contains a marker or embeds tripped primary text is the same
    note and is not counted again (quality-gate-criteria.md #8.1-#8.7)."""
    hits, tripped, pending_split = [], set(), []
    emitted = exact_markers(payload)
    # A split marker in a derived record's member or an escalation note is counted with its record or run below.
    grouped = {path for _, refs, derived in other_records(payload) if derived for slots in refs.values() for _, _, path in slots}
    for path, text, derived in collect_scan_text(payload):
        kind = withheld_kind(text)
        if kind == SPLIT and (not derived or path.endswith("]") or path in grouped or is_escalation_note(path)):
            pending_split.append((path, text))
            continue
        if kind:
            reason = OVERSIZE if kind == OVERSIZE else INSTRUCTION
        elif forged_marker(text, emitted):
            # A marker the engines cannot have produced (embedded with no exact twin): tampering, held under G8 (#8.7).
            reason = INSTRUCTION
        else:
            found = screen_text(text)
            if not found:
                continue
            # De-duplication happens only after the whole derived string has tripped: it is the same note when it
            # embeds a primary field that already raised a G8 hit, so the run is held either way.
            if derived and any(source in text for source in tripped):
                continue
            reason = hit_reason(found)
        hits.append((path, reason))
        if not derived:
            tripped.add(text)
    covered = set()
    # Primary records first: a split marker on an evidence title may be its evidence record's note, not the assertion's.
    record_hits, held = _record_hits(payload, tripped, covered, derived=False)
    hits.extend(record_hits)
    # Split markers beside text flagged on its own, on an assertion or a primary record (_record_hits), are withheld under
    # that text's hold (withhold_untrusted) and are not counted again on their own, nor as array runs (evidence IDs).
    beside = {value for _, fields in assertion_fields(payload) if tripped.intersection(fields.values())
              for value in fields.values() if withheld_kind(value) == SPLIT}
    covered.update(beside)
    for path, fields in assertion_fields(payload):
        if tripped.intersection(fields.values()):
            continue
        splits = [value for value in fields.values() if withheld_kind(value) == SPLIT]
        if splits:
            if not set(splits) <= held:
                hits.append((path, INSTRUCTION))
            covered.update(splits)
            continue
        found = screen_record(fields)
        if found:
            hits.append((path, hit_reason(found)))
    record_hits, derived_held = _record_hits(payload, tripped, covered, derived=True)
    hits.extend(record_hits)
    hits.extend(_array_hits(payload, tripped, covered, held | derived_held | beside))
    hits.extend((path, INSTRUCTION) for path, text in pending_split if text not in covered)
    return hits


def is_escalation_note(path):
    return path.startswith(ESCALATIONS_PATH + "[") and path.endswith("].note")


def unflagged(tripped):
    """keep() for record_fields at a later stage: text not withheld, not flagged on its own and not embedding flagged
    primary text, exactly what withhold_untrusted leaves for joined screening."""
    return lambda value: not (contains_withheld(value) or value in tripped or screen_text(value) or any(source in value for source in tripped))


def record_values(refs):
    """Every value a record's refs point to (list members entry by entry)."""
    return [slot_value(container, key) for slots in refs.values() for container, key, _ in slots]


def _record_hits(payload, tripped, covered, derived):
    """(hits, held) for the primary (derived=False) or derived records (other_records): one hit per record whose split
    markers not already counted sit in more than one of its fields (a record withheld whole), or whose remaining fields
    trip only when joined; held is every split marker those records carry. A record that also holds text flagged on its
    own is that note's hold and is not counted again, as withhold_untrusted decides. A single field's split marker is a
    run's or another note's and is counted there, and a copy of fields another record already counted (an engine
    finding built from a register entry) is not counted again."""
    hits, held = [], set()
    keep = unflagged(tripped)

    def flagged_alone(value):
        return isinstance(value, str) and bool(value.strip()) and withheld_kind(value) != SPLIT and not keep(value)

    for path, refs, is_derived in other_records(payload):
        if is_derived != derived:
            continue
        values = {name: [slot_value(container, key) for container, key, _ in slots] for name, slots in refs.items()}
        splits = {name: {value for value in entries if withheld_kind(value) == SPLIT} for name, entries in values.items()}
        if sum(1 for found in splits.values() if found - covered) > 1:
            marked = set().union(*splits.values())
            covered.update(marked)
            held.update(marked)
            if not any(flagged_alone(value) for value in record_values(refs)):
                hits.append((path, INSTRUCTION))
            continue
        if any(flagged_alone(value) for value in record_values(refs)):
            # Split markers beside text flagged on its own are that text's hold (withhold_untrusted), not new hits; a list
            # member's run is still counted with its array (_array_hits).
            covered.update(*splits.values())
        fields, _ = record_fields(refs, keep)
        if len(fields) > 1:
            found = screen_record(fields)
            if found:
                hits.append((path, hit_reason(found)))
    return hits, held


# Top-level sections every stage rebuilds from recomputation (assertion_mappings, gate_results) or regenerates
# (ranked_findings, release_readiness); a placeholder there is bound by that recomputation, not by a hold.
ENGINE_REBUILT_SECTIONS = ("assertion_mappings", "gate_results", "ranked_findings", "release_readiness")


def placeholder_paths(payload, engine_finding, engine_escalation):
    """Paths of every string (member names included) carrying a withheld marker in a position no stage recomputes:
    findings that are not engine findings (`engine_finding(index, item)` false), escalations no engine derived
    (`engine_escalation(entry)` false), provenance and any other top-level note. Primary sections and top-level scalars
    are screened as primary text, and engine positions are bound by recomputation (quality-gate-criteria.md #8.18)."""
    paths = []

    def collect(value, path):
        paths.extend(found for found, text in iter_strings(value, path) if contains_withheld(text))

    members = dict(RECORD_MEMBERS)[("findings", "[]")]
    for index, item in enumerate(payload.get("findings") or []):
        if not engine_finding(index, item):
            # A record's split marker is bound by the hold on the record (other_records), which is where the note is, or,
            # when the record also holds text flagged on its own, by that field's hold (withhold_untrusted). A split marker
            # in only one field is not a record withheld whole (_record_hits): it is bound by that field's own hold, the
            # run or rendered text it was withheld with (quality-gate-criteria.md #8.22).
            base = f"$.findings[{index}]"
            refs = record_refs(item, members, base) if isinstance(item, dict) else {}
            slots = [(path, slot_value(container, key)) for entries in refs.values() for container, key, path in entries]
            split = {path for path, value in slots if withheld_kind(value) == SPLIT}
            alone = [path for path, value in slots if contains_withheld(value) and withheld_kind(value) != SPLIT]
            whole = f"{base} {RECORD_LABEL}" if len(split) > 1 else None
            for found, text in iter_strings(item, base):
                if contains_withheld(text):
                    paths.append((alone[0] if alone else whole or found) if found in split else found)
    for index, entry in enumerate(payload.get("escalations") or []):
        if not engine_escalation(entry):
            collect(entry, f"$.escalations[{index}]")
    for key, path, child, is_derived in top_level_sections(payload):
        if is_derived and key not in ("findings", "escalations") and key not in ENGINE_REBUILT_SECTIONS:
            collect(child, path)
    return paths


def unbound_placeholder_hits(paths, holds):
    """(path, INSTRUCTION) for each placeholder path no hold names exactly (`holds(path)` false), in order and once.
    A hold elsewhere in the document never binds a newly placed placeholder: each needs its own (#8.18)."""
    hits = []
    for path in paths:
        if not holds(path) and (path, INSTRUCTION) not in hits:
            hits.append((path, INSTRUCTION))
    return hits


def _array_hits(payload, tripped, covered, held=frozenset()):
    """Hits for runs of split-marked adjacent array entries (escalation notes included, run_slots) that no record hold
    (`held`) already counts, then for adjacent unmarked entries that trip only joined."""
    hits = []
    for _, path, child, _ in top_level_sections(payload):
        for list_path, items in iter_arrays(child, path):
            values = [slot_value(container, key) for container, key in run_slots(list_path, items)]

            def run_marked(position):
                return withheld_kind(values[position]) == SPLIT and values[position] not in held

            index = 0
            while index < len(values):
                if not run_marked(index):
                    index += 1
                    continue
                last = index
                while last + 1 < len(values) and run_marked(last + 1):
                    last += 1
                covered.update(values[index:last + 1])
                hits.append((f"{list_path}[{index}]+[{last}]{PAIR_SUFFIX}" if last > index else f"{list_path}[{index}]", INSTRUCTION))
                index = last + 1
    used = set()
    for path, fields, refs, _, found in array_runs(payload, lambda value: not (isinstance(value, str) and value.strip()) or contains_withheld(value) or value in tripped or bool(screen_text(value)) or any(source in value for source in tripped)):
        slots = {(id(container), key) for container, key in refs.values()}
        if used & slots:
            continue
        used |= slots
        hits.append((path, hit_reason(found)))
    return hits


def _next_marker_number(payload):
    highest = 0
    for _, text in iter_strings(payload, "$"):
        for match in WITHHELD_PATTERN.finditer(text):
            highest = max(highest, int(match.group(1)))
    return highest + 1


def _replace_text(value, exact, embedded):
    # Exact first: in the raw input a forged marker is itself the text being withheld.
    if value in exact:
        return exact[value]
    if is_withheld(value):
        return value
    for source, marker in embedded:
        if source in value:
            value = value.replace(source, marker)
    return value


def _renamed(items, exact, embedded):
    """Rebuild an object with every flagged member name replaced by its marker, in the original order. Marker numbers
    are unique per text, so two names never collapse into one; if they ever would, the input is refused."""
    renamed = {}
    for key, child in items:
        new_key = _replace_text(key, exact, embedded)
        if new_key in renamed:
            raise InputError("withholding flagged field names would merge two fields of one object; the input is malformed")
        renamed[new_key] = _replace_withheld(child, exact, embedded)
    return renamed


def _replace_withheld(value, exact, embedded):
    if isinstance(value, dict):
        renamed = _renamed(list(value.items()), exact, embedded)
        value.clear()
        value.update(renamed)
        return value
    if isinstance(value, list):
        for index, child in enumerate(value):
            value[index] = _replace_withheld(child, exact, embedded)
        return value
    return _replace_text(value, exact, embedded) if isinstance(value, str) else value


# --- Rendered adjacency (quality-gate-criteria.md #8.22) ---------------------------------------------------------
# The review packet (review-packet/templates/review-packet-template.md) renders the deliverable ID in its heading, the
# review status, each ranked finding as one row (location section, the label when page or paragraph is null, title,
# detail, criteria section), the gate checklist, each unsupported or limited assertion mapping (assertion ID, text,
# evidence IDs, citation), each escalation as a list line and the provenance line, in that order (RENDERED_LINES).
# Text from several records, or an ID beside prose, can therefore be read as one sentence even when every value passes
# on its own. gate_check predicts the ranked order (rank_order, the order severity_rank uses) and screens the packet as
# one sequence of lines across every block (rendered_screen): every pair of values within a row and across two
# consecutive rows, sliding windows of consecutive lines and the whole sequence in order, both as the values read and as
# the template renders them (with its separators and line text). severity_rank and --verify refuse a ranked output in
# which any of these still trips, or that is too long to screen whole.
RANK_SEVERITY = {"release_blocker": 0, "must_fix": 1, "advisory": 2}
# Members whose values are identifiers, closed enums or tags: never read as rendered prose and never withheld as one.
NON_PROSE_KEYS = {"status", "severity", "gate_id", "support_status", "class", "type", "license_status", "client_data_handling",
                  "required_disclaimer_type", "source", "contract_version", "generated_at", "engines", "best_evidence_id"}
MIN_RENDERED_SOURCE = 4  # shorter input values are not traced into composed engine text


def rank_sort_key(item):
    """severity_rank's ranking (severity-rules.md #3.2): severity, then higher confidence, then page and paragraph
    (register- or field-level findings without them last), then finding ID. Values the ranking cannot order sort last."""
    location = item.get("location") if isinstance(item.get("location"), dict) else {}
    page, paragraph = location.get("page"), location.get("paragraph")
    confidence = item.get("confidence", 0.0)
    return (RANK_SEVERITY.get(item.get("severity"), len(RANK_SEVERITY)), -float(confidence) if is_number(confidence) else 0.0,
            page if is_integer(page) else 9999, paragraph if is_integer(paragraph) else 9999,
            item.get("finding_id") if isinstance(item.get("finding_id"), str) else "")


def rank_order(findings):
    """The findings in the order severity_rank ranks them: one per canonical finding ID at the highest severity (first
    on a tie), then sorted by rank_sort_key."""
    kept, positions = [], {}
    for item in findings:
        if not isinstance(item, dict):
            continue
        key = canonical_id(item.get("finding_id")) if isinstance(item.get("finding_id"), str) else None
        if key is None or key not in positions:
            if key is not None:
                positions[key] = len(kept)
            kept.append(item)
        elif RANK_SEVERITY.get(item.get("severity"), 9) < RANK_SEVERITY.get(kept[positions[key]].get("severity"), 9):
            kept[positions[key]] = item
    return sorted(kept, key=rank_sort_key)


# Every placeholder of the review-packet template, by the block it renders in (None outside any `{{for each}}` block),
# is either screened in its rendered order (RENDERED_LINES, read by rendered_rows) or exempt with the reason it cannot
# carry review-input text (RENDER_EXEMPT). tests/run_tests.py fails when the template gains a placeholder in neither
# (quality-gate-criteria.md #8.22). IDs, locations, labels and citations are screened, not exempt.
RENDERED_LINES = (
    (None, ("deliverable.deliverable_id",)),
    (None, ("release_readiness.summary",)),
    ("ranked_finding", ("location.section", "location.label", "title", "detail", "criteria_section")),
    ("gate_result", ("name", "citation")),
    ("assertion_mapping", ("assertion_id", "text", "evidence_ids", "citation")),
    ("escalation", ("escalation",)),
    (None, ("provenance.engines",)),
)
_ENUM = "a closed contract enum, validated at every stage, so it cannot carry review-input text"
_POSITION = "an integer or null (contract-validated), rendered as a number, so it cannot carry review-input text"
RENDER_EXEMPT = {
    ("ranked_finding", "rank"): "severity_rank's 1-based rank, an integer the engine assigns; it cannot carry review-input text",
    ("ranked_finding", "severity"): _ENUM,
    ("ranked_finding", "gate_id"): _ENUM,
    ("ranked_finding", "location.page"): _POSITION,
    ("ranked_finding", "location.paragraph"): _POSITION,
    ("gate_result", "gate_id"): _ENUM,
    ("gate_result", "status"): _ENUM,
    ("gate_result", "highest_severity"): _ENUM,
    ("assertion_mapping", "support_status"): _ENUM,
    ("assertion_mapping", "location.page"): _POSITION,
    ("assertion_mapping", "location.paragraph"): _POSITION,
    (None, "release_readiness.status"): _ENUM,
    (None, "provenance.generated_at"): "an RFC 3339 date-time checked at every stage (#8.14), so it cannot carry review-input text",
}


def _rendered_value(item, field):
    """The strings `field` (a dotted path) renders for `item`, in order: an array renders its entries."""
    value = item
    for part in field.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return list(value) if isinstance(value, list) else [value]


def _rendered_items(payload, ranked):
    """For each RENDERED_LINES entry, the records it renders a line for, in packet order, each with whether its location
    renders at register level (a ranked finding whose page or paragraph is null renders its label instead)."""
    sources = {
        None: [payload],
        "ranked_finding": ranked,
        "gate_result": payload.get("gate_results") or [],
        "assertion_mapping": [item for item in payload.get("assertion_mappings") or []
                              if isinstance(item, dict) and item.get("support_status") != "supported"],
        "escalation": [{"escalation": item.get("note") if isinstance(item, dict) else item} for item in payload.get("escalations") or []],
    }
    blocks = []
    for block, _ in RENDERED_LINES:
        items = []
        for item in sources[block] if isinstance(sources[block], list) else []:
            if isinstance(item, dict):
                location = item.get("location") if isinstance(item.get("location"), dict) else {}
                items.append((item, block == "ranked_finding" and (location.get("page") is None or location.get("paragraph") is None)))
        blocks.append(items)
    return blocks


def rendered_rows(payload, ranked):
    """The rendered text, as one sequence of rows per RENDERED_LINES entry (each row a list of the values on that
    packet line, in reading order): the heading, the review status, ranked findings, the gate checklist, unsupported or
    limited assertion mappings, escalations and the provenance line. A ranked finding's location label renders only
    when its page or paragraph is null."""
    return tuple([[value for field in fields if not (block == "ranked_finding" and field == "location.label" and not register)
                   for value in _rendered_value(item, field)] for item, register in items]
                 for (block, fields), items in zip(RENDERED_LINES, _rendered_items(payload, ranked)))


# Each line as review-packet-template.md renders it, aligned with RENDERED_LINES, so the template's own text around a
# value is screened with it: the template renders " - " between a finding's title and its detail, and a title such as
# "To the system" followed by " - " reads as an addressed instruction although neither value does alone.
# tests/run_tests.py checks every format against the template. A ranked finding whose page or paragraph is null renders
# its location as RENDERED_REGISTER_LOCATION (the template's note); an array renders its entries separated by
# RENDERED_ARRAY_JOIN; a screened value that is withheld or held already renders as RENDERED_UNSCREENED.
RENDERED_FORMATS = (
    "# DELIVERABLE REVIEW PACKET - {{deliverable.deliverable_id}} - DRAFT - HUMAN REVIEW REQUIRED",
    "**{{release_readiness.status}}** - {{release_readiness.summary}}",
    "| {{rank}} | {{severity}} | {{gate_id}} | p{{location.page}} / {{location.section}} / para {{location.paragraph}} | {{title}} - {{detail}} | {{criteria_section}} |",
    "| {{gate_id}} - {{name}} | {{status}} | {{highest_severity}} | {{citation}} |",
    "- **{{support_status}}** - {{assertion_id}} at p{{location.page}}, para {{location.paragraph}}: {{text}}\n  - Evidence: {{evidence_ids}}; citation: {{citation}}",
    "- {{escalation}}",
    "Engine provenance: {{provenance.engines}}; generated at {{provenance.generated_at}}. Raw contract payload intentionally omitted to avoid duplicating client data or untrusted source text.",
)
RENDERED_REGISTER_LOCATION = ("p{{location.page}} / {{location.section}} / para {{location.paragraph}}", "register-level / {{location.section}} / {{location.label}}")
RENDERED_ARRAY_JOIN = ", "
RENDERED_UNSCREENED = "[withheld]"
_PLACEHOLDER = re.compile(r"\{\{([^{}]+)\}\}")


class RenderedLiteral(str):
    """Template text and exempt values of the rendered packet: counted in its length, never traced to an input value."""


def rendered_layout(payload, ranked, keep):
    """The packet as the template renders it (RENDERED_FORMATS), as (units, before, tail, line_of): units are the
    screened values (RENDERED_LINES) for which keep(value) is true, in rendered order; before[k] is the text rendered
    between unit k-1 (or the start) and unit k - template text, exempt values, array separators, line breaks and
    RENDERED_UNSCREENED for a screened value not kept; tail is the text after the last unit; line_of[k] numbers the
    line unit k renders on."""
    units, before, line_of = [], [], []
    text, line = "", 0
    for (block, fields), template, items in zip(RENDERED_LINES, RENDERED_FORMATS, _rendered_items(payload, ranked)):
        for position, (item, register) in enumerate(items):
            text += "\n" if units or text else ""
            for index, piece in enumerate(_PLACEHOLDER.split(template.replace(*RENDERED_REGISTER_LOCATION) if register else template)):
                if index % 2 == 0:
                    text += piece
                    continue
                if piece == "rank":
                    text += str(position + 1)
                    continue
                for number, value in enumerate(_rendered_value(item, piece)):
                    text += RENDERED_ARRAY_JOIN if number else ""
                    if piece in fields and keep(value):
                        units.append(value)
                        before.append(text)
                        line_of.append(line)
                        text = ""
                    elif piece in fields and isinstance(value, str):
                        text += RENDERED_UNSCREENED if value.strip() else ""
                    else:
                        # An exempt value, or a screened value that is not a string (the contract refuses one at every
                        # stage), is rendered as str() renders it and screened as part of the template text.
                        text += "" if value is None else str(value)
            line += 1
    return units, before, text, line_of


def _joined_trips(texts):
    return bool(screen_text(" ".join(texts)))


# Sliding windows over the rendered lines (quality-gate-criteria.md #8.22, checklist D18), in two views of the packet:
# - the values as read, space-joined, with punctuation-only values left out (_wordless): a window starts at every line
#   and takes up to RENDERED_WINDOW_LINES lines (ARRAY_WINDOW, the bound used for adjacent array entries), stopping early
#   once it reaches RENDERED_REACH characters past its first line. RENDERED_REACH is the detector's own window overlap,
#   the longest reach of any of its rules (characters consumed plus look-ahead), so a window holds every rule match
#   that starts in its first line and fits in eight lines. Table syntax and filler rows between the values are left
#   out, so a sentence spread over consecutive rows reads as one;
# - the packet as the template renders it (rendered_layout): a window is a line and the next line
#   (RENDERED_LAYOUT_LINES) with the template text up to RENDERED_REACH characters either side, so the template's own
#   text beside a value (a separator, the start of the next line) is screened with it. Sentences across more rows are
#   the first view's. Headings and fixed notes between blocks are not part of it: they carry no input value and stand
#   between the blocks in the packet, so leaving them out only brings two blocks' lines closer.
# Each window's length is bounded by its lines plus RENDERED_REACH and by its line count, so the windows add at most
# RENDERED_WINDOW_LINES + RENDERED_LAYOUT_LINES times the packet's text plus context, linear in the number of lines. A
# composition spread over more lines than a window is caught by the whole sequence, screened once in each view.
RENDERED_WINDOW_LINES = ARRAY_WINDOW
RENDERED_LAYOUT_LINES = 2
RENDERED_REACH = sg.WINDOW_OVERLAP


def _wordless(text):
    """True for rendered text with no letter or digit (punctuation or symbols only). It carries no words, so it is left
    out of the space-joined view: a row of '.' between two halves would otherwise end the sentence for the detector,
    and filler rows would push the halves out of one window. The template view keeps it, as rendered."""
    return not any(char.isalnum() for char in text)


def _trips(text):
    """True when text trips the detector. An oversize result is not a trip here: a window never reaches the limit
    unless the whole sequence does, and that is the oversize hold (rendered_screen)."""
    found = screen_text(text)
    return bool(found) and hit_reason(found) != OVERSIZE


def _narrowed(trips, first, last):
    """For a tripping span first..last (trips(first, last) is true), the shortest tripping prefix of it, then the
    shortest tripping suffix of that prefix, each found by bisection (a logarithmic number of screens, never one screen
    per unit). Each bound is kept only where the span still trips, so the result always trips. Returns (first, last)."""
    low, high = first - 1, last
    while high - low > 1:
        middle = (low + high) // 2
        if trips(first, middle):
            high = middle
        else:
            low = middle
    end = high
    low, high = first, end + 1
    while high - low > 1:
        middle = (low + high) // 2
        if trips(middle, end):
            low = middle
        else:
            high = middle
    return low, end


def _window_groups(units, line_of, sizes, trips, lines_per_window, single):
    """Groups of units that trip within a sliding window of consecutive lines (at most lines_per_window lines, stopping
    once RENDERED_REACH characters past the first line are reached), each narrowed to the units the hit needs. sizes[k]
    is the rendered length of unit k; trips(first, last) screens units first..last. A window of one unit is screened
    only when `single` (the template view, where the template text beside a value is screened with it). After a hit,
    sliding resumes after the line where the narrowed group ends; the gates are re-run with the group withheld, so a
    second hit overlapping it is found on the next pass."""
    lines = []  # [first unit, last unit, size]
    for index, number in enumerate(line_of):
        if lines and line_of[lines[-1][0]] == number:
            lines[-1][1] = index
            lines[-1][2] += sizes[index]
        else:
            lines.append([index, index, sizes[index]])
    line_index = {line_of[first]: position for position, (first, _, _) in enumerate(lines)}
    groups, index = [], 0
    while index < len(lines):
        stop, size = index + 1, lines[index][2]
        while stop < len(lines) and stop - index < lines_per_window and size < lines[index][2] + RENDERED_REACH:
            size += lines[stop][2]
            stop += 1
        first, last = lines[index][0], lines[stop - 1][1]
        if size <= sg.MAX_TOTAL_CHARS and (single or last > first) and trips(first, last):
            low, high = _narrowed(trips, first, last)
            groups.append(tuple(units[low:high + 1]))
            index = line_index[line_of[high]] + 1
            continue
        index += 1
    return groups


def _sequence_group(units, trips, single):
    """The whole sequence screened once, in order; when it trips, the narrowed group of units the hit needs, else None."""
    if (len(units) > 1 or single and units) and trips(0, len(units) - 1):
        low, high = _narrowed(trips, 0, len(units) - 1)
        return tuple(units[low:high + 1])
    return None


def rendered_screen(payload, ranked):
    """Screen the packet as it renders (quality-gate-criteria.md #8.22; checklist D18, D22): every RENDERED_LINES block,
    in packet order, read as one sequence of lines, so text can compose within a row, across rows and across the
    boundary between two blocks. Text already withheld or tripping on its own is left out (it holds already). Screened:

    - the values an instruction split across text tripping on its own and its clean neighbours overlaps, in rendered
      order (split_partner_positions): each run of them is a group;
    - each pair of values within a row and across two consecutive rows of one block, in reading order;
    - with the values a pair already claimed left out, as they will be once withheld, sliding windows of consecutive
      lines across the whole sequence in two views (_window_groups): the values space-joined with punctuation-only
      values left out (_wordless), and the packet as the template renders it (rendered_layout);
    - when no window trips, the whole sequence in order, in the same two views, so neither filler rows nor a value that
      needs the punctuation or template text beside it can hide a hit.

    Returns (groups, oversize). groups lists tuples of rendered strings that trip together, in rendering order. When the
    packet as rendered is longer than the detector can screen (sg.MAX_TOTAL_CHARS, raw or after Unicode normalisation),
    nothing else is screened: groups is empty and oversize is the tuple of every screened value in the sequence followed
    by the template text as one RenderedLiteral, the detector's oversize result, which is a hold (#8.6), never a pass.
    gate_check withholds the longest values under an oversize marker and screens again, so the shorter packet is
    screened in full. Otherwise oversize is ()."""
    screened = {}

    def usable(value):
        if value not in screened:
            screened[value] = isinstance(value, str) and bool(value.strip()) and not contains_withheld(value) and not screen_text(value)
        return screened[value]

    units, before, tail, _ = rendered_layout(payload, ranked, lambda value: isinstance(value, str) and usable(value))
    literal = RenderedLiteral("".join(before) + tail)
    whole = "".join(text + value for text, value in zip(before, units)) + tail
    if len(whole) > sg.MAX_TOTAL_CHARS or any(hit.family == OVERSIZE for hit in screen_text(whole)):
        return [], tuple(units) + ((literal,) if literal else ())
    groups = []
    # A value that trips on its own holds already, but the clean values an instruction split across it and them
    # overlaps (split_partner_positions, in rendered order) are withheld with it: each run of them is a group.
    rendered, _, _, _ = rendered_layout(payload, ranked, lambda value: isinstance(value, str) and bool(value.strip()))
    flagged = {position for position, value in enumerate(rendered) if not contains_withheld(value) and not usable(value)}
    if flagged:
        partners = [position for position in sorted(split_partner_positions(rendered, flagged)[0]) if usable(rendered[position])]
        for first, last in position_runs(partners):
            group = tuple(dict.fromkeys(rendered[first:last + 1]))
            if group not in groups:
                groups.append(group)
    for rows in rendered_rows(payload, ranked):
        distinct = [list(dict.fromkeys(value for value in row if isinstance(value, str) and usable(value))) for row in rows]
        for index, row in enumerate(distinct):
            pairs = [(a, b) for position, a in enumerate(row) for b in row[position + 1:]]
            if index + 1 < len(distinct):
                pairs.extend((a, b) for a in row for b in distinct[index + 1] if a != b)
            groups.extend(pair for pair in pairs if _joined_trips(pair) and pair not in groups)
    claimed = {value for group in groups for value in group}
    units, before, tail, line_of = rendered_layout(payload, ranked, lambda value: isinstance(value, str) and usable(value) and value not in claimed)
    worded = [index for index, value in enumerate(units) if not _wordless(value)]
    words, word_lines = [units[index] for index in worded], [line_of[index] for index in worded]

    def spoken(first, last):
        return _trips(" ".join(words[first:last + 1]))

    def shown(first, last):
        after = before[last + 1] if last + 1 < len(units) else tail
        return _trips(before[first][-RENDERED_REACH:] + "".join((before[index] if index > first else "") + units[index] for index in range(first, last + 1))
                      + after[:RENDERED_REACH])

    found = _window_groups(words, word_lines, [len(value) + 1 for value in words], spoken, RENDERED_WINDOW_LINES, False)
    found += [group for group in _window_groups(units, line_of, [len(text) + len(value) for text, value in zip(before, units)], shown, RENDERED_LAYOUT_LINES, True)
              if group not in found]
    if not found:
        whole_group = _sequence_group(words, spoken, False) or _sequence_group(units, shown, True)
        found = [whole_group] if whole_group else []
    groups.extend(group for group in found if group not in groups)
    return groups, ()


def rendered_hits(payload, ranked):
    """Groups of rendered strings that trip the detector only when read together or with the template text beside them
    (rendered_screen), plus, when the rendered packet is too long to screen whole, one group of every rendered string:
    severity_rank and --verify refuse a ranked output for which this is non-empty (quality-gate-criteria.md #8.22)."""
    groups, oversize = rendered_screen(payload, ranked)
    return groups + ([oversize] if oversize else [])


def _free_text_slots(node, name=None):
    """(container, key) for every string value outside enum and tag members (NON_PROSE_KEYS). Identifier members
    (*_id, *_ids) are included: the packet renders IDs beside prose, so an ID can be one half of rendered text that
    trips (quality-gate-criteria.md #8.22)."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in NON_PROSE_KEYS:
                continue
            if isinstance(value, str):
                yield node, key
            else:
                yield from _free_text_slots(value, key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            if isinstance(value, str):
                yield node, index
            else:
                yield from _free_text_slots(value, name)


def rendered_sources(payload, groups):
    """The free-text values of `payload` behind rendered strings that trip together: a rendered string that is itself a
    value, else every value of at least MIN_RENDERED_SOURCE characters it contains (engine text that embeds input,
    such as a recipient name inside a finding detail). Engine-only text has no source and is never withheld."""
    values = {container[key] for container, key in _free_text_slots(payload) if not contains_withheld(container[key])}
    sources = set()
    for group in groups:
        for text in group:
            if text in values:
                sources.add(text)
            else:
                sources.update(value for value in values if len(value.strip()) >= MIN_RENDERED_SOURCE and value in text)
    return sources


def oversize_sources(payload, texts, exclude=frozenset()):
    """The free-text values of `payload` to withhold under an oversize marker when the rendered sequence `texts`
    (rendered_screen's oversize result) is too long to screen whole (quality-gate-criteria.md #8.6, #8.22): the values
    behind the longest rendered strings first (rendered order on a tie), until what is left fits the detector's limit,
    and always at least one value not in `exclude`, so each pass of gate_check withholds more and the loop ends. A
    rendered string's values are found as in rendered_sources; engine-only text (a RenderedLiteral, the template text
    and exempt values) has none and is never withheld, but counts toward the length."""
    if not texts:
        return frozenset()
    values = {container[key] for container, key in _free_text_slots(payload) if not contains_withheld(container[key])}
    remaining, chosen = sum(len(text) for text in texts), set()
    for text in sorted(texts, key=len, reverse=True):
        if chosen and remaining <= sg.MAX_TOTAL_CHARS:
            break
        if isinstance(text, RenderedLiteral):
            continue
        found = {text} if text in values else {value for value in values if len(value.strip()) >= MIN_RENDERED_SOURCE and value in text}
        found -= exclude
        if found:
            chosen |= found
            remaining -= len(text) - len(RENDERED_UNSCREENED)
    return frozenset(chosen)


def withhold_untrusted(payload, raw_input=False, rendered=frozenset(), oversize=frozenset()):
    """Screen the whole payload and replace every string that trips the detector with a numbered withheld marker,
    everywhere that text appears, so no stage, output or review packet repeats it (quality-gate-criteria.md #8.7).

    Detection runs on the original text first; nothing is stripped or rewritten before screening. Then:
    - a tripped primary or derived string is replaced wherever it appears exactly, and wherever it is embedded in a
      longer string (for example the assertion citation inside assertion_mappings[].citation);
    - a string carrying a forged marker (forged_marker: any marker at all in the raw review input, raw_input=True, or
      at a later stage a marker inside a longer string with no exact twin) is tampering: it is withheld whole under a
      new marker and is a G8 hit, so input can never supply a marker that sets text aside without a hold;
    - when only an assertion's joined fields trip, each of those fields gets a split marker wherever it appears exactly;
    - when only a run of adjacent array entries trips joined (array_runs), every entry of the run gets a split marker;
    - when only another record's joined fields trip (other_records, screen_record), every field of the record that is
      not already flagged or claimed (every entry of a list member) gets a split marker wherever it appears exactly;
    - when a value trips on its own and an instruction split across it and clean neighbours of the same assertion,
      record or array (sg.split_partners) overlaps them, each such clean neighbour gets a split marker under the flagged
      value's hold (a run of array entries is one hit), or an oversize marker when the join is too long to screen;
    - every free-text value in `rendered` (gate_check's rendered_sources, quality-gate-criteria.md #8.22) gets a split
      marker wherever it appears exactly;
    - every free-text value in `oversize` (gate_check's oversize_sources: the review packet would be too long to screen
      whole, #8.6, #8.22) gets an oversize marker wherever it appears, exactly or embedded;
    - member names are screened like values, and a flagged name is replaced by its marker in place (order kept).
    Engine markers already present are left alone and are not new hits. The payload is updated in place. Returns
    (path, reason, derived) for each newly withheld hit, in the order instruction_hits reports them."""
    primary, derived = scan_sections(payload)
    emitted = None if raw_input else exact_markers(payload)
    # In the raw input every marker is forged and is replaced, so numbering starts at 1.
    number = [1 if raw_input else _next_marker_number(payload)]
    markers, embedded, new = {}, [], []

    def mark(text, kind):
        if text not in markers:
            if number[0] > MAX_MARKER_NUMBER:
                raise InputError("the input carries more withheld markers than can be numbered; it is malformed")
            markers[text] = withheld_marker(number[0], kind)
            number[0] += 1
            if kind != SPLIT:
                embedded.append(text)

    tripped = set()
    for path, text in primary:
        if forged_marker(text, emitted):
            mark(text, INSTRUCTION)
            tripped.add(text)
            new.append((path, INSTRUCTION, False))
            continue
        if is_withheld(text):
            continue
        found = screen_text(text)
        if found:
            mark(text, hit_reason(found))
            tripped.add(text)
            new.append((path, hit_reason(found), False))
    primary_texts = {text for _, text in primary}
    derived_new = []
    for path, text in derived:
        if forged_marker(text, emitted) and text not in primary_texts:
            mark(text, INSTRUCTION)
            derived_new.append((path, INSTRUCTION, True))
            continue
        if is_withheld(text) or text in primary_texts or any(source in text for source in tripped):
            continue
        found = screen_text(text)
        if found:
            mark(text, hit_reason(found))
            derived_new.append((path, hit_reason(found), True))
    combined, split_refs = [], []

    def breaks(value):
        return not (isinstance(value, str) and value.strip()) or value in markers or contains_withheld(value) or any(source in value for source in embedded)

    # Instructions split across text flagged on its own and clean neighbours (split_partner_positions): every clean
    # value the split overlaps is withheld with a split marker under the flagged text's hold, as a record holding a
    # field flagged alone withholds its other joined-tripping fields (quality-gate-criteria.md #8.5, #8.7). A join too
    # long to screen withholds its clean values with oversize markers instead, each its own hold (#8.6).
    oversize_new, slot_paths = [], {}

    def partners_of(slots, groups=()):
        """(partner slots, oversize slots): the clean slots of `slots` ((container, key) in reading order) that a split
        instruction with flagged text overlaps, and those of a join too long to screen."""
        values = [slot_value(container, key) for container, key in slots]
        flagged = {position for position, value in enumerate(values)
                   if isinstance(value, str) and value.strip() and not contains_withheld(value) and breaks(value)}
        if not flagged:
            return [], []
        found, over = split_partner_positions(values, flagged, groups)
        clean = [position for position in sorted(found) if not breaks(values[position])]
        return [slots[position] for position in clean if position not in over], [slots[position] for position in clean if position in over]

    def hold_oversize(slots, derived_slot):
        if not slots:
            return
        if not slot_paths:
            _index_slots(payload, slot_paths)
        for container, key in slots:
            if not is_withheld(container[key]):
                oversize_new.append((slot_paths.get((id(container), key), "$"), OVERSIZE, derived_slot))
                mark(container[key], OVERSIZE)

    for path, fields, refs in assertion_records(payload):
        values = list(fields.values())
        if tripped.intersection(values) or any(is_withheld(value) for value in values):
            partners, over = partners_of(list(refs.values()), [[position] for position in range(len(refs))])
            split_refs.extend(partners)
            # A withheld evidence reference also withholds the evidence ID it names, as below.
            chosen = {(id(container), key) for container, key in partners}
            references = {slot_value(*slot) for name, slot in refs.items() if name.startswith("evidence id") and (id(slot[0]), slot[1]) in chosen}
            split_refs.extend((item, "evidence_id") for item in payload.get("evidence_set") or []
                              if isinstance(item, dict) and item.get("evidence_id") in references)
            hold_oversize(over, False)
            continue
        found = screen_record(fields)
        if found:
            # Mark the fields the note needs (removing one stops the hit), or every field when none is needed alone;
            # evidence titles are shared between assertions, so they are marked only when the note needs no field of
            # the assertion's own. No field trips alone, so identical text elsewhere in the primary sections is not
            # this note and is left as it is.
            needed = [name for name in fields if not screen_record({other: value for other, value in fields.items() if other != name})] or list(fields)
            own = [name for name in needed if not name.startswith("evidence title")]
            split_refs.extend(refs[name] for name in (own or needed))
            # A withheld evidence reference also withholds the evidence ID it names, so no copy of the ID is left behind.
            references = {slot_value(*refs[name]) for name in (own or needed) if name.startswith("evidence id")}
            split_refs.extend((item, "evidence_id") for item in payload.get("evidence_set") or []
                              if isinstance(item, dict) and item.get("evidence_id") in references)
            combined.append((path, hit_reason(found), False))
    # Prose split across adjacent array entries: each entry passes alone, a run of them trips joined (array_runs). Every
    # entry of the run is withheld with a split marker; an entry already flagged or withheld splits the array into runs.
    run_hits = []
    for path, fields, refs, is_derived, found in array_runs(payload, breaks):
        split_refs.extend(refs.values())
        run_hits.append((path, hit_reason(found), is_derived))
    # An entry flagged on its own withholds the clean entries a split instruction shares with it; each run of them is
    # one hit, as _array_hits counts it at every later stage (after the records, which may hold them instead).
    partner_arrays = []
    for _, section_path, child, is_derived in top_level_sections(payload):
        for list_path, items in iter_arrays(child, section_path):
            slots = run_slots(list_path, items)
            partners, over = partners_of(slots)
            split_refs.extend(partners)
            hold_oversize(over, is_derived)
            if partners:
                partner_arrays.append((list_path, slots, is_derived, {(id(container), key) for container, key in partners}))
    # Every other record (other_records) is screened with its fields joined the same way (screen_record). Text already
    # flagged or withheld, and fields an assertion's note or a run of entries already claimed, are that note and are
    # left out. The remaining fields are the record's own, so a record that trips joined has every one of them (every
    # entry of a list member) withheld with a split marker, wherever each appears.
    claimed = {(id(container), key) for container, key in split_refs}
    record_hits = []
    for path, refs, is_derived in other_records(payload):
        unclaimed = {name: [slot for slot in slots if (id(slot[0]), slot[1]) not in claimed] for name, slots in refs.items()}
        fields, kept = record_fields(unclaimed, lambda value: not breaks(value))
        found = screen_record(fields) if len(fields) > 1 else []
        if found:
            slots = [(container, key) for entries in kept.values() for container, key, _ in entries]
            split_refs.extend(slots)
            claimed.update((id(container), key) for container, key in slots)
            # A record already holding text flagged on its own is that note's hold: the rest is withheld with it.
            if not any(isinstance(value, str) and value.strip() and breaks(value) for value in record_values(refs)):
                record_hits.append((path, hit_reason(found), is_derived))
        # Text flagged on its own withholds the clean fields a split instruction shares with it, under its own hold.
        slots, groups = [], []
        for entries in refs.values():
            groups.append(list(range(len(slots), len(slots) + len(entries))))
            slots.extend((container, key) for container, key, _ in entries)
        partners, over = partners_of(slots, groups)
        split_refs.extend(partners)
        claimed.update((id(container), key) for container, key in partners)
        hold_oversize(over, is_derived)
    # A record whose split markers sit in more than one field is withheld whole, so its list entries are held by it and
    # are not a run of their own (_record_hits, _array_hits).
    marked = {(id(container), key) for container, key in split_refs}
    held = set()
    for _, refs, _ in other_records(payload):
        names = [[(id(container), key) for container, key, _ in slots] for slots in refs.values()]
        split_names = [slots for slots in names if any(slot in marked for slot in slots)]
        if len(split_names) > 1:
            held.update(slot for slots in split_names for slot in slots)
    for list_path, slots, is_derived, own in partner_arrays:
        ids = [(id(container), key) for container, key in slots]
        positions = [position for position, slot in enumerate(ids) if slot in marked and slot not in held and not is_withheld(slot_value(*slots[position]))]
        counted = {hit[0] for hit in run_hits}
        run_hits.extend((path, INSTRUCTION, is_derived) for path in (run_path(list_path, first, last) for first, last in position_runs(positions)
                                                                     if own.intersection(ids[first:last + 1])) if path not in counted)
    combined = [hit for hit in record_hits if not hit[2]] + combined + [hit for hit in record_hits if hit[2]] + run_hits
    # Text the review packet would render beside other text so that they trip together (#8.22).
    if oversize:
        for container, key in _free_text_slots(payload):
            if container[key] in oversize and not is_withheld(container[key]):
                mark(container[key], OVERSIZE)
    if rendered:
        split_refs.extend((container, key) for container, key in _free_text_slots(payload) if container[key] in rendered)
    split_exact = {}
    for container, key in split_refs:
        value = container[key]
        if not is_withheld(value):
            mark(value, SPLIT)
            split_exact[value] = markers[value]
            container[key] = markers[value]
    exact = {text: marker for text, marker in markers.items() if text not in split_exact}
    ordered = sorted(((text, markers[text]) for text in embedded), key=lambda pair: -len(pair[0]))
    if exact or split_exact:
        primary_keys = {key for key, _, _, is_derived in top_level_sections(payload) if not is_derived}
        renamed = {}
        for key, child in payload.items():
            if key in UNSCANNED_KEYS:
                renamed[key] = child
                continue
            # Derived copies of split fields (for example assertion_mappings[].text) are withheld with them.
            mapping = exact if key in primary_keys else {**exact, **split_exact}
            new_key = _replace_text(key, mapping, ordered)
            if new_key in renamed:
                raise InputError("withholding flagged field names would merge two top-level fields; the input is malformed")
            renamed[new_key] = _replace_withheld(child, mapping, ordered)
        payload.clear()
        payload.update(renamed)
    return new + oversize_new + derived_new + combined


def _index_slots(payload, index):
    """Fill index with (id(container), key) -> path for every member and entry below the top-level sections."""
    def walk(value, path):
        if isinstance(value, dict):
            for label, key, child in labelled_members(value):
                index[(id(value), key)] = f"{path}.{label}"
                walk(child, f"{path}.{label}")
        elif isinstance(value, list):
            for position, child in enumerate(value):
                index[(id(value), position)] = f"{path}[{position}]"
                walk(child, f"{path}[{position}]")

    for _, path, child, _ in top_level_sections(payload):
        walk(child, path)
