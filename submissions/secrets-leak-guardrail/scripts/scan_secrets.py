#!/usr/bin/env python3
"""Scan text or files for likely leaked secrets before they're shared.

Deterministic only: known credential formats by regex, plus a Shannon-entropy
check for `KEY = <random-looking string>` assignments that don't match a named
pattern. Judging whether a match is a *real* secret versus a fictional
documentation example is left to the agent. This script only finds
candidates.

Usage:
    python scripts/scan_secrets.py <file-or-directory> [--json]
    echo "some text" | python scripts/scan_secrets.py -
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

# Known formats: (name, regex). Ordered roughly by how load-bearing a false
# positive would be to explain.
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("AWS Access Key ID", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("AWS Secret Access Key (heuristic)", re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}['\"]?")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9\-_]{20}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,72}\b")),
    ("OpenAI/Anthropic-style API key", re.compile(r"\b(sk|rk)-[A-Za-z0-9]{20,64}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("Azure Storage connection string", re.compile(r"AccountKey=[A-Za-z0-9+/=]{20,}")),
    ("Generic connection-string password", re.compile(r"(?i)(password|pwd)\s*=\s*[^;'\"\s]{6,}")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("PEM private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("Bearer token", re.compile(r"(?i)authorization:\s*bearer\s+[A-Za-z0-9\-._~+/]{20,}")),
]

# KEY = value assignments where the value's own shape suggests a secret, even
# with no format above matching. Ceiling: entropy is a heuristic, not proof.
# Flag as "possible", never as a confirmed hit.
ASSIGNMENT = re.compile(
    r"(?im)^\s*([A-Za-z_][A-Za-z0-9_]*(?:SECRET|TOKEN|API_?KEY|PASSWORD|PWD|CREDENTIAL)[A-Za-z0-9_]*)\s*[:=]\s*['\"]?([^\s'\"]{12,})['\"]?\s*$"
)

ENTROPY_THRESHOLD = 3.5  # bits/char; typical English prose sits well below this


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts: dict[str, int] = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1
    length = len(value)
    return -sum((n / length) * math.log2(n / length) for n in counts.values())


def looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(word in lowered for word in ("example", "your_", "changeme", "placeholder", "xxxx", "<", "{{"))


def scan_text(text: str, source: str) -> list[dict]:
    findings: list[dict] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for name, pattern in PATTERNS:
            for match in pattern.finditer(line):
                findings.append({
                    "source": source,
                    "line": line_number,
                    "kind": name,
                    "confidence": "high",
                    "excerpt": _redact_middle(match.group(0)),
                })

        for match in ASSIGNMENT.finditer(line):
            key, value = match.group(1), match.group(2)
            if looks_like_placeholder(value):
                continue
            entropy = shannon_entropy(value)
            if entropy >= ENTROPY_THRESHOLD:
                findings.append({
                    "source": source,
                    "line": line_number,
                    "kind": f"High-entropy value assigned to {key}",
                    "confidence": "medium",
                    "excerpt": _redact_middle(f"{key}={value}"),
                })
    return findings


def _redact_middle(value: str) -> str:
    if len(value) <= 12:
        return value[:2] + "…" + value[-2:]
    return value[:6] + "…redacted…" + value[-4:]


def iter_files(path: str):
    if os.path.isfile(path):
        yield path
        return
    for root, _dirs, files in os.walk(path):
        if os.sep + ".git" in root + os.sep:
            continue
        for name in files:
            yield os.path.join(root, name)


def run(path: str) -> list[dict]:
    findings: list[dict] = []
    for file_path in iter_files(path):
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError):
            continue
        findings.extend(scan_text(text, file_path))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="file, directory, or '-' for stdin")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.path == "-":
        findings = scan_text(sys.stdin.read(), "<stdin>")
    elif os.path.exists(args.path):
        findings = run(args.path)
    else:
        raise SystemExit(f"No such file or directory: {args.path}")

    if args.json:
        print(json.dumps(findings, indent=2))
        return 0

    if not findings:
        print("No known secret patterns or high-entropy assignments found.")
        return 0

    print(f"{len(findings)} possible secret(s) found:\n")
    for item in findings:
        print(f"[{item['confidence']}] {item['kind']}")
        print(f"  {item['source']}:{item['line']}  {item['excerpt']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
