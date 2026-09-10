#!/usr/bin/env python3
"""policy_resolve - deterministic policy + promotion resolution (rtl.store-associate-assist.v1).
Rules mirror references/assist-rules.md. Promo eligibility = window AND cluster AND SKU (#2.1)."""
import argparse, json, sys
from datetime import datetime, timezone, date
ENGINE = "engine:policy_resolve"
CONFIDENCE_FLOOR = 0.75  # assist-rules.md #4.1
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True); ap.add_argument("--policies", required=True)
    ap.add_argument("--promos", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.question, encoding="utf-8")); lib = json.load(open(a.policies, encoding="utf-8"))
    promos = json.load(open(a.promos, encoding="utf-8"))
    assert p["contract_version"] == "rtl.store-associate-assist.v1"
    esc = list(p.get("escalations", []))
    qtext = p["question"]["text"].lower()
    hits = [(k, v) for k, v in lib.items() if any(t in qtext for t in v["topics"])]
    # most specific clause wins: exclusions rank above general eligibility
    hits.sort(key=lambda kv: 0 if kv[1]["determination_hint"] == "excluded" else 1)
    if not hits:
        p["policy_resolution"] = {"topic": p["question"].get("topic", "unknown"), "applicable_clause": None,
            "determination": "out_of_scope", "conditions": [], "in_scope": False, "confidence": 0.0,
            "source": ENGINE, "citation": "no matching clause (assist-rules.md #1.2)"}
        esc.append("question outside policy library scope - escalation drafted, no improvised policy (assist-rules.md #1.2)")
    else:
        k, v = hits[0]
        conf = 0.9 if len(hits) == 1 or hits[0][1]["determination_hint"] == "excluded" else 0.8
        p["policy_resolution"] = {"topic": k, "applicable_clause": v["clause"],
            "determination": v["determination_hint"], "conditions": [v["text"]], "in_scope": True,
            "confidence": conf, "source": ENGINE, "citation": f"policy clause {v['clause']}"}
        if conf < CONFIDENCE_FLOOR: esc.append(f"resolution confidence {conf} < {CONFIDENCE_FLOOR} - shift-lead escalation (assist-rules.md #4.1)")
    # promo check (#2.1)
    sku = p["question"].get("sku"); today = date.fromisoformat(p["question"]["asked_on"])
    cluster = p.get("store_context", {}).get("cluster")
    pc = {"checked": bool(sku), "eligible": False, "reasons": [], "source": ENGINE, "citation": "promo pack"}
    if sku:
        for pr in promos:
            if sku in pr["skus"]:
                in_window = date.fromisoformat(pr["start"]) <= today <= date.fromisoformat(pr["end"])
                in_cluster = cluster in pr["clusters"]
                pc["citation"] = pr["citation"]
                if in_window and in_cluster:
                    pc.update(eligible=True, promo_id=pr["promo_id"], reasons=[f"{pr['name']}: window + cluster + SKU all match (#2.1)"])
                else:
                    if not in_window: pc["reasons"].append(f"{pr['promo_id']}: outside window {pr['start']}..{pr['end']} (today {today})")
                    if not in_cluster: pc["reasons"].append(f"{pr['promo_id']}: store cluster '{cluster}' not in {pr['clusters']}")
        if not pc["reasons"]: pc["reasons"] = ["SKU on no promo list"]
    p["promo_check"] = pc; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("policy_resolve/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    pr = p["policy_resolution"]
    print(f"policy_resolve: clause={pr['applicable_clause']} det={pr['determination']} promo_eligible={pc['eligible']} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
