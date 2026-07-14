#!/usr/bin/env python3
"""Render a human-readable Markdown report from a snapshot JSON file.

    python generate_markdown_report.py snapshot.json [--out report.md]

The report summarizes the runtime, capability counts, non-Python
capabilities, and links to the library inventory. For the detailed,
category-grouped library table use generate_library_inventory.py.
"""
from __future__ import annotations

import argparse
import json
import sys


def render(snapshot: dict) -> str:
    runtime = snapshot.get("runtime", {})
    summary = snapshot.get("summary", {})
    lines = ["# Agent Harness Capability Report", ""]
    lines.append(f"- **Observation date:** {snapshot.get('capturedAt', 'unknown')}")
    lines.append(f"- **Snapshot ID:** `{snapshot.get('snapshotId', 'unknown')}`")
    lines.append(f"- **Python version:** {runtime.get('pythonVersion', 'unknown')}")
    lines.append(f"- **Platform:** {runtime.get('platform', 'unknown')}")
    lines.append(f"- **Skill version:** {snapshot.get('skillVersion', 'unknown')}")
    lines.append(f"- **Probe suite version:** {snapshot.get('probeSuiteVersion', 'unknown')}")
    lines.append(f"- **Fingerprint:** `{snapshot.get('fingerprint', 'unknown')}`")
    lines.append("")

    lines.append("## Capability summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("| --- | ---: |")
    for label, key in [
        ("Python libraries", "libraries"),
        ("Uncataloged libraries", "uncataloged"),
        ("Available capabilities", "available"),
        ("Visible tools / skills / MCP", "visible"),
        ("Restricted", "restricted"),
        ("Unknown / unverified", "unknown"),
    ]:
        lines.append(f"| {label} | {summary.get(key, 0)} |")
    lines.append("")

    # Non-library capabilities grouped by high-level kind.
    caps = [
        c
        for c in snapshot.get("capabilities", [])
        if not str(c.get("id", "")).startswith("python.package:")
    ]
    lines.append("## Runtime and environment capabilities")
    lines.append("")
    if not caps:
        lines.append("_No non-library capabilities recorded._")
    else:
        lines.append("| Capability | Status | Value |")
        lines.append("| --- | --- | --- |")
        for cap in caps:
            value = cap.get("value")
            value = "" if value is None else value
            lines.append(f"| `{cap.get('id')}` | {cap.get('status')} | {value} |")
    lines.append("")

    warnings = snapshot.get("warnings", [])
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append(
        "> For the full, category-grouped Python library table, generate the "
        "library inventory with `generate_library_inventory.py`."
    )
    return "\n".join(lines) + "\n"


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Render a Markdown snapshot report.")
    parser.add_argument("snapshot")
    parser.add_argument("--out")
    args = parser.parse_args(argv[1:])

    with open(args.snapshot, encoding="utf-8") as fh:
        snapshot = json.load(fh)
    text = render(snapshot)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote report to {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
