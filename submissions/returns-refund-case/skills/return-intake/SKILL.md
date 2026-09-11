---
name: return-intake
description: Structures a return request - item, order/receipt, reason as stated, condition, serials, customer history - into the rtl.returns-refund-case.v1 contract. Use when the user says "customer wants to return", "process this return", "can they get a refund", or a return case begins.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Return Intake
## Purpose
Assemble the case facts: request, order record, SKU attributes, customer return history.
## When to use
Start of every return case.
## Inputs
The request as stated (verbatim reason text); order/receipt lookup export; SKU attributes; customer history extract. Emits the entry hop (schema in contracts/).
## Steps
1. Capture reason_text verbatim - classification and the human exception path both depend on the actual words.
2. Record category, value, has_receipt, opened/worn flags, unit serial as presented; attach order (with sold serial) and customer_history when found.
3. Validate against the contract; write case.json.
## Output
case.json - the entry hop.
## Grounding requirements
Every fact cites its record (order id, POS receipt, history extract). The story is recorded; it is not evidence.
## Constraints
- No eligibility or fraud opinions here.
- Never skip the history pull because the customer is friendly - it is part of every case.
## Escalation / uncertainty
No order found and no receipt: record it; the Govern step decides what that means.
