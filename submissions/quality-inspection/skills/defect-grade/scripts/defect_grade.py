#!/usr/bin/env python3
"""defect_grade - deterministic severity & disposition rules engine
(mfg.quality-inspection.v1). Applies references/disposition-rules.md; every grade cites
the rule section that fired. The model narrates the result; it never changes a grade.

Constants mirror references/disposition-rules.md by section number.
"""
import argparse, json, sys
from datetime import datetime, timezone

ENGINE = "engine:defect_grade"
CONFIDENCE_FLOOR = 0.75       # disposition-rules.md #4.1
MRB_INCIDENCE_PCT = 1.0       # disposition-rules.md #2.1
BORDERLINE_BAND = 0.25        # disposition-rules.md #4.2 (percentage points)

DISPO_RANK = ["accept", "use_as_is", "rework", "return_to_vendor", "scrap", "hold_for_review"]

def grade(ch):
    """(severity, disposition, rule, confidence, rationale, requires_deviation)"""
    crit = ch.get("criticality", "minor")
    rework_ok = ch.get("rework_permitted", False)
    incidence = ch.get("incidence_pct", 0.0)
    if crit == "critical":
        return ("critical", "hold_for_review", "disposition-rules.md #1.1,#3.1", 0.92,
                f"out-of-tolerance on a critical characteristic ({ch.get('criticality_source','')}); "
                "MRB with design authority required", False)
    if crit == "major":
        if incidence > MRB_INCIDENCE_PCT or not rework_ok:
            why = []
            if incidence > MRB_INCIDENCE_PCT: why.append(f"lot incidence {incidence}% > {MRB_INCIDENCE_PCT}%")
            if not rework_ok: why.append("rework not permitted by drawing")
            return ("major", "hold_for_review", "disposition-rules.md #1.2,#3.2", 0.86, "; ".join(why), False)
        return ("major", "rework", "disposition-rules.md #1.2,#3.3", 0.88, "single-part scope, rework permitted", False)
    if rework_ok:
        return ("minor", "rework", "disposition-rules.md #1.3,#3.4", 0.90, "rework permitted", False)
    return ("minor", "use_as_is", "disposition-rules.md #1.3,#3.5", 0.80,
            "use-as-is candidate - deviation authorization and QE sign-off required", True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deviations", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.deviations, encoding="utf-8"))
    assert p["contract_version"] == "mfg.quality-inspection.v1", "wrong contract version"

    defects, watch = [], []
    esc = list(p.get("escalations", []))
    for ch in p["characteristics"]:
        st = ch["status"]
        if st == "in_tolerance_marginal":
            watch.append({"characteristic": ch["name"],
                "note": (f"worst {ch['actual']} consumes {ch.get('stats',{}).get('band_consumed_pct','>90')}% "
                         "of band - supplier next-lot watch list (disposition-rules.md #1.4)"),
                "citation": ch["citation"]})
        if st != "out_of_tolerance":
            continue
        sev, dispo, rule, conf, why, needs_dev = grade(ch)
        # #4.2 borderline incidence
        if abs(ch.get("incidence_pct", 0.0) - MRB_INCIDENCE_PCT) <= BORDERLINE_BAND:
            esc.append(f"{ch['name']}: incidence {ch.get('incidence_pct')}% is within ±{BORDERLINE_BAND} pp "
                       f"of the {MRB_INCIDENCE_PCT}% MRB threshold - borderline, human confirmation required "
                       "(disposition-rules.md #4.2)")
        # #4.3 document conflict: measurements govern, disposition floor = hold
        if ch.get("doc_conflict"):
            if DISPO_RANK.index(dispo) < DISPO_RANK.index("hold_for_review"):
                dispo, rule = "hold_for_review", rule + ",#4.3"
                why += "; CoC conflict - measurements govern, disposition floor is MRB hold"
        # #4.1 confidence floor
        if ch.get("confidence", 1.0) < CONFIDENCE_FLOOR or conf < CONFIDENCE_FLOOR:
            dispo, rule = "hold_for_review", rule + ",#4.1"
            esc.append(f"{ch['name']}: confidence below {CONFIDENCE_FLOOR} - forced hold (disposition-rules.md #4.1)")
        defects.append({"characteristic": ch["name"], "severity": sev, "disposition": dispo,
                        "rationale": why, "requires_deviation_authorization": needs_dev,
                        "confidence": conf, "source": ENGINE, "citation": rule})

    rec = max((d["disposition"] for d in defects), key=DISPO_RANK.index) if defects else "accept"
    p.update(graded_defects=defects, watch_list=watch, recommended_disposition=rec, escalations=esc)
    p.setdefault("provenance", {}).setdefault("engines", []).append("defect_grade/2.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"defect_grade: {len(defects)} defect(s), {len(watch)} watch item(s), "
          f"recommended_disposition={rec} -> {a.out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
