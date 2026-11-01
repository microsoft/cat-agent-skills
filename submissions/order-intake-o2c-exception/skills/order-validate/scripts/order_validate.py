#!/usr/bin/env python3
"""order_validate - deterministic order validation vs masters (rtl.order-intake-o2c.v1).
#1 alias identity, #2 UOM/qty sanity, #3 price tolerance, #4 credit. Constants mirror o2c-rules.md."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:order_validate"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", required=True); ap.add_argument("--masters", required=True)
    ap.add_argument("--config", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.order, encoding="utf-8")); m = json.load(open(a.masters, encoding="utf-8"))
    cfg = json.load(open(a.config, encoding="utf-8"))
    assert p["contract_version"] == "rtl.order-intake-o2c.v1"
    cust = m["customers"][p["customer"]["id"]]; esc = list(p.get("escalations", []))
    results = []; order_value = 0.0
    for ln in p["lines"]:
        issues = []
        cands = m["alias_map"].get(ln["customer_sku"], [])
        sku = None; basis = None
        if len(cands) != 1:
            issues.append({"code": "AMBIGUOUS_SKU", "detail": f"alias '{ln['customer_sku']}' resolves to {cands or 'nothing'} (o2c-rules.md #1.1)"})
            # anomaly checks still run against the customer's historical candidate (advisory
            # only - entry stays blocked on the ambiguity). Basis is disclosed in the issue.
            hist = [c for c in cands if c in cust["historical_uom"]]
            basis = hist[0] if hist else (cands[0] if cands else None)
        else:
            sku = cands[0]; basis = sku
        if basis is not None:
            prod = m["products"][basis]
            if sku is None:
                issues.append({"code": "ANOMALY_BASIS", "detail": f"anomaly checks below use historical candidate {basis} pending product confirmation"})
            hist_uom = cust["historical_uom"].get(basis)
            if hist_uom and ln["uom"] != hist_uom:
                issues.append({"code": "UOM_ANOMALY", "detail": f"ordered {ln['qty']} {ln['uom']}; customer always orders {hist_uom} (#2.1)"})
            typ = cust["typical_qty"].get(basis)
            if typ and ln["qty"] > typ * cfg["qty_band_multiplier"]:
                issues.append({"code": "QTY_ANOMALY", "detail": f"qty {ln['qty']} > {cfg['qty_band_multiplier']}x typical {typ} (#2.1)"})
            listp = prod.get(f"list_price_{(hist_uom or ln['uom']).lower()}")
            if listp and ln.get("unit_price") is not None:
                dev = 100 * (listp - ln["unit_price"]) / listp
                if abs(dev) > cfg["price_tolerance_pct"] and not ln.get("promo_ref"):
                    issues.append({"code": "PRICE_DEVIATION", "detail": f"PO price {ln['unit_price']} vs list {listp} ({round(dev,1)}% dev > {cfg['price_tolerance_pct']}%) with no promo reference (#3.1)"})
        if ln.get("unit_price") is not None:
            order_value += ln["qty"] * ln["unit_price"]
        results.append({"line": ln["line_no"], "customer_sku": ln["customer_sku"], "resolved_sku": sku,
                        "issues": issues, "source": ENGINE, "citation": f"masters + {cfg['citation']}"})
    credit_ok = cust["open_exposure"] + order_value <= cust["credit_limit"]
    credit = {"exposure_after": round(cust["open_exposure"] + order_value, 2), "limit": cust["credit_limit"],
              "within_limit": credit_ok, "source": ENGINE, "citation": "credit master (#4.1)"}
    if not credit_ok:
        results.append({"line": 0, "customer_sku": "-", "resolved_sku": None,
            "issues": [{"code": "CREDIT_REVIEW", "detail": f"exposure {credit['exposure_after']} > limit {cust['credit_limit']} - queue for credit review (#4.1)"}],
            "source": ENGINE, "citation": "credit master"})
    n_issues = sum(len(r["issues"]) for r in results)
    p["validation"] = {"line_results": results, "order_status": "clean" if n_issues == 0 else "exceptions",
                       "credit_check": credit, "confidence": 0.95, "source": ENGINE, "citation": cfg["citation"]}
    if n_issues: esc.append(f"{n_issues} validation issue(s) - order held at action level {cfg['action_level']}; creation stays human-approved (o2c-rules.md #5.1)")
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("order_validate/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"order_validate: status={p['validation']['order_status']}, issues={n_issues}, credit_ok={credit_ok} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
