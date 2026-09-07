#!/usr/bin/env python3
"""Render the Python library inventory as category-grouped Markdown.

    python generate_library_inventory.py snapshot.json [--out inventory.md]

Produces a browsable reference: libraries grouped by category, each with
version, description, and a documentation link, followed by a dedicated
section listing uncataloged packages that need curation.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict


def render(snapshot: dict) -> str:
    libs = snapshot.get("pythonLibraries", []) or []
    runtime = snapshot.get("runtime", {})

    lines = ["# Python Library Inventory", ""]
    lines.append(f"- **Observation date:** {snapshot.get('capturedAt', 'unknown')}")
    lines.append(f"- **Python version:** {runtime.get('pythonVersion', 'unknown')}")
    lines.append(f"- **Probe suite version:** {snapshot.get('probeSuiteVersion', 'unknown')}")
    lines.append(f"- **Catalog version:** {snapshot.get('catalogVersion', 'unknown')}")
    lines.append(f"- **Libraries discovered:** {len(libs)}")
    lines.append("")

    cataloged = [l for l in libs if l.get("catalogStatus") != "uncataloged"]
    uncataloged = [l for l in libs if l.get("catalogStatus") == "uncataloged"]

    by_category: dict[str, list] = defaultdict(list)
    for lib in cataloged:
        by_category[lib.get("category", "Uncategorized")].append(lib)

    for category in sorted(by_category):
        lines.append(f"## {category}")
        lines.append("")
        lines.append("| Library | Version | Description | Documentation |")
        lines.append("| --- | ---: | --- | --- |")
        for lib in sorted(by_category[category], key=lambda l: l.get("name", "").lower()):
            doc = lib.get("documentationUrl", "")
            doc_cell = f"[Documentation]({doc})" if doc else "—"
            desc = lib.get("description", "").replace("|", "\\|")
            lines.append(
                f"| {lib.get('name')} | {lib.get('version', '')} | {desc} | {doc_cell} |"
            )
        lines.append("")

    lines.append(f"## New packages ({len(uncataloged)})")
    lines.append("")
    if not uncataloged:
        lines.append("_All discovered packages are present in the curated catalog._")
    else:
        lines.append(
            "These packages are not yet in the agent-harness-explorer skill's "
            "curated catalog (`references/python-library-catalog.yaml`). "
            "Descriptions and links below are read from each package's "
            "installed metadata.")
        lines.append("")
        lines.append("| Library | Version | Description | Documentation |")
        lines.append("| --- | ---: | --- | --- |")
        for lib in sorted(uncataloged, key=lambda l: l.get("name", "").lower()):
            desc = (lib.get("description", "") or "").replace("|", "\\|")
            doc = lib.get("documentationUrl", "") or ""
            doc_cell = f"[link]({doc})" if doc else ""
            lines.append(
                f"| {lib.get('name')} | {lib.get('version', '')} | {desc} | {doc_cell} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Render the library inventory.")
    parser.add_argument("snapshot")
    parser.add_argument("--out")
    args = parser.parse_args(argv[1:])

    with open(args.snapshot, encoding="utf-8") as fh:
        snapshot = json.load(fh)
    text = render(snapshot)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote inventory to {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
