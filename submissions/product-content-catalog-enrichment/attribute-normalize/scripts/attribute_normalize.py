#!/usr/bin/env python3
"""attribute_normalize - deterministic taxonomy mapping + GS1 GTIN validation + UOM conversion
(rtl.product-content-enrichment.v1). Rules mirror references/enrichment-rules.md:
  #1.1 GS1 check digit - an invalid GTIN blocks the record, never corrected;
  #2.1 mapping-table-only - unmapped supplier fields are listed, never guessed;
  #2.2 UOM conversions are deterministic and SHOWN (v1.0.2: implemented; a mapping entry may be
       {"target": "net_weight_g", "uom": "oz"} and the conversion is recorded per attribute)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:attribute_normalize"
# factor to the canonical unit of the target field (#2.2)
UOM_TO_CANON = {"oz": ("g", 28.349523125), "lb": ("g", 453.59237), "kg": ("g", 1000.0), "g": ("g", 1.0),
                "fl oz": ("ml", 29.5735295625), "l": ("ml", 1000.0), "ml": ("ml", 1.0)}


def gtin_valid(g):
    d = [int(c) for c in str(g) if c.isdigit()]
    if len(d) not in (8, 12, 13, 14) or len(d) != len(str(g).strip()): return False
    check = d[-1]; body = d[:-1][::-1]
    s = sum(v * (3 if i % 2 == 0 else 1) for i, v in enumerate(body))
    return (10 - s % 10) % 10 == check   # GS1 check digit (enrichment-rules.md #1.1)


def to_number(v):
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True); ap.add_argument("--taxonomy", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = json.load(open(a.batch, encoding="utf-8")); tax = json.load(open(a.taxonomy, encoding="utf-8"))
    assert p["contract_version"] == "rtl.product-content-enrichment.v1"
    esc = list(p.get("escalations", [])); out = []
    for sku in p["skus"]:
        attrs, unmapped, conversions = {}, [], []
        for k, v in sku["supplier_fields"].items():
            entry = tax["mapping"].get(k)
            if entry is None:
                unmapped.append(k); continue
            if isinstance(entry, str):
                attrs[entry] = v; continue
            tgt, uom = entry["target"], entry.get("uom")
            if uom and uom in UOM_TO_CANON:
                canon, factor = UOM_TO_CANON[uom]; num = to_number(v)
                if num is None:
                    unmapped.append(k)
                    esc.append(f"GTIN {sku['gtin']}: '{k}' = {v!r} is not numeric - UOM conversion refused, field listed for the steward (#2.2)")
                    continue
                conv = round(num * factor, 1)
                attrs[tgt] = conv
                conversions.append({"field": k, "target": tgt, "from": f"{num:g} {uom}", "to": f"{conv:g} {canon}",
                                    "factor": factor, "rule": "#2.2"})
            else:
                attrs[tgt] = v
        ok = gtin_valid(sku["gtin"])
        if not ok: esc.append(f"GTIN {sku['gtin']}: GS1 check digit INVALID - record blocked (enrichment-rules.md #1.1)")
        if unmapped: esc.append(f"GTIN {sku['gtin']}: unmapped supplier fields {unmapped} - listed, not guessed (#2.1)")
        rec = {"gtin": sku["gtin"], "gtin_valid": ok, "attributes": attrs, "unmapped": unmapped,
               "source": ENGINE, "citation": f"supplier sheet row {sku.get('row', '?')}; taxonomy map"}
        if conversions: rec["conversions"] = conversions
        out.append(rec)
    p["normalized"] = out; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("attribute_normalize/1.0.3")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"attribute_normalize: {len(out)} SKUs, invalid_gtin={sum(1 for r in out if not r['gtin_valid'])}, "
          f"unmapped={sum(len(r['unmapped']) for r in out)}, conversions={sum(len(r.get('conversions', [])) for r in out)} -> {a.out}")
    return 0


if __name__ == "__main__": sys.exit(main())
