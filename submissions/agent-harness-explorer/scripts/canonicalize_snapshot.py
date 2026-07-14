#!/usr/bin/env python3
"""Canonicalization, normalization, fingerprinting, and catalog helpers.

This module is the shared foundation for the Agent Harness Explorer scripts.
It is safe to import (no side effects) and can also be run directly to
canonicalize a snapshot file:

    python canonicalize_snapshot.py snapshot.json > canonical.json

Design notes:
- No third-party dependencies are required. PyYAML is used when available,
  otherwise a small built-in loader parses the curated catalog (which uses a
  deliberately simple YAML subset).
- Fingerprints intentionally exclude volatile fields (timestamps, paths,
  prose) so that an unchanged harness produces an unchanged fingerprint.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from typing import Any, Dict, List

# Fields that must never influence the fingerprint because they change even
# when the observable capability set does not.
VOLATILE_FIELDS = {
    "capturedAt",
    "snapshotId",
    "durationMs",
    "description",
    "documentationUrl",
    "tempPath",
    "executablePath",
    "warnings",
    "errors",
}


def normalize_package_name(name: str) -> str:
    """Normalize a distribution name per PEP 503 (lowercase, dashes)."""
    return re.sub(r"[-_.]+", "-", (name or "").strip()).lower()


def stable_id(kind: str, *parts: str) -> str:
    """Build a stable capability identifier, e.g. 'python.package:python-docx'."""
    tail = "/".join(p for p in parts if p)
    return f"{kind}:{tail}" if tail else kind


def _strip_volatile(value: Any) -> Any:
    """Recursively remove volatile keys so they never affect the fingerprint."""
    if isinstance(value, dict):
        return {
            k: _strip_volatile(v)
            for k, v in value.items()
            if k not in VOLATILE_FIELDS
        }
    if isinstance(value, list):
        return [_strip_volatile(v) for v in value]
    return value


def _sort_capabilities(caps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(caps, key=lambda c: str(c.get("id", "")))


def canonical_payload(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Return the fingerprint-relevant, order-stable view of a snapshot."""
    libraries = _sort_capabilities(snapshot.get("pythonLibraries", []) or [])
    capabilities = _sort_capabilities(snapshot.get("capabilities", []) or [])
    payload = {
        "schemaVersion": snapshot.get("schemaVersion"),
        "probeSuiteVersion": snapshot.get("probeSuiteVersion"),
        "pythonLibraries": [
            {
                "id": lib.get("id"),
                "name": lib.get("name"),
                "version": lib.get("version"),
                "status": lib.get("status"),
            }
            for lib in libraries
        ],
        "capabilities": [
            {
                "id": cap.get("id"),
                "status": cap.get("status"),
                "value": cap.get("value"),
            }
            for cap in capabilities
        ],
    }
    return _strip_volatile(payload)


def canonical_json(value: Any) -> str:
    """Deterministic JSON serialization (sorted keys, compact separators)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(snapshot: Dict[str, Any]) -> str:
    """Compute the SHA-256 fingerprint of a snapshot's observable capabilities."""
    canonical = canonical_json(canonical_payload(snapshot))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


# ---------------------------------------------------------------------------
# Catalog loading (PyYAML when available, tiny fallback otherwise)
# ---------------------------------------------------------------------------

def _load_yaml_text(text: str) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return _minimal_catalog_parse(text)


def _minimal_catalog_parse(text: str) -> Dict[str, Any]:
    """Parse the curated catalog's simple YAML subset without PyYAML.

    Supports the exact shape used by python-library-catalog.yaml: top-level
    scalars, a `libraries:` list of mappings, and nested `tags:` lists.
    """
    result: Dict[str, Any] = {}
    libraries: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    in_libraries = False
    in_tags = False

    def unquote(v: str) -> str:
        v = v.strip()
        if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
            return v[1:-1]
        return v

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0:
            in_libraries = stripped.startswith("libraries:")
            in_tags = False
            if not in_libraries and ":" in stripped:
                key, _, val = stripped.partition(":")
                result[key.strip()] = unquote(val)
            continue

        if not in_libraries:
            continue

        if stripped.startswith("- "):
            current = {}
            libraries.append(current)
            in_tags = False
            key, _, val = stripped[2:].partition(":")
            if current is not None and key:
                current[key.strip()] = unquote(val)
        elif stripped.startswith("-"):
            if in_tags and current is not None:
                current.setdefault("tags", []).append(unquote(stripped[1:].strip()))
        elif current is not None:
            if stripped.startswith("tags:"):
                in_tags = True
                current["tags"] = []
            else:
                in_tags = False
                key, _, val = stripped.partition(":")
                current[key.strip()] = unquote(val)

    result["libraries"] = libraries
    return result


def load_catalog(path: str) -> Dict[str, Any]:
    """Load the curated catalog into {normalized_name: entry} plus metadata."""
    with open(path, encoding="utf-8") as fh:
        data = _load_yaml_text(fh.read())
    entries = {}
    for entry in data.get("libraries", []) or []:
        name = entry.get("name")
        if name:
            entries[normalize_package_name(name)] = entry
    return {
        "catalog_version": data.get("catalog_version"),
        "updated_at": data.get("updated_at"),
        "entries": entries,
    }


def _main(argv: List[str]) -> int:
    if len(argv) != 2:
        sys.exit("usage: python canonicalize_snapshot.py snapshot.json")
    with open(argv[1], encoding="utf-8") as fh:
        snapshot = json.load(fh)
    out = {
        "fingerprint": fingerprint(snapshot),
        "canonical": canonical_payload(snapshot),
    }
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
