# WORK-ORDER UPDATE — {{asset_id}}

> **DRAFT — PENDING PLANNER / SUPERVISOR APPROVAL** · Act steps are draft-first; no CMMS
> write-back and no work is dispatched until a human approves.

Produced by fault-intake → history-retrieve → failure-mode-rank → criticality-rank →
work-order-update under contract `mfg.maintenance-triage.v1`. Every determination carries
engine provenance, confidence, and a citation.

## 1. Asset & fault identification

| Field | Value |
|---|---|
| Asset / tag | {{asset_id}} — {{asset_name}} |
| Location | {{location}} |
| Criticality class | {{asset_criticality}} |
| Downtime cost | {{downtime_cost_per_hr}} /hr |
| Reported by / when | {{reported_by}} · {{reported_at}} |

## 2. Symptom summary

- Symptoms: {{symptoms_joined}}
- Alarm codes: {{alarm_codes_joined}}
- History window: {{history_window_days}} days · prior work orders: {{prior_wo_count}}

{{if escalations}}## ⚠ Open escalations — read before acting
{{for each escalation}}- {{escalation}}
{{end}}{{end}}

## 3. Likely failure modes (ranked)

| Rank | Failure mode | Match | Evidence | Confidence | Citation |
|---|---|---|---|---|---|
{{for each ranked_cause}}| {{rank}} | {{failure_mode}} | {{match_score}} | {{evidence_short}} | {{confidence}} | {{citation}} |
{{end}}

*Ranking source: `engine:fault_rank`. Where a recurring symptomatic fix was detected, the
underlying root cause has been promoted per `references/failure-mode-library.md` #3.1.*

## 4. Priority & downtime impact

| Field | Value |
|---|---|
| **Priority** | **{{priority_level}}** (score {{priority_score}}) |
| Response target | {{response_target}} |
| Downtime cost estimate | {{downtime_cost_estimate}} ({{expected_repair_hours}} h × {{downtime_cost_per_hr}}/hr) |
| Basis | {{priority_factors_joined}} |

*Priority source: `engine:criticality_score` · `references/asset-criticality-matrix.md` +
ISO 55000 risk-based prioritization (`references/rcm-iso55000-excerpts.md`).*

## 5. Recommended action (draft)

**{{recommended_action}}**

- Confirm the diagnosis with the check named in {{top_citation}} before ordering parts.
- Stage parts/tools for the recommended fix; assign to a qualified technician.
- On a recurring-failure escalation, open a root-cause analysis (RCM) alongside the repair.

*All actions are drafts pending planner/supervisor approval — no CMMS/EAM write-back in v1.*

## 6. Scope boundary & handoff

This work-order update completes the plugin's scope. **Predictive maintenance and PM
optimization (Wave 3)** are out of scope; this plugin triages the fault in front of you, it
does not forecast future failures.

## Appendix A — contract payload

```json
{{contract_payload}}
```
