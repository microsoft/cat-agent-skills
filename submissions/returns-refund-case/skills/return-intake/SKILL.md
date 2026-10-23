---
name: return-intake
description: 'Structures a customer return request - item, order/receipt, reason as stated, condition, serials, customer history - into the rtl.returns-refund-case.v1 contract as case.json. Use when the user says "customer wants to return", "process this return", "start a return case", "log this return", "new return at the desk", or a return case begins. Do NOT use for eligibility or refund decisions - use eligibility-check instead; not for policy text - use policy-retrieve; not for the write-up or customer response - use case-packet.'
license: Proprietary
metadata: {version: "1.0.3", author: Microsoft Retail & CPG Skills, category: productivity}
---
# Return Intake
## Purpose
Assemble the case facts: request, order record, SKU attributes, customer return history. Entry hop of every return case.
## When to use
- Start of every return case ("customer wants to return", "start a return case", "log this return").
## When NOT to use
- Deciding eligibility, refund or red flags - eligibility-check owns the determination.
- Fetching policy clauses or windows - policy-retrieve.
- Classifying the reason code - reason-classify.
- Drafting the packet, customer response or manager exception request - case-packet.
## Inputs
Plugin assets ship inside this skill folder (synced from the plugin-root shared/ copy before packaging): `config/`, `contracts/`, `references/returns-rules.md`, `demo-data/` - paths below are relative to this skill folder.
The request as stated (verbatim reason text); order/receipt lookup export; SKU attributes; customer history extract. Schema: contracts/rtl.returns-refund-case.v1.json.
## Steps
1. Mint `case_id` as `RET-<YYYY>-<5-digit sequence>` (contract convention); never encode the order id or customer identity in it.
2. Capture `reason_text` verbatim - classification and the human exception path depend on the actual words.
3. Record `category`, `value`, `has_receipt`, `opened`, `worn`, `requested_on`, `unit_serial` as presented (unknown flags -> `null`, never guessed); attach `order` (with `order_date` and `sold_serial`) and `customer_history` when found, each with a `citation`.
4. Validate against the contract (required keys, `contract_version` const, `case_id` pattern); write `case.json`.
## Example
```
User: "Customer wants to return a $249 smart speaker, gift, no receipt; order ORD-544102 found via the giver's phone."
-> tool: order/receipt lookup export (ORD-544102, 2026-07-05, sold serial SN-KX88117)
-> tool: customer history extract (receiptless_returns_90d: 4)
-> write case.json: case_id RET-2026-08977, reason_text verbatim, has_receipt false, unit_serial SN-KX88231
Reply: "Case RET-2026-08977 recorded. Order and history attached; receipt not presented. No determination made."
```
## Output format
`case.json` - the entry hop: `{contract_version, case_id, return_request{...}, order?{...}, customer_history?{...}, escalations: []}`. No `reason`, `eligibility` or `fraud_signals` keys. Tell the user which records were found and which are missing.
## Grounding requirements
Every fact cites its record (order id, POS receipt, history extract). The story is recorded; it is not evidence.
## Guardrails
- Never fabricate a fact to complete the record; write `null` or leave the block absent and cite what was searched.
- No eligibility or fraud opinions here - record the serial mismatch or the return count as facts only.
- Never fabricate an order id, date or history value; if the lookup finds nothing, leave the block absent and record it in `escalations`.
- Never skip the history pull because the customer is friendly - it is part of every case.
- Draft-first: nothing here approves, refunds or declines anything.
## Escalation / uncertainty
If the order lookup tool or the history extract is unavailable or returns nothing: record the block as absent, add an `escalations` entry naming the missing record, and never fabricate a stand-in value.
No order found and no receipt: record it; the Govern step (eligibility-check) decides what that means. Ambiguous category: ask the user before writing.
