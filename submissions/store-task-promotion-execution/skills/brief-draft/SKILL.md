---
name: brief-draft
description: Drafts the store readiness checklist, the shift brief in store language, and the exception escalation from the contract payload. Use to close every execution run - "draft the shift brief", "write up the readiness pack".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Brief Draft
## Purpose
Terminal artifacts: readiness checklist + shift brief + exception escalation, populated only from the contract payload.
## When to use
End of every execution run.
## Inputs
ranked.json (full payload).
## Steps
1. Validate against the contract; price conflicts and fixture conflicts lead.
2. Checklist: per-requirement status with citations. Shift brief: what each daypart does, in store language. Exceptions: ranked list with revenue at stake.
3. Mark DRAFT - the store manager owns execution; nothing changes POS prices, planograms, schedules or funding (plugin boundary).
## Output
READINESS-<campaign>-<store>.md + shift brief - terminal artifacts.
## Grounding requirements
Every line cites pack, price file or store record.
## Constraints
- Draft-first; a completeness % never rounds up; conflicts never disappear from the brief.
## Escalation / uncertainty
Any price conflict = explicit "do not change the shelf" instruction in the brief until HQ resolves.
