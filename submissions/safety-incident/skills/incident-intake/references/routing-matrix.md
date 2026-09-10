# Investigator Routing & Notification Matrix

Deterministic routing rules consumed by `routing_notify.py`. Given the classification (severity,
recordable, reportable + clock, repeat pattern), these rules assign the **investigator**, build the
**owner-notification list**, start any **regulatory clock**, and raise **escalations**. Cited in
contract payloads as `routing-matrix.md #<section>`.

Grounded in internal EHS policy (`ehs-policy-excerpts.md`) and ISO 45001 incident-management
practice (`rca-standards-excerpts.md`). Routing and notification are **drafted recommendations** —
the plugin never auto-sends; a human owner confirms (audit trail intact).

## 1. Investigator assignment (by severity)

| Section | Severity | `investigator.role` | Rationale |
|---|---|---|---|
| 1.1 | `low` | Area / line supervisor | Near-miss and first-aid cases are investigated at the line, logged as leading indicators. |
| 1.2 | `medium` | EHS officer | A recordable case requires a trained safety officer to complete the OSHA determination and investigation. |
| 1.3 | `high` | EHS manager | Days-away cases carry higher exposure; the EHS manager owns the investigation. |
| 1.4 | `critical` | Senior EHS investigator | Reportable events (fatality/hospitalization/amputation/eye) require the senior investigator and formal RCA. |

| Section | Override | Effect |
|---|---|---|
| 1.5 | `history.repeat_pattern = true` | Escalate the investigator one level (a repeating incident is systemic, not a one-off) and route a copy to Reliability/Process for JHA review. |

## 2. Owner-notification list (cumulative by severity)

Each tier **adds** to the tier below it. Every notification carries a `reason` and a citation.

| Section | Severity | Notify (in addition to lower tiers) |
|---|---|---|
| 2.1 | `low` | Area / line supervisor |
| 2.2 | `medium` | + EHS manager |
| 2.3 | `high` | + Plant manager |
| 2.4 | `critical` | + EHS director + Plant manager (immediate) |

| Section | Trigger | Add notification |
|---|---|---|
| 2.5 | `recordable.value = true` | EHS manager (owns the OSHA 300 entry), if not already notified. |
| 2.6 | `reportable.value = true` | EHS director + Plant manager **immediately**, and flag Regulatory/Legal for the OSHA filing. |

## 3. Regulatory clocks

| Section | Condition | Effect |
|---|---|---|
| 3.1 | `reportable.value = true` | Create a `regulatory_clock`: `type` = reportable type, `deadline_hours` from the classification (8 or 24), `due_by = occurred_at + deadline_hours`, `authority = OSHA (1904.39)`. |
| 3.2 | Clock created | Add an escalation: *file the OSHA report before `due_by`; the incident must not be closed until the filing is confirmed.* |
| 3.3 | No reportable event | No regulatory clock; the internal reporting-checklist timeline (`ehs-policy-excerpts.md` #3) still applies. |

## 4. Escalations

| Section | Condition | Escalation |
|---|---|---|
| 4.1 | `reportable.value = true` | OSHA-reportable event: notify EHS director + plant manager now; file within the clock; preserve the scene / equipment for investigation. |
| 4.2 | `recordable.value = true` | Recordable case: log on the OSHA 300 (column from the classification); EHS manager verifies the entry. |
| 4.3 | `history.repeat_pattern = true` | Repeat incidents in the same area/asset: open a systemic root-cause analysis and re-evaluate the JHA/HIRA before returning the task to service. |
| 4.4 | A request is made to reclassify a recordable/reportable case **down** to first-aid/non-recordable | **Hold.** A recordable/reportable determination cannot be silently downgraded; the request is recorded and routed to the EHS manager for sign-off (`osha-recordability-rules.md` #6.3). |
| 4.5 | Classification confidence `< 0.80` | Confirm treatment/outcome with the treating clinician before the record and routing are finalized. |

## 5. Next-best action (finalized here)

The engine composes `next_best_action` from the classification + routing:
- **Not recordable / low severity** → "Log as first-aid/near-miss (not OSHA recordable). Assign to
  the area supervisor; complete a 5-Why within the policy window; feed any control back into the JHA."
- **Recordable, not reportable** → "Record on the OSHA 300 (column <X>). Assign the EHS officer/
  manager; complete the investigation and RCA per policy."
- **Reportable** → "Do NOT classify as first-aid. Record on the OSHA 300 (column <X>). File the OSHA
  report within <N> hours (<type>, 1904.39). Assign a senior EHS investigator; notify the plant
  manager and EHS director; launch a formal RCA; preserve the scene."

The routing block (investigator, notifications, clocks, escalations) and the finalized
`next_best_action` travel to `incident-writeup`, which drafts the summary and RCA template with the
reporting checklist above the recommendation.
