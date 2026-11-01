# Quality Incident & CAPA

Picks up where **Quality Inspection & Nonconformance** leaves off: an NCR is open, and someone
has to take it through root cause to a closed CAPA that will survive an audit.

It reads the incident, complaint and inspection data, establishes root cause with a structured
method, builds corrective *and* preventive actions with mandatory effectiveness checks,
validates closure readiness as an explicit gate, and drafts the 8D report cited to the clause.

## How it works

1. Consumes the NCR payload (including directly from the Quality Inspection plugin).
2. Establishes root cause — Pareto plus a structured why-chain (deterministic).
3. Builds corrective and preventive actions with mandatory effectiveness checks.
4. The governance gate: is this actually ready to close?
5. Drafts the 8D / CAPA report, cited to the clause.

## Example scenario

The supervisor's email carries the pressure: *operator error, retrain, close by Friday.*

The data disagrees. Operator error has four rows — but calibration drift has six, across
**three part numbers and two machines**. And even if operator error ranked first, the rules
reject a human-error root cause when the issue has recurred: recurrence means the system
allowed it, not that someone was careless.

The engine finds a systemic calibration-drift cause traced to a missing recall gate, requires a
preventive action across the affected scope, and refuses to mark the CAPA closure-ready while
verification evidence is outstanding.

A naive CAPA closes on retraining. This one will not.

## What you bring

The open NCR (or the payload handed over from the Quality Inspection plugin), complaint data,
and inspection results.

## Boundaries

Draft-first: the plugin takes an open NCR to *closure readiness*. Nothing is filed and nothing
is closed by the plugin — a quality engineer signs off.
