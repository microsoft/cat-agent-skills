---
name: disruption-intake
description: Picks up a supply disruption from a PO record, shipment feed, supplier email or portal notice and pulls it into the mfg.supplier-disruption.v1 contract inputs. Use when the user says "a PO is late", "our supplier is delayed", "we're short on a part", "process this supplier notice", "shipment is going to slip", or when a Supplier Disruption Agent run begins.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Supply Chain
---

# Disruption Intake

## Purpose
Turn a supply disruption arriving from any channel — a PO/ERP record, a shipment (ASN) feed, a
supplier email, or a portal notice — into structured contract inputs: the disruption identity, the
short/delayed **part**, the **supplier and PO**, the **promised vs revised date**, the **short
quantity**, the reason, and the trigger channel. This is the entry payload every later skill builds on.

## When to use
- "A PO is late" / "our supplier is delayed" / "we're short on a part" / "process this supplier notice".
- A disruption signal arrives by PO record, shipment feed, supplier email or portal notice.
- Start of any Supplier Disruption Agent run.

## Inputs
- The disruption signal in any channel: PO/ERP record (CSV/JSON), shipment/ASN feed (CSV), supplier
  email (TXT), or portal notice (TXT).
- Emits inputs for contract `mfg.supplier-disruption.v1`.

## Steps
1. Identify the trigger channel and set `trigger_channel` (po_record | shipment_feed | supplier_email
   | portal_notice) and `disruption_type` (late_po | shipment_delay | shortage | supplier_notice).
2. Extract the anchor into `supplier`, `po_number`, `supplier_or_po`, and the short/delayed `part{}`
   (`part_no`, `description`, `uom`).
3. Capture `promised_date`, `revised_date`, `short_qty`, `reason` and `reported_at`. When the
   supplier text downplays the delay but a feed/portal shows a worse date, record **the worse,
   evidenced date** — never soften a date the data does not support.
4. Write the factual account into `description`.
5. Produce `disruption-intake.json` with `contract_version`, `disruption_id`, `supplier_or_po`, the
   fields above, and empty `supply{}`, `retrieved{}`, `history{}` for the retrieval skill to fill.

## Output
`disruption-intake.json` conforming to the contract inputs — the entry payload of the flow.

## Grounding requirements
Every extracted fact cites its source (PO row, ASN line, email line, or portal notice). The revised
date cites the feed/portal record, not just the supplier's prose.

## Constraints
- Do not map impact or choose a mitigation here — that is the two engines' job (engine/LLM split).
- Record the worst evidenced delivery date; do not accept a supplier's "minor slip" over a feed that
  shows a later date. An ambiguous date is an escalation, not a guess.
- Never invent a part, quantity or date the source does not state.

## Escalation / uncertainty
- Revised date, short quantity or affected part unclear, or the supplier text conflicts with the
  feed/portal: record it in the contract `escalations[]` and flag for confirmation; do not fabricate a
  value.
