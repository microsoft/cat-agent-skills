#!/usr/bin/env python3
"""Score claims against a corpus. Verdicts come from this script, never from the model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from auditlib import AuditError, canonical_json, load_claims, segment_claims, verify_claims


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify atomic claims against an ingested corpus.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--claims", type=Path, help="JSON file of atomic claims.")
    parser.add_argument(
        "--segment",
        action="store_true",
        help="Build deterministic sentence candidates from the draft. Split any sentence that states two facts before treating the ledger as final.",
    )
    parser.add_argument("--claims-out", type=Path, help="Where to write the claims that were verified.")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if not args.corpus.is_file():
            raise AuditError(f"Corpus file not found: {args.corpus}")
        corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
        if args.claims and args.segment:
            raise AuditError("Pass either --claims or --segment, not both.")
        if args.claims:
            claims = load_claims(json.loads(args.claims.read_text(encoding="utf-8")))
            origin = "claims-file"
        elif args.segment:
            claims = segment_claims(corpus["draft"])
            origin = "deterministic-segmenter"
        else:
            raise AuditError("Pass --claims claims.json, or --segment to draft sentence candidates.")
        verdicts = verify_claims(corpus, claims, origin)
        if args.claims_out:
            args.claims_out.parent.mkdir(parents=True, exist_ok=True)
            args.claims_out.write_text(canonical_json({"claims": claims}), encoding="utf-8")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(canonical_json(verdicts), encoding="utf-8")
    except AuditError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}", file=sys.stderr)
        return 2
    totals = verdicts["totals"]
    if not verdicts["certified"]:
        print(verdicts["reason"])
        return 2
    print(
        f"{totals['claims']} claims: {totals['SUPPORTED']} SUPPORTED, "
        f"{totals['PARTIAL']} PARTIAL, {totals['UNSUPPORTED']} UNSUPPORTED, "
        f"{totals['STALE']} STALE"
    )
    print(f"Verdicts -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
