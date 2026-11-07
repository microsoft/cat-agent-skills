#!/usr/bin/env python3
"""context_assemble - deterministic context consolidation + contradiction detection
(rtl.customer-service-order-support.v1). #2.1 DNR path selection, #3.1 money boundary.

v1.1: a delivered carrier scan is checked against the customer's account regardless of the
classified intent - any intent that implies non-receipt (delivered_not_received, wismo,
unclassified) is a contradiction and selects the DNR path; explicit input checks instead of
bare asserts; records-only grounding recorded for answer_from_records.
Run from the skill folder (skills/context-assemble); records.json is built in the session
working folder from the user's own OMS, carrier tracking and loyalty exports:
  python scripts/context_assemble.py --classified <session>/classified.json \
      --records <session>/records.json \
      --config config/service-config.json --out <session>/assembled.json
"""
import argparse
import json
import sys
from datetime import datetime, timezone

ENGINE = "engine:context_assemble"
ENGINE_VERSION = "context_assemble/1.1"
CONTRACT = "rtl.customer-service-order-support.v1"
TIERS = ["member", "silver", "gold", "platinum"]
# Intents whose customer account implies the parcel has NOT been received.
NON_RECEIPT_INTENTS = {"delivered_not_received", "wismo", "unclassified"}


def fail(msg: str) -> int:
    print(f"context_assemble: ERROR - {msg}", file=sys.stderr)
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classified", required=True)
    ap.add_argument("--records", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        with open(a.classified, encoding="utf-8") as f:
            p = json.load(f)
        with open(a.records, encoding="utf-8") as f:
            rec = json.load(f)
        with open(a.config, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return fail(f"cannot read inputs: {e}")
    if p.get("contract_version") != CONTRACT:
        return fail(f"contract_version must be {CONTRACT}, got {p.get('contract_version')!r}")
    intent = p.get("intent")
    if not isinstance(intent, dict) or "category" not in intent:
        return fail("classified.json has no intent - run inquiry-intake first")
    dnr = cfg.get("dnr_policy")
    if not isinstance(dnr, dict) or not isinstance(dnr.get("instant_resolution"), dict):
        return fail("config needs dnr_policy.instant_resolution")
    if not isinstance(p.get("inquiry"), dict):
        return fail("inquiry (object) is required")

    esc = list(p.get("escalations", []))
    contradictions = []
    order = rec.get("order", {})
    carrier = rec.get("carrier", {})
    loyalty = rec.get("loyalty", {})
    path = "answer_from_records"
    goodwill = False
    category = intent["category"]

    if carrier.get("status") == "delivered" and category in NON_RECEIPT_INTENTS:
        msg = (f"carrier scan shows delivered {carrier.get('delivered_on')} at "
               f"{carrier.get('location', '?')}; customer reports not received")
        if category != "delivered_not_received":
            msg += f" (classified {category}; delivered scan vs non-receipt account -> DNR handling, #2.1)"
        contradictions.append(msg)
        gate = dnr["instant_resolution"]
        tier_name = loyalty.get("tier", "member")
        tier_ok = tier_name in TIERS and TIERS.index(tier_name) >= TIERS.index(gate["min_tier"])
        value_ok = order.get("value", 1e9) <= gate["max_value"]
        if tier_ok and value_ok:
            path = "instant_resolution"
        else:
            path = "dnr_investigation"
            esc.append(
                f"DNR path: carrier investigation {dnr['investigation_days']} business days before "
                f"refund/replacement - instant gate not met (tier {loyalty.get('tier')} vs {gate['min_tier']}, "
                f"value {order.get('value')} vs {gate['max_value']}) ({dnr['citation']}; service-rules.md #2.1)")
    if p["inquiry"].get("requests_goodwill"):
        esc.append("customer requests goodwill credit - out of plugin scope at any tier; "
                   "draft may PROPOSE for human approval only (service-rules.md #3.1)")
    p["context"] = {
        "order": order, "carrier": carrier, "loyalty": loyalty,
        "contradictions": contradictions, "resolution_path": path, "goodwill_eligible": goodwill,
        "confidence": 0.92, "source": ENGINE,
        "citation": "OMS/carrier/loyalty extracts; " + dnr["citation"],
    }
    if path == "answer_from_records":
        p["context"]["grounding"] = ("records-only: OMS/carrier/loyalty extracts are approved grounding "
                                     "for answer_from_records; no article required (service-rules.md #4.2)")
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append(ENGINE_VERSION)
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2)
    print(f"context_assemble: path={path} contradictions={len(contradictions)} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
