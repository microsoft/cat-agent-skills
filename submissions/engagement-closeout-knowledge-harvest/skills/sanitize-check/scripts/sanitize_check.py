#!/usr/bin/env python3
"""sanitize_check - deterministic sanitisation gate and knowledge-record payload (stage 3 of 3).

Reads lesson_cluster output, re-derives it in full from the screened input it carries (an edited or
foreign intermediate is refused), assigns clearance states and builds the knowledge_record payload.
The rendered knowledge-record skeleton is screened as one document before it is returned
(confidentiality-sanitisation-rules.md #8.2). Rules live in closeout_core.py. The engine never
clears publication or external use. No network, no model calls, no side effects beyond --out.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import closeout_core as core  # noqa: E402

ENGINE = "engine:sanitize_check"
ENGINE_VERSION = core.ENGINE_VERSIONS["sanitize_check"]
CONTRACT = core.CONTRACT
AGGREGATION_MIN_TOKENS = core.AGGREGATION_MIN_TOKENS
SANITISATION_CONFIDENCE_FLOOR = core.SANITISATION_CONFIDENCE_FLOOR


def _body(argv):
    parser = argparse.ArgumentParser(description="Apply closeout sanitisation rules to lesson_cluster output.")
    parser.add_argument("--input", required=True, help="lesson_cluster output JSON")
    parser.add_argument("--out", required=True, help="output JSON path")
    args = parser.parse_args(argv)
    raw, timestamp, prior = core.verify(core.load_json(args.input), 2)
    doc = core.derive(raw, timestamp, prior, upto=3)
    core.write_text(args.out, core.dump(doc))
    overall = doc["sanitisation_report"]["overall_disposition"]
    print(f"sanitize_check: {len(doc['released_assets'])} release candidate(s), "
          f"{len(doc['held_assets'])} held asset(s), overall={overall}")
    if doc["screening_holds"]:
        print(f"sanitize_check: {len(doc['screening_holds'])} field(s) withheld for embedded-instruction review")
    return 0


def main(argv=None):
    return core.run("sanitize_check", argv, _body)


if __name__ == "__main__":
    sys.exit(main())