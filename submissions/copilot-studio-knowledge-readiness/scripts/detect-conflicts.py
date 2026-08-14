#!/usr/bin/env python3

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


KEYWORD_PATTERN = re.compile(
    r"\b(policy|eligib\w+|approval|required|must|cannot|allowed|deadline|limit|exception|access|request)\b",
    re.IGNORECASE,
)


def normalize_statement(line: str) -> str:
    line = re.sub(r"\s+", " ", line.strip())
    return line


def statement_key(statement: str) -> str:
    words = re.findall(r"\b[a-zA-Z]{4,}\b", statement.lower())
    filtered = [word for word in words if word not in {"should", "would", "could", "there", "their", "about"}]
    return " ".join(filtered[:8])


def collect_statements(root: Path) -> list[dict]:
    rows = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".md", ".html"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            statement = normalize_statement(line)
            if len(statement) < 40 or not KEYWORD_PATTERN.search(statement):
                continue
            rows.append({
                "file": str(path),
                "line": line_number,
                "key": statement_key(statement),
                "statement": statement,
            })
    return rows


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python detect-conflicts.py <folder>", file=sys.stderr)
        sys.exit(1)

    root = Path(sys.argv[1])
    if not root.exists():
        print(f"Folder not found: {root}", file=sys.stderr)
        sys.exit(1)
    if not root.is_dir():
        print(f"Expected a folder, got a file: {root}", file=sys.stderr)
        sys.exit(1)

    statements = collect_statements(root)
    groups = defaultdict(list)
    for row in statements:
        if row["key"]:
            groups[row["key"]].append(row)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(newline="")

    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=["key", "file", "line", "statement"],
        lineterminator="\n",
    )
    writer.writeheader()
    for key, rows in sorted(groups.items()):
        source_files = {row["file"] for row in rows}
        if len(rows) > 1 and len(source_files) > 1:
            for row in rows:
                writer.writerow(row)


if __name__ == "__main__":
    main()
