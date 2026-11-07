# WORK-ORDER UPDATE — {{asset_id}}

> **DRAFT — PENDING PLANNER / SUPERVISOR APPROVAL** · Act steps are draft-first; no CMMS
> write-back or dispatch is performed by this plugin. No reset/restart, protective-device
> bypass, energized work or repair authorization is provided, regardless of priority.

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

- Below 0.75 top confidence, or with no ranked cause: human diagnosis required; no corrective repair is selected.
- At or above 0.75: any candidate assessment remains subject to qualified human diagnosis and verification of applicable OEM evidence; it is not an instruction to perform a repair.
- Planner/supervisor review of evidence, unknowns and any recurring-failure RCA escalation is pending; no parts staging or technician assignment is directed here.

*All actions are drafts pending planner/supervisor approval — no CMMS/EAM write-back in v1.*

## 6. Scope boundary & handoff

This work-order update completes the plugin's scope. **Predictive maintenance and PM
optimization (Wave 3)** are out of scope; this plugin triages the fault in front of you, it
does not forecast future failures.

## Appendix A — contract payload

Only the fresh 1.3.1 bounded engine payload belongs here. Historical actions/manual excerpts
are source evidence, not current work instructions; never reuse legacy recommended actions.

```json
{{contract_payload}}
```
