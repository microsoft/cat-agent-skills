#!/usr/bin/env python3
"""reason_classify - deterministic reason classification vs taxonomy (rtl.returns-refund-case.v1).

v1.0.2: tie-break is explicit and deterministic - highest keyword-hit count, then the longest
matched keyword (more specific phrase wins), then alphabetical category - and the ranked
candidate list is recorded so the agent can confirm the right one with the customer."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:reason_classify"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True); ap.add_argument("--taxonomy", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.case, encoding="utf-8")); tax = json.load(open(a.taxonomy, encoding="utf-8"))
    if p.get("contract_version") != "rtl.returns-refund-case.v1":
        raise SystemExit(f"contract_version mismatch: {p.get('contract_version')!r}")
    text = p["return_request"]["reason_text"].lower()
    hits = []
    for cat, kws in tax.items():
        spans = []
        for k in kws:
            start = text.find(k)
            while start != -1:
                spans.append((start, start + len(k), k)); start = text.find(k, start + 1)
        if not spans:
            continue
        # merge overlapping spans so "looks different" + "different from the photos" count once
        spans.sort(); merged = []
        for st, en, k in spans:
            if merged and st < merged[-1][1]:
                merged[-1] = (merged[-1][0], max(en, merged[-1][1]), merged[-1][2] if len(merged[-1][2]) >= len(k) else k)
            else:
                merged.append((st, en, k))
        matched = sorted({k for _, _, k in merged})
        hits.append({"category": cat, "hits": len(merged), "longest_match": max(en - st for st, en, _ in merged), "matched_keywords": matched})
    hits.sort(key=lambda h: (-h["hits"], -h["longest_match"], h["category"]))
    if not hits:
        cat, conf = "unclassified", 0.4
    elif len(hits) == 1 or hits[0]["hits"] > hits[1]["hits"]:
        cat, conf = hits[0]["category"], 0.9
    else:
        cat, conf = hits[0]["category"], 0.7  # tie on hit count: deterministic pick, low confidence
    p["reason"] = {"category": cat, "confidence": conf, "source": ENGINE,
                   "candidates": [{"category": h["category"], "hits": h["hits"], "matched_keywords": h["matched_keywords"]} for h in hits],
                   "tie_break": "hits desc, longest matched keyword desc, category asc",
                   "citation": "reason-code taxonomy (config/reason-taxonomy.json)"}
    if conf < 0.75:
        alts = ", ".join(h["category"] for h in hits[1:]) or "none"
        p.setdefault("escalations", []).append(f"reason classification ambiguous ({cat}, conf {conf}; alternatives: {alts}) - agent confirms with customer")
    p.setdefault("provenance", {}).setdefault("engines", []).append("reason_classify/1.0.2")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"reason_classify: {cat} (conf {conf}) -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
