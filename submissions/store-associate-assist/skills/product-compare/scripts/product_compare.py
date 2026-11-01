#!/usr/bin/env python3
"""product_compare - deterministic PIM attribute comparison (rtl.store-associate-assist.v1).
Differences from the PIM extract only; missing shown as missing (assist-rules.md #3.1)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:product_compare"
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resolved", required=True); ap.add_argument("--pim", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.resolved, encoding="utf-8")); pim = json.load(open(a.pim, encoding="utf-8"))
    assert p["contract_version"] == "rtl.store-associate-assist.v1"
    skus = p["question"].get("compare_skus", [])
    if len(skus) == 2 and all(s in pim for s in skus):
        A, B = pim[skus[0]], pim[skus[1]]
        keys = sorted(set(A["attributes"]) | set(B["attributes"]))
        rows = [{"attribute": k, skus[0]: A["attributes"].get(k, "MISSING"), skus[1]: B["attributes"].get(k, "MISSING"),
                 "differs": A["attributes"].get(k) != B["attributes"].get(k)} for k in keys]
        p["product_comparison"] = {"skus": skus, "names": [A["name"], B["name"]], "prices": [A["price"], B["price"]],
            "rows": rows, "differences": sum(1 for r in rows if r["differs"]),
            "source": ENGINE, "citation": f"PIM extract {skus[0]}, {skus[1]} (assist-rules.md #3.1)"}
    else:
        p["product_comparison"] = {"skus": skus, "rows": [], "differences": 0, "source": ENGINE,
                                   "citation": "no comparison requested or SKU missing from PIM"}
        if skus: p.setdefault("escalations", []).append("comparison SKU missing from PIM extract - shown as missing, not guessed (#3.1)")
    p.setdefault("provenance", {}).setdefault("engines", []).append("product_compare/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"product_compare: {len(p['product_comparison']['rows'])} attributes, {p['product_comparison']['differences']} differ -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
