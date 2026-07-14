#!/usr/bin/env python3
"""Compare two normalized capability snapshots by stable capability ID.

    python compare_snapshots.py old_snapshot.json new_snapshot.json \
        [--out comparison.json] [--markdown]

Comparison rules (see references/comparison-rules.md):
- A capability that is only missing because its probe failed or was skipped is
  reported as `unverified`, never `removed`.
- Package version changes are highlighted under `versionChanged`.
- Description / documentation-URL changes are catalog updates, not harness
  changes, so they never appear as behavior changes here.
"""
from __future__ import annotations

import argparse
import json
import sys

UNVERIFIED_STATUSES = {"unverified", "not-visible", "unknown"}

# Which probe is responsible for each capability-id namespace. Used so that a
# capability missing only because its probe was skipped/failed is reported as
# `unverified` rather than `removed`.
NAMESPACE_PROBE = [
    ("tool:", "tool-mcp-visibility"),
    ("skill:", "tool-mcp-visibility"),
    ("mcp.", "tool-mcp-visibility"),
    ("tool.visibility", "tool-mcp-visibility"),
    ("python.package:", "python-runtime-packages"),
    ("python.runtime", "python-runtime-packages"),
    ("runtime.", "runtime-environment"),
]

INCONCLUSIVE_PROBE_STATUSES = {"skipped", "failed", "partial"}


def _probe_status(snapshot: dict) -> dict:
    return {p.get("probeId"): p.get("status") for p in snapshot.get("probes", []) or []}


def _probe_inconclusive_for(cap_id: str, probe_status: dict) -> bool:
    """True if the probe covering this capability id was skipped/failed/partial."""
    for prefix, probe_id in NAMESPACE_PROBE:
        if cap_id.startswith(prefix):
            return probe_status.get(probe_id) in INCONCLUSIVE_PROBE_STATUSES
    return False


def _index(snapshot: dict) -> dict:
    """Map stable id -> record across libraries and capabilities."""
    records = {}
    for lib in snapshot.get("pythonLibraries", []) or []:
        records[lib["id"]] = {
            "kind": "library",
            "status": lib.get("status"),
            "version": lib.get("version"),
        }
    for cap in snapshot.get("capabilities", []) or []:
        records[cap["id"]] = {
            "kind": "capability",
            "status": cap.get("status"),
            "value": cap.get("value"),
        }
    return records


def compare(old: dict, new: dict) -> dict:
    old_idx = _index(old)
    new_idx = _index(new)
    new_probe_status = _probe_status(new)

    result = {
        "fromSnapshotId": old.get("snapshotId"),
        "toSnapshotId": new.get("snapshotId"),
        "fromFingerprint": old.get("fingerprint"),
        "toFingerprint": new.get("fingerprint"),
        "identical": old.get("fingerprint") == new.get("fingerprint"),
        "probeChanged": old.get("probeSuiteVersion") != new.get("probeSuiteVersion"),
        "added": [],
        "removed": [],
        "versionChanged": [],
        "statusChanged": [],
        "unverified": [],
    }

    for cid, rec in new_idx.items():
        if cid not in old_idx:
            result["added"].append({"id": cid, "status": rec.get("status")})

    for cid, old_rec in old_idx.items():
        new_rec = new_idx.get(cid)
        if new_rec is None:
            # Missing in new: only a removal if the responsible probe actually
            # ran. If that probe was skipped/failed/partial, absence is
            # inconclusive and must be reported as unverified, not removed.
            if _probe_inconclusive_for(cid, new_probe_status):
                result["unverified"].append({"id": cid})
            else:
                result["removed"].append({"id": cid, "wasStatus": old_rec.get("status")})
            continue
        # A capability that flipped to an unverified status is not a change of
        # the harness — mark it unverified.
        if new_rec.get("status") in UNVERIFIED_STATUSES and old_rec.get("status") not in UNVERIFIED_STATUSES:
            result["unverified"].append({"id": cid})
            continue
        if old_rec.get("version") != new_rec.get("version") and rec_has_version(old_rec, new_rec):
            result["versionChanged"].append(
                {
                    "id": cid,
                    "from": old_rec.get("version"),
                    "to": new_rec.get("version"),
                }
            )
        if old_rec.get("status") != new_rec.get("status"):
            result["statusChanged"].append(
                {
                    "id": cid,
                    "from": old_rec.get("status"),
                    "to": new_rec.get("status"),
                }
            )

    for key in ("added", "removed", "versionChanged", "statusChanged", "unverified"):
        result[key].sort(key=lambda x: x["id"])
    return result


def rec_has_version(old_rec: dict, new_rec: dict) -> bool:
    return "version" in old_rec and "version" in new_rec


def to_markdown(cmp: dict) -> str:
    lines = ["# Snapshot Comparison", ""]
    lines.append(f"- From: `{cmp['fromSnapshotId']}`")
    lines.append(f"- To: `{cmp['toSnapshotId']}`")
    lines.append(f"- Identical fingerprint: **{cmp['identical']}**")
    if cmp["probeChanged"]:
        lines.append("- ⚠️ Probe suite version changed — differences may reflect probe changes.")
    lines.append("")

    def section(title: str, items: list, fmt) -> None:
        lines.append(f"## {title} ({len(items)})")
        if not items:
            lines.append("_None_")
        else:
            for it in items:
                lines.append(f"- {fmt(it)}")
        lines.append("")

    section("Added", cmp["added"], lambda i: f"`{i['id']}`")
    section("Removed", cmp["removed"], lambda i: f"`{i['id']}` (was {i['wasStatus']})")
    section(
        "Version changed",
        cmp["versionChanged"],
        lambda i: f"`{i['id']}`: {i['from']} → {i['to']}",
    )
    section(
        "Status changed",
        cmp["statusChanged"],
        lambda i: f"`{i['id']}`: {i['from']} → {i['to']}",
    )
    section("Unverified", cmp["unverified"], lambda i: f"`{i['id']}`")
    return "\n".join(lines) + "\n"


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Compare two snapshots.")
    parser.add_argument("old")
    parser.add_argument("new")
    parser.add_argument("--out")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args(argv[1:])

    with open(args.old, encoding="utf-8") as fh:
        old = json.load(fh)
    with open(args.new, encoding="utf-8") as fh:
        new = json.load(fh)

    cmp = compare(old, new)
    text = to_markdown(cmp) if args.markdown else json.dumps(cmp, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
        print(f"Wrote comparison to {args.out}")
    else:
        sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
