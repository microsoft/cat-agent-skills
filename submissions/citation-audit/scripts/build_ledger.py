#!/usr/bin/env python3
"""Write the claim-evidence ledger and the SHA-256 audit manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from auditlib import (
    AuditError,
    canonical_json,
    load_template,
    manifest_for,
    render_html,
    versioned_paths,
    write_csv,
    write_xlsx,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the citation ledger from verifier output.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--verdicts", type=Path, required=True)
    parser.add_argument("--claims", type=Path, help="Claims JSON. Defaults to claims embedded by a sibling claims file.")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
        verdicts = json.loads(args.verdicts.read_text(encoding="utf-8"))
        if args.claims:
            loaded = json.loads(args.claims.read_text(encoding="utf-8"))
            claims = loaded["claims"] if isinstance(loaded, dict) else loaded
        else:
            claims = [
                {
                    "id": row["id"],
                    "text": row["text"],
                    "type": row["type"],
                    "location": row["draft_location"],
                }
                for row in verdicts.get("results", [])
            ]
        manifest = manifest_for(corpus, claims, verdicts)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        paths = versioned_paths(args.out_dir)
        paths["html"].write_text(render_html(load_template(), verdicts), encoding="utf-8")
        write_csv(paths["csv"], verdicts)
        write_xlsx(paths["xlsx"], verdicts)
        paths["manifest"].write_text(canonical_json(manifest), encoding="utf-8")
    except AuditError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"Could not build the ledger: {exc}", file=sys.stderr)
        return 2
    if not verdicts.get("certified", False):
        print(verdicts.get("reason") or "Declined to certify.")
        print(f"Decline record -> {paths['manifest']}")
        return 2
    totals = verdicts["totals"]
    print(
        f"{totals['claims']} claims: {totals['SUPPORTED']} SUPPORTED, "
        f"{totals['PARTIAL']} PARTIAL, {totals['UNSUPPORTED']} UNSUPPORTED, "
        f"{totals['STALE']} STALE"
    )
    print(f"Ledger -> {paths['html']}")
    print(f"Manifest -> {paths['manifest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
