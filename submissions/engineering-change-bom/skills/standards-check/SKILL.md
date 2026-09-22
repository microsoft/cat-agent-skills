---
name: standards-check
description: Checks the proposed change against drawing standards and internal design rules, citing each rule applied. Use when the user says "does this meet the design rules", "standards check", "is this change allowed", or after bom-impact in a change run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Engineering}
---
# Standards Check
## Purpose
Apply the design-standards excerpts to the classified change: fit-definition implications (ASME Y14.5), press-fit band rule DR-12, fatigue-surface rule DR-31, re-baselining requirements.
## When to use
After bom-impact in every change run.
## Inputs
impact.json + references/design-standards-excerpts.md.
## Steps
1. Validate against the contract.
2. For each applicable rule, record a finding {rule, applies, result, citation} - grounded in the excerpt text, never from memory.
3. A finding never overrides an engine escalation; it can only add findings.
## Output
standards_findings[] appended to the payload.
## Grounding requirements
Every finding cites the standard or design-rule id verbatim from the reference file.
## Constraints
- Findings are cited or they do not exist; no un-grounded standards claims.
- No approval language - the change board decides.
## Escalation / uncertainty
A rule requiring analysis this plugin cannot do (stackup, stress sign-off): record as an open requirement, not a pass.
