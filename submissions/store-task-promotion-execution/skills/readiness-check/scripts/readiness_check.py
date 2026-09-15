#!/usr/bin/env python3
"""readiness_check - deterministic store readiness vs campaign pack
(rtl.store-task-promotion-execution.v1). Rules mirror references/execution-rules.md."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:readiness_check"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True); ap.add_argument("--store", required=True)
    ap.add_argument("--prices", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.pack, encoding="utf-8")); store = json.load(open(a.store, encoding="utf-8"))
    prices = json.load(open(a.prices, encoding="utf-8"))
    assert p["contract_version"] == "rtl.store-task-promotion-execution.v1"
    p["store"] = store; esc = list(p.get("escalations", []))
    items = []; applicable = 0; ready = 0
    for r in p["requirements"]:
        if store["format"] not in r["formats"] or store["cluster"] not in r["clusters"]:
            items.append({"req_id": r["req_id"], "status": "not_applicable",
                          "detail": f"format/cluster outside applicability (execution-rules.md #1.1)",
                          "source": ENGINE, "citation": r["citation"]}); continue
        applicable += 1
        if r.get("fixture_required") and r["fixture_required"] not in store.get("fixtures", []):
            items.append({"req_id": r["req_id"], "status": "conflict",
                          "detail": f"requires fixture '{r['fixture_required']}' not in store format (execution-rules.md #4.1)",
                          "source": ENGINE, "citation": r["citation"]})
            esc.append(f"{r['req_id']}: fixture conflict - store cannot resolve locally (#4.1)"); continue
        missing = [x for x in r.get("assets", []) if x not in store.get("received_assets", [])]
        missing += [t for t in r.get("tasks", []) if t not in store.get("completed_tasks", [])]
        if missing:
            items.append({"req_id": r["req_id"], "status": "missing",
                          "detail": f"outstanding: {', '.join(missing)} (execution-rules.md #2.1)",
                          "source": ENGINE, "citation": r["citation"]})
        else:
            ready += 1
            items.append({"req_id": r["req_id"], "status": "ready", "detail": "all assets/tasks confirmed",
                          "source": ENGINE, "citation": r["citation"]})
    conflicts = []
    for sku, promo_price in p.get("promo_prices", {}).items():
        shelf = prices.get(sku)
        if shelf is not None and promo_price >= shelf:
            conflicts.append({"sku": sku, "promo_price": promo_price, "shelf_price": shelf,
                "detail": f"promo {promo_price} >= shelf {shelf} - MISPRICING, block shelf change (execution-rules.md #3.1)",
                "source": ENGINE, "citation": f"price file {sku}"})
            esc.append(f"PRICE CONFLICT {sku}: promo {promo_price} >= shelf {shelf} (#3.1)")
    p["readiness"] = {"items": items, "completeness_pct": round(100*ready/applicable, 1) if applicable else 0.0,
        "price_conflicts": conflicts, "confidence": 0.95, "source": ENGINE,
        "citation": f"campaign {p['campaign_id']} pack vs store {store['store_id']} profile"}
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("readiness_check/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"readiness_check: {ready}/{applicable} ready ({p['readiness']['completeness_pct']}%), conflicts={sum(1 for i in items if i['status']=='conflict')}, price_conflicts={len(conflicts)} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
