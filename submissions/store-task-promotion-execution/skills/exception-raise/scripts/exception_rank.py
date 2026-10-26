#!/usr/bin/env python3
"""exception_rank - deterministic revenue-impact ranking of readiness exceptions
(rtl.store-task-promotion-execution.v1). rank = velocity x promo price x proximity (#5.1)."""
import argparse, json, sys
from datetime import datetime, timezone, date
ENGINE = "engine:exception_rank"
PROXIMITY_DAYS = 3; PROXIMITY_FACTOR = 2.0  # execution-rules.md #5.1
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checked", required=True); ap.add_argument("--velocity", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.checked, encoding="utf-8")); vel = json.load(open(a.velocity, encoding="utf-8"))
    assert p["contract_version"] == "rtl.store-task-promotion-execution.v1"
    days_out = (date.fromisoformat(p["launch_date"]) - date.fromisoformat(p["as_of_date"])).days
    prox = PROXIMITY_FACTOR if days_out <= PROXIMITY_DAYS else 1.0
    req = {r["req_id"]: r for r in p["requirements"]}
    exceptions = []
    for it in p["readiness"]["items"]:
        if it["status"] in ("missing", "conflict"):
            skus = req[it["req_id"]].get("skus", [])
            rev = sum(vel.get(s, {}).get("weekly_units", 0) * vel.get(s, {}).get("promo_price", 0) for s in skus)
            exceptions.append({"req_id": it["req_id"], "status": it["status"], "detail": it["detail"],
                "revenue_at_stake_weekly": round(rev, 2), "rank_score": round(rev * prox, 2),
                "source": ENGINE, "citation": f"{it['citation']}; velocity extract (#5.1)"})
    for c in p["readiness"]["price_conflicts"]:
        v = vel.get(c["sku"], {}); rev = v.get("weekly_units", 0) * v.get("promo_price", 0)
        exceptions.append({"req_id": f"PRICE-{c['sku']}", "status": "conflict", "detail": c["detail"],
            "revenue_at_stake_weekly": round(rev, 2), "rank_score": round(rev * prox * 1.5, 2),
            "source": ENGINE, "citation": c["citation"] + " (#3.1, #5.1)"})
    exceptions.sort(key=lambda e: -e["rank_score"])
    p["exceptions"] = exceptions
    p.setdefault("provenance", {}).setdefault("engines", []).append("exception_rank/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"exception_rank: {len(exceptions)} exception(s), top={exceptions[0]['req_id'] if exceptions else None} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
