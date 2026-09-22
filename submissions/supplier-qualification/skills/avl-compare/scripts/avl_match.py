#!/usr/bin/env python3
"""avl_match - deterministic AVL / category-requirement comparison + recommendation
(mfg.supplier-qualification.v1). Recommendation bands per qualification-rules.md #5."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:avl_match"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True); ap.add_argument("--avl", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.scored, encoding="utf-8")); avl = json.load(open(a.avl, encoding="utf-8"))
    assert p["contract_version"] == "mfg.supplier-qualification.v1"
    esc = list(p.get("escalations", []))
    cat = p["category"]; region = p["dossier"].get("region")
    incumbents = [s for s in avl if s["category"] == cat]
    same_region = [s["supplier"] for s in incumbents if s["region"] == region]
    dual = len({s["region"] for s in incumbents} | {region}) > 1
    p["avl"] = {"incumbents": [s["supplier"] for s in incumbents], "same_region_incumbents": same_region,
                "adds_regional_diversity": not same_region, "dual_source_after_add": dual,
                "source": ENGINE, "citation": f"approved vendor list, category '{cat}'"}
    band = p["risk"]["overall_band"]
    conds = []
    for e in esc:
        if "#4.1" in e: conds.append("submit missing PPAP elements before first production order")
        if "#1.1" in e: conds.append("provide current (re-issued) certificate before any order")
        if "#3.1" in e: conds.append("approved dual-source plan required before award")
    if band == "low" and not conds: outcome = "qualify"
    elif band == "high": outcome = "do_not_qualify"; conds.append("commodity-council written override required to proceed (#5)")
    else: outcome = "conditional"
    p["recommendation"] = {"outcome": outcome, "conditions": conds,
                           "confidence": min(0.92, p["risk"]["confidence"]), "source": ENGINE,
                           "citation": "qualification-rules.md #5"}
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("avl_match/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"avl_match: outcome={outcome} conditions={len(conds)} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
