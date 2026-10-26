#!/usr/bin/env python3
"""gap_rank - deterministic revenue-impact gap ranking + suggested order
(rtl.retail-execution-perfect-store.v1). #2.1 value at stake; #2.2 promo 2x; #4.1 rep confirms."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:gap_rank"
PROMO_MULT = 2.0  # execution-standards.md #2.2
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True); ap.add_argument("--scan", required=True)
    ap.add_argument("--standards", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.scored, encoding="utf-8")); scan = json.load(open(a.scan, encoding="utf-8"))
    std = json.load(open(a.standards, encoding="utf-8"))
    assert p["contract_version"] == "rtl.retail-execution-perfect-store.v1"
    key = f"{p['outlet']['channel']}:{p['outlet']['cluster']}"; pars = {c["sku"]: c["par"] for c in std[key]["criteria"] if c.get("sku") and c.get("par") is not None}
    active_promos = set(p["visit"].get("active_promo_skus", []))
    gaps = []; order = []
    for r in p["compliance"]["criteria"]:
        if r["pass"]: continue
        sku = r.get("sku"); v = scan.get(sku, {}) if sku else {}
        value = v.get("weekly_units", 0) * v.get("price", 0)
        mult = PROMO_MULT if sku in active_promos else 1.0
        gaps.append({"id": r["id"], "desc": r["desc"], "sku": sku,
                     "weekly_value_at_stake": round(value, 2), "promo_multiplier": mult,
                     "rank_score": round(value * mult, 2), "photo_ref": r.get("photo_ref"),
                     "source": ENGINE, "citation": f"scan extract {sku or '-'}; execution-standards.md #2.1" + (" #2.2" if mult > 1 else "")})
        if r["type"] == "must_stock" and sku:
            order.append({"sku": sku, "qty": pars.get(sku, 0), "reason": f"OOS must-stock {r['id']}",
                          "source": ENGINE, "citation": "par from standard (#4.1 - rep confirms; plugin never transmits)"})
    gaps.sort(key=lambda g: -g["rank_score"])
    p["ranked_gaps"] = gaps; p["suggested_order"] = order
    if gaps and gaps[0]["promo_multiplier"] > 1:
        p.setdefault("escalations", []).append(f"top gap {gaps[0]['id']} is on an ACTIVE promo SKU - most expensive kind of empty (#2.2)")
    p.setdefault("provenance", {}).setdefault("engines", []).append("gap_rank/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"gap_rank: {len(gaps)} gap(s), top={gaps[0]['id'] if gaps else None}, order_lines={len(order)} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
