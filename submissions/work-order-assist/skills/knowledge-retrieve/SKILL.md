---
name: knowledge-retrieve
description: Retrieves the SOPs, OEM manuals, prior fixes and parts history relevant to a work order and attaches them to the mfg.work-order-assist.v1 contract. Use when the user says "find the SOP and manual", "pull prior fixes for <asset>", "get the parts history", "what did we do last time", or after wo-intake completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# Knowledge Retrieve

## Purpose
Enrich the work-order payload with grounded knowledge: the relevant SOP and OEM manual sections,
the asset's prior work orders (with the action taken, parts used and outcome), any prior fix notes
that recommend a change, and the parts catalog rows for the required parts.

## When to use
- After wo-intake, in every run.
- "Find the SOP and manual section" / "pull prior fixes and parts history for this asset".

## Inputs
- `wo-intake.json` (contract inputs from wo-intake).
- SOP (PDF/Markdown) and OEM manual excerpt (PDF).
- Work-order history export (CSV): date, asset, component, keywords, action, parts_used, outcome.
- Prior fix notes (Markdown/TXT): reliability notes that may recommend a superseding part.
- Parts catalog (CSV): part_no, on_hand, min_stock, superseded_by, lead_time, criticality.

## Steps
1. Filter the work-order history to this `asset_id` and issue; extract each prior WO into
   `history.prior_work_orders[]` with its `action_taken`, `parts_used[]`, and `outcome`.
2. Set `history.window_days` to the span covered.
3. Attach retrieved SOP/manual references and any `prior_fixes[]`, flagging a fix note that carries
   `recommended_change` and a `superseding_part`.
4. Attach the `parts_catalog[]` rows for the required parts (stock, supersession, lead time).
5. Write the enriched payload back onto the contract.

## Output
The contract payload with populated `history{}`, `retrieved{}` and `parts_catalog[]` — the input to
similar-work-rank.

## Grounding requirements
Every prior work order cites its CMMS record ID; every manual/SOP reference cites its section; every
fix note cites its note ID.

## Constraints
- Retrieval only — do not rank prior work or judge readiness here (engine/LLM split).
- Do not infer an outcome for a prior WO that its record does not state.
- Do not drop a fix note that contradicts the SOP; surfacing it is the point.

## Escalation / uncertainty
- If history or the catalog is unavailable, proceed on the SOP/manual alone and note it in
  `escalations[]`; do not block the run.
