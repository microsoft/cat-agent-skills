#!/usr/bin/env python3
"""attribute_normalize - deterministic taxonomy mapping + GS1 GTIN validation
(rtl.product-content-enrichment.v1). Rules mirror references/enrichment-rules.md."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:attribute_normalize"
def gtin_valid(g):
    d = [int(c) for c in g if c.isdigit()]
    if len(d) not in (8, 12, 13, 14): return False
    check = d[-1]; body = d[:-1][::-1]
    s = sum(v * (3 if i % 2 == 0 else 1) for i, v in enumerate(body))
    return (10 - s % 10) % 10 == check   # GS1 check digit (enrichment-rules.md #1.1)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True); ap.add_argument("--taxonomy", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.batch, encoding="utf-8")); tax = json.load(open(a.taxonomy, encoding="utf-8"))
    assert p["contract_version"] == "rtl.product-content-enrichment.v1"
    esc = list(p.get("escalations", [])); out = []
    for sku in p["skus"]:
        attrs, unmapped = {}, []
        for k, v in sku["supplier_fields"].items():
            tgt = tax["mapping"].get(k)
            if tgt is None: unmapped.append(k)
            else: attrs[tgt] = v
        ok = gtin_valid(sku["gtin"])
        if not ok: esc.append(f"GTIN {sku['gtin']}: GS1 check digit INVALID - record blocked (enrichment-rules.md #1.1)")
        if unmapped: esc.append(f"GTIN {sku['gtin']}: unmapped supplier fields {unmapped} - listed, not guessed (#2.1)")
        out.append({"gtin": sku["gtin"], "gtin_valid": ok, "attributes": attrs, "unmapped": unmapped,
                    "source": ENGINE, "citation": f"supplier sheet row {sku.get('row', '?')}; taxonomy map"})
    p["normalized"] = out; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("attribute_normalize/1.0")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"attribute_normalize: {len(out)} SKUs, invalid_gtin={sum(1 for r in out if not r['gtin_valid'])} -> {a.out}")
    return 0
if __name__ == "__main__": sys.exit(main())
