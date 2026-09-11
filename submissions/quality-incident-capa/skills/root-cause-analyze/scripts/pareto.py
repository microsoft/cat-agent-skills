#!/usr/bin/env python3
"""pareto - deterministic complaint-window Pareto (mfg.quality-incident-capa.v1).
Ranks cause categories by frequency; tracks part/machine spread for the systemic test.
Constants mirror references/capa-rules.md / rca-methods.md."""
import argparse, csv, json, sys
from datetime import datetime, timezone
ENGINE = "engine:pareto"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capa", required=True); ap.add_argument("--complaints", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.capa, encoding="utf-8"))
    assert p["contract_version"] == "mfg.quality-incident-capa.v1"
    rows = list(csv.DictReader(open(a.complaints, encoding="utf-8")))
    agg = {}
    for r in rows:
        c = r["cause_category"]
        d = agg.setdefault(c, {"count": 0, "parts": set(), "machines": set()})
        d["count"] += 1; d["parts"].add(r["part_number"]); d["machines"].add(r.get("machine", ""))
    total = sum(d["count"] for d in agg.values()); cum = 0.0; pareto = []
    for c, d in sorted(agg.items(), key=lambda kv: -kv[1]["count"]):
        share = round(100 * d["count"] / total, 1); cum = round(cum + share, 1)
        pareto.append({"cause_category": c, "count": d["count"], "share_pct": share,
                       "cumulative_pct": cum, "parts_affected": sorted(d["parts"]),
                       "machines_affected": sorted(x for x in d["machines"] if x),
                       "source": ENGINE, "citation": f"complaint log, {len(rows)} rows / {p.get('complaint_window_days','?')}d window"})
    p["pareto"] = pareto
    p.setdefault("provenance", {}).setdefault("engines", []).append("pareto/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"pareto: {len(pareto)} categories, top={pareto[0]['cause_category'] if pareto else None} ({pareto[0]['share_pct'] if pareto else 0}%) -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
