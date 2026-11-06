#!/usr/bin/env python3
"""validate_contract - stdlib-only validator for payloads on hls.reg-submission-authoring.v1.

  python3 base/scripts/validate_contract.py --payload <payload.json>

Supports the draft-07 subset the contract uses (type, required, properties, additionalProperties,
items, enum, const, minLength, maxLength, $ref to #/definitions). jsonschema is not needed and is not
available offline. minLength is what makes an empty citation ("") invalid, so an ungrounded fact cannot pass.
Exit 0 = valid, 1 = invalid (every violation printed), 2 = payload or contract unreadable.
Also reports source_facts keys that are not in config/field-dictionary.json (advisory, never a failure).
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CONTRACT = os.path.join(ROOT, "base", "contracts", "hls.reg-submission-authoring.v1.json")
DICTIONARY = os.path.join(ROOT, "config", "field-dictionary.json")
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def type_ok(value, t):
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES.get(t, object))


def check(value, schema, root, path, errors):
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        schema = root.get("definitions", {}).get(name, {})
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    t = schema.get("type")
    if t:
        allowed = t if isinstance(t, list) else [t]
        if not any(type_ok(value, x) for x in allowed):
            errors.append(f"{path}: expected type {t}, got {type(value).__name__}")
            return
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength {schema['minLength']} (got {len(value)})")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: string longer than maxLength {schema['maxLength']} (got {len(value)})")
    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: missing required key '{req}'")
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties")
        for k, v in value.items():
            if k in props:
                check(v, props[k], root, f"{path}.{k}", errors)
            elif isinstance(extra, dict):
                check(v, extra, root, f"{path}.{k}", errors)
            elif extra is False:
                errors.append(f"{path}: unexpected key '{k}'")
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for i, v in enumerate(value):
            check(v, schema["items"], root, f"{path}[{i}]", errors)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True)
    ap.add_argument("--contract", default=CONTRACT)
    a = ap.parse_args()
    try:
        payload = json.load(open(a.payload, encoding="utf-8"))
        contract = json.load(open(a.contract, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"validate_contract: ERROR unreadable input: {e}", file=sys.stderr)
        return 2
    errors = []
    check(payload, contract, contract, "$", errors)
    for e in errors:
        print(f"INVALID {e}")
    if os.path.exists(DICTIONARY) and isinstance(payload, dict):
        known = set(json.load(open(DICTIONARY, encoding="utf-8")).get("fields", {}))
        for k in sorted(set(payload.get("source_facts", {}) or {}) - known):
            print(f"ADVISORY source_facts['{k}'] is not in config/field-dictionary.json - add it or rename it")
    print(f"validate_contract: {'valid' if not errors else 'invalid'} ({len(errors)} violation(s)) -> {a.payload}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
