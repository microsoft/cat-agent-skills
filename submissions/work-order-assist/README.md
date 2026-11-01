# Work Order Assistant

Everything a technician or planner needs for one work order, gathered in one place instead of
across four systems and a filing cabinet.

It pulls the work order and asset context, retrieves the SOPs, OEM manuals and prior fix notes
that actually apply, ranks the most similar past jobs, checks parts readiness against the
storeroom and the supersession table, and drafts clean technician notes or a planner summary
with the next best action.

## How it works

1. Reads the work order and asset context.
2. Retrieves relevant SOPs, OEM manual sections and prior fix notes.
3. Ranks the most similar past work orders (deterministic).
4. Checks parts against the storeroom and supersession table (deterministic).
5. Drafts the technician notes or planner summary, cited.

## Example scenario

Instrument air compressor C-500 — class A, no redundancy — threw the same intake-valve fault
again. The technician is about to do exactly what the SOP says: pull another VK-100 intake
valve and fit it.

Two facts change the answer:

- **History:** the last *three* VK-100 swaps on C-500 all came back. The fault recurred every
  time.
- **A recommended change:** a fix note flags VK-100 as prone to this failure and recommends the
  superseding VK-200.

The SOP is not wrong, it is just out of date. Following it books a fourth repeat visit.

## What you bring

The work order, the asset register, work-order history, a parts catalogue and usage data, plus
whatever SOPs and OEM manual excerpts you have.

## Boundaries

Draft-first and document-grounded. No auto-scheduling and no CMMS write-back — a planner still
owns the schedule.
