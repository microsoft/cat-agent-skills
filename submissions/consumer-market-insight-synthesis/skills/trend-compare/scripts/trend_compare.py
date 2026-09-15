#!/usr/bin/env python3
"""trend_compare - deterministic retrieval ranking + like-for-like trend deltas +
contradiction flags (rtl.consumer-insight-synthesis.v1). Rules mirror insight-rules.md."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:trend_compare"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True); ap.add_argument("--index", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.question, encoding="utf-8")); idx = json.load(open(a.index, encoding="utf-8"))
    assert p["contract_version"] == "rtl.consumer-insight-synthesis.v1"
    q = p["question"]; esc = list(p.get("escalations", []))
    scored = []
    for s in idx:
        rel = (2 if s["market"] == q["market"] else 0) + sum(1 for t in q["topics"] if t in s["topics"])
        rel += 1 if s["period"] >= q.get("recency_floor", "2024") else 0
        if rel > 0: scored.append({**s, "relevance": rel, "source": ENGINE, "citation": f"research index {s['study_id']} (#1.1)"})
    scored.sort(key=lambda s: (-s["relevance"], s["period"]))
    p["retrieved"] = scored
    # like-for-like trends (#2.1)
    trends, contradictions = [], []
    by_metric = {}
    for s in scored: by_metric.setdefault((s["metric"], s["market"]), []).append(s)
    for (metric, market), studies in by_metric.items():
        studies.sort(key=lambda s: s["period"])
        if len(studies) >= 2:
            for i in range(len(studies)-1):
                a_, b_ = studies[i], studies[i+1]
                delta = round(b_["value"] - a_["value"], 2)
                trends.append({"metric": metric, "market": market,
                    "from": {"study": a_["study_id"], "period": a_["period"], "value": a_["value"]},
                    "to": {"study": b_["study_id"], "period": b_["period"], "value": b_["value"]},
                    "delta": delta, "direction": "up" if delta > 0 else ("down" if delta < 0 else "flat"),
                    "source": ENGINE, "citation": f"{a_['study_id']} vs {b_['study_id']} (#2.1)"})
            dirs = {t["direction"] for t in trends if t["metric"] == metric and t["direction"] != "flat"}
            if len(dirs) > 1:
                pair = [t for t in trends if t["metric"] == metric]
                contradictions.append({"metric": metric, "market": market,
                    "detail": f"{metric} moves BOTH directions across periods: " + "; ".join(f"{t['from']['study']}->{t['to']['study']} {t['direction']} ({t['delta']:+})" for t in pair),
                    "methods": [s["method"] for s in studies],
                    "source": ENGINE, "citation": "both presented with dates and methods (#3.1)"})
                esc.append(f"CONTRADICTION on {metric}: opposing directions across studies - both sides go in the brief, no midpoint smoothing (insight-rules.md #3.1)")
    p["trends"] = trends; p["contradictions"] = contradictions; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("trend_compare/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"trend_compare: {len(scored)} retrieved, {len(trends)} trend(s), {len(contradictions)} contradiction(s) -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
