#!/usr/bin/env python3
"""claim_match - deterministic claim-to-term/promotion matching (rtl.trade-deduction-recovery.v1, #1.1)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:claim_match"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deduction", required=True); ap.add_argument("--terms", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.deduction, encoding="utf-8")); terms = json.load(open(a.terms, encoding="utf-8"))
    assert p["contract_version"] == "rtl.trade-deduction-recovery.v1"
    esc = list(p.get("escalations", [])); matches = []
    for c in p["claims"]:
        hit = next((t for t in terms if t["customer"] == p["customer"] and t["type"] == c["type"] and t["period"] == c["period"] and t["signed"]), None)
        if hit:
            matches.append({"claim_id": c["claim_id"], "term_id": hit["term_id"], "term": hit,
                            "backup_present": bool(c.get("backup_doc")),
                            "source": ENGINE, "citation": hit["citation"]})
        else:
            matches.append({"claim_id": c["claim_id"], "term_id": None, "term": None,
                            "backup_present": bool(c.get("backup_doc")),
                            "source": ENGINE, "citation": "no signed term/promotion matches customer+period+type (#1.1)"})
            esc.append(f"{c['claim_id']}: UNMATCHED - no signed term for {c['type']} {c['period']} (deduction-rules.md #1.1)")
    p["matches"] = matches; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("claim_match/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"claim_match: {sum(1 for m in matches if m['term_id'])}/{len(matches)} matched -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
