---
name: resolution-draft
description: Drafts the customer-facing resolution in the right channel and tone from the assembled context and approved sources. Use to close resolvable runs - "draft the reply", "answer the customer".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Resolution Draft
## Purpose
Terminal artifact for resolvable runs: a grounded, channel-appropriate response.
## When to use
End of runs where the path is answer_from_records or instant_resolution.
## Inputs
Full payload with approved sources.
## Steps
1. Validate against the contract; escalations present means this is NOT the terminal skill - go to handoff-packet.
2. Draft: acknowledge, answer with the record facts (order status, dates, next step), citation available on request, next-step clarity (e.g., investigation clock for DNR with empathy, per #2.2).
3. Mark DRAFT for agent send; the agent owns the send.
## Output
Response draft - terminal artifact.
## Grounding requirements
Every fact cites order/carrier/loyalty extract or article.
## Constraints
- Never promise a refund, credit or exception the path does not support (#3.1); never dispute the customer's account (#2.2).
## Escalation / uncertainty
Anything below confidence or contradicted -> handoff-packet instead.
