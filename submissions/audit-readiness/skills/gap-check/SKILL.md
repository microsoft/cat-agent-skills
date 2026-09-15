---
name: gap-check
description: Validates the evidence register against clause requirements and flags gaps with severity - the explicit Govern step and the core work of this plugin, via the deterministic gap_check engine. Use when the user says "are we ready for the audit", "check for gaps", "will we pass", or after evidence-gather in a readiness run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Quality}
---
# Gap Check (Govern)
## Purpose
Deterministic conformity check: recency (#1), coverage (#2), severity (#3), readiness verdict (#4). Compliance determination IS the work here.
## When to use
After evidence-gather in every run; on any "are we ready" question.
## Inputs
mapped.json + evidence.json.
## Steps
1. Validate against the contract.
2. Run scripts/gap_check.py --mapped mapped.json --evidence evidence.json --out gaps.json
3. Quote statuses and the verdict verbatim. A 13-month-old management review is STALE however complete the folder looks - a full folder is not a current folder (#1.1).
## Output
gaps.json - the {gaps, readiness} hop.
## Grounding requirements
Every gap cites its clause-table row and rule section.
## Constraints
- Verdicts are engine-only; the model never rounds not_ready up to "should be fine".
- Gaps close by producing evidence, never by rewording (#5).
## Escalation / uncertainty
Major gaps escalate to the quality director with owner + action attached.
