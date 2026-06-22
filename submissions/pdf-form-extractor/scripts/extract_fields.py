#!/usr/bin/env python3
"""Normalize and validate extracted PDF form fields against a JSON Schema.

Usage:
    python extract_fields.py fields.json schema.example.json

`fields.json` is a list of {"field": str, "value": str, "confidence": float}.
Outputs a normalized object plus a list of validation problems.
"""
import json
import re
import sys

LOW_CONFIDENCE = 0.7


def normalize(field: str, value: str):
    v = (value or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return v  # already ISO date
    if v.lower() in {"yes", "true", "checked", "x"}:
        return True
    if v.lower() in {"no", "false", "unchecked"}:
        return False
    digits = re.sub(r"[^\d+]", "", v)
    if re.fullmatch(r"\+?\d{10,15}", digits):
        return digits if digits.startswith("+") else "+" + digits
    return v


def main(fields_path: str, schema_path: str) -> int:
    with open(fields_path, encoding="utf-8") as fh:
        fields = json.load(fh)
    with open(schema_path, encoding="utf-8") as fh:
        schema = json.load(fh)

    required = set(schema.get("required", []))
    result, problems = {}, []

    for item in fields:
        name = item["field"]
        result[name] = normalize(name, item.get("value", ""))
        if float(item.get("confidence", 1)) < LOW_CONFIDENCE:
            problems.append(f"low confidence: {name}")

    for name in required - result.keys():
        problems.append(f"missing required field: {name}")

    json.dump({"fields": result, "problems": problems}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python extract_fields.py fields.json schema.example.json")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
