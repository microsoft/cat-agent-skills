# Failure-Mode Library — Rotating Equipment (Centrifugal Pumps)

Deterministic failure-mode signatures consumed by `fault_rank.py`. Each mode lists the
symptom and alarm-code signals that point to it, its typical corrective action, and the OEM
manual section that grounds it. Cited in contract payloads as `failure-mode-library.md #<section>`.

Grounded in OEM Pump Manual **CP-200** (troubleshooting chapter) and RCM practice
(`rcm-iso55000-excerpts.md`). This is a **diagnostic aid, not predictive maintenance** —
it reasons over reported symptoms and history, never over live vibration trending.

## 1. Signal vocabulary

Symptoms (normalized names the intake maps free text onto):
`high_vibration`, `bearing_temp_high`, `grinding_noise`, `reduced_flow`, `overload_trip`,
`motor_hot`, `seal_leak`, `low_suction_pressure`, `noise_intermittent`.

Alarm codes (from PLC/SCADA export):
`VIB-HH` (vibration high-high), `TEMP-BRG-H` (bearing temp high), `OL-TRIP` (motor overload
trip), `FLOW-LO` (low flow), `SEAL-LEAK` (seal leak detected), `SUCT-LO` (low suction).

## 2. Failure modes and signatures

| Section | Failure mode | Signature symptoms (weight) | Signature alarms (weight) | Corrective action | Manual |
|---|---|---|---|---|---|
| 2.1 | `bearing_degradation` | high_vibration(3), bearing_temp_high(3), grinding_noise(2) | VIB-HH(3), TEMP-BRG-H(3) | Replace pump bearings; verify lubrication and shaft alignment | CP-200 §6.3 |
| 2.2 | `coupling_misalignment` | high_vibration(3), overload_trip(2), bearing_temp_high(1), grinding_noise(1) | VIB-HH(2), OL-TRIP(2) | Laser-align pump/motor coupling; inspect coupling element | CP-200 §5.2 |
| 2.3 | `motor_overload_electrical` | overload_trip(3), motor_hot(2) | OL-TRIP(3) | Reset overload relay; verify motor current draw and supply voltage | CP-200 §7.1 |
| 2.4 | `mechanical_seal_failure` | seal_leak(3), reduced_flow(1) | SEAL-LEAK(3) | Replace mechanical seal; inspect shaft sleeve | CP-200 §6.1 |
| 2.5 | `impeller_cavitation` | reduced_flow(3), grinding_noise(2), high_vibration(1), low_suction_pressure(2) | FLOW-LO(3), SUCT-LO(2) | Correct suction/NPSH condition; inspect impeller for cavitation erosion | CP-200 §6.4 |

Scoring (deterministic): a mode's raw score is the weighted sum of the observed signals that
appear in its signature. `match_score` is the mode's share of total raw score across all
modes. Ranked by raw score, ties broken by the section order above.

## 3. Repeat-failure inference (root-cause promotion)

The rule that separates real triage from "reset it again":

| Section | Condition | Effect |
|---|---|---|
| 3.1 | A **symptomatic** fix (overload-relay reset, breaker reset, `motor_overload_electrical`) recurs **>= 3 times** in the history window **AND** any mechanical signal (`high_vibration`, `bearing_temp_high`, `VIB-HH`, `TEMP-BRG-H`) is present | Treat the symptomatic mode as a **symptom, not a root cause**. Promote the corroborated mechanical root-cause mode (`bearing_degradation` or `coupling_misalignment`) to rank 1, boost its confidence by +0.20 (cap 0.97), and record the repeat pattern as evidence. |
| 3.2 | Same failure mode recurs >= 2 times but < 3 in the window | Add it to evidence and raise the mode's confidence by +0.08; do not force promotion. |
| 3.3 | Repeat-failure promotion fired (3.1) | Add an escalation: recurring failure — route to reliability engineering for RCA. |

## 4. Confidence and escalation

| Section | Condition | Effect |
|---|---|---|
| 4.1 | Top candidate confidence **< 0.75** (floor) | Do not assert a single cause. Emit the ranked list, add `escalations[]`, flag for a human diagnostician. |
| 4.2 | Top two candidates within **0.08** match_score of each other and no history tiebreaker | Ambiguous — return both, add escalation "differential diagnosis: <a> vs <b>", request an additional check named in the manual. |
| 4.3 | No known signal matched (unrecognized symptoms/alarms) | `not_diagnosed`; escalate to the OEM manual / vendor support; never guess a fix. |
