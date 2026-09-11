# Supplier Communications Standards — Excerpts (grounding)

Reference excerpts the `disruption-writeup` skill cites when drafting the **supplier follow-up** and
the **internal escalation brief**. Grounded in professional procurement communication practice.
Cited as `supplier-comms-standards.md #<section>`.

## 1. Supplier follow-up — required elements

A complete supplier follow-up carries: the **PO number and part**, the **original promised date** and
the **revised date** (state the gap plainly), the **quantity affected**, a specific **ask** (confirm
the revised date, expedite/partial-ship, or provide a recovery plan), and a **response-by** date.
State facts and the business impact; keep it firm and professional, not accusatory.

## 2. Ask, matched to the mitigation

| Mitigation | The ask to the supplier |
|---|---|
| `reschedule` | Confirm the revised date in writing so the schedule can be aligned; flag any further slip early. |
| `substitute` | (Usually internal) — notify the supplier the shortfall is covered by an approved substitute; hold the balance to the revised date. |
| `expedite` | Request a partial shipment / premium freight to hit the first-impact date, or a firm recovery plan; ask whether a qualified alternate lot is available. |

## 3. Internal escalation brief — required elements

A complete escalation brief carries, in order: the **disruption** (supplier, PO, part, delay), the
**impact** (affected products, lines and orders, quantity and first-impact date, worst severity), the
**recommended mitigation** (option + specific actions), the **owners to notify** (by role), and the
**decision needed** (e.g. approve premium freight, approve a substitute, accept a late customer
shipment). Lead with the impact and the decision — the reader is deciding, not investigating.

## 4. Tone & governance

- **Draft-first.** Every artifact is a draft for a buyer/planner to review and send. Nothing is
  auto-sent to the supplier and no ERP/schedule change is written (`sourcing-standards-excerpts.md`
  #6).
- **Cite the basis.** The impact numbers trace to `engine:shortage_impact_map`; the mitigation and
  escalation trace to `engine:mitigation_recommend`. The draft states the severity and the
  first-impact date so the owner can act without re-deriving them.
- **Don't soften a customer-order risk.** A `late_shipment` (a customer order going late) is stated
  explicitly in both the brief and the escalation — it is the reason the case is critical.

## 5. Structure the writeup emits

- **Header** — disruption id, supplier/PO, part, DRAFT banner.
- **Impact summary** — worst severity, first-impact date, affected products/lines/orders, qty at risk.
- **Impact map table** — per-order rows (product, line, order, need-by, qty at risk, status).
- **Recommended mitigation** — option, urgency, actions, substitute/alternate.
- **Open items / escalations** — the escalation list, above the recommendation.
- **Supplier follow-up (draft)** — per Sec 1-2.
- **Internal escalation brief (draft)** — per Sec 3.
- **Appendix** — the contract payload.
