#!/usr/bin/env python3
"""slate_rank - deterministic provisional ranking for staffing slates.

``rank(scored_payload)`` is the pure engine (no file I/O); constraint_check and slate_validate import
it to re-derive this stage from roles.json and bench.json (independence-eligibility-rules.md #9.8).
A malformed scored.json is one ``error:`` line naming a field path, exit 2, and no output file.
"""
import copy
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from input_guard import (
    ArgumentParser,
    check_confidence,
    check_id,
    check_name,
    check_timestamp,
    field,
    is_num,
    load_json,
    need,
    run,
    write_json,
)

ENGINE = "engine:slate_rank"
ENGINE_VERSION = "slate_rank/1.1.14"
CONTRACT = "ps.engagement-staffing-bench-match.v1"


def append_engine(provenance, engine_version):
    engines = [
        engine for engine in provenance.get("engines", [])
        if not engine.startswith("slate_rank/")
    ]
    engines.append(engine_version)
    provenance["engines"] = list(dict.fromkeys(engines))


def validate_scored(payload):
    """Refuse a scored document whose ranking members are missing or mistyped (A1/A2/A7)."""
    need(isinstance(payload, dict), "scored.json: top level must be a JSON object")
    need(payload.get("contract_version") == CONTRACT, "scored.json: wrong contract version")
    roles = field(payload, "scored_roles", "list", "")
    need(roles, "scored_roles must not be empty")
    for index, role in enumerate(roles):
        where = f"scored_roles[{index}]"
        need(isinstance(role, dict), f"{where} must be an object")
        check_id(field(role, "role_id", "str", where), f"{where}.role_id")
        check_name(field(role, "role_title", "str", where), f"{where}.role_title")
        if "confidence" in role:
            check_confidence(role["confidence"], f"{where}.confidence")
        scores = field(role, "candidate_scores", "list", where)
        for position, candidate in enumerate(scores):
            path = f"{where}.candidate_scores[{position}]"
            need(isinstance(candidate, dict), f"{path} must be an object")
            check_id(field(candidate, "candidate_id", "str", path), f"{path}.candidate_id")
            need(is_num(candidate.get("fit_score")), f"{path}.fit_score must be a number")
    provenance = field(payload, "provenance", "obj", "", required="provenance" in payload)
    if provenance is not None:
        if "generated_at" in provenance:
            check_timestamp(provenance["generated_at"], "provenance.generated_at")
        engines = field(provenance, "engines", "list", "provenance", required="engines" in provenance)
        for position, engine in enumerate(engines or []):
            need(isinstance(engine, str), f"provenance.engines[{position}] must be a string")


def rank(scored_payload):
    """Rank every role's candidates by fit score; returns the ranked document. No file I/O."""
    validate_scored(scored_payload)
    payload = copy.deepcopy(scored_payload)
    ranked_roles = []
    for role in payload["scored_roles"]:
        ranked = sorted(
            role["candidate_scores"],
            key=lambda c: (-float(c["fit_score"]), c["candidate_id"])  # fit-scoring-rubric.md #7.1
        )
        for i, candidate in enumerate(ranked, start=1):
            candidate["provisional_rank"] = i
            candidate["rank_source"] = ENGINE
            candidate["rank_citation"] = "fit-scoring-rubric.md #7.1,#7.3"
        ranked_roles.append({
            "role_id": role["role_id"],
            "role_title": role["role_title"],
            "candidate_slate": ranked,
            "source": ENGINE,
            "confidence": role.get("confidence", 0.99),
            "citation": "fit-scoring-rubric.md #7.1,#7.3"
        })

    payload["ranked_roles"] = ranked_roles
    append_engine(payload.setdefault("provenance", {}), ENGINE_VERSION)
    return payload


def _main(argv):
    parser = ArgumentParser(prog="slate_rank.py", description="Deterministic provisional ranking.")
    parser.add_argument("--scored", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    payload = rank(load_json(args.scored, "scored.json"))
    write_json(args.out, payload)
    print(f"slate_rank: {len(payload['ranked_roles'])} role(s) ranked -> ranked output written")
    return 0


def main(argv=None):
    """CLI entry point: one clean ``error:`` line and exit 2 on any input error, no output file."""
    return run(lambda: _main(argv))


if __name__ == "__main__":
    sys.exit(main())
