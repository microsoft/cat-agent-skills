#!/usr/bin/env python3
"""validate_contract - validate a hop payload against contracts/rtl.store-task-promotion-execution.v1.json.

Usage: python tools/validate_contract.py <payload.json> [--schema contracts/rtl.store-task-promotion-execution.v1.json]
Exit 0 = valid, 1 = invalid (errors printed), 2 = unreadable input.
Uses the `jsonschema` package when installed; otherwise a built-in checker covers the
schema's required / const / type / enum constraints so validation never silently skips.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMA = os.path.join(HERE, "..", "contracts", "rtl.store-task-promotion-execution.v1.json")
TYPES = {"object": dict, "array": list, "string": str, "number": (int, float), "integer": int, "boolean": bool}


def _check(node, schema, path, errors):
    if "const" in schema and node != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {node!r}")
    if "enum" in schema and node not in schema["enum"]:
        errors.append(f"{path}: {node!r} not in {schema['enum']}")
    t = schema.get("type")
    if t and (not isinstance(node, TYPES[t]) or (t == "number" and isinstance(node, bool))):
        errors.append(f"{path}: expected {t}, got {type(node).__name__}")
        return
    if isinstance(node, dict):
        for k in schema.get("required", []):
            if k not in node:
                errors.append(f"{path}: missing required '{k}'")
        for k, sub in schema.get("properties", {}).items():
            if k in node:
                _check(node[k], sub, f"{path}/{k}", errors)
    if isinstance(node, list) and "items" in schema:
        for i, item in enumerate(node):
            _check(item, schema["items"], f"{path}[{i}]", errors)


def validate(payload, schema):
    try:
        import jsonschema  # type: ignore
        errs = sorted(jsonschema.Draft7Validator(schema).iter_errors(payload), key=lambda e: list(e.path))
        return [f"/{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errs]
    except ImportError:
        errors = []
        _check(payload, schema, "", errors)
        return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("payload"); ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    a = ap.parse_args()
    try:
        payload = json.load(open(a.payload, encoding="utf-8"))
        schema = json.load(open(a.schema, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"validate_contract: cannot read input: {e}", file=sys.stderr); return 2
    errors = validate(payload, schema)
    if errors:
        print(f"validate_contract: INVALID ({len(errors)} error(s))")
        for e in errors:
            print("  -", e)
        return 1
    print(f"validate_contract: VALID - {os.path.basename(a.payload)} conforms to {schema.get('$id', 'schema')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
