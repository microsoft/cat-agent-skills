#!/usr/bin/env python3
"""tolerance_check - deterministic deviation engine (mfg.quality-inspection.v1).

Reads the ingested spec (characteristics.json), normalized measurements (CSV), and the
CoC claims (coc.json, optional). Computes per-characteristic statistics and deviation
status, and cross-checks certificate claims against measured reality.

Same input, same output, always: no LLM calls, no network, no randomness. The model
invokes this and quotes its output; it never recomputes a deviation itself.

Constants mirror references/disposition-rules.md by section number.
"""
import argparse, csv, json, sys
from datetime import datetime, timezone

ENGINE = "engine:tolerance_check"
MARGINAL_BAND = 0.90          # disposition-rules.md #1.4

def band_position(value, lsl, usl, nominal):
    center = nominal if nominal is not None else (lsl + usl) / 2.0
    half = max(usl - center, center - lsl)
    return abs(value - center) / half if half > 0 else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--coc", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    spec = json.load(open(a.spec, encoding="utf-8"))
    rows = list(csv.DictReader(open(a.measurements, encoding="utf-8")))
    coc = json.load(open(a.coc, encoding="utf-8")) if a.coc else None

    claimed = {}
    if coc:
        for cl in coc.get("claims", []):
            for ch in cl["characteristics"]:
                claimed[ch] = cl

    by_char = {}
    for r in rows:
        by_char.setdefault(r["characteristic"], []).append(float(r["value"]))

    characteristics, escalations = [], []
    for ch in spec["characteristics"]:
        name = ch["name"]; vals = by_char.get(name, [])
        base = {
            "name": name, "unit": ch.get("unit", ""),
            "nominal": ch.get("nominal"), "lower_tolerance": ch.get("lsl"),
            "upper_tolerance": ch.get("usl"),
            "criticality": ch.get("criticality", "minor"),
            "criticality_source": ch.get("criticality_source", ch.get("citation", "")),
            "rework_permitted": bool(ch.get("rework_permitted", False)),
            "doc_conflict": False,
            "source": ENGINE, "citation": ch.get("citation", "UNCITED"),
        }
        lsl, usl = ch.get("lsl"), ch.get("usl")
        if not vals or lsl is None or usl is None:
            reason = "no measurements found" if not vals else "missing tolerance"
            base.update(actual=0.0, stats={"n": len(vals)}, n_out_of_tolerance=0,
                        incidence_pct=0.0, status="not_evaluated", confidence=0.0)
            escalations.append(f"{name}: {reason} - grading blocked (disposition-rules.md #4.4)")
            characteristics.append(base); continue

        out_vals = [v for v in vals if v < lsl or v > usl]
        worst = max(vals, key=lambda v: band_position(v, lsl, usl, ch.get("nominal")) or 0)
        pos = band_position(worst, lsl, usl, ch.get("nominal"))
        if out_vals: status = "out_of_tolerance"
        elif pos is not None and pos > MARGINAL_BAND: status = "in_tolerance_marginal"
        else: status = "in_tolerance"
        base.update(
            actual=round(worst, 4),
            stats={"n": len(vals), "mean": round(sum(vals)/len(vals), 4),
                   "min": round(min(vals), 4), "max": round(max(vals), 4),
                   "band_consumed_pct": round(100 * pos, 1) if pos is not None else None},
            n_out_of_tolerance=len(out_vals),
            incidence_pct=round(100.0 * len(out_vals) / len(vals), 2),
            status=status, confidence=0.99)
        # CoC cross-check: measurements govern (disposition-rules.md #4.3)
        if status == "out_of_tolerance" and name in claimed:
            base["doc_conflict"] = True
            escalations.append(
                f"{name}: CoC {coc.get('doc_id','?')} claims '{claimed[name]['claim']}' but "
                f"{len(out_vals)}/{len(vals)} measurements are out of tolerance - measurements govern; "
                f"supplier-quality review / SCAR candidate (disposition-rules.md #4.3; ISO 9001 8.4.3)")
        characteristics.append(base)

    payload = {
        "contract_version": "mfg.quality-inspection.v1",
        "part_number": spec["part_number"], "part_revision": spec.get("part_revision", ""),
        "lot_id": spec["lot_id"], "lot_quantity": spec.get("lot_quantity", 0),
        "sample_size": max((c["stats"].get("n", 0) for c in characteristics), default=0),
        "coc": coc or {}, "characteristics": characteristics, "escalations": escalations,
        "provenance": {"engines": ["tolerance_check/2.0"],
                       "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
    }
    json.dump(payload, open(a.out, "w", encoding="utf-8"), indent=2)
    n_out = sum(1 for c in characteristics if c["status"] == "out_of_tolerance")
    n_conf = sum(1 for c in characteristics if c["doc_conflict"])
    print(f"tolerance_check: {len(characteristics)} characteristics, {n_out} out_of_tolerance, "
          f"{n_conf} doc_conflict, {len(escalations)} escalation(s) -> {a.out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
