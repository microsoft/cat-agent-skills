#!/usr/bin/env python3
"""lesson_cluster - deterministic lesson clustering (stage 2 of 3).

Reads asset_identify output, re-derives it in full from the screened input it carries (an edited or
foreign intermediate is refused) and adds lesson_clusters. Withheld evidence is never read; it is
clustered as unclassified with an embedded_instruction signal. Rules live in closeout_core.py and
mirror references/lesson-taxonomy.md. No network, no model calls, no side effects beyond --out.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import closeout_core as core  # noqa: E402

ENGINE = "engine:lesson_cluster"
ENGINE_VERSION = core.ENGINE_VERSIONS["lesson_cluster"]
CONTRACT = core.CONTRACT
CLUSTER_KEYWORDS = core.CLUSTER_KEYWORDS
category_for = core.category_for


def _body(argv):
    parser = argparse.ArgumentParser(description="Cluster closeout lessons from asset_identify output.")
    parser.add_argument("--input", required=True, help="asset_identify output JSON")
    parser.add_argument("--out", required=True, help="output JSON path")
    args = parser.parse_args(argv)
    raw, timestamp, prior = core.verify(core.load_json(args.input), 1)
    doc = core.derive(raw, timestamp, prior, upto=2)
    core.write_text(args.out, core.dump(doc))
    clusters = doc["lesson_clusters"]
    review = sum(1 for c in clusters if c["review_candidate"])
    print(f"lesson_cluster: {len(clusters)} cluster(s), {review} review candidate(s)")
    return 0


def main(argv=None):
    return core.run("lesson_cluster", argv, _body)


if __name__ == "__main__":
    sys.exit(main())