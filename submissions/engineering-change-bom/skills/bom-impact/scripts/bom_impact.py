#!/usr/bin/env python3
"""bom_impact - deterministic change-impact rollup (mfg.engineering-change-bom.v1).
Impact class (#1), interface rule (#2), document rule (#3), inventory disposition (#4).
Constants mirror references/change-rules.md."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:bom_impact"
CLASS_MAP = {"dimension_change": "fit", "tolerance_relax": "fit", "tolerance_tighten": "fit",
             "material_change": "function", "finish_change": "form", "note_change": "form"}  # change-rules.md #1
DISPO = {"form": "use-up permitted", "fit": "use-up with QE concurrence; WIP review required",
         "function": "hold WIP and on-hand pending change board"}                              # change-rules.md #4
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traced", required=True); ap.add_argument("--docs", required=True)
    ap.add_argument("--inventory", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.traced, encoding="utf-8")); docs = json.load(open(a.docs, encoding="utf-8"))
    inv = json.load(open(a.inventory, encoding="utf-8"))
    assert p["contract_version"] == "mfg.engineering-change-bom.v1"
    esc = list(p.get("escalations", []))
    cls = CLASS_MAP.get(p["change_type"], "function")
    iface = any(r["interface_critical"] for r in p.get("where_used", []))
    if iface and p["change_type"] in ("dimension_change", "tolerance_relax", "tolerance_tighten"):
        cls = "function"
        esc.append(f"INTERFACE VIOLATION candidate: {p['affected_characteristic']} on {p['part_number']} has "
                   f"interface-critical where-used link(s) - mating-part analysis + change-board review required; "
                   f"not a minor change (change-rules.md #2; ASME Y14.5 fit definition)")
    affected = [{"item": r["parent"], "level": r["level"], "reason": "where-used parent",
                 "source": ENGINE, "citation": r["citation"]} for r in p.get("where_used", [])]
    to_update, blocked = [], False
    for d in docs:
        if p["affected_characteristic"] in d.get("references", []):
            row = {"doc": d["doc"], "revision": d["revision"], "current_revision": d["current_revision"],
                   "obsolete": d["revision"] != d["current_revision"], "source": ENGINE,
                   "citation": f"{d['doc']} references {p['affected_characteristic']} (change-rules.md #3)"}
            to_update.append(row)
            if row["obsolete"]:
                blocked = True
                esc.append(f"{d['doc']} is at obsolete rev {d['revision']} (current {d['current_revision']}) - "
                           f"release blocked until updated (change-rules.md #3)")
    stock = inv.get(p["part_number"], {"on_hand": 0, "wip": 0})
    conf = 0.95 if p.get("where_used") else 0.5
    if conf < 0.75: esc.append("where-used trace incomplete - ECN blocked (change-rules.md #5)")
    p["impact"] = {"impact_class": cls, "interface_violation": iface and cls == "function",
                   "affected_items": affected, "documents_to_update": to_update,
                   "inventory_disposition": {"policy": DISPO[cls], "on_hand": stock["on_hand"], "wip": stock["wip"],
                                             "citation": "change-rules.md #4"},
                   "release_blocked": blocked, "confidence": conf, "source": ENGINE,
                   "citation": "change-rules.md #1-#4"}
    p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("bom_impact/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"bom_impact: class={cls} interface_violation={p['impact']['interface_violation']} docs={len(to_update)} blocked={blocked} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
