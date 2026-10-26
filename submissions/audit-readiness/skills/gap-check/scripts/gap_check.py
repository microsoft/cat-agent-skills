#!/usr/bin/env python3
"""gap_check - deterministic evidence validation vs clause requirements (Govern engine,
mfg.audit-readiness.v1). Recency (#1), coverage (#2), severity (#3), verdict (#4).
Constants mirror references/audit-rules.md."""
import argparse, json, sys
from datetime import datetime, timezone, date
ENGINE = "engine:gap_check"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapped", required=True); ap.add_argument("--evidence", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.mapped, encoding="utf-8")); ev = json.load(open(a.evidence, encoding="utf-8"))
    assert p["contract_version"] == "mfg.audit-readiness.v1"
    audit_date = date.fromisoformat(p["audit_date"]); esc = list(p.get("escalations", []))
    by_type = {}
    for e in ev: by_type.setdefault(e["type"], []).append(e)
    gaps = []
    for c in p["clause_map"]:
        for req in c["required_evidence"]:
            items = by_type.get(req, [])
            if not items:
                st, det = "missing", f"no {req} in the register"
            else:
                newest = max(items, key=lambda e: e["date"])
                age = (audit_date - date.fromisoformat(newest["date"])).days
                if age > c["max_age_days"]:
                    st, det = "stale", f"newest {req} dated {newest['date']} - {age} days old vs {c['max_age_days']} max (audit-rules.md #1.1)"
                elif c["clause"] == "9.2":
                    covered = {e.get("area") for e in items if (audit_date - date.fromisoformat(e["date"])).days <= c["max_age_days"]}
                    missing_areas = [s for s in p["scope"] if s not in covered]
                    if missing_areas: st, det = "partial", f"internal-audit coverage missing area(s): {', '.join(missing_areas)} (audit-rules.md #2.1)"
                    else: st, det = "present", f"{len(items)} report(s), full coverage"
                elif c["clause"] == "7.2":
                    roles = p.get("active_roles", []); have = {e.get("person") for e in items}
                    missing_people = [r for r in roles if r not in have]
                    if missing_people: st, det = "partial", f"training record absent for: {', '.join(missing_people)}"
                    else: st, det = "present", f"records current ({newest['date']})"
                else:
                    st, det = "present", f"current ({newest['date']}, {age}d old)"
            sev = "none" if st == "present" else (c["criticality"] if c["criticality"] == "major" else "minor")
            row = {"clause": c["clause"], "status": st, "severity": sev, "detail": det,
                   "owner": p.get("owners", {}).get(c["clause"], "process owner"),
                   "action": "" if st == "present" else f"produce/refresh {req} before {p['audit_date']} (audit-rules.md #5 - evidence, not wording)",
                   "source": ENGINE, "citation": c["citation"] + "; audit-rules.md #1-#3"}
            gaps.append(row)
            if sev == "major": esc.append(f"clause {c['clause']} {st}: {det} - MAJOR finding-in-waiting (audit-rules.md #3.1)")
    majors = sum(1 for g in gaps if g["severity"] == "major"); minors = sum(1 for g in gaps if g["severity"] == "minor")
    verdict = "not_ready" if majors else ("conditionally_ready" if minors else "ready")
    p.update(gaps=gaps, readiness={"verdict": verdict, "major_gaps": majors, "minor_gaps": minors,
             "confidence": 0.93, "source": ENGINE, "citation": "audit-rules.md #4"}, escalations=esc)
    p.setdefault("provenance", {}).setdefault("engines", []).append("gap_check/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"gap_check: verdict={verdict} majors={majors} minors={minors} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
