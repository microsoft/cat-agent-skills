#!/usr/bin/env python3
"""issue_cluster - deterministic issue clustering + term mapping
(rtl.supplier-vendor-performance.v1). #2.1 clusters need >=3 occurrences; #3.1 breaches map to clauses."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:issue_cluster"
MIN_CLUSTER = 3  # vendor-review-rules.md #2.1
OTIF_TERM_FLOOR = 90.0
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True); ap.add_argument("--issues", required=True)
    ap.add_argument("--terms", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.scored, encoding="utf-8")); issues = json.load(open(a.issues, encoding="utf-8"))
    terms = json.load(open(a.terms, encoding="utf-8"))
    assert p["contract_version"] == "rtl.supplier-vendor-performance.v1"
    esc = list(p.get("escalations", []))
    agg = {}
    for i in issues:
        agg.setdefault((i["type"], i["lane"]), []).append(i["record_id"])
    clusters = [{"type": t, "lane": l, "count": len(ids), "evidence": ids,
                 "source": ENGINE, "citation": f"{len(ids)} records (#2.1)"}
                for (t, l), ids in agg.items() if len(ids) >= MIN_CLUSTER]
    clusters.sort(key=lambda c: -c["count"])
    vterms = [t for t in terms if t["vendor"] == p["vendor"]["name"]]
    gov = []
    latest = p["scorecard"]["quarters"][-1]
    if latest["otif_pct"] < OTIF_TERM_FLOOR:
        hit = next((t for t in vterms if t["topic"] == "otif"), None)
        if hit:
            gov.append({"term_id": hit["term_id"], "text": hit["text"], "trigger": f"OTIF {latest['otif_pct']}% < 90%",
                        "remedies": ["corrective action request", "2% quarterly rebate"],
                        "source": ENGINE, "citation": hit["citation"] + " (#3.1/#3.2)"})
            esc.append(f"term TT trigger: OTIF {latest['otif_pct']}% < 90% - remedies stated per {hit['term_id']}; invoking them is the buyer's decision (#3.2)")
        else:
            esc.append("OTIF breach without a retrieved clause - open item (#3.1)")
    if any(c["type"] == "short_ship" for c in clusters):
        hit = next((t for t in vterms if t["topic"] == "short_ship"), None)
        if hit: gov.append({"term_id": hit["term_id"], "text": hit["text"], "trigger": "short-ship cluster",
                            "remedies": ["substantiated credit within 14 days"], "source": ENGINE, "citation": hit["citation"]})
    p["issue_clusters"] = clusters; p["governing_terms"] = gov; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("issue_cluster/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"issue_cluster: {len(clusters)} cluster(s), {len(gov)} governing term(s) -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
