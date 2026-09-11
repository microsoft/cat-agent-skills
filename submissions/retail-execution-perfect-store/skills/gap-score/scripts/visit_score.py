#!/usr/bin/env python3
"""visit_score - deterministic perfect-store scoring (rtl.retail-execution-perfect-store.v1).
#1.1 pass/fail per criterion from audit answers; photos referenced, never scored (#3.1)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:visit_score"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--visit", required=True); ap.add_argument("--standards", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.visit, encoding="utf-8")); std = json.load(open(a.standards, encoding="utf-8"))
    assert p["contract_version"] == "rtl.retail-execution-perfect-store.v1"
    key = f"{p['outlet']['channel']}:{p['outlet']['cluster']}"
    esc = list(p.get("escalations", []))
    if key not in std:
        esc.append(f"no perfect-store standard for '{key}' - scoring blocked (#5)")
        p.update(compliance={"criteria": [], "compliance_pct": 0.0, "confidence": 0.0,
                             "source": ENGINE, "citation": "standard missing"}, escalations=esc)
    else:
        s = std[key]; answers = p["visit"]["audit_answers"]; rows = []
        for c in s["criteria"]:
            ans = answers.get(c["id"])
            passed = bool(ans and ans.get("pass"))
            rows.append({"id": c["id"], "type": c["type"], "sku": c.get("sku"), "desc": c["desc"],
                         "pass": passed, "answer": ans, "photo_ref": (ans or {}).get("photo"),
                         "source": ENGINE, "citation": f"{s['citation']} {c['id']}; audit answer (photos evidence-only, #3.1)"})
        n = len(rows); passes = sum(1 for r in rows if r["pass"])
        p["compliance"] = {"criteria": rows, "compliance_pct": round(100*passes/n, 1),
                           "confidence": 0.95, "source": ENGINE, "citation": s["citation"]}
        p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("visit_score/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    c = p["compliance"]; print(f"visit_score: {c['compliance_pct']}% ({sum(1 for r in c['criteria'] if r['pass'])}/{len(c['criteria'])}) -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
