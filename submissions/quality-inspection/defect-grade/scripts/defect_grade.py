#!/usr/bin/env python3
"""defect_grade - deterministic severity & disposition rules engine
(mfg.quality-inspection.v2). Applies references/disposition-rules.md; every grade cites
the rule section that fired. The model narrates the result; it never changes a grade.

Constants mirror references/disposition-rules.md by section number.
"""
import argparse, json, sys, math, tempfile
from replay_quality import verify_deviations
from datetime import datetime, timezone
from pathlib import Path

ENGINE = "engine:defect_grade"
CONFIDENCE_FLOOR = 0.75       # disposition-rules.md #4.1
MRB_INCIDENCE_PCT = 1.0       # disposition-rules.md #2.1
BORDERLINE_BAND = 0.25        # disposition-rules.md #4.2 (percentage points)

DISPO_RANK = ["accept", "use_as_is", "rework", "return_to_vendor", "scrap", "hold_for_review"]

def grade(ch):
    """(severity, disposition, rule, confidence, rationale, requires_deviation)"""
    crit = ch.get("criticality") or "critical"
    if crit not in ("minor", "major", "critical"): crit = "critical"
    rework_ok = ch.get("rework_permitted", False)
    incidence = ch.get("incidence_pct", 0.0)
    if crit == "critical":
        return ("critical", "hold_for_review", "disposition-rules.md #1.1,#3.1", 0.92,
                f"out-of-tolerance on a critical characteristic ({ch.get('criticality_source','')}); "
                "MRB with design authority required", False)
    if crit == "major":
        if incidence > MRB_INCIDENCE_PCT or not rework_ok:
            why = []
            if incidence > MRB_INCIDENCE_PCT: why.append(f"sample incidence {incidence}% > {MRB_INCIDENCE_PCT}%")
            if not rework_ok: why.append("rework not permitted by drawing")
            return ("major", "hold_for_review", "disposition-rules.md #1.2,#3.2", 0.86, "; ".join(why), False)
        return ("major", "rework", "disposition-rules.md #1.2,#3.3", 0.88, "single-part scope, rework permitted", False)
    if rework_ok:
        return ("minor", "rework", "disposition-rules.md #1.3,#3.4", 0.90, "rework permitted", False)
    return ("minor", "use_as_is", "disposition-rules.md #1.3,#3.5", 0.80,
            "use-as-is candidate - deviation authorization and QE sign-off required", True)

def validate(p):
    if not isinstance(p, dict): raise ValueError("deviations must be an object")
    if p.get("contract_version") != "mfg.quality-inspection.v2": raise ValueError("requires v2 contract; rerun source inputs")
    if not p.get("part_number") or not p.get("part_revision") or not p.get("lot_id"): raise ValueError("missing identity")
    chars=p.get("characteristics")
    if not isinstance(chars,list) or not chars: raise ValueError("empty characteristic evidence")
    if any(not isinstance(c, dict) for c in chars): raise ValueError("characteristics must contain objects")
    names=[c.get("name") for c in chars]
    if len(names)!=len(set(names)): raise ValueError("duplicate characteristic")
    for c in chars:
        if not isinstance(c.get("stats", {}), dict): raise ValueError("characteristic stats must be an object")
        st=c.get("status")
        if st not in ("in_tolerance","in_tolerance_marginal","out_of_tolerance","not_evaluated"): raise ValueError("invalid status")
        conf=c.get("confidence")
        if isinstance(conf,bool) or not isinstance(conf,(int,float)) or not math.isfinite(conf) or not 0<=conf<=1: raise ValueError("invalid confidence")
        if c.get("source")!="engine:tolerance_check" or not c.get("citation"): raise ValueError("uncited/unproven deviation")
        if st!="not_evaluated":
            actual=c.get("actual");n=c.get("stats",{}).get("n");oot=c.get("n_out_of_tolerance")
            if isinstance(actual,bool) or not isinstance(actual,(int,float)) or not math.isfinite(actual): raise ValueError("invalid actual")
            if type(n) is not int or n<1 or type(oot) is not int or not 0<=oot<=n: raise ValueError("invalid counts")
            if abs(c.get("incidence_pct",-1)-round(100*oot/n,2))>1e-8: raise ValueError("incidence mismatch")
            if (st=="out_of_tolerance") != (oot>0): raise ValueError("status/count mismatch")
        elif c.get("actual") is not None: raise ValueError("not_evaluated actual must remain null")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deviations", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--coc")
    a = ap.parse_args()
    with open(a.deviations, encoding="utf-8") as handle:
        p = json.load(handle)
    if not isinstance(p, dict):
        raise ValueError("deviations must be an object")
    if p.get("contract_version") != "mfg.quality-inspection.v2":
        raise ValueError("wrong contract version")

    validate(p)
    p = verify_deviations(p, a.spec, a.measurements, a.coc)
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
                        "confidence": min(conf, ch.get("confidence",0)), "source": ENGINE, "citation": rule})

    rec = max((d["disposition"] for d in defects), key=DISPO_RANK.index) if defects else "accept"
    if any(c.get("status") == "not_evaluated" or c.get("confidence", 0) < CONFIDENCE_FLOOR for c in p["characteristics"]):
        rec = "hold_for_review"
        esc.append("Incomplete/low-confidence evidence: lot hold, no acceptance (#4.1,#4.4)")
    p.update(graded_defects=defects, watch_list=watch, recommended_disposition=rec, escalations=esc)
    p.setdefault("provenance", {}).setdefault("engines", []).append("defect_grade/3.1.1")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    destination = Path(a.out)
    pending = None
    try:
        # Replace only after validation, replay and serialization succeed.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                         prefix=".quality-grade-", delete=False) as handle:
            pending = Path(handle.name)
            json.dump(p, handle, indent=2, allow_nan=False)
        pending.replace(destination)
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)
    print(f"defect_grade: {len(defects)} defect(s), {len(watch)} watch item(s), "
          f"recommended_disposition={rec} -> {a.out}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(2)
