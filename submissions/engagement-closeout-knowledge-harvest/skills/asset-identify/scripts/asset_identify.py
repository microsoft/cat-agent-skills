#!/usr/bin/env python3
"""asset_identify - deterministic closeout deliverable index and reuse scoring (stage 1 of 3).

Reads a ps.engagement-closeout-knowledge-harvest.v1 engagement input and writes JSON. Every input is
validated strictly and every supplied free-text field is screened for embedded instructions before
any scoring (confidentiality-sanitisation-rules.md #8). Rules live in closeout_core.py and mirror
references/reuse-asset-rubric.md. No network, no model calls, no side effects beyond --out.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import closeout_core as core  # noqa: E402

ENGINE = "engine:asset_identify"
ENGINE_VERSION = core.ENGINE_VERSIONS["asset_identify"]
CONTRACT = core.CONTRACT
asset_score = core.asset_score
recommendation = core.recommendation
shelf_score = core.shelf_score


def _body(argv):
    parser = argparse.ArgumentParser(description="Score reusable closeout assets and index final deliverables.")
    parser.add_argument("--input", required=True, help="ps.engagement-closeout-knowledge-harvest.v1 engagement input JSON")
    parser.add_argument("--out", required=True, help="output JSON path")
    parser.add_argument("--generated-at", help="run timestamp YYYY-MM-DDTHH:MM:SSZ (else run_metadata.generated_at)")
    args = parser.parse_args(argv)
    raw, timestamp = core.validate_input(core.load_json(args.input), args.generated_at)
    doc = core.derive(raw, timestamp, upto=1)
    core.write_text(args.out, core.dump(doc))
    shortlist = doc["reusable_asset_shortlist"]
    gaps = sum(1 for d in doc["deliverable_index"] if d["completeness_gap"])
    shortlisted = sum(1 for a in shortlist if a["recommendation"] == "shortlist")
    print(f"asset_identify: {len(shortlist)} assets scored, {shortlisted} shortlisted, {gaps} deliverable gap(s)")
    if doc["screening_holds"]:
        print(f"asset_identify: {len(doc['screening_holds'])} field(s) withheld for embedded-instruction review")
    return 0


def main(argv=None):
    return core.run("asset_identify", argv, _body)


if __name__ == "__main__":
    sys.exit(main())