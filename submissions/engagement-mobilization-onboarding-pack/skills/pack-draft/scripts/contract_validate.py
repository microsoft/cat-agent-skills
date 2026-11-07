#!/usr/bin/env python3
"""Stdlib validator for the shipped pipeline contract (ps.engagement-mobilization-onboarding-pack.v1).

It walks the contract JSON itself, so the schema is the only definition of shape: $ref ("#" or "#/$defs/<name>"),
allOf, anyOf, type, const, enum, pattern, format (date-time, date), minimum, maximum, minItems, maxProperties, required,
properties, prefixItems and items, through nested objects and arrays. The extension keyword x-uniqueKeys on an array of records names the keys that identify a
record: a repeat (unique_key, i.e. canon_id: NFKC, Cf stripped, case-folded, whitespace and -_. separators
collapsed; blanks and the engine's exact withheld placeholders are not identifiers) is a violation, so no stage ever indexes records
last-wins. canon_text / canon_person / canon_id / canon_header defined here are the plugin's one canonical comparison
form (safety_text re-exports them). The stage schemas ($defs/stage_scope, stage_matched, stage_governed, stage_access)
add what each point in the chain must carry, including the provenance engine prefixes. No coercion and no defaults: the
first violation raises ContractViolation, which every engine turns into a clean InputError before writing anything
(messages name the field path and the expected type, enum or pattern; a supplied value is never echoed)
(confidentiality-and-ethical-wall-rules.md #1.3). Byte-identical in every skill's scripts/ folder
(tests/check_shared_copies.py).
"""
import json, math, os, re, unicodedata
from datetime import datetime
CONTRACT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "contracts", "ps.engagement-mobilization-onboarding-pack.v1.json")
STAGES = ("scope", "matched", "governed", "access")
class ContractViolation(ValueError): pass
_JT = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}
_CACHE = {}
def load_contract(path=CONTRACT_FILE):
    if path not in _CACHE:
        try:
            with open(path, encoding="utf-8-sig") as f: _CACHE[path] = json.load(f, parse_constant=_no_constant)
        except (OSError, ValueError) as e: raise ContractViolation(f"bundled contract schema unreadable ({path}); fail closed") from e
    return _CACHE[path]
def _no_constant(c): raise ValueError(f"non-finite number {c}")
def _num(v): return isinstance(v, (int, float)) and not isinstance(v, bool)
def _type_ok(v, t):
    if t == "number": return _num(v)
    if t == "integer": return isinstance(v, int) and not isinstance(v, bool)
    if t not in _JT: raise ContractViolation(f"contract uses unsupported type {t!r}; fail closed")
    return isinstance(v, _JT[t])
def _need(ok, msg):
    if not ok: raise ContractViolation(msg)
# Carried timestamps are format-checked wherever the contract declares them, not only on the command line: date-time
# is the engines' own form (ISO-8601 UTC, seconds, Z) and a real calendar instant; date is YYYY-MM-DD and a real day.
_FORMATS = {"date-time": (re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ"), "%Y-%m-%dT%H:%M:%SZ", "2026-10-01T00:00:00Z"),
    "date": (re.compile(r"\d{4}-\d\d-\d\d"), "%Y-%m-%d", "2026-10-01")}
def format_ok(v, fmt):
    rx, f, _ = _FORMATS[fmt]
    if not isinstance(v, str) or not rx.fullmatch(v): return False
    try: datetime.strptime(v, f)
    except ValueError: return False
    return True
# The one canonical comparison form for identities, IDs, enums and CSV header names, shared by the contract walker
# and every engine (safety_text re-exports it). Comparisons use it; outputs keep the supplied value.
def _strip_cf(s): return "".join(c for c in s if unicodedata.category(c) != "Cf")
def canon_text(v):
    """NFKC, format (Cf) characters stripped, case-folded, whitespace collapsed; "" for a non-string."""
    if not isinstance(v, str): return ""
    return " ".join(_strip_cf(unicodedata.normalize("NFKC", _strip_cf(v))).casefold().split())
def canon_person(v):
    """A person's or client's name: `Taylor  Reed`, ` taylor reed ` and `Tay\u200blor Reed` compare equal."""
    return canon_text(v)
def canon_id(v):
    """An identifier: canon_text with the -, _ and . separators folded to spaces (`ws-a-plan` == `WS_A_PLAN`)."""
    return " ".join(re.sub(r"[-_.]+", " ", canon_text(v)).split())
def canon_header(v):
    """A CSV header name: canon_id joined with underscores (`ｃｌｉｅｎｔ＿ｎａｍｅ`, `Client Name` -> `client_name`)."""
    return canon_id(v).replace(" ", "_")
# The engine's withheld placeholders, exactly as the engines write them (safety_text uses this tuple). Only these exact
# strings are engine-withheld text; anything else shaped like them is supplied input (confidentiality-and-ethical-wall-rules.md #4.3).
ENGINE_PLACEHOLDERS = ("[withheld - source text held for embedded-instruction review, see Escalations and holds]",
    "[withheld - names another client or matter, see Escalations and holds]",
    "[briefing topic withheld - it names another client or matter, Risk/Conflicts brief the joiner directly]",
    "[withheld member name]")
def unique_key(v):
    """canon_id for duplicate detection; blanks and the exact engine placeholders are not identifiers (None). A
    marker-shaped value the engine did not write is an identifier like any other."""
    t = canon_id(v)
    return None if not t or v in ENGINE_PLACEHOLDERS else t
_id = unique_key
def _target(ref, root):
    if ref == "#": return root
    if ref.startswith("#/$defs/") and ref[8:] in root.get("$defs", {}): return root["$defs"][ref[8:]]
    raise ContractViolation(f"contract uses unsupported or unknown $ref {ref!r}; fail closed")
def _walk(v, s, path, root):
    if isinstance(v, float): _need(math.isfinite(v), f"{path} must be a finite number; fail closed")  # NaN/inf never pass a range check
    if "$ref" in s: _walk(v, _target(s["$ref"], root), path, root)
    for sub in s.get("allOf", []): _walk(v, sub, path, root)
    if "anyOf" in s:
        for sub in s["anyOf"]:
            try: _walk(v, sub, path, root); break
            except ContractViolation: continue
        else: raise ContractViolation(f"{path} matches none of the contract's allowed shapes for this field (value not repeated); fail closed")
    if "type" in s:
        ts = s["type"] if isinstance(s["type"], list) else [s["type"]]
        _need(any(_type_ok(v, t) for t in ts), f"{path} must be {' or '.join(ts)}, got {type(v).__name__}; fail closed")
    if "const" in s: _need(v == s["const"], f"{path} must be the contract constant {s['const']!r}; the supplied value is not repeated; fail closed")
    if "enum" in s: _need(v in s["enum"], f"{path} has an unrecognised value (not repeated); expected one of {', '.join(map(str, s['enum']))}; fail closed")
    if "pattern" in s and isinstance(v, str): _need(re.search(s["pattern"], v) is not None, f"{path} does not match the contract pattern {s['pattern']!r}; fail closed")
    if "format" in s and isinstance(v, str):
        if s["format"] not in _FORMATS: raise ContractViolation(f"contract uses unsupported format {s['format']!r}; fail closed")
        _need(format_ok(v, s["format"]), f"{path} is not a valid {s['format']} (expected the form {_FORMATS[s['format']][2]}; value not repeated); fail closed")
    if _num(v):
        if "minimum" in s: _need(v >= s["minimum"], f"{path} must be >= {s['minimum']}; fail closed")
        if "maximum" in s: _need(v <= s["maximum"], f"{path} must be <= {s['maximum']}; fail closed")
    if isinstance(v, dict):
        if "maxProperties" in s: _need(len(v) <= s["maxProperties"], f"{path} must have at most {s['maxProperties']} member(s); fail closed")
        for k in s.get("required", []): _need(k in v, f"{path}.{k} is required; fail closed")
        for k, sub in s.get("properties", {}).items():
            if k in v: _walk(v[k], sub, f"{path}.{k}", root)
    if isinstance(v, list):
        if "minItems" in s: _need(len(v) >= s["minItems"], f"{path} must have at least {s['minItems']} item(s); fail closed")
        pre = s.get("prefixItems", [])
        for i, (x, sub) in enumerate(zip(v, pre)): _walk(x, sub, f"{path}[{i}]", root)
        if "items" in s:
            for i, x in enumerate(v[len(pre):], len(pre)): _walk(x, s["items"], f"{path}[{i}]", root)
        for key in s.get("x-uniqueKeys", []):
            seen = {}
            for i, x in enumerate(v):
                t = _id(x.get(key)) if isinstance(x, dict) else None
                if t is None: continue
                _need(t not in seen, f"{path}[{i}].{key} repeats {path}[{seen.get(t)}].{key} (value not repeated); records keyed by {key} must be unique; fail closed")
                seen[t] = i
def validate(doc, where, stage=None, contract=None):
    """Validate doc against the whole contract (stage=None) or a stage schema; raise ContractViolation on the first
    violation, naming its path."""
    root = contract if contract is not None else load_contract()
    if stage is None: schema = root
    else:
        _need(stage in STAGES, f"unknown contract stage {stage!r}; fail closed")
        schema = _target("#/$defs/stage_" + stage, root)
    _walk(doc, schema, where, root)
