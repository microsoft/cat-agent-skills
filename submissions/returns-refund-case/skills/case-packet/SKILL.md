---
name: case-packet
description: 'Drafts the return case packet - determination, recommendation, evidence list, fraud signals, customer response draft - from the contract payload. Use to close every return case: "build the case packet", "write up the return".'
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Case Packet
## Purpose
Terminal artifact: the complete case packet on first touch - the retail equivalent of the NCR.
## When to use
End of every return case.
## Inputs
governed.json (full payload).
## Steps
1. Validate against the contract; escalations and fraud-signal holds lead.
2. Packet: case facts with citations, reason code, determination + clause, recommendation, missing-evidence list, fraud signals (factual), customer response draft in the right tone, and the manager exception-request draft when the customer asked for one (#5.1).
3. Mark DRAFT - a human authorises any refund, exchange or decline.
## Output
CASE-<id>.md - terminal artifact.
## Grounding requirements
Every claim cites order, receipt, history, clause or config.
## Constraints
- Never authorise a refund, release funds, adjudicate fraud, dispose inventory or book a carrier (plugin boundary).
- Signals appear as signals; the packet never calls the customer a fraud.
## Escalation / uncertainty
hold_for_review packets route to asset protection with the signal citations attached.
