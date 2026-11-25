#!/usr/bin/env python3
"""Extract draft and source text for citation-audit. Standard library only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from auditlib import AuditError, canonical_json, document_record, text_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest a draft and its source corpus.")
    parser.add_argument("--draft", type=Path, help="Draft file (.md, .txt, .html, .docx, or .pdf).")
    parser.add_argument("--draft-text", help="Draft text when no file is available.")
    parser.add_argument("--draft-name", default="draft.txt", help="Label used with --draft-text.")
    parser.add_argument("--source", action="append", type=Path, default=[], help="Source file. Repeat for each source.")
    parser.add_argument(
        "--source-text",
        action="append",
        default=[],
        help="Inline source as name=text. Repeat for each source.",
    )
    parser.add_argument("--out", type=Path, required=True, help="Path for corpus.json.")
    args = parser.parse_args()
    try:
        if args.draft and args.draft_text:
            raise AuditError("Pass either --draft or --draft-text, not both.")
        if args.draft:
            draft = document_record(args.draft)
        elif args.draft_text:
            draft = text_record(args.draft_name, args.draft_text)
        else:
            raise AuditError("A draft is required (--draft or --draft-text).")
        sources = []
        for path in args.source:
            sources.append(document_record(path))
        for item in args.source_text:
            if "=" not in item:
                raise AuditError("--source-text must look like name=text.")
            name, text = item.split("=", 1)
            if not name.strip() or not text.strip():
                raise AuditError("--source-text needs a name and some text.")
            sources.append(text_record(name.strip(), text))
        if not sources:
            raise AuditError(
                "No source corpus was supplied. Citation audit declines to certify. "
                "Add the files the draft claims to be based on, then run ingest again."
            )
        payload = {"draft": draft, "sources": sources}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(canonical_json(payload), encoding="utf-8")
    except AuditError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Ingested 1 draft and {len(sources)} source(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
