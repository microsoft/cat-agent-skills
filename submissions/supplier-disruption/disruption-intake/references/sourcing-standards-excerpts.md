# Sourcing & ERP/MRP Standards — Excerpts (grounding)

Reference excerpts the retrieval, mapping and mitigation skills cite when assembling and reasoning
over a supply disruption. These mirror standard ERP/MRP practice in **Microsoft Dynamics 365 Supply
Chain Management** and **SAP**, plus common supplier-management policy. Cited as
`sourcing-standards-excerpts.md #<section>`.

## 1. Core objects & terms

- **Purchase order (PO)** — a committed buy from a supplier for a part, with an ordered quantity and
  a **promised (confirmed) delivery date**. A supplier confirmation or ASN can move that date; the
  gap between the promised and the revised date is the **delay**.
- **ASN (advance shipment notice)** — the supplier's notice of what shipped and when it will arrive.
  A pushed ASN is often the first hard signal that a PO is late.
- **On-hand / on-order** — on-hand is physical stock available now; on-order is quantity due in on
  open POs (including the delayed one).
- **Safety stock** — the buffer held to absorb demand/supply variability. Netting below safety stock
  is a **stock-out risk**, even if no single order is formally short.
- **Lead time** — the time from placing/expediting an order to receipt. A **single-source** part with
  a long lead time and no buffer is the highest-risk supply position.

## 2. MRP netting (how a shortage propagates)

MRP nets supply against demand over time: `projected_balance = on_hand + scheduled_receipts −
requirements`. When a scheduled receipt (a PO) moves later, every requirement (work order / sales
order) dated **before** the new receipt date that the remaining on-hand cannot cover becomes a
**shortage**. The shortage is dated to the **first requirement it cannot cover** (the first-impact
date). This is exactly what `shortage_impact_map` computes.

## 3. BOM & where-used

- **BOM (bill of materials)** — the components (and per-unit quantities) that go into a finished
  product. `per_unit` is how many of the short part each finished unit needs.
- **Where-used** — the inverse: given a component, which parent products and open orders consume it.
  Mapping a shortage to impact is a **where-used explosion** across open production and sales orders.

## 4. Supplier master

- Holds, per supplier/part: **single-source** flag, approved **alternate suppliers** (with their
  lead times and qualification status), and delivery **on-time performance** history.
- An **approved substitute** part (form/fit/function equivalent, engineering-approved) can cover a
  shortage without a new qualification; an **unapproved** substitute cannot be used without sign-off.

## 5. Mitigation levers (standard planner playbook)

- **Expedite** — pull the shortfall in faster: premium/air freight, partial shipment, or an alternate
  qualified supplier. Used when a line or a customer order is at risk and no substitute covers it.
- **Substitute** — swap in an approved equivalent part for the shortfall. Cheapest/fastest when one
  exists and is approved with sufficient quantity.
- **Reschedule** — move the affected production/sales orders to the revised availability, or resequence
  the line. Used when buffer/incoming supply covers demand, or as a fallback.

## 6. Boundaries (what the assistant does not do)

The assistant **drafts** the impact map, the mitigation recommendation, the supplier follow-up and the
escalation brief. It does **not** place or expedite a PO, write to the ERP/MRP, change a schedule, or
email the supplier. A buyer/planner reviews and executes — this keeps the commitment and the audit
trail with a human owner.
