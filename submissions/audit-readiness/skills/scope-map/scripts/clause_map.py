#!/usr/bin/env python3
"""clause_map - deterministic scope-to-clause mapping (mfg.audit-readiness.v1)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:clause_map"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True); ap.add_argument("--clauses", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.audit, encoding="utf-8")); table = json.load(open(a.clauses, encoding="utf-8"))
    assert p["contract_version"] == "mfg.audit-readiness.v1"
    rows = table.get(p["standard"], [])
    esc = list(p.get("escalations", []))
    if not rows: esc.append(f"no clause table for standard {p['standard']} - scope mapping blocked")
    cmap = []
    for c in rows:
        if "all" in c["areas"] or any(s in c["areas"] for s in p["scope"]):
            cmap.append({"clause": c["clause"], "title": c["title"], "required_evidence": c["required_evidence"],
                         "max_age_days": c["max_age_days"], "criticality": c["criticality"],
                         "source": ENGINE, "citation": f"clause-table[{p['standard']}] {c['clause']}"})
    p.update(clause_map=cmap, escalations=esc)
    p.setdefault("provenance", {}).setdefault("engines", []).append("clause_map/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"clause_map: {len(cmap)} clauses in scope -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
