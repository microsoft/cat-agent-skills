#!/usr/bin/env python3
"""risk_score - deterministic supplier risk scoring (mfg.supplier-qualification.v1).
Quality (cert validity #1, audit score, PPAP #4), financial (#2), geographic (#3).
Constants mirror references/qualification-rules.md."""
import argparse, json, sys
from datetime import datetime, timezone, date
ENGINE = "engine:risk_score"
QUICK_RATIO_FLOOR = 1.0   # #2.1
QUICK_RATIO_HIGH = 0.8    # #2.3
BANDS = ["low", "moderate", "high"]
def bump(band, n=1): return BANDS[min(2, BANDS.index(band) + n)]
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dossier", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.dossier, encoding="utf-8"))
    assert p["contract_version"] == "mfg.supplier-qualification.v1"
    d = p["dossier"]; esc = list(p.get("escalations", [])); as_of = date.fromisoformat(p["as_of_date"])
    # quality
    q = "low"; qnotes = []
    cert = d.get("cert", {})
    expired = date.fromisoformat(cert.get("expiry", "1900-01-01")) < as_of
    if expired:
        q = "high"; qnotes.append(f"cert {cert.get('standard','?')} EXPIRED {cert.get('expiry')} (#1.1)")
        esc.append(f"certificate {cert.get('doc_id','?')} expired {cert.get('expiry')} - a cert on file is not a cert in force (qualification-rules.md #1.1)")
    if d.get("audit_score", 100) < 80: q = bump(q); qnotes.append(f"audit score {d['audit_score']} < 80")
    missing = [e for e in p.get("ppap_required", []) if e not in d.get("ppap_elements", [])]
    if missing:
        q = bump(q); qnotes.append(f"PPAP missing: {', '.join(missing)} (#4.1)")
        esc.append(f"PPAP incomplete - missing {', '.join(missing)} (qualification-rules.md #4.1)")
    # financial
    f = "low"; fnotes = []
    qr = d.get("financials", {}).get("quick_ratio"); trend = d.get("financials", {}).get("trend", "stable")
    conf = 0.93
    if qr is None:
        f = "moderate"; conf = 0.6; esc.append("financials missing - confidence below floor, sourcing review (qualification-rules.md #6)")
    else:
        if qr < QUICK_RATIO_FLOOR: f = bump(f); fnotes.append(f"quick ratio {qr} < {QUICK_RATIO_FLOOR} (#2.1)")
        if trend == "declining": f = bump(f); fnotes.append("declining trend (#2.2)")
        if qr < QUICK_RATIO_HIGH and trend == "declining": f = "high"; fnotes.append(f"quick ratio {qr} < {QUICK_RATIO_HIGH} with decline (#2.3)")
    # geographic
    g = "low"; gnotes = []
    conc = p.get("category_region_concentration_pct", 0); region = d.get("region", "?")
    if p.get("candidate_region_matches_concentration") and conc >= 60:
        g = "moderate"; gnotes.append(f"category already {conc}% in {region} (#3.1)")
        esc.append(f"qualification would deepen {region} concentration ({conc}%) - dual-source plan required (qualification-rules.md #3.1)")
    overall = BANDS[max(BANDS.index(q), BANDS.index(f), BANDS.index(g))]
    p["risk"] = {"quality": {"band": q, "notes": qnotes}, "financial": {"band": f, "notes": fnotes},
                 "geographic": {"band": g, "notes": gnotes}, "overall_band": overall,
                 "confidence": conf, "source": ENGINE, "citation": "qualification-rules.md #1-#4"}
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("risk_score/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"risk_score: quality={q} financial={f} geographic={g} overall={overall} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
