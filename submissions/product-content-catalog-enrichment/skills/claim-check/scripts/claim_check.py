#!/usr/bin/env python3
"""claim_check - deterministic claim / regulated-term validation (Govern engine,
rtl.product-content-enrichment.v1). #4.1 library match per GTIN; #4.2 regulated terms blocked
without substantiation for the market; #4.3 blocked claims never appear in copy."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:claim_check"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True); ap.add_argument("--library", required=True)
    ap.add_argument("--market", default="US"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.scored, encoding="utf-8")); lib = json.load(open(a.library, encoding="utf-8"))
    assert p["contract_version"] == "rtl.product-content-enrichment.v1"
    esc = list(p.get("escalations", [])); findings = []
    approved = {(e["gtin"], e["claim"].lower()): e for e in lib["approved"]}
    for r in p["normalized"]:
        copy = (r["attributes"].get("supplier_copy") or "").lower()
        for term in lib["regulated_terms"]:
            if term in copy:
                key = (r["gtin"], term)
                hit = approved.get(key)
                if hit and a.market in hit["markets"]:
                    findings.append({"gtin": r["gtin"], "claim": term, "verdict": "approved",
                        "detail": f"substantiated: {hit['substantiation']}", "source": ENGINE,
                        "citation": f"claim library {hit['substantiation']} (#4.1)"})
                else:
                    findings.append({"gtin": r["gtin"], "claim": term, "verdict": "regulated_blocked",
                        "detail": f"regulated term without substantiation for market {a.market} - BLOCKED from copy (#4.2, #4.3)",
                        "source": ENGINE, "citation": "config/claim-library.json regulated_terms"})
                    esc.append(f"GTIN {r['gtin']}: regulated claim '{term}' BLOCKED - no substantiation for {a.market} (enrichment-rules.md #4.2)")
    p["claim_findings"] = findings; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("claim_check/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    blocked = sum(1 for f in findings if f["verdict"] == "regulated_blocked")
    print(f"claim_check: {len(findings)} finding(s), blocked={blocked} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
