---
name: question-intake
description: Takes an associate's floor question with store, role and department context into the rtl.store-associate-assist.v1 contract. Use when an associate asks "can a customer return this", "do we price match", "is this on promo", "which of these two should I recommend", or any store policy, product or promotion question.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Question Intake
## Purpose
Structure the question with the context that changes the answer: store, cluster, department, role, date, SKU(s).
## When to use
Start of every assist run - any policy/product/promotion question from the floor.
## Inputs
The question as asked (chat/voice transcript); store profile (id, format, cluster); asking role. Emits the entry hop of rtl.store-associate-assist.v1 (schema in contracts/).
## Steps
1. Capture the question verbatim; extract topic hints, SKU/GTIN(s) if named, compare list if two products.
2. Attach store_context (store id, cluster, department) and asked_on date - promo eligibility depends on all three.
3. Validate against the contract; write question.json.
## Output
question.json - the entry hop.
## Grounding requirements
The question text stays verbatim; store context cites the store master.
## Constraints
- No answering here; resolution belongs to policy-retrieve.
- Never guess a GTIN - ask the associate to scan if ambiguous.
## Escalation / uncertainty
Missing store context blocks promo checks - ask for the store id.
