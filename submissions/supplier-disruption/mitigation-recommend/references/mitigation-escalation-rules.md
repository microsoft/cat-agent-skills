# Mitigation & Escalation Rules — Decision Tree + Escalation Matrix

Deterministic rules consumed by `mitigation_recommend.py`. Given the impact summary (worst severity,
first-impact date, quantity at risk) and the ERP supply position (substitutes, alternate suppliers,
lead time, single-source flag, supplier history), these rules choose the **mitigation**
(expedite / substitute / reschedule), set the **urgency**, build the cumulative **owner-notification
list**, and raise the **escalations**. Cited in contract payloads as `mitigation-escalation-rules.md
#<section>`.

Grounded in ERP/MRP planning practice and supplier-management policy
(`sourcing-standards-excerpts.md`). Mitigation and escalation are **drafted recommendations** — the
plugin never expedites, substitutes, reschedules, or emails on its own; a buyer/planner confirms.

## 1. Mitigation decision tree (first match wins)

Let `sev = impact_summary.worst_severity`, `risk = impact_summary.total_qty_at_risk`, and
`days_to_impact = first_impact_date − reported_at` (calendar days).

| Section | Condition | `option` | Meaning |
|---|---|---|---|
| 1.1 | `sev` in {`none`,`low`} (buffer / incoming PO covers) | `reschedule` | Align the schedule to the revised date and monitor; no material action needed. |
| 1.2 | `sev` >= `medium` **and** an **approved** substitute exists with `available_qty >= risk` | `substitute` | Draft buyer/planner review of the substitute; availability is screening only, not a quantity to substitute or purchase. |
| 1.3 | `sev` >= `medium`, no sufficient substitute, **and** a **qualified** alternate supplier has `lead_time_days <= days_to_impact` | `expedite` | Draft buyer/planner review of alternate recovery; separately determine feasible PO-level quantity and timing, never use aggregate risk as an expedite quantity. |
| 1.4 | `sev` >= `medium`, no substitute and no in-time qualified alternate | `expedite` | Expedite the current supplier (partial/air-freight) **and** begin qualifying an alternate; reschedule downstream orders as a fallback. |

## 2. Urgency

| Section | `worst_severity` | `urgency` |
|---|---|---|
| 2.1 | `none` / `low` | `routine` |
| 2.2 | `medium` | `elevated` |
| 2.3 | `high` | `urgent` |
| 2.4 | `critical` | `immediate` |

## 3. Escalation matrix

| Section | Condition | Escalation |
|---|---|---|
| 3.1 | `sev = medium` | Production planner owns a schedule adjustment; buyer chases the PO. |
| 3.2 | `sev = high` (a line will stop) | Escalate to the **materials manager**; approve expedite/premium freight against downtime cost. |
| 3.3 | `sev = critical` (a customer order will ship late) | Escalate to the **materials manager + plant manager**; notify customer service/account before the customer finds out. |
| 3.4 | `supply.single_source = true` **and** `sev` in {`high`,`critical`} | Open a **second-source qualification** — a single-source critical part with no buffer is a standing risk, not a one-off. |
| 3.5 | `history.chronic_pattern = true` | Repeated late deliveries from this supplier: open a **supplier-performance / SQM review**; do not treat this as a one-off slip. |
| 3.6 | `impact_summary.below_safety_stock = true` | Projected balance dips below safety stock: flag a stock-out risk even where no single order is formally short. |
| 3.7 | `impact_summary.confidence < 0.80` | Confirm the MRP position (on-hand, open orders, revised date) before committing the mitigation. |

## 4. Owner-notification list (cumulative by severity)

Each tier **adds** to the tier below it. Every notification carries a `reason` and a citation.

| Section | Severity | Notify (in addition to lower tiers) |
|---|---|---|
| 4.1 | `low` / `none` | Buyer (owns the PO) |
| 4.2 | `medium` | + Production planner |
| 4.3 | `high` | + Materials manager |
| 4.4 | `critical` | + Plant manager |

| Section | Trigger | Add notification |
|---|---|---|
| 4.5 | any affected `order_type = sales` | Customer service / account manager (customer order at risk). |
| 4.6 | `history.chronic_pattern = true` | Supplier quality management (SQM) — performance review. |

## 5. Next-best action (finalized here)

The engine composes `next_best_action` from the mitigation + severity:
- **`reschedule` (none/low)** → "Buffer/incoming PO covers demand through the revised date. Align the
  schedule and monitor; no expedite required."
- **`substitute` (>= medium)** → Draft buyer/planner review of the approved substitute:
  separately determine feasible PO-level quantity, timing and form/fit/function; review possible
  work-order and delayed-PO changes, without issuing any change.
- **`expedite` (>= medium)** → Draft recovery investigation with the qualified alternate/current
  supplier. Original-need-by aggregate demand risk is not an expedite quantity. Buyer/planner
  review must separately establish feasible PO-level quantities and dates; escalation recipients
  remain proposed and unsent.

The mitigation block (option, urgency, actions, substitute/alternate), the notification list, the
escalations and the finalized `next_best_action` travel to `disruption-writeup`, which drafts the
supplier follow-up and the internal escalation brief with the impact summary above the recommendation.

## Quantity and target amendment 1.2
Total quantity at risk is demand exposed at original need-by dates, not the quantity of one delayed PO and not net shortage after receipt. Never issue an expedite for that aggregate. The buyer must determine feasible PO-level partial recovery and timing. An unqualified or out-of-time alternate is qualification-only; fallback recovery targets the current supplier.

1.4.1 wording reconciliation: this boundary applies to actions, rationale, next-best action,
templates and appendices, including substitution. Never translate aggregate demand risk into
a quantity to purchase, substitute or expedite. No PO issuance, execution, hold or cancellation
is instructed by the plugin; buyer/planner review and any authorized action occur outside it.
The decision-tree conditions, risk calculations and thresholds above are unchanged.
