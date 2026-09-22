#!/usr/bin/env python3
"""capa_logic - deterministic CA/PA builder + closure-readiness check
(mfg.quality-incident-capa.v1). Builds actions from the action library, enforces
effectiveness checks (#4), systemic PA (#5), and names closure blockers (#6)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:capa_logic"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rca", required=True); ap.add_argument("--actions", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.rca, encoding="utf-8")); lib = json.load(open(a.actions, encoding="utf-8"))
    assert p["contract_version"] == "mfg.quality-incident-capa.v1"
    esc = list(p.get("escalations", []))
    rc = p.get("root_cause", {}); cat = rc.get("category")
    entry = lib.get(cat, {})
    def tag(items, kind):
        out = []
        for it in items:
            it = dict(it); it["source"] = ENGINE; it["citation"] = f"action library[{cat}] · capa-rules.md #{ '5' if kind=='preventive' else '2' }"
            out.append(it)
        return out
    containment = tag(entry.get("containment", []), "containment")
    corrective = tag(entry.get("corrective", []), "corrective")
    preventive = tag(entry.get("preventive", []), "preventive") if rc.get("systemic") else []
    checks = []
    for act in corrective + preventive:
        checks.append({"action": act["action"], "metric": act.get("metric", "recurrence rate = 0 in window"),
                       "owner": act.get("owner", "quality engineer"), "window_days": act.get("window_days", 90),
                       "source": ENGINE, "citation": "capa-rules.md #4"})
    blockers = []
    if not containment: blockers.append("no containment documented (capa-rules.md #1)")
    if not rc.get("why_chain"): blockers.append("root cause not established by structured method (capa-rules.md #2)")
    if rc.get("systemic") and not preventive: blockers.append("systemic cause without preventive action (capa-rules.md #5)")
    if rc.get("confidence", 0) < 0.75: blockers.append("root-cause confidence below floor (capa-rules.md #7)")
    blockers.append("effectiveness verification evidence pending - checks defined, verification not yet run (capa-rules.md #6)")
    p["capa"] = {"containment": containment, "corrective": corrective, "preventive": preventive,
                 "effectiveness_checks": checks}
    p["closure"] = {"ready": len(blockers) == 0,
                    "blockers": blockers, "confidence": 0.9, "source": ENGINE, "citation": "capa-rules.md #6"}
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("capa_logic/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"capa_logic: CA={len(corrective)} PA={len(preventive)} checks={len(checks)} blockers={len(blockers)} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
