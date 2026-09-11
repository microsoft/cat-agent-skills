---
name: eligibility-check
description: Determines return eligibility against the configured policy and surfaces fraud signals deterministically - the explicit Govern step of this plugin. Use on "is this returnable", "do they get a refund", "any red flags", after reason-classify.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Eligibility Check (Govern)
## Purpose
The compliance determination IS the work: eligible / ineligible / needs_evidence with the clause cited (#2.1), plus fraud signals surfaced - never adjudicated (#3).
## When to use
After reason-classify in every case.
## Inputs
classified.json + config/return-windows.json.
## Steps
1. Validate against the contract.
2. Run scripts/eligibility_check.py --classified classified.json --config return-windows.json --out governed.json
3. Quote the determination, clause and any missing-evidence list verbatim. A sympathetic story is context for a HUMAN exception (#5.1), never a reason to change the determination.
4. Any fraud signal holds the recommendation for asset-protection review (#4.2) - present signals factually, no accusations.
## Output
governed.json - the {eligibility, fraud_signals} hop.
## Grounding requirements
Every determination cites its clause and config; every signal cites the record it came from.
## Constraints
- The engine decides; the model never grants an exception (#5.1), never drops a signal, never softens ineligible to "probably fine".
- Draft-first: nothing here authorises a refund or releases funds.
## Escalation / uncertainty
Signals or low confidence -> hold_for_review with the packet routed to asset protection / manager.
