---
name: routing-notify
description: Routes a classified incident to the right investigator, builds the owner-notification list, and starts any OSHA regulatory clock, deterministically. Use when the user says "who investigates this", "who do we notify", "route this incident", "start the OSHA clock", "who owns this", or after severity-recordability completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: EHS
---

# Routing & Notify

## Purpose
Deterministically assign the investigator by severity (escalated one level on a repeat pattern),
build the cumulative owner-notification list, start any OSHA reportability clock with a computed
due-by, and raise the governance escalations — then finalize the recommended next-best action.

## When to use
- After severity-recordability, in every run.
- "Who investigates this and who do we notify?" / "start the OSHA clock" / "route this incident".

## Inputs
- The contract payload with `classification{}` (severity, recordable, reportable + deadline) and
  `history.repeat_pattern`, plus `occurred_at` (contract `mfg.safety-incident-assist.v1`).

## Steps
1. Validate the payload against the contract.
2. Run `scripts/routing_notify.py --classification classification.json --out incident-packet.json`.
3. Do not restate or recompute any assignment or clock in prose; quote the engine output verbatim.
4. Emit the `{routing}` contract payload and the finalized `next_best_action`.

## Output
Contract `mfg.safety-incident-assist.v1` with a populated `routing{}` object (investigator,
notifications[], regulatory_clocks[], confidence, source=engine:routing_notify, citation) plus the
finalized `next_best_action` and appended `escalations[]` — the `{routing}` hop.

## Grounding requirements
The investigator assignment cites `references/routing-matrix.md` #1; each notification cites #2; a
regulatory clock cites #3; escalations cite #4.

## Constraints
- All routing/notification/clock logic happens in the engine. The model must never assign or notify
  itself.
- Draft-first: the plugin drafts the routing and notifications; it never auto-sends a notification
  or files an OSHA report. A human owner confirms (audit trail intact).
- Never drop or suppress a regulatory clock or a reportable escalation because of time pressure.

## Escalation / uncertainty
- A reportable event, a recordable case, a repeat pattern, or low classification confidence: the
  engine adds to `escalations[]`; surface them so the clock and the sign-offs are visible
  (routing-matrix.md #4).
