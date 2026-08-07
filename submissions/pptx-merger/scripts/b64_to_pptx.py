#!/usr/bin/env python3
"""
b64_to_pptx.py — Materialise a base64 string into a binary .pptx on disk, safely.

This is the stage that fixes the upstream corruption. The SharePoint connector
returns file content as base64 (pure ASCII), which survives any text pipeline.
The ONLY way that data gets destroyed is if some layer decodes the *binary*
through a UTF-8 text codec. This script never does that: it base64-decodes to
raw bytes and writes them with a binary handle ('wb'), then proves the result is
an intact OOXML ZIP before anyone downstream is allowed to touch it.

Usage:
    python b64_to_pptx.py <base64_input> <output.pptx> [--expected-bytes N] [--json]

<base64_input> may be:
    * a path to a file containing the base64 text, or
    * the literal base64 string (auto-detected if it isn't an existing path).

Exit code is 0 only if the written file is a valid, readable PPTX package.
On any integrity failure it exits non-zero and prints a diagnosis, so the agent
fails loudly instead of passing corrupted bytes to the merge stage.
"""

import sys
import json
import base64
import zipfile
import argparse
from pathlib import Path


def _load_b64_text(arg: str) -> str:
    p = Path(arg)
    if p.exists() and p.is_file():
        raw = p.read_text(encoding="utf-8", errors="strict")
    else:
        raw = arg
    # Strip whitespace/newlines and an optional data-URI prefix.
    raw = raw.strip()
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    return "".join(raw.split())


def _has_replacement_chars(arg: str) -> bool:
    # If the caller passed a file, a genuine base64 string can't contain U+FFFD.
    # Its presence means corruption already happened upstream of this script.
    p = Path(arg)
    try:
        txt = p.read_text(encoding="utf-8", errors="strict") if (p.exists() and p.is_file()) else arg
    except UnicodeDecodeError:
        return True
    return "\ufffd" in txt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("b64_input")
    ap.add_argument("output")
    ap.add_argument("--expected-bytes", type=int, default=None,
                    help="If provided, assert the decoded size matches exactly.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = {"ok": False, "output": args.output, "stage": "ingest"}

    # Guard 1: the base64 text itself must be clean ASCII.
    if _has_replacement_chars(args.b64_input):
        result["error"] = ("Input already contains U+FFFD replacement characters — "
                           "the binary was corrupted upstream of this script (a text/UTF-8 "
                           "codec touched the bytes before base64 reached here). Fix the "
                           "connector output so it stays base64/ASCII end to end.")
        print(json.dumps(result, indent=2) if args.json else result["error"])
        return 3

    try:
        b64 = _load_b64_text(args.b64_input)
    except UnicodeDecodeError:
        result["error"] = "Input file is not valid UTF-8 text; it is not clean base64."
        print(json.dumps(result, indent=2) if args.json else result["error"])
        return 3

    # Guard 2: decode strictly. validate=True rejects stray non-alphabet bytes.
    try:
        data = base64.b64decode(b64, validate=True)
    except Exception as e:  # noqa: BLE001
        result["error"] = f"base64 decode failed: {e}"
        print(json.dumps(result, indent=2) if args.json else result["error"])
        return 4

    # Binary write — never a text codec.
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as fh:
        fh.write(data)

    size = out.stat().st_size
    result["bytes"] = size

    # Guard 3: exact-size check if the connector reported a size.
    if args.expected_bytes is not None and size != args.expected_bytes:
        result["error"] = (f"Size mismatch: wrote {size} bytes, expected "
                           f"{args.expected_bytes}. Bytes were altered in transit.")
        print(json.dumps(result, indent=2) if args.json else result["error"])
        return 5

    # Guard 4: it must be a real, readable OOXML ZIP with the PPTX marker part.
    try:
        with zipfile.ZipFile(out) as z:
            bad = z.testzip()
            if bad is not None:
                raise zipfile.BadZipFile(f"CRC error in {bad}")
            names = set(z.namelist())
            if "[Content_Types].xml" not in names:
                raise KeyError("[Content_Types].xml missing — not an OOXML package")
            if not any(n.startswith("ppt/") for n in names):
                raise KeyError("no ppt/ parts — not a PowerPoint package")
            result["entries"] = len(names)
            result["slides"] = sum(
                1 for n in names
                if n.startswith("ppt/slides/slide") and n.endswith(".xml")
            )
    except Exception as e:  # noqa: BLE001
        result["error"] = (f"Decoded bytes are not a valid PPTX: {e}. "
                           "This means the file was corrupted before it reached ingest.")
        print(json.dumps(result, indent=2) if args.json else result["error"])
        return 6

    result["ok"] = True
    result["message"] = f"Wrote intact PPTX: {size} bytes, {result['slides']} slides."
    print(json.dumps(result, indent=2) if args.json else result["message"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
