---
name: case-packet
description: 'Drafts the return case packet - determination, recommendation, evidence list, fraud signals, customer response draft, manager exception request - from the governed contract payload using the packet template. Use to close every return case: "build the case packet", "write up the return", "draft the customer response", "draft the manager exception request", "close the return case". Do NOT use to start a case - use return-intake instead; not for eligibility or red flags - use eligibility-check; not for incident or safety write-ups.'
license: Proprietary
metadata: {version: "1.0.3", author: Microsoft Retail & CPG Skills, category: writing}
---
# Case Packet
## Purpose
Terminal artifact: the complete case packet on first touch - the retail equivalent of the NCR.
## When to use
- End of every return case, once `governed.json` exists; or when asked for the customer response or manager exception draft.
## When NOT to use
- A case that has not been through eligibility-check (no `eligibility` block) - run the chain first; do not decide here.
- Starting a case from raw desk facts - return-intake.
- Policy questions - policy-retrieve. Non-return write-ups (incidents, safety, HR) - other plugins.
## Inputs
Plugin assets ship inside this skill folder (synced from the plugin-root shared/ copy before packaging): `config/`, `contracts/`, `references/returns-rules.md`, `demo-data/` - paths below are relative to this skill folder.
`governed.json` (full payload) + references/case-packet-template.md + references/returns-rules.md.
## Steps
1. Validate `governed.json` against the contract; escalations and fraud-signal holds lead the packet.
2. Fill references/case-packet-template.md section by section: cited case facts, reason code (+ ambiguity note), determination + clause, recommendation, missing-evidence list, factual fraud signals, customer response draft in the template's tone, and the manager exception-request draft only when the customer asked for one (#5.1).
3. Every `<slot>` is filled from the payload, policy text or config, or written as `not on record`. No angle-bracket or square-bracket placeholders remain.
4. Mark DRAFT with the sign-off block - a human authorises any refund, exchange or decline.
## Example
```
User: "Build the case packet for RET-2026-08977; the customer asked for a goodwill exception."
-> read governed.json (ineligible RET-2.1, hold_for_review, 3 signals) + references/case-packet-template.md
-> fill sections 0-9; section 8 (manager exception request) included because the customer asked
-> customer draft: policy outcome + clause + next step; no mention of signals; no timings
Reply: "CASE-RET-2026-08977.md drafted (DRAFT). Routing: hold_for_review -> Asset Protection. Determination: ineligible, RET-2.1.
        Customer response and manager exception request drafted; decision block left for the manager."
```
## Output format
`CASE-<case_id>.md` following the template's numbered sections 0-9. In chat: routing line, determination + clause, recommendation, signal count, and the two drafts' status.
## Grounding requirements
Every claim cites order, receipt, history, clause or config. Customer-facing text states only what policy text and the record support - no processing times, refund timings or goodwill promises unless quoted from policy text (#5.0).
## Guardrails
- Never fabricate facts, timings, approvals or review outcomes; every claim cites the payload, policy text or config.
- Never authorise a refund, release funds, adjudicate fraud, dispose inventory, book a carrier, or send the response to the customer (plugin boundary).
- Signals appear as signals in the internal sections only; the customer response never mentions suspicion, fraud or asset protection.
- Never state that asset protection or a manager has reviewed or cleared anything unless the payload records it.
- Never fill the manager's decision block.
## Escalation / uncertainty
If `governed.json` lacks an `eligibility` block, stop and route the case back through eligibility-check - never decide here. If a template slot has no source, write `not on record`; never fabricate a value to fill it.
hold_for_review packets route to asset protection with the signal citations attached; missing payload fields are written as `not on record` and listed under Missing evidence.
