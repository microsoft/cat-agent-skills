# Store Task & Promotion Execution

For the store manager or field operations lead who receives an HQ campaign pack built for
hundreds of stores and has to make it true for *this* one — before launch day, not after the
mispriced shelf is photographed.

It ingests the pack, price file, planogram and task list, maps the requirements to the store's
format and cluster, tests completeness, flags pricing and signage conflicts deterministically,
ranks exceptions by revenue impact, and drafts the readiness checklist, shift brief and
exception list.

## How it works

1. Reads the campaign pack, price file, planogram and task list.
2. Maps requirements to this store's format and cluster.
3. Tests completeness; flags pricing and signage conflicts (deterministic).
4. Ranks what the store cannot fix, by revenue at stake.
5. Drafts the readiness checklist and shift brief in store language.

## Example scenario

*"Everything shipped, reporting READY Monday."* The check finds what the confidence hides:

- An end-cap requirement calls for a fixture **the small format does not carry** — a conflict
  the store cannot fix locally, so it escalates to HQ.
- A **price conflict on the hero SKU**: the promotional price is *higher* than the current
  shelf price, so executing the change would raise the price during the promotion. Blocked,
  and ranked first at roughly 340 units a week at stake.
- Two signage kits were never received while their tasks sit open.

Ranking by revenue rather than by count is what puts the pricing trap at the top.

## What you bring

Promotion briefs and campaign packs, price and price-change files, planograms and signage
lists, launch calendars, store task lists, and the store master with cluster definitions.

## Boundaries

It does not change POS prices, planograms, labour schedules or campaign funding. It produces
the readiness pack and the exception list; the store and HQ act on them.
