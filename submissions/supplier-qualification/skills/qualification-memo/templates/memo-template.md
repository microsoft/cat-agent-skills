# SUPPLIER QUALIFICATION MEMO — {{supplier.name}} ({{category}}) · DRAFT
{{if escalations}}## ⚠ Escalations
{{for each escalation}}- {{escalation}}{{end}}{{end}}
Recommendation: **{{recommendation.outcome}}** (qualification-rules.md #5) · Conditions: {{recommendation.conditions}}
Risk: quality {{risk.quality.band}} {{risk.quality.notes}} · financial {{risk.financial.band}} {{risk.financial.notes}} · geographic {{risk.geographic.band}} {{risk.geographic.notes}}
AVL: incumbents {{avl.incumbents}} · adds regional diversity: {{avl.adds_regional_diversity}}
Appendix: contract payload (mfg.supplier-qualification.v1)
