# Maintenance Triage

For the maintenance technician, reliability engineer or shift supervisor holding a fault that
needs a next action right now.

It reads the fault note, alarm codes and asset history, ranks the likely failure modes against
OEM manuals and past work orders, prioritises by asset criticality and downtime cost, and
drafts the work-order update with a recommended action. Documents are enough — a historian
feed is optional.

## How it works

1. Reads fault notes, alarm and event logs, and the asset register.
2. Pulls prior work orders, similar failures, and the relevant OEM manual sections.
3. Ranks likely failure modes against symptoms, manual and history (deterministic).
4. Prioritises by asset criticality × downtime cost (deterministic).
5. Drafts the work-order update and recommended action, cited.

Confidence, provenance and citations stay attached to findings throughout the workflow.

## Example scenario

Boiler feed water pump P-201 — criticality class A, $12,000/hour, no redundancy — "tripped on
overload again." The technician is about to do what worked the last three times: reset the
overload relay and move on. The alarm in front of them and the cheap fix agree.

Two facts change the answer:

- **History:** three motor-overload resets in 78 days.
- **A new signal:** a vibration alarm appeared for the first time this event, and vibration has
  been climbing across the quarter.

A repeat symptomatic fix is a signal, not a solution. The engine promotes bearing degradation
over the easy electrical reset and escalates the priority to P1.

## What you bring

The fault note or ticket, an alarm/event log, the asset register with criticality, and work-order
history. OEM manual excerpts help. Historian data is optional.

## Boundaries

Draft-first: the recommended action is a recommendation pending planner or supervisor approval,
and there is no CMMS write-back. This triages the fault in front of you — it does not forecast
future failures or optimise PM intervals.
