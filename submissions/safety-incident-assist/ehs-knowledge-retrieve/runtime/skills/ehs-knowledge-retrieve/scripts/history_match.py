#!/usr/bin/env python3
"""Deterministic local evidence matching; no retrieval connectors."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from safety_common import load, history_match, finish, diagnostic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    payload = load(args.intake)
    payload["history"] = history_match(payload)
    for stale in ("classification", "routing", "governance", "writeup", "next_best_action"):
        payload.pop(stale, None)
    finish(payload, args.out, "history_match")
    print("history_match: local DRAFT saved; supplied-file history only; HUMAN REVIEW REQUIRED.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"VALIDATION ERROR: {diagnostic(exc)}", file=sys.stderr)
        sys.exit(2)
