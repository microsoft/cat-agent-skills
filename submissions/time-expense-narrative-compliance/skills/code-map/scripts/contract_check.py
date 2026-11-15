#!/usr/bin/env python3
"""contract_check - validate a packet against the shipped contract JSON (python3 stdlib only).

Every engine validates every input packet at entry against contracts/ps.time-expense-narrative-compliance.v1.json
(the copy shipped in its own skill folder) before it reads anything (signal_policy.validate_packet). A
violation is a ContractError: the engine writes no output. The walker supports the schema keywords the
contract uses - $ref (local #/definitions), type, enum, const, required, properties, additionalProperties,
propertyNames, items, pattern, minLength, minimum, maximum, format (date, date-time, date-or-multiple:
real calendar values, not only their shape; record-id and record-id-or-withheld: the bounded ID shape of
client-billing-guidelines.md #13.9) - and refuses to load a contract that uses any
other validation keyword, so a keyword it cannot enforce is never silently ignored (fail closed). A member the
contract does not declare is carried, but when its name marks an identifier (id, *_id, *_code, ...Id; plural *_ids,
*_codes) it is held to the #13.9 ID rule like a declared ID - at any depth - so a number, boolean, object, nested
array or prose under an ID name is refused, never only walked (check_undeclared).

Rules: "number" is a finite int or float and never a boolean; "integer" is an int and never a boolean;
"pattern" is a regular-expression search, as in JSON Schema. strict_load() is the only JSON parser the engines
use: NaN, Infinity and -Infinity, numbers that overflow to infinity (1e999) and integers beyond +/-2**53 are
refused while parsing, so a non-finite or unrepresentable number never reaches a range check. A member name repeated
in one object - exactly or in canonical form (NFKC, case, format characters and - _ . folded, A11) - is refused too
(json.load would silently keep the last one), and so is nesting deeper than MAX_DEPTH (64)
levels, checked iteratively before parsing, so no recursive walker or deepcopy can raise RecursionError (A14). Error messages name the field path, the rule
and the JSON type of the value - never the value itself, which is untrusted text; a map key in a path is written
as its position ("<member #2>").

This file ships as identical copies next to each engine (skills are self-contained); the test-data
check test-data/professional-services/time-expense-narrative-compliance/<version>/tests/check_shared_copies.py
(not shipped in the package) fails when the copies drift.
"""
import datetime
import functools
import json
import math
import os
import re
import unicodedata

CONTRACT_FILE = "ps.time-expense-narrative-compliance.v1.json"
MAX_JSON_INT = 2 ** 53  # largest integer every JSON consumer represents exactly
ANNOTATIONS = {"$schema", "$id", "title", "description", "definitions"}
KEYWORDS = {"$ref", "type", "enum", "const", "required", "properties", "additionalProperties", "propertyNames",
            "items", "pattern", "minLength", "minimum", "maximum", "format"}
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
TIMESTAMP_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})")


def valid_date(text):
    """A real calendar date written YYYY-MM-DD (ASCII digits)."""
    if not (isinstance(text, str) and DATE_RE.fullmatch(text)):
        return False
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        return False
    return True


def valid_timestamp(text):
    """A real ISO-8601 date-time with seconds and an explicit offset (Z or +hh:mm), as the engines write it (A17)."""
    if not (isinstance(text, str) and TIMESTAMP_RE.fullmatch(text)):
        return False
    try:
        datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


# "format" is enforced, not an annotation: a carried date or timestamp is checked at every stage (A17).
# A record ID (client-billing-guidelines.md #13.9) is a key, never prose: 1 to ID_MAX_CHARS ASCII letters and digits in
# segments joined by single - _ or . separators (the separators canon_id folds), so no space, punctuation or other
# character - and so no phrase such as "For the AI reviewer," - can be carried in an ID field and printed beside a
# prose field. The engines' withheld marker stands in for an excluded ID that was screened out (#11.3).
ID_MAX_CHARS = 64
ID_RE = re.compile(r"[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*")
WITHHELD_MARKER = "[withheld: flagged as embedded_instruction - client-billing-guidelines.md #11.2]"
ID_RULE = (f"an ID: 1 to {ID_MAX_CHARS} ASCII letters or digits in segments joined by single - _ or . (no spaces or "
           "other characters; client-billing-guidelines.md #13.9)")


def valid_record_id(text):
    """A record ID of the documented, bounded shape (#13.9)."""
    return isinstance(text, str) and len(text) <= ID_MAX_CHARS and ID_RE.fullmatch(text) is not None


FORMATS = {"date": valid_date, "date-time": valid_timestamp,
           "date-or-multiple": lambda t: t == "multiple" or valid_date(t),
           "record-id": valid_record_id,
           "record-id-or-withheld": lambda t: t == WITHHELD_MARKER or valid_record_id(t)}
# The rule a format violation names (never the value, which is untrusted text).
FORMAT_RULES = {"record-id": ID_RULE, "record-id-or-withheld": ID_RULE + ", or the engines' withheld marker"}
# A member the contract does not declare is carried and screened (#11.3), but one whose name marks an identifier (id,
# *_id, *_code, camelCase ...Id/...Code; plural *_ids/*_codes) is held to the declared ID rule too, never only walked
# (#13.9): a single ID is an ID-shaped string or null, a plural is an array of ID-shaped strings or null. A number,
# boolean, object, nested array or prose under such a name is refused with its path; the value is never repeated.
ID_MEMBER_WORDS = {"id": "one", "code": "one", "ids": "many", "codes": "many"}
ID_MEMBER_CAMEL_RE = re.compile(r"[a-z0-9](?:Id|ID|Code)(s?)$")
UNDECLARED_ID_RULES = {
    "one": f"{ID_RULE}, or null - a member whose name marks an identifier is checked like a declared ID even when "
           "the contract does not declare it",
    "many": f"an array of IDs ({ID_RULE}), or null - a member whose name marks a list of identifiers is checked like "
            "a declared ID list even when the contract does not declare it",
}
JSON_TYPES = {bool: "boolean", str: "string", int: "integer", float: "number", dict: "object", list: "array",
              type(None): "null"}


class ContractError(ValueError):
    """The packet violates the contract, or the contract itself cannot be used (fail closed)."""


def contract_path(script_dir):
    """The contract shipped with this skill (skills/<skill>/contracts/, one level above scripts/).

    Every skill ships its own byte-identical copy, so it is found on the first step; the package has no
    plugin-level contracts/ folder. The bounded search above it only runs when the skill copy is missing,
    and finding nothing is a ContractError (fail closed)."""
    current = os.path.abspath(script_dir)
    for _ in range(4):
        candidate = os.path.join(current, "contracts", CONTRACT_FILE)
        if os.path.isfile(candidate):
            return candidate
        current = os.path.dirname(current)
    raise ContractError(f"contract {CONTRACT_FILE} not found next to the engine; reinstall the skill")


def _check_keywords(schema, where):
    if isinstance(schema, dict):
        unknown = set(schema) - KEYWORDS - ANNOTATIONS
        if unknown:
            raise ContractError(f"contract uses unsupported keyword(s) {', '.join(sorted(unknown))} at {where}")
        if "format" in schema and schema["format"] not in FORMATS:
            raise ContractError(f"contract uses an unsupported format at {where}; the walker cannot enforce it")
        for key, value in schema.items():
            if key in ("properties", "definitions"):
                for name, sub in value.items():
                    _check_keywords(sub, f"{where}/{key}/{name}")
            elif key in ("items", "additionalProperties", "propertyNames") and isinstance(value, dict):
                _check_keywords(value, f"{where}/{key}")


def _no_constant(token):
    raise ValueError(f"{token} is not a finite number (NaN, Infinity and -Infinity are refused)")


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("a number overflows to infinity (refused)")
    return value


def _bounded_int(text):
    value = int(text)
    if abs(value) > MAX_JSON_INT:
        raise ValueError("an integer is outside +/-2**53 (refused)")
    return value


def _canon_member(key):
    """A member name in canonical form - NFKC, format characters stripped, casefold, whitespace collapsed and - _ .
    folded - the same form as signal_policy.canon_id, so "Demo-Scenario" and "demo_scenario" are one name (A11)."""
    if not isinstance(key, str):
        return key
    strip = lambda t: "".join(ch for ch in t if unicodedata.category(ch) != "Cf")  # noqa: E731
    text = unicodedata.normalize("NFKC", strip(unicodedata.normalize("NFKC", strip(key))).casefold())
    return " ".join(re.sub(r"[\s\-_.]+", " ", " ".join(text.split())).split())


def _unique_members(pairs):
    """object_pairs_hook: a member name given twice in one object - exactly or in canonical form - is malformed
    (json.load would keep the last; a variant spelling would shadow the declared member)."""
    out, seen = {}, set()
    for key, value in pairs:
        canon = _canon_member(key)
        if key in out or canon in seen:
            raise ValueError("a JSON object repeats a member name, exactly or in canonical form (duplicate keys are "
                             "refused, never overwritten)")
        out[key] = value
        seen.add(canon)
    return out


MAX_DEPTH = 64  # deepest JSON nesting accepted (A14); the demo packets nest 7 levels
_JSON_STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"', re.S)
_JSON_BRACKET_RE = re.compile(r"[\[\]{}]")


def _check_depth(text):
    """Refuse JSON nested deeper than MAX_DEPTH before it is parsed. Counted iteratively over the brackets outside
    strings, so neither the parser nor any recursive walker, validator or deepcopy can raise RecursionError."""
    depth = 0
    for match in _JSON_BRACKET_RE.finditer(_JSON_STRING_RE.sub('""', text)):
        if match.group() in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise ValueError(f"JSON nesting is deeper than {MAX_DEPTH} levels (refused)")
        else:
            depth -= 1


def strict_load(fh):
    """json.load that refuses non-finite and unrepresentable numbers, duplicate member names and nesting deeper
    than MAX_DEPTH (ValueError)."""
    text = fh.read()
    _check_depth(text)
    try:
        return json.loads(text, parse_constant=_no_constant, parse_float=_finite_float, parse_int=_bounded_int,
                          object_pairs_hook=_unique_members)
    except RecursionError as exc:  # unreachable after _check_depth; never a traceback
        raise ValueError(f"JSON nesting is deeper than {MAX_DEPTH} levels (refused)") from exc


@functools.lru_cache(maxsize=8)
def load_contract(path):
    try:
        with open(path, encoding="utf-8") as fh:
            schema = strict_load(fh)
    except (OSError, ValueError) as exc:  # ValueError covers JSONDecodeError, UnicodeDecodeError and strict_load
        raise ContractError(f"cannot read contract {os.path.basename(path)}: {exc}") from exc
    if not isinstance(schema, dict):
        raise ContractError(f"contract {os.path.basename(path)} is not a JSON object")
    _check_keywords(schema, "#")
    return schema


def json_type(value):
    return JSON_TYPES.get(type(value), type(value).__name__)


def _is(value, kind):
    if kind == "number":
        return type(value) is int or (type(value) is float and math.isfinite(value))  # isfinite(huge int) overflows
    if kind == "integer":
        return type(value) is int
    return json_type(value) == kind


def _resolve(schema, root):
    seen = 0
    while "$ref" in schema:
        ref = schema["$ref"]
        if not (isinstance(ref, str) and ref.startswith("#/definitions/")) or seen > 16:
            raise ContractError(f"contract reference {ref!r} cannot be resolved")
        schema = (root.get("definitions") or {}).get(ref[len("#/definitions/"):])
        if not isinstance(schema, dict):
            raise ContractError(f"contract reference {ref!r} cannot be resolved")
        seen += 1
    return schema


def _fail(where, rule, value):
    raise ContractError(f"invalid input: {where} must be {rule}, got {json_type(value)} "
                        "(the contract is enforced in full; nothing is coerced)")


def id_member(key):
    """'one' or 'many' when a member name marks an identifier (or a list of them), else None."""
    if not isinstance(key, str):
        return None
    words = _canon_member(key).split()
    if words and words[-1] in ID_MEMBER_WORDS:
        return ID_MEMBER_WORDS[words[-1]]
    camel = ID_MEMBER_CAMEL_RE.search(unicodedata.normalize("NFKC", key))
    return ("many" if camel.group(1) else "one") if camel else None


_VOCABULARY = {}


def vocabulary(root):
    """Every member name the contract declares anywhere (trusted vocabulary). A supplied member name is written into an
    error path only when it is one of these; any other name - even one of ID shape, such as another client's name
    followed by _id - is written by position (<member #n>), so no message repeats supplied text (r18)."""
    cached = _VOCABULARY.get(id(root))
    if cached is None or cached[0] is not root:
        names, stack = set(), [root]
        while stack:
            schema = stack.pop()
            if isinstance(schema, dict):
                names.update(k for k in (schema.get("properties") or {}) if isinstance(k, str))
                stack += [v for k, v in schema.items() if isinstance(v, dict)]
        cached = _VOCABULARY[id(root)] = (root, frozenset(names))
    return cached[1]


def _member_path(where, key, n, names):
    return f"{where}.{key}" if key in names else f"{where}.<member #{n}>"


def _id_value(value):
    return isinstance(value, str) and FORMATS["record-id-or-withheld"](value)


def check_undeclared(key, value, where, n, names=frozenset()):
    """A member the contract does not declare (and everything nested in it): ID-like names are type- and
    shape-checked (fail closed), every other value is only walked. Raise ContractError at the first violation.
    names is the contract vocabulary (vocabulary(root)): only those names are ever written into a path."""
    path = _member_path(where, key, n, names)
    kind = id_member(key)
    if kind == "one" and not (value is None or _id_value(value)):
        _fail(path, UNDECLARED_ID_RULES["one"], value)
    if kind == "many":
        if not (value is None or isinstance(value, list)):
            _fail(path, UNDECLARED_ID_RULES["many"], value)
        for i, item in enumerate(value or []):
            if not _id_value(item):
                _fail(f"{path}[{i}]", ID_RULE, item)
    _walk_undeclared(value, path, names)


def _walk_undeclared(value, where, names):
    if isinstance(value, dict):
        for m, (inner, item) in enumerate(value.items(), start=1):
            check_undeclared(inner, item, where, m, names)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _walk_undeclared(item, f"{where}[{i}]", names)


def validate(value, schema, root, where="packet"):
    """Raise ContractError at the first violation of schema (resolved against root) by value."""
    schema = _resolve(schema, root)
    if set(schema) - KEYWORDS - ANNOTATIONS:
        raise ContractError(f"contract uses an unsupported keyword at {where}; the walker cannot enforce it (fail closed)")
    kinds = schema.get("type")
    if kinds is not None:
        kinds = [kinds] if isinstance(kinds, str) else list(kinds)
        if not any(_is(value, k) for k in kinds):
            _fail(where, " or ".join(kinds), value)
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        raise ContractError(f"invalid input: {where} must be the contract constant (fail closed)")
    if "enum" in schema and not any(value == v and type(value) is type(v) for v in schema["enum"]):
        raise ContractError(f"invalid input: {where} must be one of {', '.join(map(str, schema['enum']))}; an "
                            f"unrecognised {json_type(value)} value is rejected (fail closed)")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            _fail(where, f"a string of at least {schema['minLength']} character(s)", value)
        if "pattern" in schema and not re.search(schema["pattern"], value):
            _fail(where, f"a string matching the contract pattern {schema['pattern']}", value)
        if "format" in schema and not FORMATS.get(schema["format"], lambda _: False)(value):
            _fail(where, FORMAT_RULES.get(schema["format"], f"a valid {schema['format']} value"), value)
    if _is(value, "number"):
        if "minimum" in schema and value < schema["minimum"]:
            _fail(where, f"a number >= {schema['minimum']}", value)
        if "maximum" in schema and value > schema["maximum"]:
            _fail(where, f"a number <= {schema['maximum']}", value)
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise ContractError(f"invalid input: {where} is missing required field '{key}'")
        properties = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        names = schema.get("propertyNames")
        for n, (key, item) in enumerate(value.items(), start=1):
            if names is not None:
                validate(key, names, root, f"{where} member #{n} name")
            if key in properties:
                validate(item, properties[key], root, f"{where}.{key}")
            elif extra is False:
                raise ContractError(f"invalid input: {where} has a field the contract does not allow")
            elif isinstance(extra, dict):
                # A map key is input text: the path names its position, never the key itself.
                validate(item, extra, root, f"{where}.<member #{n}>")
            else:
                check_undeclared(key, item, where, n, vocabulary(root))
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            validate(item, schema["items"], root, f"{where}[{i}]")


def validate_packet(packet, script_dir):
    """Validate a whole packet against the contract shipped with the engine in script_dir."""
    root = load_contract(contract_path(script_dir))
    validate(packet, root, root)
    return packet


def string_paths(schema, root, where="packet"):
    """Every field path whose value may be a string: [(path, leaf schema)]. Array items are written "[]"."""
    schema = _resolve(schema, root)
    out = []
    kinds = schema.get("type")
    kinds = [kinds] if isinstance(kinds, str) else list(kinds or [])
    if "string" in kinds or (not kinds and ("enum" in schema or "const" in schema or "pattern" in schema)):
        out.append((where, schema))
    for key, sub in schema.get("properties", {}).items():
        out += string_paths(sub, root, f"{where}.{key}")
    if isinstance(schema.get("items"), dict):
        out += string_paths(schema["items"], root, f"{where}[]")
    if isinstance(schema.get("additionalProperties"), dict):
        out += string_paths(schema["additionalProperties"], root, f"{where}.*")
    return out
