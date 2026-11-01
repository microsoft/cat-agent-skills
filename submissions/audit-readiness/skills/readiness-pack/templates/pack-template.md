# AUDIT READINESS PACK — {{audit_id}} ({{standard}}, audit {{audit_date}}) · DRAFT
Verdict: **{{readiness.verdict}}** — {{readiness.major_gaps}} major / {{readiness.minor_gaps}} minor (audit-rules.md #4)
{{if escalations}}## ⚠ Major gaps
{{for each escalation}}- {{escalation}}{{end}}{{end}}
## Gap table
{{for each gap}}| {{clause}} | {{status}} | {{severity}} | {{detail}} | {{owner}} | {{action}} |{{end}}
## Clause map / evidence index: from payload.
Appendix: contract payload (mfg.audit-readiness.v1)
