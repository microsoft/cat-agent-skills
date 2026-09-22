#!/usr/bin/env python3
"""reason_classify - deterministic reason classification vs taxonomy (rtl.returns-refund-case.v1)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:reason_classify"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True); ap.add_argument("--taxonomy", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.case, encoding="utf-8")); tax = json.load(open(a.taxonomy, encoding="utf-8"))
    assert p["contract_version"] == "rtl.returns-refund-case.v1"
    text = p["return_request"]["reason_text"].lower()
    hits = [(cat, sum(1 for k in kws if k in text)) for cat, kws in tax.items()]
    hits = [(c, n) for c, n in hits if n > 0]; hits.sort(key=lambda t: -t[1])
    cat = hits[0][0] if hits else "unclassified"
    conf = 0.9 if hits and (len(hits) == 1 or hits[0][1] > hits[1][1]) else (0.7 if hits else 0.4)
    p["reason"] = {"category": cat, "confidence": conf, "source": ENGINE,
                   "citation": "reason-code taxonomy (config/reason-taxonomy.json)"}
    if conf < 0.75: p.setdefault("escalations", []).append(f"reason classification ambiguous ({cat}, conf {conf}) - agent confirms with customer")
    p.setdefault("provenance", {}).setdefault("engines", []).append("reason_classify/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"reason_classify: {cat} (conf {conf}) -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
