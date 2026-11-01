#!/usr/bin/env python3
"""exception_route - deterministic exception queueing with recommended corrections
(rtl.order-intake-o2c.v1). Reason codes -> queue + correction; action level from config (#5.1)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:exception_route"
ROUTES = {"AMBIGUOUS_SKU": ("order-management", "confirm intended product with the customer (list candidates)"),
          "UOM_ANOMALY": ("order-management", "confirm unit of measure with the customer before entry"),
          "QTY_ANOMALY": ("order-management", "confirm quantity - outside historical band"),
          "PRICE_DEVIATION": ("pricing-desk", "confirm price basis or promo reference; else correct to list"),
          "CREDIT_REVIEW": ("credit-team", "credit review before release; do not bounce the customer"),
          "ANOMALY_BASIS": ("order-management", "note: anomaly checks used the historical candidate; resolve the alias first")}
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validated", required=True); ap.add_argument("--config", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.validated, encoding="utf-8")); cfg = json.load(open(a.config, encoding="utf-8"))
    assert p["contract_version"] == "rtl.order-intake-o2c.v1"
    ex = []
    for r in p["validation"]["line_results"]:
        for i in r["issues"]:
            q, fix = ROUTES[i["code"]]
            ex.append({"line": r["line"], "reason_code": i["code"], "detail": i["detail"],
                       "queue": q, "recommended_correction": fix,
                       "action_level": cfg["action_level"], "source": ENGINE,
                       "citation": f"routing table (o2c-rules.md); {cfg['citation']}"})
    p["exceptions"] = ex
    p.setdefault("provenance", {}).setdefault("engines", []).append("exception_route/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"exception_route: {len(ex)} exception(s) queued -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
