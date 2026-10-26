#!/usr/bin/env python3
"""completeness_score - deterministic channel completeness (rtl.product-content-enrichment.v1, #3.1)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:completeness_score"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized", required=True); ap.add_argument("--taxonomy", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.normalized, encoding="utf-8")); tax = json.load(open(a.taxonomy, encoding="utf-8"))
    assert p["contract_version"] == "rtl.product-content-enrichment.v1"
    req = tax["required_by_channel"][p["channel"]]
    rows = []
    for r in p["normalized"]:
        missing = [f for f in req if f not in r["attributes"] or r["attributes"][f] in (None, "")]
        rows.append({"gtin": r["gtin"], "completeness_pct": round(100 * (len(req) - len(missing)) / len(req), 1),
                     "missing_fields": missing, "source": ENGINE,
                     "citation": f"channel '{p['channel']}' requirements (config/taxonomy-map.json, #3.1)"})
    p["completeness"] = rows
    p.setdefault("provenance", {}).setdefault("engines", []).append("completeness_score/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"completeness_score: {len(rows)} SKUs, avg={round(sum(r['completeness_pct'] for r in rows)/len(rows),1)}% -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
