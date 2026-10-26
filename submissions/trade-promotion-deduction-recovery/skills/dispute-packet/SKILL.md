---
name: dispute-packet
description: 'Drafts the dispute packet and the post-event promotion brief from the governed payload. Use to close every deduction case: "draft the dispute", "build the packet for the retailer".'
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Revenue Growth Management}
---
# Dispute Packet
## Purpose
Terminal artifacts: evidence-backed dispute packet + post-event brief (on the fixed baseline when in scope).
## When to use
End of every deduction case with disputable amounts.
## Inputs
governed.json (full payload).
## Steps
1. Validate against the contract; partial/unsupported verdicts lead with their calculations.
2. Packet per disputable claim: claim facts, signed term quoted, entitled-vs-claimed arithmetic, backup gaps, requested credit; internal summary with the recovery total.
3. Mark DRAFT - the deduction analyst files the dispute; nothing is posted or written off by the plugin.
## Output
DISPUTE-<deduction_id>.md + post-event brief - terminal artifacts.
## Grounding requirements
Every number traces to the engine calculation; every term is quoted with its id.
## Constraints
- Draft-first; the packet requests, the retailer and analyst resolve.
- A skipped lift section states the scoping rule, never fabricates a baseline (#3.2).
## Escalation / uncertainty
Disputes above the analyst's threshold route to the trade manager with the packet.
