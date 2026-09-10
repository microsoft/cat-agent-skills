---
name: defect-grade
description: Grades each out-of-tolerance characteristic by severity and recommends a disposition (use-as-is / rework / scrap / return-to-vendor / hold-for-review) using the deterministic disposition rules engine. Use when the user says "grade the defects", "what disposition?", "how bad is it?", "can we ship it?", or after tolerance-check finds any out-of-tolerance characteristic.
license: MIT
metadata:
  version: "2.0"
  author: Microsoft Manufacturing Skills
  category: Quality
---
# Defect Grade
## Purpose
Apply references/disposition-rules.md deterministically: severity, disposition, watch-list, lot recommendation - every grade citing the rule section that fired.
## When to use
After tolerance-check, whenever any characteristic is out_of_tolerance or marginal - and on any "can we ship it / use it as is" question.
## Inputs
deviations.json (contract mfg.quality-inspection.v1, the {deviations} hop).
## Steps
1. Validate input against the contract.
2. Run scripts/defect_grade.py --deviations deviations.json --out graded.json
3. Quote severities, dispositions and rule citations verbatim. The model may write the rationale narrative but never changes a grade - not for schedule pressure, not because a certificate says the part is fine, not because the value "looks basically in spec".
4. Surface borderline-incidence (#4.2) and document-conflict (#4.3) escalations explicitly.
## Output
graded.json - the {graded_defects} hop: graded_defects[], watch_list[], recommended_disposition, escalations[].
## Grounding requirements
Every grade cites its disposition-rules.md section; note-derived criticality carries its drawing-note citation; use_as_is candidates carry requires_deviation_authorization=true.
## Constraints
- Grading is rules-engine-only; the model never overrides a severity or disposition.
- A hold_for_review from #4.1 (confidence), #4.3 (doc conflict) or #3.1 (critical) is never downgraded.
- use_as_is is a candidate pending deviation authorization, never a self-approved outcome (#3.5).
## Escalation / uncertainty
Confidence < 0.75 forces hold (#4.1). Unknown criticality on an OOT characteristic: treat as critical, escalate.
