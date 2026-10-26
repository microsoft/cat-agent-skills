# Similar-Work Ranking Rules — CMMS Work-Order History

Deterministic similarity rules consumed by `similar_work.py`. Given the current work order's
signals (asset, component, issue keywords, required parts) and the asset's prior work orders,
these rules score how similar each prior work order is, detect a **recurring failure**, and surface
a **superseding fix** recommended by a prior fix note. Cited in contract payloads as
`similar-work-rules.md #<section>`.

Grounded in CMMS/EAM work-order records and site reliability practice
(`cmms-standards-excerpts.md`). This is a **retrieval-and-ranking aid**, not predictive
maintenance — it reasons over recorded past work, never over a forecast.

## 1. Signal vocabulary

Issue keywords (normalized names the intake maps free text onto):
`oil_leak`, `high_temp`, `seal_weep`, `bearing_noise`, `low_discharge_pressure`, `unloading`,
`short_cycling`, `valve_fault`, `overheating`, `vibration`, `low_flow`, `trip`, `leak`.

Signals compared between the current WO and each prior WO:
- **asset** — same `asset_id` (strongest) or same `asset_class`.
- **component** — same sub-component (e.g. `gearbox`, `intake_valve`, `mechanical_seal`).
- **issue keywords** — overlap between the two keyword sets.
- **parts** — overlap between required parts and the parts the prior WO consumed.

## 2. Similarity scoring (deterministic)

Each prior work order earns a raw score = weighted sum of matched signals:

| Section | Signal | Weight |
|---|---|---|
| 2.1 | Same `asset_id` | 4 |
| 2.2 | Same `asset_class` (when not the same asset) | 2 |
| 2.3 | Same component | 3 |
| 2.4 | Each shared issue keyword | 2 |
| 2.5 | Each shared part number | 2 |

`similarity_score` is the work order's share of the total raw score across all scored prior WOs
(rounded to 3 dp). Prior WOs are ranked by raw score; ties break by most-recent date, then by
work-order ID. A prior WO with raw score 0 (no shared signal) is dropped from `similar_work[]`.

Per-item confidence starts at a base of 0.60 and gains +0.06 for each distinct matched signal
type (asset, component, keyword-overlap, parts-overlap), capped at 0.97.

## 3. Recurring-failure and superseding-fix rules

The rules that separate real work-order assembly from "do what the SOP says again":

| Section | Condition | Effect |
|---|---|---|
| 3.1 | The **same default remedy** (the SOP default action / same parts) recurs **>= 3 times** on this asset for this issue **AND** the recorded outcome of those prior WOs is `recurred` or `reopened` | Set `history.repeat_promotion = true` and mark those matches `repeat_failure`. The SOP-default fix is **not resolving the problem**; do not simply repeat it. Raise a recurring-failure escalation (route to reliability engineering for RCA). |
| 3.2 | Same remedy recurs **2 times** (< 3) with a mixed outcome | Note it as evidence and raise the matched item's confidence by +0.05; do not force a repeat-failure promotion. |
| 3.3 | A retrieved **prior fix note** carries `recommended_change = true` with a `superseding_part` (a revised/upgraded part that resolved the identical issue elsewhere) | Activate `superseding_fix`: recommend the superseding part **over** the SOP-default part. The drafted next-best action becomes the superseding remedy, citing the fix-note ID. |
| 3.4 | Repeat-failure (3.1) fired **and** a superseding fix (3.3) exists | This is the high-value case: the recurring SOP-default fix is superseded by a better remedy. Both the escalation and the superseding recommendation are carried forward to parts-readiness and the write-up. |

## 4. Confidence and escalation

| Section | Condition | Effect |
|---|---|---|
| 4.1 | Top similar match confidence **< 0.75** (floor) | Do not assert "this is the same as WO-x." Return the ranked list, add `escalations[]`, and ask the planner to confirm the closest prior work manually. |
| 4.2 | No prior work order shares any signal (empty `similar_work[]`) | First-time work on this asset/issue: proceed from the SOP and manual alone, and note in `escalations[]` that no comparable history was found. |
| 4.3 | A repeat-failure was promoted (3.1) | Always add an escalation: recurring failure on this asset — open a root-cause analysis before repeating the default fix. |
