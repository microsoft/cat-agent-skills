---
name: context-assemble
description: Assembles customer, order, loyalty and carrier context, detects record-vs-account contradictions, and selects the resolution path deterministically with the context_assemble engine. Use after inquiry-intake, or on "pull up everything on this order".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Context Assemble
## Purpose
One consolidated view + deterministic path selection: contradictions trigger the DNR process (#2.1); money boundaries enforced (#3.1).
## When to use
After inquiry-intake in every run.
## Inputs
classified.json + records.json (the records extract that ships with the case: OMS order, carrier scans, loyalty) + config/service-config.json.
## Steps
1. Run scripts/context_assemble.py --classified classified.json --records records.json --config service-config.json --out assembled.json
2. Quote the path and gate arithmetic verbatim (tier and value against the instant-resolution gate). The response never disputes the customer's account - it explains the process and the clock (#2.2).
## Output
assembled.json - the {context} hop.
## Grounding requirements
Every context fact cites its extract; the path cites the policy config.
## Constraints
- Path selection is engine-only; sympathy, volume or channel pressure never flips dnr_investigation to instant refund.
- Goodwill credit is out of scope at any tier - propose-for-human at most (#3.1).
## Escalation / uncertainty
Contradiction present -> the escalation carries the carrier scan citation for the investigation.
