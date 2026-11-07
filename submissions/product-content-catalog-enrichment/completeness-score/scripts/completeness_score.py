#!/usr/bin/env python3
"""completeness_score - deterministic channel completeness (rtl.product-content-enrichment.v1, #3.1).
Required-fields-only arithmetic per SKU against config required_by_channel; missing fields named.
v1.0.2: --channel override (what-if scoring without editing the payload), graceful failure on an
unknown channel (exit 2, known channels listed), records with an invalid GTIN flagged record_blocked,
and the customer completeness floor (config completeness_floor_pct) raises a steward escalation (#3.2)."""
import argparse, json, sys
from datetime import datetime, timezone
ENGINE = "engine:completeness_score"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized", required=True); ap.add_argument("--taxonomy", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--channel", help="Score against this channel instead of the payload's channel (what-if); the payload is not modified")
    a = ap.parse_args()
    p = json.load(open(a.normalized, encoding="utf-8")); tax = json.load(open(a.taxonomy, encoding="utf-8"))
    assert p["contract_version"] == "rtl.product-content-enrichment.v1"
    channel = a.channel or p.get("channel")
    known = tax.get("required_by_channel", {})
    if channel not in known:
        print(f"completeness_score: unknown channel {channel!r} - no requirements configured. "
              f"Known channels: {sorted(known)}. Add it to config/taxonomy-map.json required_by_channel or pass --channel.", file=sys.stderr)
        return 2
    req = known[channel]
    floors = tax.get("completeness_floor_pct", {})
    floor = floors.get(channel, floors.get("default"))
    esc = list(p.get("escalations", [])); rows = []
    for r in p["normalized"]:
        missing = [f for f in req if f not in r["attributes"] or r["attributes"][f] in (None, "")]
        row = {"gtin": r["gtin"], "channel": channel,
               "completeness_pct": round(100 * (len(req) - len(missing)) / len(req), 1),
               "missing_fields": missing, "source": ENGINE,
               "citation": f"channel '{channel}' requirements (config/taxonomy-map.json, #3.1)"}
        if not r.get("gtin_valid", True):
            row["record_blocked"] = True  # scored for the gap report only; identity block stands (#1.1)
        rows.append(row)
    avg = round(sum(r["completeness_pct"] for r in rows) / len(rows), 1) if rows else 0.0
    summary = {"channel": channel, "sku_count": len(rows), "average_pct": avg, "floor_pct": floor,
               "below_floor": (floor is not None and avg < floor), "source": ENGINE,
               "citation": "config/taxonomy-map.json completeness_floor_pct (#3.2)"}
    if summary["below_floor"]:
        esc.append(f"Batch {p.get('batch_id', '?')}: completeness average {avg}% is below the {channel} floor of {floor}% - "
                   f"steward review before drafting (enrichment-rules.md #3.2)")
    p["completeness"] = rows; p["completeness_summary"] = summary; p["escalations"] = esc
    p.setdefault("provenance", {}).setdefault("engines", []).append("completeness_score/1.0.3")
    p["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(p, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"completeness_score: {len(rows)} SKUs, channel={channel}, avg={avg}%"
          f"{' BELOW floor ' + str(floor) + '%' if summary['below_floor'] else ''} -> {a.out}")
    return 0


if __name__ == "__main__": sys.exit(main())
