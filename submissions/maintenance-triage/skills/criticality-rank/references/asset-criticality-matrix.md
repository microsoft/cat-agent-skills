# Asset Criticality Matrix — Priority & Downtime Weighting

Deterministic prioritization rules consumed by `criticality_score.py`. Cited in contract
payloads as `asset-criticality-matrix.md #<section>`. Grounded in RCM / ISO 55000 asset-management
practice (`rcm-iso55000-excerpts.md`).

## 1. Asset criticality classes

| Class | Meaning | Examples |
|---|---|---|
| A | Critical — failure stops production, breaches safety/environmental limits, or has no redundancy | Boiler feed pump, reactor cooling, main line drive |
| B | Essential — failure degrades output or has limited redundancy | Cooling-water pump (duty/standby pair), transfer pump |
| C | Non-critical — spared, offline, or non-production | Sump pump, utility fan, bench equipment |

## 2. Base priority by class

| Section | Class | Base priority |
|---|---|---|
| 2.A | A | P2 |
| 2.B | B | P3 |
| 2.C | C | P4 |

Base priority is the **starting point**; the modifiers in section 3 move it up (never below P1,
never above P4).

## 3. Priority modifiers (deterministic, additive on a numeric score)

Priority score starts from the base level's numeric value (P1=4, P2=3, P3=2, P4=1) and is adjusted:

| Section | Condition | Score effect |
|---|---|---|
| 3.1 | Downtime cost > $10,000/hr | +1.0 |
| 3.2 | Downtime cost $2,000–$10,000/hr | +0.5 |
| 3.3 | Downtime cost < $2,000/hr | +0.0 |
| 3.4 | Repeat-failure promotion fired in fault_rank (recurring failure, rules #3.1) | +1.0 and force minimum **P2** |
| 3.5 | Top failure mode carries secondary-damage risk (`bearing_degradation`, `coupling_misalignment` — seizure/collateral risk per CP-200 §6.3) on a Class A asset | +0.5 |
| 3.6 | No redundancy recorded for the asset (single unit, no installed spare) | +0.5 |

Final level = round the adjusted score to the nearest priority band (>=3.5 → P1, >=2.5 → P2,
>=1.5 → P3, else P4).

## 4. Response targets

| Section | Level | Response target |
|---|---|---|
| 4.1 | P1 | Immediate — respond within 1 hour; escalate to shift supervisor now |
| 4.2 | P2 | Same shift — respond within 8 hours |
| 4.3 | P3 | Planned — schedule within 72 hours |
| 4.4 | P4 | Next PM window |

## 5. Downtime cost estimate

`downtime_cost_estimate = downtime_cost_per_hr x expected_repair_hours`, where expected repair
hours come from the recommended corrective action's standard job time (default 4 h if unknown).
If `downtime_cost_per_hr` is missing, leave the estimate `null` and add an escalation to obtain
the asset's costing (do not guess).

## 6. Escalation

| Section | Condition | Effect |
|---|---|---|
| 6.1 | Final level P1 | Add escalation: notify shift supervisor + reliability engineer immediately. |
| 6.2 | Repeat-failure promotion fired (rules #3.4) | Add escalation: open an RCA; the symptomatic fix is masking a root cause. |
| 6.3 | Missing criticality class or downtime cost | Do not assume a class. Add escalation to complete the asset register; score on what is known and flag confidence. |
