#!/usr/bin/env python3
"""readiness_check - deterministic store readiness vs campaign pack
(rtl.store-task-promotion-execution.v1). Rules mirror ../../references/execution-rules.md.

Rules implemented: #1.1 applicability, #2.1 completeness, #3.1 promo >= shelf,
#3.2 pack price != price-file price, #4.1 fixture conflict, #6 confidence floor.
A missing/incomplete store profile or price file never crashes the engine: it lowers
confidence below the 0.75 floor and blocks readiness (#6) with an explicit escalation.
"""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:readiness_check"
ENGINE_VERSION = "readiness_check/1.1"
CONFIDENCE_FULL = 0.95              # profile + price file both present (#6)
CONFIDENCE_MISSING_PROFILE = 0.50   # store profile absent/incomplete -> below floor (#6)
CONFIDENCE_MISSING_PRICES = 0.60    # shelf-price extract absent/empty -> below floor (#6)
CONFIDENCE_FLOOR = 0.75
PROFILE_REQUIRED = ("store_id", "format", "cluster")


def load_json(path):
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True); ap.add_argument("--store", required=True)
    ap.add_argument("--prices", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = load_json(a.pack)
    if not isinstance(p, dict) or p.get("contract_version") != "rtl.store-task-promotion-execution.v1":
        print("readiness_check: pack.json missing or not rtl.store-task-promotion-execution.v1", file=sys.stderr)
        return 2
    store = load_json(a.store)
    prices = load_json(a.prices)
    esc = list(p.get("escalations", []))

    # --- #6 confidence floor: compute, never assume -----------------------------------
    profile_ok = isinstance(store, dict) and all(store.get(k) for k in PROFILE_REQUIRED)
    prices_ok = isinstance(prices, dict) and len(prices) > 0
    confidence = CONFIDENCE_FULL
    if not profile_ok:
        confidence = min(confidence, CONFIDENCE_MISSING_PROFILE)
        missing_keys = [k for k in PROFILE_REQUIRED if not (isinstance(store, dict) and store.get(k))]
        esc.append(f"STORE PROFILE MISSING ({', '.join(missing_keys) or 'file'}) - readiness blocked, confidence {confidence} < {CONFIDENCE_FLOOR} (#6); request the store master export")
    if not prices_ok:
        confidence = min(confidence, CONFIDENCE_MISSING_PRICES)
        esc.append(f"SHELF-PRICE EXTRACT MISSING - price integrity untested, readiness blocked, confidence {confidence} < {CONFIDENCE_FLOOR} (#6); request the POS price extract")
    blocked = confidence < CONFIDENCE_FLOOR
    store = store if isinstance(store, dict) else {}
    prices = prices if isinstance(prices, dict) else {}
    p["store"] = store if store else (p.get("store") if isinstance(p.get("store"), dict) else {})  # real profile replaces the entry-hop stub

    # --- #1.1 / #2.1 / #4.1 per requirement --------------------------------------------
    items = []; applicable = 0; ready = 0
    for r in p.get("requirements", []):
        if not profile_ok:
            items.append({"req_id": r["req_id"], "status": "missing",
                          "detail": "store profile missing - applicability untestable (execution-rules.md #6)",
                          "source": ENGINE, "citation": r.get("citation", "")}); continue
        if store["format"] not in r.get("formats", []) or store["cluster"] not in r.get("clusters", []):
            items.append({"req_id": r["req_id"], "status": "not_applicable",
                          "detail": "format/cluster outside applicability (execution-rules.md #1.1)",
                          "source": ENGINE, "citation": r.get("citation", "")}); continue
        applicable += 1
        if r.get("fixture_required") and r["fixture_required"] not in store.get("fixtures", []):
            items.append({"req_id": r["req_id"], "status": "conflict",
                          "detail": f"requires fixture '{r['fixture_required']}' not in store format (execution-rules.md #4.1)",
                          "source": ENGINE, "citation": r.get("citation", "")})
            esc.append(f"{r['req_id']}: fixture conflict - store cannot resolve locally (#4.1)"); continue
        missing = [x for x in r.get("assets", []) if x not in store.get("received_assets", [])]
        missing += [t for t in r.get("tasks", []) if t not in store.get("completed_tasks", [])]
        if missing:
            items.append({"req_id": r["req_id"], "status": "missing",
                          "detail": f"outstanding: {', '.join(missing)} (execution-rules.md #2.1)",
                          "source": ENGINE, "citation": r.get("citation", "")})
        else:
            ready += 1
            items.append({"req_id": r["req_id"], "status": "ready", "detail": "all assets/tasks confirmed",
                          "source": ENGINE, "citation": r.get("citation", "")})

    # --- #3.1 promo >= shelf, #3.2 pack price != price-file price ----------------------
    conflicts = []
    promo_prices = p.get("promo_prices", {}) or {}
    pack_prices = p.get("pack_prices", {}) or {}   # prices printed in the pack body (optional)
    for sku, promo_price in promo_prices.items():
        shelf = prices.get(sku)
        if shelf is not None and promo_price >= shelf:
            conflicts.append({"sku": sku, "promo_price": promo_price, "shelf_price": shelf,
                "detail": f"promo {promo_price} >= shelf {shelf} - MISPRICING, block shelf change (execution-rules.md #3.1)",
                "source": ENGINE, "citation": f"price file {sku}"})
            esc.append(f"PRICE CONFLICT {sku}: promo {promo_price} >= shelf {shelf} (#3.1)")
        pack_price = pack_prices.get(sku)
        if pack_price is not None and pack_price != promo_price:
            conflicts.append({"sku": sku, "promo_price": promo_price, "pack_price": pack_price,
                "detail": f"pack states {pack_price} but price file states {promo_price} - PRICE CONFLICT, two prices for one SKU (execution-rules.md #3.2)",
                "source": ENGINE, "citation": f"pack vs price file {sku}"})
            esc.append(f"PRICE CONFLICT {sku}: pack {pack_price} != price file {promo_price} (#3.2)")

    readiness = {"items": items, "completeness_pct": round(100*ready/applicable, 1) if applicable else 0.0,
        "price_conflicts": conflicts, "confidence": confidence, "source": ENGINE,
        "citation": f"campaign {p.get('campaign_id')} pack vs store {store.get('store_id', 'UNKNOWN')} profile"}
    if blocked:
        readiness["blocked"] = True
        readiness["blocked_reason"] = f"confidence {confidence} below floor {CONFIDENCE_FLOOR} (execution-rules.md #6)"
    p["readiness"] = readiness
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append(ENGINE_VERSION)
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(p, fh, indent=2)
    state = "BLOCKED (#6)" if blocked else f"{ready}/{applicable} ready ({readiness['completeness_pct']}%)"
    print(f"readiness_check: {state}, conflicts={sum(1 for i in items if i['status']=='conflict')}, "
          f"price_conflicts={len(conflicts)}, confidence={confidence} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
