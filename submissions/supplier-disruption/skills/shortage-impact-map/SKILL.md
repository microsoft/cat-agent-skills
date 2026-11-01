---
name: shortage-impact-map
description: Maps a part shortage through BOM/where-used to the affected products, production lines and open orders, with the quantity and date at risk per order, deterministically. Use when the user says "what does this shortage affect", "which lines and orders are hit", "when does this bite", "map the impact", "what's at risk", or after supply-knowledge-retrieve completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Supply Chain
---

# Shortage Impact Map

## Purpose
Deterministically explode the shortage: net the short part's usable on-hand and the incoming (late)
PO against every open order that consumes it, and produce a per-order impact row (product, line,
order, need-by, quantity at risk, status) plus a rolled-up impact summary (worst severity + the
first-impact date). This is the mapping the whole packet turns on.

## When to use
- After supply-knowledge-retrieve, in every run.
- "Which lines and orders does this shortage hit, and when does it bite?".

## Inputs
- The contract payload with `supply{}` (on_hand, on_order, safety_stock), `promised_date`,
  `revised_date` and `retrieved.open_orders[]` (contract `mfg.supplier-disruption.v1`).

## Steps
1. Validate the payload against the contract.
2. Run `scripts/shortage_impact_map.py --intake disruption-intake.json --out impact-map.json`.
3. Do not restate or re-derive the netting in prose; quote the engine output verbatim.
4. Emit the `{impact_map, impact_summary}` contract payload and the preliminary `next_best_action`.

## Output
Contract `mfg.supplier-disruption.v1` with a populated `impact_map[]` (per-order status + qty at risk)
and `impact_summary{}` (worst_severity, first_impact_date, affected products/orders, total qty at
risk, below_safety_stock, confidence, source=engine:shortage_impact_map) — the `{impact}` hop.

## Grounding requirements
The netting and per-order status cite `references/impact-mapping-rules.md` #3-#4; the first-impact
date cites #5; the summary cites #6.

## Constraints
- All mapping logic happens in the engine. The model must never decide the impact or the dates itself.
- The incoming (late) PO only covers orders whose need-by is on/after the revised date
  (impact-mapping-rules.md #2) — do not credit it earlier.
- Never drop a `late_shipment` (customer order at risk) to make the picture look better — it is the
  reason a case is critical.

## Escalation / uncertainty
- Incomplete MRP position (missing open orders, on-hand or revised date) or a below-safety-stock
  projection: the engine adds to `escalations[]`; surface it and confirm the netting in the ERP
  before a mitigation is committed (impact-mapping-rules.md #7).
