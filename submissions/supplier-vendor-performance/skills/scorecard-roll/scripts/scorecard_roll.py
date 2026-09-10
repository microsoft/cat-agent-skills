#!/usr/bin/env python3
"""scorecard_roll - deterministic vendor scorecard from records
(rtl.supplier-vendor-performance.v1). #1.1 computed OTIF; #1.2 trend flags."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:scorecard_roll"
TREND_QUARTERS = 3  # vendor-review-rules.md #1.2
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vendor", required=True); ap.add_argument("--records", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.vendor, encoding="utf-8")); rec = json.load(open(a.records, encoding="utf-8"))
    assert p["contract_version"] == "rtl.supplier-vendor-performance.v1"
    esc = list(p.get("escalations", [])); quarters = []
    for q in rec["quarters"]:
        lines = q["lines"]; otif_lines = q["on_time_in_full_lines"]
        quarters.append({"quarter": q["quarter"], "otif_pct": round(100*otif_lines/lines, 1),
            "defect_rate_pct": q["defect_rate_pct"], "dispute_rate_pct": q["dispute_rate_pct"],
            "lines": lines, "source": ENGINE, "citation": f"receipts vs PO dates, {q['quarter']} ({lines} lines) (#1.1)"})
    flags = []
    otifs = [q["otif_pct"] for q in quarters]
    if len(otifs) >= TREND_QUARTERS and all(otifs[i] > otifs[i+1] for i in range(len(otifs)-TREND_QUARTERS, len(otifs)-1)):
        flags.append(f"OTIF declining {TREND_QUARTERS} consecutive quarters: {otifs[-TREND_QUARTERS:]} (#1.2)")
        esc.append(f"TREND FLAG: OTIF {otifs[-TREND_QUARTERS:]} across last {TREND_QUARTERS} quarters (vendor-review-rules.md #1.2)")
    p["scorecard"] = {"quarters": quarters, "trend_flags": flags, "confidence": 0.95,
                      "source": ENGINE, "citation": "ERP PO/receipt/return/dispute extracts"}
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("scorecard_roll/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"scorecard_roll: {len(quarters)} quarters, latest OTIF {otifs[-1] if otifs else '-'}%, flags={len(flags)} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
