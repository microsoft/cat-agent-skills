# DELIVERABLE REVIEW PACKET - {{deliverable.deliverable_id}} - DRAFT - HUMAN REVIEW REQUIRED

> Draft-first: this packet does not approve release, clear a gate, sign off the deliverable or substitute for reviewing-partner/QRM judgement.

Produced by deliverable-ingest -> criteria-retrieve -> assertion-map -> gate-check -> review-packet under contract `ps.deliverable-review-quality-gate.v1`.

## Review status
**{{release_readiness.status}}** - {{release_readiness.summary}}

## Ranked findings for partner review
| Rank | Severity | Gate | Location | Issue | Criteria |
|---|---|---|---|---|---|
{{for each ranked_finding}}| {{rank}} | {{severity}} | {{gate_id}} | p{{location.page}} / {{location.section}} / para {{location.paragraph}} | {{title}} - {{detail}} | {{criteria_section}} |
{{end}}

When `location.page` or `location.paragraph` is null (a register-level finding such as a register that was not supplied), render `register-level` / `{{location.section}}` / `{{location.label}}` instead of a page or paragraph number. Never substitute page 1 or any other placeholder page.

If `ranked_findings[]` is empty, and only after `severity_rank.py --verify` passed on this exact file (review-packet SKILL.md step 1; quality-gate-criteria.md #8.21), replace the table with exactly: "None: the engines produced no findings. This does not clear any gate; the reviewing partner/QRM owner decides release." A ranked output that verify refused is never rendered, so an emptied list can never reach this wording.

## Gate checklist
| Gate | Status | Highest severity | Evidence |
|---|---|---|---|
{{for each gate_result}}| {{gate_id}} - {{name}} | {{status}} | {{highest_severity}} | {{citation}} |
{{end}}

## Unsupported and limited assertions
{{for each assertion_mapping where support_status != "supported"}}
- **{{support_status}}** - {{assertion_id}} at p{{location.page}}, para {{location.paragraph}}: {{text}}
  - Evidence: {{evidence_ids}}; citation: {{citation}}
{{end}}

If every assertion mapping is `supported`, write exactly: "None: assertion-map found no unsupported or limited assertions." Do not remove the heading.

## Escalations
{{for each escalation}}- {{escalation}}
{{end}}

If `escalations[]` is empty, write exactly: "None: the engines raised no escalations. This does not clear any gate." Do not remove the heading.

## Draft routing hold
Do not add user-supplied external recipients. Any recipient not already confirmed in `deliverable.intended_recipients` must be held for reviewing-partner/QRM confirmation before routing, because a third-party recipient changes the required reliance language (quality-gate-criteria.md #2.2) and client data must not reach unconfirmed readers (quality-gate-criteria.md #4.2).

## Required human decision
The reviewing partner/QRM owner decides whether fixes are sufficient. The engine can flag or block; it cannot sign off the gate or authorize client issue.

## Provenance and redaction notes
Engine provenance: {{provenance.engines}}; generated at {{provenance.generated_at}}. Raw contract payload intentionally omitted to avoid duplicating client data or untrusted source text.
