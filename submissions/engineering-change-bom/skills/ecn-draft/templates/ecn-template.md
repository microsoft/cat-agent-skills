# ENGINEERING CHANGE NOTICE — {{ecr_id}} (DRAFT — change board approval required)
{{if escalations}}## ⚠ Blocking items
{{for each escalation}}- {{escalation}}{{end}}{{end}}
Change: {{change_description}} ({{change_type}} on {{affected_characteristic}}, {{part_number}})
Impact class: {{impact.impact_class}} · interface violation: {{impact.interface_violation}} · release blocked: {{impact.release_blocked}}
Affected items: {{impact.affected_items}} · Documents to update: {{impact.documents_to_update}}
Inventory: {{impact.inventory_disposition}} (change-rules.md #4)
Standards findings: {{standards_findings}}
Appendix: contract payload (mfg.engineering-change-bom.v1)
