#!/usr/bin/env python3
"""where_used - deterministic BOM where-used trace (mfg.engineering-change-bom.v1)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:where_used"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ecr", required=True); ap.add_argument("--bom", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.ecr, encoding="utf-8")); bom = json.load(open(a.bom, encoding="utf-8"))
    assert p["contract_version"] == "mfg.engineering-change-bom.v1"
    links = {}
    for l in bom: links.setdefault(l["child"], []).append(l)
    esc = list(p.get("escalations", [])); rows = []
    def walk(part, level):
        for l in links.get(part, []):
            rows.append({"parent": l["parent"], "level": level, "qty_per": l.get("qty_per", 1),
                         "interface_critical": bool(l.get("interface_critical", False)),
                         "source": ENGINE, "citation": f"BOM link {part} -> {l['parent']}"})
            walk(l["parent"], level + 1)
    walk(p["part_number"], 1)
    if not rows: esc.append(f"{p['part_number']}: no where-used links found - trace incomplete (change-rules.md #5)")
    p.update(where_used=rows, escalations=esc)
    p.setdefault("provenance", {}).setdefault("engines", []).append("where_used/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"where_used: {len(rows)} parent link(s), interface_critical={sum(1 for r in rows if r['interface_critical'])} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
