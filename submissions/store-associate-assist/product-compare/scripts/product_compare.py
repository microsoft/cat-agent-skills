#!/usr/bin/env python3
"""product_compare - deterministic PIM attribute comparison (rtl.store-associate-assist.v1).
Differences from the PIM extract only; missing shown as missing (assist-rules.md #3.1).

v1.0.2 changes
- One representation of "missing": an attribute that is absent from a SKU OR recorded as null renders as
  the string MISSING, and `differs` is computed on the SAME rendered values (absent vs null == not different).
- Attributes the associate asked about (question.compare_attributes) that neither SKU carries are surfaced
  as MISSING / MISSING rows and listed in `missing_from_pim`, with a PIM-steward escalation.
- No `assert`: contract checks fail with an explicit message (exit 2).
- compare_skus with != 2 entries, or a SKU absent from the PIM, is reported by cause.
"""
import argparse, json, sys
from datetime import datetime, timezone

ENGINE = "engine:product_compare"
ENGINE_VERSION = "product_compare/1.0.2"
CONTRACT = "rtl.store-associate-assist.v1"
MISSING = "MISSING"


def fail(msg):
    print(f"product_compare: {msg}", file=sys.stderr)
    sys.exit(2)


def rendered(attrs, key):
    """Absent key and explicit null both render as MISSING (#3.1)."""
    v = attrs.get(key)
    return MISSING if v is None else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resolved", required=True); ap.add_argument("--pim", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.resolved, encoding="utf-8")); pim = json.load(open(a.pim, encoding="utf-8"))
    if p.get("contract_version") != CONTRACT:
        fail(f"contract_version must be '{CONTRACT}' (got {p.get('contract_version')!r})")
    q = p.get("question") or {}
    skus = q.get("compare_skus") or []
    requested = q.get("compare_attributes") or []
    if not isinstance(skus, list) or not isinstance(requested, list):
        fail("question.compare_skus and question.compare_attributes must be arrays")
    esc = p.setdefault("escalations", [])
    absent = [s for s in skus if s not in pim]

    if len(skus) == 2 and not absent:
        A, B = pim[skus[0]], pim[skus[1]]
        keys = sorted(set(A["attributes"]) | set(B["attributes"]) | set(requested))
        rows = []
        for k in keys:
            va, vb = rendered(A["attributes"], k), rendered(B["attributes"], k)
            rows.append({"attribute": k, skus[0]: va, skus[1]: vb, "differs": va != vb})
        missing_both = [k for k in keys if rendered(A["attributes"], k) == MISSING and rendered(B["attributes"], k) == MISSING]
        p["product_comparison"] = {"skus": skus, "names": [A["name"], B["name"]], "prices": [A["price"], B["price"]],
            "rows": rows, "differences": sum(1 for r in rows if r["differs"]),
            "missing_from_pim": missing_both,
            "source": ENGINE, "citation": f"PIM extract {skus[0]}, {skus[1]} (assist-rules.md #3.1)"}
        if missing_both:
            esc.append(f"attributes not in PIM extract for either SKU: {missing_both} - shown as MISSING, not guessed; PIM steward to add (#3.1)")
    else:
        if not skus:
            reason = "no comparison requested"
        elif len(skus) != 2:
            reason = f"comparison needs exactly 2 SKUs, got {len(skus)}"
        else:
            reason = f"SKU(s) missing from PIM extract: {absent}"
        p["product_comparison"] = {"skus": skus, "rows": [], "differences": 0, "missing_from_pim": [],
                                   "source": ENGINE, "citation": reason}
        if skus and absent:
            esc.append(f"comparison SKU missing from PIM extract {absent} - shown as missing, not guessed; PIM steward escalation (#3.1)")
        elif skus and len(skus) != 2:
            esc.append(f"{reason} - ask the associate which two products to compare")
    p.setdefault("provenance", {}).setdefault("engines", []).append(ENGINE_VERSION)
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    pc = p["product_comparison"]
    print(f"product_compare: {len(pc['rows'])} attributes, {pc['differences']} differ, {len(pc['missing_from_pim'])} missing from PIM -> {a.out}")
    return 0


if __name__ == "__main__": sys.exit(main())
