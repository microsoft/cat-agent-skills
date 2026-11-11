"""Shared local validation, deterministic history, and draft-only governance.

No network, wall-clock reads, notifications, filing, or persistence beyond --out.
The schema checker deliberately supports only the keywords used by this contract;
it is not a general JSON Schema implementation.
"""
import hashlib
import json
import math
import re
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTRACT = "mfg.safety-incident-assist.v2"
RELEASE = "2.0.0-rc.7"


def check_schema(value, schema, path="$"):
    types = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None,
    }
    if "type" in schema:
        allowed = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(types[t](value) for t in allowed):
            raise ValueError(f"{path}: expected {allowed}")
    def json_equal(a, b):
        # Python otherwise equates true/1 and false/0; JSON does not.
        if isinstance(a, bool) or isinstance(b, bool):
            return type(a) is type(b) and a == b
        return a == b
    if "enum" in schema and not any(json_equal(value, item) for item in schema["enum"]):
        raise ValueError(f"{path}: not in enum")
    if "const" in schema and not json_equal(value, schema["const"]):
        raise ValueError(f"{path}: wrong constant")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise ValueError(f"{path}.{key}: required")
        props = schema.get("properties", {})
        for key, item in value.items():
            if key in props:
                check_schema(item, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                raise ValueError(f"{path}: unsupported field")
    elif isinstance(value, list):
        if len(value) > schema.get("maxItems", len(value)):
            raise ValueError(f"{path}: too many items")
        for index, item in enumerate(value):
            check_schema(item, schema.get("items", {}), f"{path}[{index}]")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            raise ValueError(f"{path}: duplicate items")
    elif isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            raise ValueError(f"{path}: empty string")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ValueError(f"{path}: invalid pattern")
        if schema.get("format") == "date":
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                raise ValueError(f"{path}: canonical calendar date YYYY-MM-DD required")
            date.fromisoformat(value)
        if schema.get("format") == "date-time":
            # Deliberately narrower canonical RFC3339 profile: uppercase T/Z, seconds,
            # explicit known offset, no leap seconds or unknown-offset -00:00.
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})", value):
                raise ValueError(f"{path}: canonical timezone-qualified RFC3339 required")
            if value.endswith("-00:00"):
                raise ValueError(f"{path}: unknown timezone offset not supported")
            if value[-6:-5] in ("+", "-") and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
                raise ValueError(f"{path}: invalid timezone offset")
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError(f"{path}: timezone offset required")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{path}: non-finite number")
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            raise ValueError(f"{path}: outside bounds")


def validate(payload):
    schema = json.loads((ROOT / "contracts" / f"{CONTRACT}.json").read_text(encoding="utf-8"))
    check_schema(payload, schema)
    query = payload.get("history_query", {})
    if query.get("as_of") is not None and query.get("window_days") is not None:
        # Compare ordinals before timedelta construction: date.min is ordinal 1.
        if query["window_days"] >= date.fromisoformat(query["as_of"]).toordinal():
            raise ValueError("$.history_query: as_of - window_days precedes supported calendar minimum")


def load(path):
    def reject_constant(value):
        raise ValueError(f"non-finite JSON number: {value}")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("non-finite JSON number")
        return parsed
    with open(path, encoding="utf-8") as stream:
        payload = json.load(stream, parse_constant=reject_constant, parse_float=finite_float,
                            object_pairs_hook=pairs)
    validate(payload)
    return payload


def history_match(payload):
    query = payload.get("history_query")
    source = payload.get("history_input")
    failed = {"status": "review_required", "repeat_count": None, "repeat_pattern": None,
              "prior_incidents": [], "source": "engine:history_match",
              "reason": "Complete, cited log and explicit date/window/area/asset query required."}
    if not query or not source or source.get("complete") is not True:
        return failed
    if not all(query.get(k) for k in ("as_of", "window_days", "area", "asset_or_area", "citation")):
        return failed
    if not source.get("citation"):
        return failed
    records = source.get("records")
    if records is None:
        return failed
    end = date.fromisoformat(query["as_of"])
    if query["window_days"] >= end.toordinal():
        raise ValueError("$.history_query: as_of - window_days precedes supported calendar minimum")
    start = end - timedelta(days=query["window_days"])
    unique = {}
    for record in records:
        if not all(record.get(k) for k in ("incident_id", "date", "area", "asset_or_area", "type", "citation")):
            return {**failed, "reason": "History row missing identity/date/matching fields/citation."}
        key = record["incident_id"]
        if key in unique and unique[key] != record:
            return {**failed, "reason": f"Conflicting duplicate history ID: {key}"}
        unique[key] = record
    matches = []
    for record in unique.values():
        d = date.fromisoformat(record["date"])
        if not (start <= d < end) or record["incident_id"] == payload["incident_id"]:
            continue
        if any(record[k] != query[k] for k in ("area", "asset_or_area")):
            continue
        if query.get("types") and record["type"] not in query["types"]:
            continue
        if query.get("body_parts"):
            if not record.get("body_part", "").strip():
                return {**failed, "reason": "Eligible history row missing body_part required by the active filter."}
            if record["body_part"] not in query["body_parts"]:
                continue
        matches.append(record)
    matches.sort(key=lambda r: (r["date"], r["incident_id"]))
    return {"status": "computed", "as_of": query["as_of"], "window_days": query["window_days"],
            "window_start_inclusive": start.isoformat(), "window_end_exclusive": end.isoformat(),
            "match_criteria": {k: query.get(k, []) for k in ("area", "asset_or_area", "types", "body_parts")},
            "repeat_count": len(matches), "repeat_pattern": len(matches) >= 2,
            "prior_incidents": matches, "source": "engine:history_match",
            "citation": source["citation"], "query_citation": query["citation"],
            "source_sha256": hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest(),
            "reason": "Exact area AND asset; optional exact type/body filters; two prior matches trigger repeat."}


def governance(payload, classification):
    prior = payload.get("prior_determination", {})
    downward = (prior.get("recordable") is True and classification["recordable"]["value"] is not True
                or prior.get("reportable") is True and classification["reportable"]["value"] is not True)
    hold = payload.get("downgrade_request", {}).get("present") is True or downward
    return {"status": "draft_review_required", "downgrade_hold": bool(hold),
            "ehs_approval_verified": False, "filing_confirmation_verified": False,
            "closure_allowed": False, "action_execution_allowed": False,
            "reason": "EHS REVIEW REQUIRED / COWORK RE-EVAL PENDING. No authenticated approval, filing, or closure workflow.",
            "reporting_review_required": classification["reportable"]["value"] is None}


def finish(payload, out, engine):
    prov = payload.setdefault("provenance", {})
    engines = prov.setdefault("engines", [])
    name = f"{engine}/{RELEASE}"
    if name not in engines:
        engines.append(name)
    prov.pop("generated_at", None)
    prov["determinism"] = "No wall-clock timestamp; facts and supplied history as_of only."
    validate(payload)
    serialized = json.dumps(payload, indent=2, allow_nan=False) + "\n"
    with open(out, "w", encoding="utf-8") as stream:
        stream.write(serialized)


def diagnostic(exc):
    """Keep local validation detail without echoing filenames or arbitrary keys."""
    if isinstance(exc, OSError):
        return "Local file access/write failed; inspect permissions and paths in the approved environment."
    if isinstance(exc, KeyError):
        return "Required field missing; inspect the supplied payload locally."
    return str(exc)
