#!/usr/bin/env python3
"""criticality_score - deterministic priority/downtime engine (mfg.maintenance-triage.v1).

Reads the {ranked_causes} contract produced by fault_rank and computes the maintenance
priority (P1-P4), response target, and downtime cost, using the asset-criticality matrix.
Emits the {priority} hop and the recommended action for the work-order draft.

Deterministic: no LLM, no network, no randomness. Rules mirror
references/asset-criticality-matrix.md by section number.
"""
import argparse, json, sys
from datetime import datetime, timezone

ENGINE = "engine:criticality_score"

# base priority by asset criticality class (asset-criticality-matrix.md #2)
# numeric scale P1=4, P2=3, P3=2, P4=1
BASE = {"A": 3, "B": 2, "C": 1}
LEVEL_NAME = {4: "P1", 3: "P2", 2: "P3", 1: "P4"}
# response targets (asset-criticality-matrix.md #4)
RESPONSE = {"P1": "Immediate — begin within 1 hour; escalate to shift supervisor.",
            "P2": "Same shift — begin within 8 hours.",
            "P3": "Planned — schedule within 7 days.",
            "P4": "Backlog — schedule at next planned outage."}
DEFAULT_REPAIR_HOURS = 4.0  # asset-criticality-matrix.md #5.1
MECHANICAL_ROOTS = {"bearing_degradation", "coupling_misalignment"}


def band(score):
    if score >= 3.5: return 4
    if score >= 2.5: return 3
    if score >= 1.5: return 2
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ranked", required=True, help="output of fault_rank (contract with ranked_causes)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    payload = json.load(open(a.ranked, encoding="utf-8"))
    assert payload["contract_version"] == "mfg.maintenance-triage.v1", "wrong contract version"

    cls = (payload.get("asset_criticality") or "C").upper()
    cost_hr = payload.get("downtime_cost_per_hr")
    ranked = payload.get("ranked_causes", [])
    history = payload.get("history", {}) or {}
    repeat_promotion = bool(history.get("repeat_promotion"))
    redundancy = (payload.get("redundancy") or "unknown").lower()
    escalations = list(payload.get("escalations", []))

    base = BASE.get(cls, 1)
    score = float(base)
    factors = [f"base P{5-base} for criticality class {cls} (asset-criticality-matrix.md #2)"]

    # #3.1-3.3 downtime cost bands
    if cost_hr is not None:
        if cost_hr >= 10000:
            score += 1.0; factors.append(f"+1.0 downtime cost ${cost_hr:,}/hr >= $10k (#3.1)")
        elif cost_hr >= 5000:
            score += 0.5; factors.append(f"+0.5 downtime cost ${cost_hr:,}/hr >= $5k (#3.2)")
        else:
            factors.append(f"+0.0 downtime cost ${cost_hr:,}/hr < $5k (#3.3)")

    # #3.4 repeat-failure escalation (force minimum P2)
    force_min = 0
    if repeat_promotion:
        score += 1.0; force_min = 3
        factors.append("+1.0 recurring failure promoted by fault_rank; force minimum P2 (#3.4)")
        escalations.append("Priority escalated for a recurring failure on this asset; notify reliability "
                           "engineering and the maintenance planner (asset-criticality-matrix.md #6.2).")

    # #3.5 mechanical root cause on a class A asset
    top_mode = ranked[0]["failure_mode"] if ranked else None
    if top_mode in MECHANICAL_ROOTS and cls == "A":
        score += 0.5; factors.append(f"+0.5 mechanical root cause '{top_mode}' on class A asset (#3.5)")

    # #3.6 no installed redundancy
    if redundancy in ("none", "no", "false"):
        score += 0.5; factors.append("+0.5 no installed redundancy / no standby (#3.6)")

    level_num = max(band(score), force_min)
    level = LEVEL_NAME[level_num]

    # #5 downtime cost estimate
    repair_hours = float(payload.get("expected_repair_hours") or DEFAULT_REPAIR_HOURS)
    if cost_hr is not None:
        downtime_cost = round(cost_hr * repair_hours, 2)
        cost_conf = 0.9
    else:
        downtime_cost = None
        cost_conf = 0.6
        escalations.append("Downtime cost/hr not provided; cost impact is an estimate — confirm with the "
                           "planner (asset-criticality-matrix.md #6.3).")

    if level == "P1":
        escalations.append("P1 priority assigned; immediate escalation to the shift supervisor required "
                           "(asset-criticality-matrix.md #6.1).")

    priority = {
        "level": level,
        "score": round(score, 2),
        "response_target": RESPONSE[level],
        "downtime_cost_per_hr": cost_hr,
        "expected_repair_hours": repair_hours,
        "downtime_cost_estimate": downtime_cost,
        "factors": factors,
        "confidence": round(min(0.95, 0.75 + (0.15 if cost_hr is not None else 0.0) +
                                (0.05 if ranked else 0.0)), 2),
        "source": ENGINE,
        "citation": "asset-criticality-matrix.md #2-#5; rcm-iso55000-excerpts.md ISO-55000-2 (risk-based prioritization)",
    }

    payload["priority"] = priority
    if ranked:
        payload["recommended_action"] = ranked[0]["recommended_fix"]
    payload["escalations"] = escalations

    prov = payload.setdefault("provenance", {})
    prov.setdefault("engines", [])
    if "criticality_score/1.0" not in prov["engines"]:
        prov["engines"].append("criticality_score/1.0")
    prov["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    json.dump(payload, open(a.out, "w", encoding="utf-8"), indent=2)
    cost_str = f"${downtime_cost:,.0f}" if downtime_cost is not None else "n/a"
    print(f"criticality_score: {level} (score {priority['score']}), downtime~{cost_str} "
          f"over {repair_hours}h -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
