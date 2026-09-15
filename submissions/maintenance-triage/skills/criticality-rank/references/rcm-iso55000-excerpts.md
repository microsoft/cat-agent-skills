# RCM / ISO 55000 — Grounding Excerpts

Condensed, paraphrased reference points that ground Maintenance Triage decisions. Cited in
contract payloads and the drafted work-order update. These are practice summaries for demo
grounding, not a substitute for the standards themselves.

## RCM-1 — Failure modes, not just symptoms
Reliability-Centered Maintenance asks *what function is lost, and by what failure mode*.
A tripped overload is a **functional symptom**; the failure mode is the physical mechanism that
caused it (bearing wear, misalignment). Triage must name the failure mode, not just clear the symptom.

## RCM-2 — Consequence-based prioritization
Work is prioritized by the **consequence of failure** (safety, environmental, operational,
economic), not by how loud the alarm is. This is why asset criticality class and downtime cost —
not symptom severity alone — drive priority (`asset-criticality-matrix.md`).

## RCM-3 — Repeat failures signal an unaddressed root cause
Recurring failures on the same asset indicate the corrective action treated a symptom, not the
cause. RCM routes repeat failures to root-cause analysis (RCA) rather than repeating the fix
(`failure-mode-library.md #3`).

## ISO-55000-1 — Value and line-of-sight
Asset management aligns maintenance decisions to organizational value. A critical asset's
downtime cost and risk justify a faster response and, where a root cause is masked, an RCA —
even when the immediate fix looks cheap.

## ISO-55000-2 — Risk-based decision making
Decisions balance cost, risk and performance. Prioritization weights (class x downtime cost x
repeat-failure risk) are the deterministic expression of this principle.

## ISO-55000-3 — Documented, auditable decisions
Every maintenance decision should be traceable to evidence. This is why each ranked cause and
priority carries a `confidence`, a `source`, and a `citation` on the contract.

## Boundary note
Maintenance Triage is **document- and history-grounded diagnosis**. It is **not** condition
monitoring or predictive maintenance (historian/vibration-trend analytics). Predictive is the
Wave 3 upgrade; historian input here is optional context only.
