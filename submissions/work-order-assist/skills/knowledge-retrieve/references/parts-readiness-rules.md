# Parts-Readiness Rules — Storeroom Stock & Supersession

Deterministic parts-readiness rules consumed by `parts_readiness.py`. Given the parts a work
order requires (from the SOP/BOM, plus any superseding part surfaced by `similar_work`) and the
parts catalog (on-hand stock, minimum stock, supersession chain, lead time, criticality), these
rules compute a per-part line status and an overall work-order readiness. Cited in contract
payloads as `parts-readiness-rules.md #<section>`.

Grounded in the plant parts catalog and storeroom/MRO practice (`cmms-standards-excerpts.md`).

## 1. Per-part line status

For each required part, look up its catalog row and classify the line:

| Section | Condition | `line_status` |
|---|---|---|
| 1.1 | `on_hand >= required_qty` | `IN_STOCK` |
| 1.2 | `0 < on_hand < required_qty` | `SHORT` |
| 1.3 | `on_hand == 0` **and** the part has a `superseded_by` replacement that is itself in stock (>= required_qty) | `SUPERSEDED_AVAILABLE` — set `effective_part` to the replacement |
| 1.4 | `on_hand == 0` **and** no usable substitute in stock | `OUT`; if the part is flagged `criticality = critical`, escalate to `BLOCKED` |

## 2. Supersession handling

| Section | Condition | Effect |
|---|---|---|
| 2.1 | A required part has a non-empty `superseded_by` value | The obsolete part must **not** be ordered. Redirect procurement to the replacement part and record the supersession on the line note. |
| 2.2 | `similar_work` activated a `superseding_fix` (a fix note recommends a revised part) | Treat the recommended part as the effective part for that line, even if the SOP still lists the old part. Add an escalation to update the SOP so it no longer references a superseded part. |
| 2.3 | The SOP-default part is both **out of stock** and **superseded** by an in-stock replacement | Line is `SUPERSEDED_AVAILABLE`; the work can proceed with the replacement. This is a procurement redirect, not a blocker. |

## 3. Critical-part escalation

| Section | Condition | Effect |
|---|---|---|
| 3.1 | A `critical` part is `OUT` with no substitute in stock | Overall readiness `BLOCKED`; escalate: expedite the critical part; do not schedule the job until it lands. |
| 3.2 | A `critical` part is `SHORT` | Add an escalation to reserve/expedite before scheduling; overall readiness at best `PARTIAL`. |
| 3.3 | On a class-A (critical, non-redundant) asset, any part `SHORT`/`OUT` | Notify the maintenance planner and storeroom lead so the job is expedited (`cmms-standards-excerpts.md` #4). |

## 4. Overall readiness status

Fold the line statuses into one work-order readiness (worst-case wins, in this order):

| Section | Condition | `status` |
|---|---|---|
| 4.1 | Any line `BLOCKED` | `BLOCKED` |
| 4.2 | Else any line `SHORT` or `OUT` | `PARTIAL` |
| 4.3 | Else any line `SUPERSEDED_AVAILABLE` (all others in stock) | `READY_WITH_SUBSTITUTION` |
| 4.4 | Else all lines `IN_STOCK` | `READY` |

Confidence: 0.90 when every required part resolved to a definite catalog row; 0.70 when any
required part was not found in the catalog (add an escalation to confirm the part number).

The readiness status and its blockers travel to `work-order-writeup`, which surfaces them above the
recommended action so a planner never schedules a job that cannot be executed.
