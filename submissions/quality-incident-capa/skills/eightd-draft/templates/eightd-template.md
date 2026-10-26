# 8D REPORT — {{capa_id}} (DRAFT — pending quality-manager approval)
{{if escalations}}## ⚠ Open items
{{for each escalation}}- {{escalation}}{{end}}{{end}}
D1 Team · D2 Problem: {{ncr_ref}} · D3 Containment: {{capa.containment}}
D4 Root cause ({{root_cause.method}}): {{root_cause.why_chain}} — systemic: {{root_cause.systemic}} · {{root_cause.citation}}
D5/D6 Corrective: {{capa.corrective}} · D7 Preventive: {{capa.preventive}}
Effectiveness checks: {{capa.effectiveness_checks}} (capa-rules.md #4)
D8 Closure: ready={{closure.ready}} · blockers: {{closure.blockers}} (capa-rules.md #6)
Appendix: contract payload (mfg.quality-incident-capa.v1)
