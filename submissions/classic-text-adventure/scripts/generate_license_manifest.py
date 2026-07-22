#!/usr/bin/env python3
"""Generate deterministic third-party and bundle file manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SIDECARS = {"metadata.json", "README.md"}
MANIFESTS = {
    "references/licenses/THIRD_PARTY_MANIFEST.json",
    "references/licenses/BUNDLE_MANIFEST.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record(root: Path, path: Path, origin: str, license_expression: str) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    if relative.startswith("scripts/runtime/adventure/"):
        copyright_notice = "Copyright 2010-2015 Brandon Rhodes; original Adventure content is public domain"
        modified = False
    elif relative == "assets/fonts/JetBrainsMono-Regular.ttf":
        copyright_notice = "Copyright 2020 The JetBrains Mono Project Authors"
        modified = False
    else:
        copyright_notice = "Copyright (c) Microsoft Corporation and contributors"
        modified = None
    return {
        "path": relative,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "origin": origin,
        "license": license_expression,
        "copyright": copyright_notice,
        "modified": modified,
    }


def classify(relative: str) -> tuple[str, str]:
    if relative == "assets/fonts/JetBrainsMono-Regular.ttf":
        return "JetBrains Mono 2.304", "OFL-1.1"
    if relative.startswith("scripts/runtime/adventure/"):
        if relative.endswith("advent.dat"):
            return "Adventure 1.7 / original Colossal Cave data", "LicenseRef-Public-Domain"
        if relative.endswith("README.txt") or "/tests/" in relative:
            return "Adventure 1.7", "Apache-2.0 AND LicenseRef-Public-Domain"
        return "Adventure 1.7", "Apache-2.0"
    if relative == "references/licenses/Apache-2.0.txt":
        return "Apache Software Foundation license text", "Apache-2.0"
    if relative == "references/licenses/OFL-1.1.txt":
        return "SIL Open Font License text", "OFL-1.1"
    return "classic-text-adventure skill", "MIT"


def build_manifests(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    third_party = []
    bundle = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        if relative == "references/licenses/BUNDLE_MANIFEST.json":
            continue
        origin, license_expression = classify(relative)
        record = _record(root, path, origin, license_expression)
        if relative not in SIDECARS:
            bundle.append(record)
        if relative.startswith("scripts/runtime/adventure/") or relative == "assets/fonts/JetBrainsMono-Regular.ttf":
            third_party.append(record)
    return (
        {
            "schema": 1,
            "sources": [
                {
                    "name": "adventure",
                    "version": "1.7",
                    "archive": "adventure-1.7.tar.gz",
                    "archive_sha256": "fba584064d3b8b1ef6b62f6df6099092522d6bd3bce0525db002c54dc29ac6a1",
                    "url": "https://files.pythonhosted.org/packages/source/a/adventure/adventure-1.7.tar.gz",
                },
                {
                    "name": "JetBrains Mono",
                    "version": "2.304",
                    "archive": "JetBrainsMono-2.304.zip",
                    "archive_sha256": "6f6376c6ed2960ea8a963cd7387ec9d76e3f629125bc33d1fdcd7eb7012f7bbf",
                    "url": "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip",
                },
            ],
            "files": third_party,
        },
        {
            "schema": 1,
            "excludes": sorted([*SIDECARS, "references/licenses/BUNDLE_MANIFEST.json"]),
            "files": bundle,
        },
    )


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    root = args.submission_root.resolve()
    third_party, _ = build_manifests(root)
    license_dir = root / "references" / "licenses"
    write_json(license_dir / "THIRD_PARTY_MANIFEST.json", third_party)
    _, bundle = build_manifests(root)
    write_json(license_dir / "BUNDLE_MANIFEST.json", bundle)
    print(json.dumps({"third_party_files": len(third_party["files"]), "bundle_files": len(bundle["files"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
