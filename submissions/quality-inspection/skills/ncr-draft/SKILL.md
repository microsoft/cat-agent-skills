---
name: ncr-draft
description: Drafts the nonconformance report (NCR) and inspection summary from the graded contract payload, with every determination cited to the spec and rules. Use when the user says "draft the NCR", "write up the nonconformance", "inspection summary please", or after defect-grade completes with defects.
license: MIT
metadata:
  version: "2.0"
  author: Microsoft Manufacturing Skills
  category: Quality
---
# NCR Draft
## Purpose
Produce the terminal artifact: NCR + inspection summary rendered from templates/ncr-template.md, populated only from the contract payload.
## When to use
After defect-grade whenever graded_defects[] is non-empty; on request for an inspection summary even with zero defects (accept lot).
## Inputs
graded.json (contract mfg.quality-inspection.v1, the {graded_defects} hop).
## Steps
1. Validate input against the contract; surface escalations[] - document conflicts (#4.3) and borderline calls (#4.2) go in a visible "Open escalations" block above the disposition.
2. Fill templates/ncr-template.md: lot identification, nonconformance description with statistics, full characteristic table, grading with rule citations, watch list, draft-first containment actions, CAPA handoff note, contract payload as appendix.
3. Render to the requested format (markdown by default; other formats via the template).
4. Mark the document DRAFT - pending QE approval.
## Output
NCR-<id>.md - the terminal artifact of the contract flow.
## Grounding requirements
Every numeric claim traces to engine:tolerance_check; every grade cites its rule section; certificate conflicts cite the CoC document ID and ISO 9001 8.4.3.
## Constraints
- Draft-first: no containment is executed and nothing is filed or sent; the draft is a recommendation for the quality engineer.
- Nothing appears in the NCR that is not in the contract payload.
- Scope ends at the NCR; corrective/preventive action belongs to Quality Incident & CAPA (Wave 2).
## Escalation / uncertainty
If escalations[] is non-empty the NCR must lead with them; an NCR with an unresolved #4.3 conflict is never presented as ready to close.
