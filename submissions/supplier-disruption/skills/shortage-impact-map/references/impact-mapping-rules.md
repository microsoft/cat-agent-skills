# Shortage → Impact Mapping Rules — Where-Used Explosion & Coverage

Deterministic mapping rules consumed by `shortage_impact_map.py`. Given the disruption (the short/
delayed part, the revised delivery date and the ERP supply position) and the BOM/where-used open
orders, these rules explode the shortage to the affected **products, production lines and open
orders**, compute the **quantity and date at risk** per order, and roll up an **impact summary**
(worst severity + first-impact date). Cited in contract payloads as `impact-mapping-rules.md
#<section>`.

Grounded in **ERP/MRP practice** (`sourcing-standards-excerpts.md`) — MRP netting, safety stock,
lead time, BOM/where-used. This is a **mapping aid** that applies netting logic to the facts on the
intake; a planner's judgment always governs the final commitment.

## 1. Inputs

The engine reads, from the contract payload:
- `supply.on_hand`, `supply.on_order` (the quantity on the delayed PO), `supply.safety_stock`.
- `promised_date`, `revised_date` (the delay).
- `retrieved.open_orders[]` — each open production/sales order that consumes the part, with
  `finished_qty`, `per_unit` (BOM quantity of the short part per finished unit), `need_by`,
  `order_type` (`production`/`sales`), `line`, `product`, `customer`, `high_runner`.

## 2. Usable stock and the incoming (late) PO

- **Usable on-hand** = `supply.on_hand`. This is the pool that covers demand **before** the delayed
  PO lands.
- The **delayed PO** (`supply.on_order`) is assumed to arrive on `revised_date`. Any order whose
  `need_by` is **on or after** `revised_date` can be covered by the incoming PO (the delay does not
  hurt it). Any order whose `need_by` is **before** `revised_date` can only be covered by usable
  on-hand.
- **Safety stock** is a floor, not free supply. If the demand due **before** the delayed PO lands
  (orders with `need_by < revised_date`) drives usable on-hand below `supply.safety_stock`, set
  `impact_summary.below_safety_stock = true` (a stock-out risk even where no order is formally short).

## 3. Per-order coverage test (netting)

Sort `open_orders` by `need_by` ascending and walk them, accumulating demand:

```
demand(order)   = finished_qty * per_unit
running_demand += demand(order)
covered_by_stock    = running_demand <= usable_on_hand
arrives_in_time     = revised_date is set AND need_by >= revised_date
```

| Section | Condition | `status` | `qty_at_risk` |
|---|---|---|---|
| 3.1 | `covered_by_stock` | `covered` | 0 |
| 3.2 | not covered by stock **and** `arrives_in_time` | `covered_by_incoming` | 0 |
| 3.3 | not covered by stock **and** not in time **and** `order_type = sales` | `late_shipment` | `min(demand, running_demand − usable_on_hand)` |
| 3.4 | not covered by stock **and** not in time **and** `high_runner = true` | `line_down` | `min(demand, running_demand − usable_on_hand)` |
| 3.5 | not covered by stock **and** not in time (other) | `at_risk` | `min(demand, running_demand − usable_on_hand)` |

## 4. Per-order severity

| Section | `status` | `severity` |
|---|---|---|
| 4.1 | `covered` | `none` |
| 4.2 | `covered_by_incoming` | `low` |
| 4.3 | `at_risk` (production, not a high-runner) | `medium` |
| 4.4 | `line_down` (high-runner production line stops) | `high` |
| 4.5 | `late_shipment` (a customer sales order goes late) | `critical` |

## 5. First-impact date

`impact_summary.first_impact_date` = the earliest `need_by` among all orders whose `status` is
`at_risk`, `line_down` or `late_shipment` (the first day the shortage actually bites). Null when
every order is `covered`/`covered_by_incoming`.

## 6. Impact summary (roll-up)

Fold the per-order rows into one summary (most-severe wins):

| Field | Value |
|---|---|
| `worst_severity` | the maximum per-order severity on the ladder `none < low < medium < high < critical`. |
| `first_impact_date` | Sec 5. |
| `affected_products` | distinct `product` among impacted orders (status not `covered`). |
| `affected_orders` | count of impacted orders (status not `covered`/`covered_by_incoming`). |
| `affected_sales_orders` | count of impacted orders with `order_type = sales`. |
| `total_qty_at_risk` | sum of `qty_at_risk`. |
| `below_safety_stock` | Sec 2. |

## 7. Confidence & governance

| Section | Condition | Effect |
|---|---|---|
| 7.1 | `open_orders` present **and** `supply.on_hand`/`revised_date` populated | confidence `0.92`. |
| 7.2 | Open orders or the revised date missing/ambiguous | confidence `0.7`; add an escalation to confirm the MRP position before committing a mitigation. |
| 7.3 | A `late_shipment` (customer order at risk) is detected | It **cannot be silently dropped**; it drives the mitigation and escalation in `mitigation_recommend`. |

The impact map + summary travel to `mitigation_recommend`, which chooses the mitigation
(expedite / substitute / reschedule) and computes the escalation tier and owner notifications.
