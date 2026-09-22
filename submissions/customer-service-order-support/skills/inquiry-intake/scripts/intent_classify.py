#!/usr/bin/env python3
"""intent_classify - deterministic intent classification (rtl.customer-service-order-support.v1, #1.1)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:intent_classify"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inquiry", required=True); ap.add_argument("--config", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.inquiry, encoding="utf-8")); cfg = json.load(open(a.config, encoding="utf-8"))
    assert p["contract_version"] == "rtl.customer-service-order-support.v1"
    text = p["inquiry"]["text"].lower()
    hits = [(cat, sum(1 for k in kws if k in text)) for cat, kws in cfg["intent_taxonomy"].items()]
    hits = [(c, n) for c, n in hits if n > 0]; hits.sort(key=lambda t: -t[1])
    # DNR outranks generic WISMO when both match (#2.1 is the safety-relevant path)
    if any(c == "delivered_not_received" for c, _ in hits): cat, conf = "delivered_not_received", 0.9
    elif hits: cat, conf = hits[0][0], (0.9 if len(hits) == 1 or hits[0][1] > hits[1][1] else 0.7)
    else: cat, conf = "unclassified", 0.3
    p["intent"] = {"category": cat, "confidence": conf, "source": ENGINE,
                   "citation": "intent taxonomy (config/service-config.json)"}
    if conf < cfg["confidence_floor"]:
        p.setdefault("escalations", []).append(f"intent confidence {conf} < {cfg['confidence_floor']} - handoff, not a guessed answer (service-rules.md #1.1)")
    p.setdefault("provenance", {}).setdefault("engines", []).append("intent_classify/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"intent_classify: {cat} (conf {conf}) -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
