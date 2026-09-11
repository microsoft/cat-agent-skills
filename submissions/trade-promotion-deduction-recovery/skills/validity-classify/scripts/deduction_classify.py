#!/usr/bin/env python3
"""deduction_classify + promo_lift - deterministic validity (Govern) + scoped lift
(rtl.trade-deduction-recovery.v1). Constants mirror references/deduction-rules.md."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:deduction_classify"; LIFT = "engine:promo_lift"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matched", required=True); ap.add_argument("--scoping", required=True)
    ap.add_argument("--scan", default=None); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.matched, encoding="utf-8")); scope = json.load(open(a.scoping, encoding="utf-8"))
    assert p["contract_version"] == "rtl.trade-deduction-recovery.v1"
    esc = list(p.get("escalations", [])); validity = []
    claims = {c["claim_id"]: c for c in p["claims"]}
    for m in p["matches"]:
        c = claims[m["claim_id"]]
        if not m["term_id"] or not m["backup_present"]:
            why = [] 
            if not m["term_id"]: why.append("no matching signed term (#2.3)")
            if not m["backup_present"]: why.append("no backup document (#2.3)")
            validity.append({"claim_id": c["claim_id"], "verdict": "unsupported",
                "disputable_amount": round(c["claimed_amount"], 2),
                "calculation": f"fully disputable pending backup/term: {'; '.join(why)}",
                "confidence": 0.9, "source": ENGINE, "citation": m["citation"] + "; deduction-rules.md #2.3"})
            continue
        t = m["term"]
        entitled = round(t["rate_pct"]/100.0 * c["actual_volume_value"], 2) if "rate_pct" in t else t.get("flat_amount", 0.0)
        if c["claimed_amount"] <= entitled + 0.01:
            validity.append({"claim_id": c["claim_id"], "verdict": "valid", "disputable_amount": 0.0,
                "calculation": f"claimed {c['claimed_amount']} <= entitled {entitled} ({t.get('rate_pct','flat')}% x {c.get('actual_volume_value','-')})",
                "confidence": 0.93, "source": ENGINE, "citation": t["citation"] + "; deduction-rules.md #2.1"})
        else:
            disp = round(c["claimed_amount"] - entitled, 2)
            validity.append({"claim_id": c["claim_id"], "verdict": "partial", "disputable_amount": disp,
                "calculation": f"claimed {c['claimed_amount']} - entitled {entitled} ({t['rate_pct']}% x {c['actual_volume_value']}) = {disp}",
                "confidence": 0.9, "source": ENGINE, "citation": t["citation"] + "; deduction-rules.md #2.2"})
            esc.append(f"{c['claim_id']}: claimed rate exceeds signed {t['rate_pct']}% - disputable {disp} with calculation shown (#2.2). Write-off is a human decision (#2.4)")
    total = round(sum(v["disputable_amount"] for v in validity), 2)
    # promo lift - scoped by RGM foundation (#3.1)
    if scope.get("account_pnl_present") and a.scan:
        scan = json.load(open(a.scan, encoding="utf-8"))
        base = sum(scan["pre_period_units"]) / len(scan["pre_period_units"])
        lift = round(100 * (sum(scan["promo_period_units"])/len(scan["promo_period_units"]) - base) / base, 1)
        p["promo_lift"] = {"baseline_weekly_units": round(base, 1), "lift_pct": lift,
                           "source": LIFT, "citation": "fixed pre-period baseline (#3.2)"}
    else:
        p["promo_lift"] = {"skipped": True, "reason": scope["note"], "source": LIFT, "citation": scope["citation"] + "; deduction-rules.md #3.1"}
        esc.append("promo_lift SKIPPED by scoping rule - account P&L foundation absent; deduction validity unaffected (#3.1)")
    p["validity"] = validity; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).extend(["deduction_classify/1.0", "promo_lift/1.0"])
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"deduction_classify: {len(validity)} claim(s), disputable total {total} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
