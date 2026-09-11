---
name: response-draft
description: Drafts the customer confirmation or clarification message and the internal entry note from the routed payload. Use to close every order run - "draft the reply to the customer", "write up the order status".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Commerce}
---
# Response Draft
## Purpose
Terminal artifacts: customer response (confirmations needed, in their language) + internal note (validated order file or exception summary).
## When to use
End of every order run.
## Inputs
routed.json (full payload).
## Steps
1. Validate against the contract; exceptions lead the internal note.
2. Clean order: prepared order file + confirmation draft. Exceptions: clarification draft asking exactly the open questions (product intent, UOM, price basis) - one message, all questions.
3. Mark DRAFT - entry/release is human at L0-L2 (#5.1).
## Output
Response draft + order file/exception summary - terminal artifacts.
## Grounding requirements
Every question cites its exception; the order file cites the masters.
## Constraints
- Never claim the order is entered; never ship a guessed line.
## Escalation / uncertainty
Customer replies changing lines -> the run restarts at validation, not at entry.
