#!/usr/bin/env python3
"""
pptx_to_b64.py — Encode a binary .pptx back to base64 for the return trip.

The merged file must leave the sandbox the same way inputs came in: as base64
(ASCII), never as raw binary through a text channel. This encodes the file and
optionally verifies a round-trip (decode == original bytes) so a truncated or
altered encoding is caught here rather than in the user's PowerPoint.

Usage:
    python pptx_to_b64.py <input.pptx> [--out <file.txt>] [--json]

With --out, the base64 is written to that file (recommended for large decks so
the string never has to be inlined). Without it, the base64 is printed to stdout.
"""

import sys
import json
import base64
import zipfile
import argparse
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.pptx)
    meta = {"ok": False, "stage": "export", "file": str(path)}

    if not path.exists():
        meta["error"] = "input file does not exist"
        print(json.dumps(meta, indent=2) if args.json else meta["error"])
        return 2

    # Confirm we are exporting a real package, not something already broken.
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if (
                z.testzip() is not None
                or "[Content_Types].xml" not in names
                or not any(n.startswith("ppt/") for n in names)
            ):
                raise zipfile.BadZipFile("not a valid PPTX package")

    except Exception as e:  # noqa: BLE001
        meta["error"] = f"refusing to export invalid package: {e}"
        print(json.dumps(meta, indent=2) if args.json else meta["error"])
        return 3

    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")

    # Round-trip guard.
    if base64.b64decode(b64) != raw:
        meta["error"] = "round-trip mismatch (encoder produced altered bytes)"
        print(json.dumps(meta, indent=2) if args.json else meta["error"])
        return 4

    meta["ok"] = True
    meta["bytes"] = len(raw)
    meta["b64_len"] = len(b64)

    if args.out:
        Path(args.out).write_text(b64, encoding="ascii")
        meta["out"] = args.out
        print(json.dumps(meta, indent=2) if args.json else
              f"Wrote base64 ({len(b64)} chars) for {len(raw)} byte deck to {args.out}")
    else:
        if args.json:
            meta["base64"] = b64
            print(json.dumps(meta, indent=2))
        else:
            print(b64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
