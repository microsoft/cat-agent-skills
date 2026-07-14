#!/usr/bin/env python3
"""Capture a normalized capability snapshot of the current harness.

Runs the probes, enriches the Python package inventory from the curated
catalog, assembles a canonical snapshot, and computes its fingerprint.

    python capture_snapshot.py \
        --catalog ../references/python-library-catalog.yaml \
        --out snapshot.json \
        [--active-safe] [--tools observations.json]

By default only passive probes run. `--active-safe` enables the opt-in
filesystem/subprocess/network probes described in the safety boundaries.
The snapshot is written to --out (or stdout when --out is omitted).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import canonicalize_snapshot as canon  # noqa: E402
import inspect_python  # noqa: E402
import inspect_runtime  # noqa: E402
import inspect_tools  # noqa: E402

SCHEMA_VERSION = "1.0"
SKILL_VERSION = "0.1.0"
PROBE_SUITE_VERSION = "0.1.0"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _enrich_packages(package_caps: list[dict], catalog: dict) -> list[dict]:
    entries = catalog.get("entries", {})
    enriched: list[dict] = []
    for cap in package_caps:
        name = cap.get("name", "")
        norm = canon.normalize_package_name(name)
        entry = entries.get(norm)
        record = {
            "id": f"python.package:{norm}",
            "name": name,
            "version": cap.get("version", ""),
            "status": "available",
        }
        if entry:
            record.update(
                {
                    "importName": entry.get("import_name"),
                    "category": entry.get("category", "Uncategorized"),
                    "description": entry.get("description", ""),
                    "documentationUrl": entry.get("documentation_url", ""),
                    "tags": entry.get("tags", []) or [],
                    "catalogStatus": "cataloged",
                    "descriptionSource": "catalog",
                }
            )
        else:
            meta_summary = (cap.get("metaSummary") or "").strip()
            meta_url = (cap.get("metaUrl") or "").strip()
            record.update(
                {
                    "category": "Uncataloged",
                    "description": meta_summary,
                    "documentationUrl": meta_url,
                    "catalogStatus": "uncataloged",
                    "descriptionSource": "package-metadata"
                    if (meta_summary or meta_url)
                    else "none",
                }
            )
        enriched.append(record)
    return sorted(enriched, key=lambda r: r["id"])


def _split_python_probe(envelope: dict) -> tuple[list[dict], list[dict]]:
    """Separate runtime capabilities from package capabilities."""
    runtime, packages = [], []
    for cap in envelope.get("capabilities", []):
        if str(cap.get("id", "")).startswith("python.package:"):
            packages.append(cap)
        else:
            runtime.append(cap)
    return runtime, packages


def build_snapshot(
    catalog_path: str,
    active_safe: bool = False,
    tools_observations: dict | None = None,
) -> dict:
    catalog = canon.load_catalog(catalog_path)

    py_env = inspect_python.run()
    rt_env = inspect_runtime.run(active_safe=active_safe)
    tools_env = inspect_tools.run(tools_observations)

    py_runtime_caps, py_package_caps = _split_python_probe(py_env)
    python_libraries = _enrich_packages(py_package_caps, catalog)

    capabilities: list[dict] = []
    capabilities.extend(py_runtime_caps)
    capabilities.extend(rt_env.get("capabilities", []))
    capabilities.extend(tools_env.get("capabilities", []))
    capabilities.sort(key=lambda c: str(c.get("id", "")))

    warnings: list[str] = []
    for env in (py_env, rt_env, tools_env):
        warnings.extend(env.get("warnings", []))

    runtime_meta = {}
    for cap in py_runtime_caps:
        if cap.get("id") == "python.runtime":
            runtime_meta = {
                "pythonVersion": cap.get("value"),
                **(cap.get("details") or {}),
            }

    now = _now()
    summary = {
        "available": sum(
            1 for c in capabilities if c.get("status") == "available"
        )
        + len(python_libraries),
        "visible": len(
            [c for c in capabilities if str(c.get("id", "")).startswith(("tool:", "skill:", "mcp."))]
        ),
        "restricted": sum(1 for c in capabilities if c.get("status") == "restricted"),
        "unknown": sum(
            1
            for c in capabilities
            if c.get("status") in {"unknown", "unverified", "not-visible"}
        ),
        "libraries": len(python_libraries),
        "uncataloged": sum(
            1 for l in python_libraries if l.get("catalogStatus") == "uncataloged"
        ),
    }

    snapshot = {
        "schemaVersion": SCHEMA_VERSION,
        "snapshotId": now.strftime("%Y-%m-%dT%H-%M-%SZ"),
        "capturedAt": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skillVersion": SKILL_VERSION,
        "probeSuiteVersion": PROBE_SUITE_VERSION,
        "catalogVersion": catalog.get("catalog_version"),
        "runtime": runtime_meta,
        "pythonLibraries": python_libraries,
        "capabilities": capabilities,
        "probes": [
            {
                "probeId": e["probeId"],
                "probeVersion": e["probeVersion"],
                "status": e["status"],
                "safetyLevel": e["safetyLevel"],
            }
            for e in (py_env, rt_env, tools_env)
        ],
        "warnings": warnings,
        "summary": summary,
    }
    snapshot["fingerprint"] = canon.fingerprint(snapshot)
    return snapshot


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Capture a harness snapshot.")
    parser.add_argument(
        "--catalog",
        default=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "references",
            "python-library-catalog.yaml",
        ),
    )
    parser.add_argument("--out")
    parser.add_argument("--active-safe", action="store_true")
    parser.add_argument("--tools", help="Path to a tool-observations JSON file.")
    args = parser.parse_args(argv[1:])

    observations = None
    if args.tools:
        with open(args.tools, encoding="utf-8") as fh:
            observations = json.load(fh)

    snapshot = build_snapshot(
        catalog_path=args.catalog,
        active_safe=args.active_safe,
        tools_observations=observations,
    )

    text = json.dumps(snapshot, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"Wrote snapshot {snapshot['snapshotId']} to {args.out}")
        print(f"Fingerprint: {snapshot['fingerprint']}")
        print(f"Libraries: {snapshot['summary']['libraries']} "
              f"({snapshot['summary']['uncataloged']} uncataloged)")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
