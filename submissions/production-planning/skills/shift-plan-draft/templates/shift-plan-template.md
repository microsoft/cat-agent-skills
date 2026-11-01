# SHIFT PLAN — {{plan_week}} · {{line}} (DRAFT — planner publishes; nothing written to execution systems)
{{if escalations}}## ⚠ Constraints & escalations
{{for each escalation}}- {{escalation}}{{end}}{{end}}
Utilization (run-hours): {{capacity.utilization_pct}}% of {{capacity.available_hours}}h · changeovers: naive {{schedule.naive_changeover_hours}}h vs optimized {{schedule.optimized_changeover_hours}}h
Sequence: {{schedule.optimized_sequence}} (campaigns per scheduling-rules.md #3; gates per #2)
Late committed: naive {{schedule.late_committed_naive}} -> optimized {{schedule.late_committed_optimized}} (#4)
Appendix: contract payload (mfg.production-planning.v1)
