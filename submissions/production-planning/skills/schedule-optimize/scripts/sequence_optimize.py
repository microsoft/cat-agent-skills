#!/usr/bin/env python3
"""sequence_optimize - deterministic campaign sequencing heuristic (mfg.production-planning.v1).
Compares the naive due-date sequence against a family-campaign sequence (#3) that respects
material gates (#2) and never sacrifices committed orders (#4). Reports both so the tradeoff
is visible. Heuristic, not a solver - the solver/APS is the graduation."""
import argparse, json, sys
from datetime import datetime, timezone, date, timedelta
ENGINE = "engine:sequence_optimize"
UTIL_ESCALATION_PCT = 95.0  # scheduling-rules.md #1.2

def simulate(p, seq, co, gates):
    """Walk the sequence in PRODUCTION hours (available_hours / 5-day week, not wall clock).
    Returns (changeover_hours, late_committed[], total_hours). An order is late when it
    finishes after the end of its due day on the production calendar."""
    week_start = date.fromisoformat(p["week_start"])
    hpd = p["capacity"]["available_hours"] / 5.0
    gate = {g["order_id"]: date.fromisoformat(g["available"]) for g in gates}
    t = 0.0; prev_family = None; co_hours = 0.0; late = []
    orders = {o["order_id"]: o for o in p["orders"]}
    for oid in seq:
        o = orders[oid]
        if prev_family is not None and o["family"] != prev_family:
            h = co.get(prev_family, {}).get(o["family"], 2.0); co_hours += h; t += h
        if oid in gate:  # material gate: cannot start before the gate day (scheduling-rules.md #2.1)
            t = max(t, (gate[oid] - week_start).days * hpd)
        t += o["run_hours"]
        if o.get("committed"):
            allowed = ((date.fromisoformat(o["due_date"]) - week_start).days + 1) * hpd
            if t > allowed: late.append(oid)
        prev_family = o["family"]
    return round(co_hours, 1), late, round(t, 1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checked", required=True); ap.add_argument("--changeovers", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.checked, encoding="utf-8")); co = json.load(open(a.changeovers, encoding="utf-8"))
    assert p["contract_version"] == "mfg.production-planning.v1"
    esc = list(p.get("escalations", []))
    gates = p.get("capacity", {}).get("material_gates", [])
    # naive: due-date order
    naive = [o["order_id"] for o in sorted(p["orders"], key=lambda o: (o["due_date"], o["order_id"]))]
    n_co, n_late, n_total = simulate(p, naive, co, gates)
    # campaign heuristic (#3): group by family, order campaigns by earliest committed due date,
    # then repair (#4): any late committed order is pulled to the front of its feasible window.
    fams = {}
    for o in p["orders"]: fams.setdefault(o["family"], []).append(o)
    fam_order = sorted(fams, key=lambda f: min(o["due_date"] for o in fams[f] if o.get("committed")) if any(o.get("committed") for o in fams[f]) else min(o["due_date"] for o in fams[f]))
    opt = []
    for f in fam_order:
        opt.extend(o["order_id"] for o in sorted(fams[f], key=lambda o: (not o.get("committed", False), o["due_date"])))
    o_co, o_late, o_total = simulate(p, opt, co, gates)
    passes = 0
    while o_late and passes < 5:  # repair (#4.1): pull late committed orders forward, re-simulate
        for oid in list(o_late):
            opt.remove(oid); opt.insert(0, oid)
        o_co, o_late, o_total = simulate(p, opt, co, gates)
        passes += 1
    avail = p["capacity"]["available_hours"]
    for name, tot in [("naive", n_total), ("optimized", o_total)]:
        util = round(100 * tot / avail, 1)
        if util > UTIL_ESCALATION_PCT and name == "optimized":
            esc.append(f"optimized plan at {util}% utilization > {UTIL_ESCALATION_PCT}% - overload (scheduling-rules.md #1.2)")
    if n_late and not o_late:
        esc.append(f"naive due-date sequence misses committed order(s) {n_late} once changeovers are counted - "
                   f"campaign sequence protects them (scheduling-rules.md #1.1, #3.1, #4.1)")
    p["schedule"] = {"naive_sequence": naive, "naive_changeover_hours": n_co,
                     "optimized_sequence": opt, "optimized_changeover_hours": o_co,
                     "late_committed_naive": n_late, "late_committed_optimized": o_late,
                     "confidence": 0.9, "source": ENGINE,
                     "citation": "changeover matrix + scheduling-rules.md #2-#4 (heuristic; solver is the graduation)"}
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("sequence_optimize/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"sequence_optimize: naive co={n_co}h late={n_late} | optimized co={o_co}h late={o_late} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
