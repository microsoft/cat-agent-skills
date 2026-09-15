#!/usr/bin/env python3
"""capacity_check - deterministic capacity + material-gate check (mfg.production-planning.v1).
Rules #1 (load/utilization), #2 (material gate), #6 (data completeness)."""
import argparse, json, sys
from datetime import datetime, timezone, date
ENGINE = "engine:capacity_check"
UTIL_ESCALATION_PCT = 95.0   # scheduling-rules.md #1.2
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True); ap.add_argument("--workcenter", required=True)
    ap.add_argument("--materials", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.plan, encoding="utf-8")); wc = json.load(open(a.workcenter, encoding="utf-8"))
    mats = json.load(open(a.materials, encoding="utf-8"))
    assert p["contract_version"] == "mfg.production-planning.v1"
    esc = list(p.get("escalations", []))
    run_hours = 0.0; gates = []; conf = 0.95
    for o in p["orders"]:
        if "run_hours" not in o: esc.append(f"{o['order_id']}: missing routing hours (scheduling-rules.md #6)"); conf = 0.5; continue
        run_hours += o["run_hours"]
        m = mats.get(o["order_id"])
        if m and date.fromisoformat(m["available"]) > date.fromisoformat(p["week_start"]):
            gates.append({"order_id": o["order_id"], "material": m["part"], "available": m["available"],
                          "source": ENGINE, "citation": f"material plan {o['order_id']} (scheduling-rules.md #2.1)"})
    avail = wc["available_hours"]
    util_run_only = round(100 * run_hours / avail, 1)
    p["capacity"] = {"available_hours": avail, "load_hours": run_hours, "utilization_pct": util_run_only,
                     "material_gates": gates, "feasible": util_run_only <= 100.0,
                     "confidence": conf, "source": ENGINE,
                     "citation": f"work center {wc['id']} calendar; run-hours only - changeovers added by sequence_optimize (scheduling-rules.md #1.1)"}
    if conf < 0.75: esc.append("planning data incomplete - schedule blocked (scheduling-rules.md #6)")
    for g in gates: esc.append(f"{g['order_id']} material-gated until {g['available']} - must not start earlier (scheduling-rules.md #2.1)")
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("capacity_check/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"capacity_check: run-hours {run_hours}/{avail} ({util_run_only}%), gates={len(gates)} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
