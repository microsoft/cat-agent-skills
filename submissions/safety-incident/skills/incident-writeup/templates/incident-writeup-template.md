# INCIDENT WRITE-UP — {{incident_id}} · {{asset_or_area}}

> **DRAFT — PENDING EHS-OWNER REVIEW & SIGN-OFF** · Act steps are draft-first; no OSHA filing, no
> auto-notification, and no incident closure until a human owner approves. Reporting checklist and
> audit trail intact.

Produced by incident-intake → ehs-knowledge-retrieve → severity-recordability → routing-notify →
incident-writeup under contract `mfg.safety-incident-assist.v1`. Every determination carries engine
provenance, confidence, and a citation.

## 1. Incident context

| Field | Value |
|---|---|
| Incident | {{incident_id}} — {{incident_type}} |
| Area / asset | {{asset_or_area}} |
| Location | {{location}} |
| Occurred / reported | {{occurred_at}} · {{reported_at}} |
| Reported by / channel | {{reported_by}} · {{report_channel}} |
| Injured person / body part | {{injury_employee}} · {{injury_body_part}} |
| Treatment / outcome | {{injury_treatment_given}} · {{injury_outcome}} ({{injury_days_away}} days away) |
| What happened | {{description}} |

## 2. Classification (engine determination)

| Determination | Value | Citation |
|---|---|---|
| Severity | **{{classification_severity}}** | osha-recordability-rules.md #5 |
| Near miss | {{classification_near_miss}} | osha-recordability-rules.md #1 |
| OSHA recordable | **{{classification_recordable_value}}** — {{classification_recordable_reason}} | osha-recordability-rules.md #3 |
| OSHA 300 column | {{classification_recordable_column}} | osha-recordability-rules.md #3 |
| OSHA reportable | **{{classification_reportable_value}}** — {{classification_reportable_type}} | osha-recordability-rules.md #4 |
| Confidence | {{classification_confidence}} | source `engine:recordability_classify` |

## 3. Routing & notification (engine determination)

- **Investigator:** {{routing_investigator_role}} — {{routing_investigator_rationale}}
  (`engine:routing_notify` · routing-matrix.md #1)

| Notify | Role | Reason | Citation |
|---|---|---|---|
{{for each routing.notifications}}| {{name}} | {{role}} | {{reason}} | {{citation}} |
{{end}}

{{if routing.regulatory_clocks}}### ⏱ Regulatory clock — ACTION REQUIRED
{{for each routing.regulatory_clocks}}- **{{type}}**: file within **{{deadline_hours}}h** — due by **{{due_by}}** ({{authority}}, {{citation}}).
{{end}}{{end}}

{{if escalations}}## ⚠ Open items / escalations — read before you act
{{for each escalation}}- {{escalation}}
{{end}}{{end}}

## 4. Recommended next-best action (draft)

**{{next_best_action}}**

- Follow internal EHS policy and the JHA/HIRA for the task, except where a control gap above changes it.
- Any recordable case is logged on the OSHA 300 by the EHS manager; any reportable case is filed
  within the regulatory clock by the EHS director.
- On a repeat pattern, open a systemic RCA and re-evaluate the JHA/HIRA before returning to service.

*All actions are drafts pending EHS-owner review — no OSHA filing or notification is auto-sent in v1.*

## 5. Root-cause analysis template ({{rca_method}})

*Complete during the investigation — grounded in `references/rca-standards-excerpts.md` #4
(ISO 45001 §10.2).*

**Problem statement:** {{description}}

5-Why:
1. Why did the incident occur? — ______
2. Why? — ______
3. Why? — ______
4. Why? — ______
5. Root cause — ______

| Contributing factor | Category (People / Process / Equipment / Environment) | Evidence |
|---|---|---|
|  |  |  |

**Corrective actions (with owner + due date):**
| Action | Type (eliminate / engineer / admin / PPE) | Owner | Due |
|---|---|---|---|
|  |  |  |  |

## 6. Reporting checklist

- [ ] Injured person's status confirmed with the treating clinician
- [ ] OSHA 300 entry created (if recordable, column {{classification_recordable_column}})
- [ ] OSHA report filed within the clock (if reportable)
- [ ] Investigator assigned and RCA opened
- [ ] Owners notified and sign-off recorded

## 7. Scope boundary & handoff

This write-up completes the plugin's scope. **Auto-filing to OSHA, auto-notification, and incident
closure/CAPA tracking (Wave 3)** are out of scope; this plugin classifies, routes and drafts the
incident in front of you — an EHS owner reviews, files and closes it.

## Appendix A — contract payload

```json
{{contract_payload}}
```
