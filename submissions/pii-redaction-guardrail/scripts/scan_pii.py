#!/usr/bin/env python3
"""Scan text or files for likely PII before it's shared, published, or sent to
a third-party service.

General-purpose, not the HIPAA Safe Harbor identifier set (see the
`phi-deidentifier` skill for clinical text specifically). Deterministic only:
regex shapes plus a checksum where one exists (credit cards via Luhn). Whether
a match is real PII versus a fictional example, and what to do about it
(redact, pseudonymize, ask first), is left to the agent.

Usage:
    python scan_pii.py <file-or-directory> [--json]
    echo "some text" | python scan_pii.py -
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Loose on purpose: phone formats vary too much by country to be precise.
# Flag as a candidate; false positives (order numbers, version strings) are
# expected and left for the agent to dismiss.
PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)[\s.-]?)?\d{3}[\s.-]?\d{3,4}[\s.-]?\d{3,4}(?!\d)")
US_SSN = re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")
IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b")
CREDIT_CARD_CANDIDATE = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def luhn_valid(digits: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(digits)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def find_credit_cards(line: str) -> list[str]:
    hits = []
    for match in CREDIT_CARD_CANDIDATE.finditer(line):
        digits = re.sub(r"[ -]", "", match.group(0))
        if 13 <= len(digits) <= 19 and luhn_valid(digits):
            hits.append(match.group(0))
    return hits


def redact(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def scan_text(text: str, source: str) -> list[dict]:
    findings: list[dict] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in EMAIL.finditer(line):
            findings.append(_hit(source, line_number, "Email address", match.group(0)))
        for match in US_SSN.finditer(line):
            findings.append(_hit(source, line_number, "US SSN-shaped number", match.group(0)))
        for match in IPV4.finditer(line):
            findings.append(_hit(source, line_number, "IPv4 address", match.group(0)))
        for card in find_credit_cards(line):
            findings.append(_hit(source, line_number, "Credit card number (Luhn-valid)", card))
        for match in PHONE.finditer(line):
            digits = re.sub(r"\D", "", match.group(0))
            if 7 <= len(digits) <= 15:
                findings.append(_hit(source, line_number, "Phone number (candidate)", match.group(0), confidence="low"))
    return findings


def _hit(source: str, line: int, kind: str, value: str, confidence: str = "high") -> dict:
    return {"source": source, "line": line, "kind": kind, "confidence": confidence, "value": redact(value)}


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
        print("No known PII patterns found. Phone-number matching is low-confidence by nature; review manually if the content is sensitive.")
        return 0

    print(f"{len(findings)} possible PII item(s) found:\n")
    for item in findings:
        print(f"[{item['confidence']}] {item['kind']}")
        print(f"  {item['source']}:{item['line']}  {item['value']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
