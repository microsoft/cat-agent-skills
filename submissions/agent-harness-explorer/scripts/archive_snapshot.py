#!/usr/bin/env python3
"""Write a date-stamped, reviewable snapshot bundle to an archive folder.

Each capture is stored under one date-based name so the JSON (source of truth),
the Markdown inventory (diff-friendly for review), and the self-contained HTML
report (for eyeballing) always line up:

    2026-07-14-agent-harness-snapshot.json
    2026-07-14-agent-harness-snapshot.md
    2026-07-14-agent-harness-snapshot.html

A second capture on the same day gets a `-2`, `-3`, ... suffix so historical
files are never overwritten.

An `index.md` in the archive folder is created and updated so captures can be
browsed and reviewed without regenerating anything.

Typical use (keep the growing archive OUTSIDE any published skill bundle):

    python archive_snapshot.py --out-dir ../../../snapshot-archive
    python archive_snapshot.py --snapshot existing.json --out-dir ./reports
    python archive_snapshot.py --out-dir ./reports --formats json,md

Historical files are never overwritten; each run adds a new dated set.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import capture_snapshot
import generate_html_report
import generate_library_inventory

DEFAULT_CATALOG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "references",
    "python-library-catalog.yaml",
)
INDEX_START = "<!-- captures:start -->"
INDEX_END = "<!-- captures:end -->"


def _unique_base(out_dir: str, base: str, formats: list[str]) -> str:
    """Return a base filename that does not collide with existing captures.

    Date-based names can repeat within a day; append -2, -3, ... so historical
    files are never overwritten.
    """
    exts = list(formats)
    candidate = base
    n = 2
    while any(os.path.exists(os.path.join(out_dir, f"{candidate}.{e}")) for e in exts):
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def _load_snapshot(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _summary_counts(snapshot: dict) -> dict:
    summ = snapshot.get("summary", {}) or {}
    libs = snapshot.get("pythonLibraries", []) or []
    new = sum(1 for l in libs if l.get("catalogStatus") == "uncataloged")
    return {
        "libraries": summ.get("libraries", len(libs)),
        "new": new,
        "fingerprint": snapshot.get("fingerprint", ""),
    }


def _index_row(stamp: str, base: str, counts: dict, formats: list[str]) -> str:
    links = []
    for ext, label in (("html", "HTML"), ("md", "Markdown"), ("json", "JSON")):
        if ext in formats:
            links.append(f"[{label}]({base}.{ext})")
    fp = counts["fingerprint"].replace("sha256:", "")[:12]
    return (
        f"| {stamp} | {counts['libraries']} | {counts['new']} | "
        f"`{fp}` | {' &middot; '.join(links)} |"
    )


def _rewrite_index(out_dir: str, new_row: str) -> str:
    path = os.path.join(out_dir, "index.md")
    header = [
        "# Snapshot archive",
        "",
        "Timestamped harness captures. Each row links the self-contained HTML "
        "report, the Markdown inventory, and the canonical JSON snapshot. "
        "Historical entries are never overwritten.",
        "",
        "| Captured (UTC) | Libraries | New | Fingerprint | Reports |",
        "| --- | ---: | ---: | --- | --- |",
        INDEX_START,
        INDEX_END,
    ]
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        if INDEX_START in text and INDEX_END in text:
            head, rest = text.split(INDEX_START, 1)
            rows_block, tail = rest.split(INDEX_END, 1)
            rows = [r for r in rows_block.splitlines() if r.strip()]
            rows.insert(0, new_row)  # newest first
            text = (
                head + INDEX_START + "\n" + "\n".join(rows) + "\n" + INDEX_END + tail
            )
        else:  # pragma: no cover - legacy/foreign index
            text = text.rstrip() + "\n" + new_row + "\n"
    else:
        rows = "\n".join(header).replace(
            INDEX_START + "\n" + INDEX_END,
            INDEX_START + "\n" + new_row + "\n" + INDEX_END,
        )
        text = rows + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def archive(
    out_dir: str,
    snapshot: dict,
    formats: list[str],
    when: datetime | None = None,
) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    when = when or datetime.now(timezone.utc)
    date_str = when.strftime("%Y-%m-%d")
    display = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    base = _unique_base(out_dir, f"{date_str}-agent-harness-snapshot", formats)
    written: dict[str, str] = {}

    if "json" in formats:
        p = os.path.join(out_dir, base + ".json")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
        written["json"] = p
    if "md" in formats:
        p = os.path.join(out_dir, base + ".md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(generate_library_inventory.render(snapshot))
        written["md"] = p
    if "html" in formats:
        p = os.path.join(out_dir, base + ".html")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(generate_html_report.render(snapshot))
        written["html"] = p

    counts = _summary_counts(snapshot)
    index_path = _rewrite_index(out_dir, _index_row(display, base, counts, formats))
    written["index"] = index_path
    return written


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Archive a timestamped snapshot bundle (json/md/html + index)."
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Archive folder. Keep this OUTSIDE any published skill bundle.",
    )
    parser.add_argument(
        "--snapshot",
        help="Existing snapshot.json to archive. If omitted, a fresh one is captured.",
    )
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--active-safe", action="store_true")
    parser.add_argument("--tools", help="Path to a tool-observations JSON file.")
    parser.add_argument(
        "--formats",
        default="json,md,html",
        help="Comma-separated subset of: json, md, html (default: all).",
    )
    args = parser.parse_args(argv[1:])

    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    invalid = [f for f in formats if f not in ("json", "md", "html")]
    if invalid:
        parser.error(f"unknown format(s): {', '.join(invalid)}")

    if args.snapshot:
        snapshot = _load_snapshot(args.snapshot)
    else:
        observations = None
        if args.tools:
            with open(args.tools, encoding="utf-8") as fh:
                observations = json.load(fh)
        snapshot = capture_snapshot.build_snapshot(
            catalog_path=args.catalog,
            active_safe=args.active_safe,
            tools_observations=observations,
        )

    written = archive(args.out_dir, snapshot, formats)
    print(f"Archived capture to {args.out_dir}")
    for kind in ("json", "md", "html", "index"):
        if kind in written:
            print(f"  {kind:5} -> {written[kind]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
