---
name: answer-draft
description: Drafts the cited answer for the associate - or the escalation when the question is out of scope or below confidence. Use to close every assist run.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Answer Draft
## Purpose
Terminal artifact: a floor-ready answer with the source shown, or an escalation record.
## When to use
End of every assist run.
## Inputs
Full contract payload.
## Steps
1. Validate against the contract; escalations lead.
2. Draft in floor language: the determination, the clause/promo citation visible to the associate, the comparison card if present, and what the associate can and cannot do next (manager actions flagged).
3. Out-of-scope or low-confidence -> escalation draft to the shift lead instead of an answer.
## Output
Answer or escalation draft - terminal artifact.
## Grounding requirements
No sentence without a citation available on request (#1.1).
## Constraints
- Answers and drafts only: never override a price, authorise a refund, reserve inventory or change a schedule (plugin boundary).
- Nothing in the answer that is not in the contract payload.
## Escalation / uncertainty
Anything the associate cannot resolve at their role level is drafted as a manager escalation.
