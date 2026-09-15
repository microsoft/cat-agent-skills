---
name: disruption-writeup
description: Drafts the supplier follow-up and the internal escalation brief from the assembled contract payload, with the impact and mitigation cited to the ERP/MRP, supplier master and rules. Use when the user says "draft the supplier email", "write the escalation brief", "draft the follow-up", "give me the escalation", "write it up", or after mitigation-recommend completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Supply Chain
---

# Disruption Write-up

## Purpose
Produce the human-readable artifacts: a **supplier follow-up** (chasing the late PO / requesting the
expedite / confirming the revised date) and an **internal escalation brief** (impact + mitigation +
owners + decision needed), rendered from `templates/disruption-writeup-template.md` and populated only
from the contract payload — the disruption context, the impact summary and map, the mitigation, the
owner notifications, the escalations and the recommended next-best action.

## When to use
- After mitigation-recommend, to close the loop.
- "Draft the supplier follow-up" / "write the escalation brief".

## Inputs
- `disruption-packet.json` (contract `mfg.supplier-disruption.v1`, the `{mitigation}` hop with
  `impact_map[]`, `impact_summary{}`, `mitigation{}`, `notifications[]`, `next_best_action`,
  `escalations[]`).

## Steps
1. Validate input against the contract.
2. Fill `templates/disruption-writeup-template.md`: disruption identification, the impact summary +
   per-order impact map table, the mitigation block, the owner-notification list, a visible "Open
   items / escalations" block, the recommended next-best action, the drafted supplier follow-up
   (`references/supplier-comms-standards.md` #1-#2) and the drafted internal escalation brief (#3).
3. Render to the requested format (markdown; DOCX/PDF via the platform document component).
4. Choose the audience voice: buyer, production planner, or materials manager.
5. Mark the write-up DRAFT — pending buyer/planner review and sign-off.

## Output
`DISR-<disruption_id>-writeup.md` (or .docx) — the terminal artifact of the contract flow.

## Grounding requirements
The impact traces to `engine:shortage_impact_map`; the mitigation and escalations trace to
`engine:mitigation_recommend`; the drafting standards cite `supplier-comms-standards.md`.

## Constraints
- Draft-first: no PO placed/expedited, no ERP or schedule write, no email sent, and no supplier
  commitment in v1. The write-up is a recommendation, not an executed action.
- Nothing appears in the write-up that is not present in the contract payload.
- A customer-order (late_shipment) risk and its first-impact date must never be softened or hidden in
  the draft.

## Escalation / uncertainty
- If `escalations[]` is non-empty, the write-up must surface them in a visible "Open items /
  escalations" block above the recommended action — especially a customer-order risk, a single-source
  second-source need, or a chronic-supplier review.
