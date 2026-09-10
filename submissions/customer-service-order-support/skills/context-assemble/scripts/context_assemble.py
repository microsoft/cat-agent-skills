#!/usr/bin/env python3
"""context_assemble - deterministic context consolidation + contradiction detection
(rtl.customer-service-order-support.v1). #2.1 DNR path selection, #3.1 money boundary."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:context_assemble"
TIERS = ["member", "silver", "gold", "platinum"]
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classified", required=True); ap.add_argument("--records", required=True)
    ap.add_argument("--config", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.classified, encoding="utf-8")); rec = json.load(open(a.records, encoding="utf-8"))
    cfg = json.load(open(a.config, encoding="utf-8"))
    assert p["contract_version"] == "rtl.customer-service-order-support.v1"
    esc = list(p.get("escalations", [])); contradictions = []
    order, carrier, loyalty = rec.get("order", {}), rec.get("carrier", {}), rec.get("loyalty", {})
    path = "answer_from_records"; goodwill = False
    if carrier.get("status") == "delivered" and p["intent"]["category"] == "delivered_not_received":
        contradictions.append(f"carrier scan shows delivered {carrier.get('delivered_on')} at {carrier.get('location','?')}; customer reports not received")
        gate = cfg["dnr_policy"]["instant_resolution"]
        tier_ok = TIERS.index(loyalty.get("tier", "member")) >= TIERS.index(gate["min_tier"])
        value_ok = order.get("value", 1e9) <= gate["max_value"]
        if tier_ok and value_ok:
            path = "instant_resolution"
        else:
            path = "dnr_investigation"
            esc.append(f"DNR path: carrier investigation {cfg['dnr_policy']['investigation_days']} business days before refund/replacement - instant gate not met (tier {loyalty.get('tier')} vs {gate['min_tier']}, value {order.get('value')} vs {gate['max_value']}) ({cfg['dnr_policy']['citation']}; service-rules.md #2.1)")
    if p["inquiry"].get("requests_goodwill"):
        esc.append("customer requests goodwill credit - out of plugin scope at any tier; draft may PROPOSE for human approval only (service-rules.md #3.1)")
    p["context"] = {"order": order, "carrier": carrier, "loyalty": loyalty,
        "contradictions": contradictions, "resolution_path": path, "goodwill_eligible": goodwill,
        "confidence": 0.92, "source": ENGINE, "citation": "OMS/carrier/loyalty extracts; " + cfg["dnr_policy"]["citation"]}
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("context_assemble/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"context_assemble: path={path} contradictions={len(contradictions)} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
