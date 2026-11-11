# Investigator Routing & Notification Matrix

Deterministic routing rules consumed by `routing_notify.py`. Given the classification (severity,
recordable, reportable + clock, repeat pattern), these rules propose an **unassigned investigator**, build the
**draft owner-notification list**, explicitly block unverified clocks, and raise **escalations**. Cited in
contract payloads as `routing-matrix.md #<section>`.

Grounded in internal EHS policy (`ehs-policy-excerpts.md`) and ISO 45001 incident-management
practice (`rca-standards-excerpts.md`). Routing and notification are **drafted recommendations** —
the plugin never sends, assigns or confirms; no authenticated audit trail is implemented.

**Draft review guidance — EHS REVIEW REQUIRED.** Reportability and deadlines
remain undetermined. Every packet is a draft and no approval or filing is verified.

## 1. Investigator assignment (by severity)

| Section | Severity | `investigator.role` | Rationale |
|---|---|---|---|
| 1.1 | `low` | Area / line supervisor | Near-miss and first-aid cases are investigated at the line, logged as leading indicators. |
| 1.2 | `medium` | EHS officer | A recordable case requires a trained safety officer to complete the OSHA determination and investigation. |
| 1.3 | `high` | EHS manager | Days-away cases carry higher exposure; the EHS manager owns the investigation. |
| 1.4 | `critical` | Senior EHS investigator | Reportable events (fatality/hospitalization/amputation/eye) require the senior investigator and formal RCA. |
| 1.6 | `review_required` | EHS manager | Missing/contradictory evidence is not low severity. |

| Section | Override | Effect |
|---|---|---|
| 1.5 | `history.repeat_pattern = true` | Propose the investigator one level higher and include Reliability/Process in the unsent review list. Recurrence is a review cue, not proof of systemic cause. |

Repeat flags are recomputed from history_input/history_query, not trusted aggregates. Exact
area AND asset matching, fixed as_of, inclusive lower/exclusive upper date boundary, unique IDs,
and two prior matches define this candidate's recurrence signal. Same-day rows are excluded
because the source has dates only, not times. Missing/conflicting logs produce unknown, not false.
This threshold/window policy requires EHS approval.

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
| 2.7 | Every candidate draft packet | Include EHS manager for independent draft review; approval is not verified. |
| 2.8 | Critical event evidence with reporting applicability unconfirmed | Include Regulatory / Legal for URGENT applicability/timing review; no filing or deadline is asserted. |

In this candidate reportability is never confirmed: critical events instead add Regulatory/Legal
for URGENT applicability/timing review. Every draft includes EHS manager. Notifications are
`draft_not_sent`; all names/assignees remain unassigned placeholders. A candidate output is NOT
proof of notification or an operational assignment.

## 3. Regulatory clocks

| Section | Condition | Effect |
|---|---|---|
| 3.1 | All candidate packets | `regulatory_clocks=[]`, `clock_status=review_required`; no asserted deadline. NEVER add hours to occurred_at. |
| 3.2 | Severe outcome | URGENT EHS/Regulatory assessment of event, knowledge, scope and exceptions. Do not wait for this plugin. |
| 3.3 | No severe outcome supplied | Reporting applicability is still unverified, not a definitive negative. |

## 4. Escalations

| Section | Condition | Escalation |
|---|---|---|
| 4.1 | Critical event evidence | URGENT draft escalation to EHS/Regulatory; preserve evidence; deadline undetermined. |
| 4.2 | `recordable.value = true` | Draft OSHA 300 recommendation; EHS manager verifies before any entry. |
| 4.3 | `history.repeat_pattern = true` | Draft recurrence cue for qualified EHS review: assess need for systemic root-cause analysis and JHA/HIRA review; no operational or return-to-service instruction. |
| 4.4 | A request is made to reclassify a recordable/reportable case **down** to first-aid/non-recordable | **Hold.** A recordable/reportable determination cannot be silently downgraded; the request is recorded and routed to the EHS manager for sign-off (`osha-recordability-rules.md` #6.3). |
| 4.5 | confidence=null (all candidate packets) | No probability estimated; confirm cited evidence and review reasons. |

The executable governance block always sets closure_allowed=false and action_execution_allowed=false.
No input can mark EHS approval or filing confirmation as verified. Downgrade holds cannot be
released in this candidate. These controls constrain local packet recommendations only; they
do not enforce or authenticate an external EHS system.

## 5. Next-best action (finalized here)

The draft action ALWAYS quotes the actual `investigator.role`, including repeat escalation.
It states EHS REVIEW REQUIRED, no deadline asserted, and no notification, filing or closure
authorized. It adds URGENT review for critical events and HOLD for downgrade requests.
Routing recomputes classification/history/governance and rejects missing, stale or altered hops.

The routing block (investigator, notifications, clocks, escalations) and the finalized
`next_best_action` travel to `incident-writeup`, which drafts the summary and RCA template with the
reporting checklist above the recommendation.
