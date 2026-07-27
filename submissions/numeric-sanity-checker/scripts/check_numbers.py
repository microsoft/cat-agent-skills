#!/usr/bin/env python3
"""Verify the arithmetic in a numeric report before it ships.

Catches the three most common numeric slips in generated reports: parts that
don't actually sum to the stated total, percentages that don't sum to the
stated whole, and a percent-change figure that doesn't match the two numbers
it's supposedly derived from. Deterministic only. Whether the underlying
numbers themselves are correct is not this script's job, only whether the
arithmetic between the numbers given is consistent.

Usage:
    python check_numbers.py checks.json
    echo '[{"type": "sum", ...}]' | python check_numbers.py -

Input is a JSON list of check objects:

  {"type": "sum", "parts": [10, 20, 30], "claimed_total": 61, "tolerance": 0.01}
  {"type": "percentages", "values": [40, 35, 26], "expected_total": 100, "tolerance": 0.5}
  {"type": "percent_change", "old": 80, "new": 100, "claimed_pct": 20, "tolerance": 0.5}

"tolerance" is optional on every check type; sensible defaults are used if
omitted (rounding in a report is normal and not itself an error).
"""

from __future__ import annotations

import argparse
import json
import sys

DEFAULT_SUM_TOLERANCE = 0.01
DEFAULT_PERCENTAGE_TOLERANCE = 0.5
DEFAULT_PERCENT_CHANGE_TOLERANCE = 0.5


def check_sum(parts: list[float], claimed_total: float, tolerance: float = DEFAULT_SUM_TOLERANCE) -> dict:
    actual = sum(parts)
    diff = actual - claimed_total
    return {
        "type": "sum",
        "ok": abs(diff) <= tolerance,
        "actual": actual,
        "claimed": claimed_total,
        "diff": diff,
        "detail": f"parts sum to {actual}, claimed total is {claimed_total}",
    }


def check_percentages(values: list[float], expected_total: float = 100, tolerance: float = DEFAULT_PERCENTAGE_TOLERANCE) -> dict:
    actual = sum(values)
    diff = actual - expected_total
    return {
        "type": "percentages",
        "ok": abs(diff) <= tolerance,
        "actual": actual,
        "claimed": expected_total,
        "diff": diff,
        "detail": f"percentages sum to {actual}, expected {expected_total}",
    }


def check_percent_change(old: float, new: float, claimed_pct: float, tolerance: float = DEFAULT_PERCENT_CHANGE_TOLERANCE) -> dict:
    if old == 0:
        return {
            "type": "percent_change",
            "ok": False,
            "actual": None,
            "claimed": claimed_pct,
            "diff": None,
            "detail": "old value is 0; percent change is undefined, don't state one",
        }
    actual = (new - old) / old * 100
    diff = actual - claimed_pct
    return {
        "type": "percent_change",
        "ok": abs(diff) <= tolerance,
        "actual": round(actual, 4),
        "claimed": claimed_pct,
        "diff": round(diff, 4),
        "detail": f"({new} - {old}) / {old} * 100 = {round(actual, 4)}, claimed {claimed_pct}",
    }


CHECKERS = {
    "sum": lambda c: check_sum(c["parts"], c["claimed_total"], c.get("tolerance", DEFAULT_SUM_TOLERANCE)),
    "percentages": lambda c: check_percentages(c["values"], c.get("expected_total", 100), c.get("tolerance", DEFAULT_PERCENTAGE_TOLERANCE)),
    "percent_change": lambda c: check_percent_change(c["old"], c["new"], c["claimed_pct"], c.get("tolerance", DEFAULT_PERCENT_CHANGE_TOLERANCE)),
}


def run(checks: list[dict]) -> list[dict]:
    results = []
    for check in checks:
        kind = check.get("type")
        checker = CHECKERS.get(kind)
        if checker is None:
            results.append({"type": kind, "ok": False, "detail": f"unknown check type {kind!r}"})
            continue
        try:
            results.append(checker(check))
        except (KeyError, TypeError) as error:
            results.append({"type": kind, "ok": False, "detail": f"malformed check: {error}"})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="JSON file of checks, or '-' for stdin")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    checks = json.loads(text)
    results = run(checks)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0 if all(r["ok"] for r in results) else 1

    failed = [r for r in results if not r["ok"]]
    print(f"{len(results)} check(s), {len(failed)} failed.\n")
    for result in results:
        mark = "OK" if result["ok"] else "FAIL"
        print(f"[{mark}] {result['type']}: {result['detail']}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
