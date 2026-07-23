#!/usr/bin/env python3

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


DATE_PATTERN = re.compile(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b")
HEADING_PATTERN = re.compile(r"^(#{1,6}\s+.+|[A-Z][A-Za-z0-9 ,/&()-]{3,80})$", re.MULTILINE)


def analyze_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    words = re.findall(r"\b\w+\b", text)
    headings = [match.group(0).strip() for match in HEADING_PATTERN.finditer(text)]
    dates = sorted(set(DATE_PATTERN.findall(text)))

    metadata_hints = {
        "owner": bool(re.search(r"\b(owner|owned by|contact)\b", text, re.IGNORECASE)),
        "review_date": bool(re.search(r"\b(reviewed|last reviewed|last updated)\b", text, re.IGNORECASE)),
        "effective_date": bool(re.search(r"\b(effective|starts on|valid from)\b", text, re.IGNORECASE)),
        "audience": bool(re.search(r"\b(audience|applies to|eligible|eligibility)\b", text, re.IGNORECASE)),
    }

    return {
        "file": str(path),
        "wordCount": len(words),
        "headingCount": len(headings),
        "sampleHeadings": headings[:10],
        "datesFound": dates[:20],
        "metadataHints": metadata_hints,
        "chunkingRisk": classify_chunking_risk(len(words), len(headings)),
    }


def classify_chunking_risk(word_count: int, heading_count: int) -> str:
    if word_count > 2500 and heading_count < 4:
        return "high"
    if word_count > 1500 and heading_count < 3:
        return "medium"
    return "low"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python analyze-exported-docs.py <folder>", file=sys.stderr)
        sys.exit(1)

    root = Path(sys.argv[1])
    if not root.exists():
        print(f"Folder not found: {root}", file=sys.stderr)
        sys.exit(1)
    if not root.is_dir():
        print(f"Expected a folder, got a file: {root}", file=sys.stderr)
        sys.exit(1)

    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".html", ".csv"}
    ]

    result = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "root": str(root),
        "fileCount": len(files),
        "files": [analyze_file(path) for path in files],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
