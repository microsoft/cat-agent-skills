#!/usr/bin/env python3
"""rca_tree - deterministic 5-Why chain selection (mfg.quality-incident-capa.v1).
Selects the evidenced why-chain for the top Pareto category from the cause-link library;
applies the systemic test and the operator-error rejection (capa-rules.md #3.4)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:rca_tree"
MIN_DEPTH = 3          # capa-rules.md #2.2
SYSTEMIC_MIN = 2       # rca-methods.md systemic test / capa-rules.md #5
CONFIDENCE_FLOOR = 0.75  # capa-rules.md #7

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pareto", required=True); ap.add_argument("--links", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.pareto, encoding="utf-8")); links = json.load(open(a.links, encoding="utf-8"))
    assert p["contract_version"] == "mfg.quality-incident-capa.v1"
    esc = list(p.get("escalations", []))
    top = p["pareto"][0]
    cat = top["cause_category"]
    recurrence = top["count"]
    systemic = len(top["parts_affected"]) >= SYSTEMIC_MIN or len(top.get("machines_affected", [])) >= SYSTEMIC_MIN
    # operator-error rejection (#3.4): fires whenever a recurring operator-error label
    # exists in the window - the narrative label is never accepted as terminal root cause.
    oe = next((r for r in p["pareto"] if r["cause_category"] == "operator_error" and r["count"] > 1), None)
    if oe and cat != "operator_error":
        esc.append(f"'operator_error' label present with recurrence {oe['count']} - rejected as terminal "
                   f"root cause; systemic analysis applied instead (capa-rules.md #3.4)")
    if cat == "operator_error" and recurrence > 1:
        alt = p["pareto"][1] if len(p["pareto"]) > 1 else None
        esc.append(f"'operator_error' rejected as terminal root cause - recurrence {recurrence} across "
                   f"{len(top['parts_affected'])} part(s) requires a deeper systemic cause (capa-rules.md #3.4)")
        if alt: cat, top, systemic = alt["cause_category"], alt, (len(alt["parts_affected"]) >= SYSTEMIC_MIN or len(alt.get("machines_affected", [])) >= SYSTEMIC_MIN)
    entry = links.get(cat)
    if not entry:
        esc.append(f"no cause-link entry for '{cat}' - root cause requires manual 5-Why (capa-rules.md #2.1)")
        p.update(root_cause={"method": "pareto+5why", "category": cat, "why_chain": [],
                             "systemic": systemic, "confidence": 0.0, "source": ENGINE,
                             "citation": "rca-methods.md; no library chain"}, escalations=esc)
    else:
        chain = entry["why_chain"]; conf = entry["base_confidence"]
        if len(chain) < MIN_DEPTH:
            esc.append(f"why-chain depth {len(chain)} < {MIN_DEPTH} (capa-rules.md #2.2)"); conf = min(conf, 0.6)
        if conf < CONFIDENCE_FLOOR:
            esc.append(f"root-cause confidence {conf} < {CONFIDENCE_FLOOR} - quality-manager review (capa-rules.md #7)")
        p.update(root_cause={"method": "pareto+5why", "category": cat, "why_chain": chain,
                             "systemic": systemic, "confidence": conf, "source": ENGINE,
                             "citation": f"rca-methods.md; cause-links[{cat}]; {top['citation']}"}, escalations=esc)
    p.setdefault("provenance", {}).setdefault("engines", []).append("rca_tree/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    rc = p["root_cause"]
    print(f"rca_tree: category={rc['category']} systemic={rc['systemic']} conf={rc['confidence']} depth={len(rc['why_chain'])} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
