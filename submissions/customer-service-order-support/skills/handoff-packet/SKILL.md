---
name: handoff-packet
description: 'Builds the structured escalation packet when the run cannot resolve - intent, context, contradictions, what was checked, recommended next step. Use on any low-confidence, contradicted, or out-of-scope run: "escalate this", "hand off to tier 2".'
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Handoff Packet
## Purpose
Terminal artifact for non-resolvable runs: no bare transfers (#4.1).
## When to use
Low confidence, contradictions, no approved answer, or money-boundary requests.
## Inputs
Full payload.
## Steps
1. Packet: intent + confidence, consolidated context with citations, contradiction flags with the carrier scan reference, everything already checked, the recommended next step (e.g., open carrier investigation SVC-DNR-2), and the customer-visible interim reply draft.
2. Goodwill requests appear as PROPOSALS for the human, never as commitments (#3.1).
## Output
Handoff packet + interim reply draft - terminal artifacts.
## Grounding requirements
Every packet line cites its record.
## Constraints
- The packet recommends; the human decides. No credits, no payment changes, no exceptions (plugin boundary).
## Escalation / uncertainty
Angry-customer pressure changes tone handling, never the path.
