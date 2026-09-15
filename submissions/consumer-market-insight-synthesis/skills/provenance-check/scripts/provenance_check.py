#!/usr/bin/env python3
"""provenance_check - deterministic rights/geography/expiry gate (Govern engine,
rtl.consumer-insight-synthesis.v1). #4.1 restricted/expired unusable for the declared use."""
import argparse, json, sys
from datetime import datetime, timezone, date
ENGINE = "engine:provenance_check"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compared", required=True); ap.add_argument("--rights", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.compared, encoding="utf-8")); reg = json.load(open(a.rights, encoding="utf-8"))
    assert p["contract_version"] == "rtl.consumer-insight-synthesis.v1"
    use = p["question"]["use_case"]; asof = date.fromisoformat(p["question"]["as_of_date"])
    external = use in ("external", "board", "press")
    esc = list(p.get("escalations", [])); rec = []
    for s in p["retrieved"]:
        r = reg.get(s["study_id"])
        usable, restriction = True, None
        if r is None:
            usable, restriction = False, "no rights register entry - unusable until registered (#4.1)"
        else:
            if r["expires"] and date.fromisoformat(r["expires"]) < asof:
                usable, restriction = False, f"license EXPIRED {r['expires']} (#4.1)"
            elif external and not r["external_use"]:
                usable, restriction = False, f"license '{r['license']}' is internal-only; declared use '{use}' is external-facing (#4.1/#4.2)"
        rec.append({"study_id": s["study_id"], "usable": usable, "restriction": restriction,
                    "source": ENGINE, "citation": (r or {}).get("citation", "rights register (missing row)")})
        if not usable:
            esc.append(f"{s['study_id']}: {restriction} - excluded from the '{use}' brief however strong the stat (insight-rules.md #4.1)")
    p["provenance_record"] = rec; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("provenance_check/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"provenance_check: {sum(1 for r in rec if r['usable'])}/{len(rec)} usable for '{use}' -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
