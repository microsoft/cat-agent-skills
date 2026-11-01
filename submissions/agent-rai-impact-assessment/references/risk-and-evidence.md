# Risk and evidence method

Use supplied organizational criteria first. The following is a qualitative fallback for this skill, not a legal classification or an official framework scoring system.

## Keep three judgments separate

1. **Consequence severity:** describe scale, duration, reversibility, and who bears the impact. High means potentially serious or hard-to-reverse harm, such as a major access/privacy breach or consequential loss of opportunity. Medium means material but generally remediable harm or repeated burdens. Low means limited, readily corrected impact. Explain context; a small affected population does not make severity low.
2. **Plausibility/exposure:** record the evidenced or plausible path, frequency of exposure if known, and preconditions. Use Unknown when evidence cannot support an estimate. Do not derive probability from a model's confidence or assign a low likelihood merely because no incidents were reported.
3. **Evidence confidence:** distinguish directly observed, design-supported, and hypothetical reasoning. State what evidence could strengthen or refute it. Missing evidence is not a confirmed failure, but it can prevent a release recommendation.

Do not multiply ordinal values into a precise-looking risk number.

## Control status

- **Evidenced:** implementation or test evidence supports the control within a stated scope and version.
- **Claimed:** the design or owner says it exists; enforcement/effectiveness has not been shown.
- **Proposed:** recommended work, not an implemented control.
- **Not established:** supplied material does not show whether the control exists.

Describe the exposure before the relevant controls and the risk remaining with evidenced controls. For proposed controls, use "expected residual risk, contingent on validation". A passing test limits uncertainty for that test's conditions, not every possible input or user group.

Separate accepting risk from analyzing it. A review board recommendation, an organizational exception, and legal permission are different things.

## Prioritization heuristic

Combine the judgments with this table, per harm, using the status of the control that actually interrupts the chain. It is this skill's heuristic for consistency, not a standard.

| Severity | Key control status | Recommendation |
| --- | --- | --- |
| High | Not established or Claimed | Collect evidence before any consequential use. A bounded pilot is defensible only with that pathway disabled or fully human-executed. |
| High | Evidenced, plausibility Unknown | Bounded pilot with monitoring aimed at this pathway and an explicit stop condition; do not scale until exposure data exists. |
| High | Evidenced, plausibility shown low | Present for accountable release review with the residual risk and its evidence stated. |
| Medium | Not established or Claimed | Pilot may proceed if the verification gate is scheduled before scale-up; treat the gate as a release blocker. |
| Medium | Evidenced | Release review with a monitoring signal and owner named. |
| Low | Any | Record, monitor if cheap, no gate required. |

Adjustments: a sensitive-use flag moves any row to accountable review regardless of severity. Low evidence confidence moves the recommendation one step toward collecting evidence. Unknown plausibility never lowers a row. A severe plausible scenario with an unverified critical control warrants investigation before consequential use even when other tests pass.

## Evaluation design

For each material harm, specify:

- A case tied to the triggering condition and affected party; include failure/recovery and relevant user variation.
- The expected observable behavior, including action state and downstream effects.
- A measurable pass criterion and its authority: supplied requirement or proposed threshold pending agreement.
- Evidence to retain, such as redacted action traces, result counts, and versioned test configuration.
- The owner role and the action if the gate fails.

Test the full system where the harm depends on tools or human decisions; model-answer quality alone cannot validate an action authorization control. Security tests use authorized environments and harmless fixtures.

Where statistical evaluation is relevant, request workload coverage and sample sizes; explain uncertainty and class imbalance. Zero failures in a small sample is not proof of zero failure probability. Synthetic fairness cases can expose problems but do not establish real-world parity or replace stakeholder input.

## Monitoring and reassessment

Select harm-specific signals rather than collecting every conversation: erroneous actions, reversals, unanswered escalations, correction delays, unsupported claims, or disproportionate failure patterns where appropriate. Define an owner, review cadence, alert threshold if agreed, and response. Keep collection proportional to privacy needs.

Reassess when authority, users, languages, data boundaries, models, tools, memory, or material operating conditions change, or when complaints/incidents undermine assumptions. Preserve the prior assessment and identify which conclusions changed.
