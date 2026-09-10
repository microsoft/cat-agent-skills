---
name: supply-knowledge-retrieve
description: Retrieves the ERP/MRP supply position, supplier master, BOM/where-used and open orders relevant to a disruption and attaches them plus the supplier's delivery history to the mfg.supplier-disruption.v1 contract. Use when the user says "what does this part go into", "where is this used", "what's our on-hand and lead time", "is this single-source", "has this supplier been late before", or after disruption-intake completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Supply Chain
---

# Supply Knowledge Retrieve

## Purpose
Enrich the disruption payload with grounded supply context: the ERP/MRP position for the part
(on-hand, on-order, safety stock, lead time), the supplier master (single-source flag, approved
alternates, substitutes), the BOM/where-used mapping and the open production/sales orders that
consume the part, and the supplier's on-time delivery history (to reveal a chronic pattern).

## When to use
- After disruption-intake, in every run.
- "Where is this part used and what's our on-hand?" / "has this supplier been late before?".

## Inputs
- `disruption-intake.json` (contract inputs from disruption-intake).
- ERP inventory/MRP export (CSV): part, on_hand, on_order, safety_stock, lead_time_days.
- Supplier master (CSV): single_source, alternate suppliers + lead times, approved substitutes.
- BOM/where-used (CSV): parent product, component, per-unit qty, line.
- Open orders (CSV): order_id, type (production/sales), product, finished_qty, need_by, customer.
- Supplier on-time history (CSV): prior POs, promised vs actual, days late.

## Steps
1. Populate `supply{}`: `on_hand`, `on_order` (the delayed PO qty), `safety_stock`, `lead_time_days`,
   `single_source`, `substitutes[]` (with `approved` + `available_qty`), `alternates[]` (with
   `lead_time_days` + `qualified`).
2. Explode the BOM/where-used and join to open orders into `retrieved.open_orders[]`: each with
   `order_type`, `product`, `line`, `finished_qty`, `per_unit`, `need_by`, `customer`, `high_runner`.
3. Populate `history{}`: `window_days`, `late_count`, `on_time_pct`, `prior_shipments[]`, and set
   `chronic_pattern = true` when the supplier is repeatedly late (a systemic signal).
4. Attach supplier master + sourcing standards into `retrieved{}`, each with a citation.

## Output
The contract payload with populated `supply{}`, `retrieved{}` and `history{}` — the input to
shortage-impact-map.

## Grounding requirements
Every open order cites its order record; every supply figure cites the ERP/master export; every prior
shipment cites its PO row.

## Constraints
- Retrieval only — do not map impact or choose a mitigation here (engine/LLM split).
- Do not infer an approved substitute or a qualified alternate the master does not state.
- Do not drop an open order (especially a customer sales order) that a shortage would hit; surfacing
  it is the point.

## Escalation / uncertainty
- If the where-used, open-order or supplier-master data is unavailable, proceed on the PO and
  on-hand alone and note it in `escalations[]`; do not block the run.
