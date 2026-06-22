#!/usr/bin/env python3
"""Convert extracted expense line items (JSON) into the finance CSV format.

Usage:
    python build_report.py line_items.json > expense_report.csv

The input JSON is a list of objects:
    {"merchant": str, "date": "YYYY-MM-DD", "amount": float,
     "currency": str, "category": str, "note": str}
"""
import csv
import json
import sys

FIELDS = ["date", "merchant", "category", "amount", "currency", "note"]


def main(path: str) -> int:
    with open(path, encoding="utf-8") as fh:
        items = json.load(fh)

    writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS, extrasaction="ignore")
    writer.writeheader()
    total = 0.0
    for item in items:
        writer.writerow({k: item.get(k, "") for k in FIELDS})
        total += float(item.get("amount", 0) or 0)

    sys.stderr.write(f"Wrote {len(items)} line items, total {total:.2f}\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python build_report.py line_items.json")
    raise SystemExit(main(sys.argv[1]))
