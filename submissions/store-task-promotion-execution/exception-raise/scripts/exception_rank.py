#!/usr/bin/env python3
"""exception_rank - deterministic revenue-impact ranking of readiness exceptions
(rtl.store-task-promotion-execution.v1). Rules mirror ../../references/execution-rules.md #5.1:
rank = weekly revenue at stake (velocity x promo price) x launch-proximity factor
       x price-conflict factor (PRICE CONFLICTS only).
Constants below are the documented values in #5.1; change them there first.
"""
import argparse, json, sys
from datetime import datetime, timezone, date
ENGINE = "engine:exception_rank"
ENGINE_VERSION = "exception_rank/1.1"
PROXIMITY_DAYS = 3            # #5.1: inside 3 days of launch ...
PROXIMITY_FACTOR = 2.0        # #5.1: ... every exception carries 2x
PRICE_CONFLICT_FACTOR = 1.5   # #5.1: a PRICE CONFLICT (#3.1/#3.2) carries an additional 1.5x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checked", required=True); ap.add_argument("--velocity", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        with open(a.checked, encoding="utf-8") as fh:
            p = json.load(fh)
    except (OSError, json.JSONDecodeError):
        print("exception_rank: checked.json missing or unreadable", file=sys.stderr); return 2
    if p.get("contract_version") != "rtl.store-task-promotion-execution.v1":
        print("exception_rank: checked.json is not rtl.store-task-promotion-execution.v1", file=sys.stderr); return 2
    try:
        with open(a.velocity, encoding="utf-8") as fh:
            vel = json.load(fh)
    except (OSError, json.JSONDecodeError):
        # #5.1 needs velocity; never estimate it. Fail closed with an explicit escalation.
        p.setdefault("escalations", []).append("VELOCITY EXTRACT MISSING - ranking not computed (#5.1); request the extract")
        p["exceptions"] = []
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(p, fh, indent=2)
        print("exception_rank: velocity extract missing - no ranking produced (#5.1)", file=sys.stderr); return 3
    if p.get("readiness", {}).get("blocked"):
        print("exception_rank: readiness is BLOCKED (#6) - ranking still computed for the items present; resolve the block first", file=sys.stderr)
    days_out = (date.fromisoformat(p["launch_date"]) - date.fromisoformat(p["as_of_date"])).days
    prox = PROXIMITY_FACTOR if days_out <= PROXIMITY_DAYS else 1.0
    req = {r["req_id"]: r for r in p.get("requirements", [])}
    exceptions = []
    for it in p.get("readiness", {}).get("items", []):
        if it["status"] in ("missing", "conflict"):
            skus = req.get(it["req_id"], {}).get("skus", [])
            rev = sum(vel.get(s, {}).get("weekly_units", 0) * vel.get(s, {}).get("promo_price", 0) for s in skus)
            exceptions.append({"req_id": it["req_id"], "status": it["status"], "detail": it["detail"],
                "revenue_at_stake_weekly": round(rev, 2), "rank_score": round(rev * prox, 2),
                "source": ENGINE, "citation": f"{it['citation']}; velocity extract (#5.1)"})
    for c in p.get("readiness", {}).get("price_conflicts", []):
        v = vel.get(c["sku"], {}); rev = v.get("weekly_units", 0) * v.get("promo_price", 0)
        exceptions.append({"req_id": f"PRICE-{c['sku']}", "status": "conflict", "detail": c["detail"],
            "revenue_at_stake_weekly": round(rev, 2), "rank_score": round(rev * prox * PRICE_CONFLICT_FACTOR, 2),
            "source": ENGINE, "citation": c["citation"] + " (#3.1, #5.1)"})
    exceptions.sort(key=lambda e: -e["rank_score"])
    p["exceptions"] = exceptions
    p.setdefault("provenance", {}).setdefault("engines", []).append(ENGINE_VERSION)
    p["provenance"]["ranking_factors"] = {"proximity_days": PROXIMITY_DAYS, "proximity_factor_applied": prox,
                                          "price_conflict_factor": PRICE_CONFLICT_FACTOR, "rule": "execution-rules.md #5.1"}
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(p, fh, indent=2)
    print(f"exception_rank: {len(exceptions)} exception(s), top={exceptions[0]['req_id'] if exceptions else None}, "
          f"proximity={prox}x, price_conflict={PRICE_CONFLICT_FACTOR}x -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
