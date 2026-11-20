# Disposition Rules — Quality Inspection & Nonconformance
Deterministic rules consumed by tolerance_check.py and defect_grade.py. Engines cite
these by section number; the constants in the engines mirror this document 1:1.

## 1. Severity assignment
| Rule | Condition | Severity |
|---|---|---|
| 1.1 | Out-of-tolerance on `criticality: critical` (including note-derived criticality, e.g. a drawing note marking a surface fatigue-critical) | critical |
| 1.2 | Out-of-tolerance on `criticality: major` | major |
| 1.3 | Out-of-tolerance on `criticality: minor` | minor |
| 1.4 | In tolerance but > 90% of band consumed (MARGINAL_BAND = 0.90) | none — watch-list entry, not a defect |

## 2. Lot incidence
| Rule | Condition | Effect |
|---|---|---|
| 2.1 | Sample incidence > 1.0% (MRB_INCIDENCE_PCT) on critical or major characteristic | disposition escalates to MRB hold |
| 2.2 | Single-part anomaly on minor characteristic | disposition may stay at part level |

## 3. Disposition
| Rule | Condition | Disposition |
|---|---|---|
| 3.1 | Severity critical | hold_for_review — MRB with design authority required |
| 3.2 | Severity major AND (incidence > 1% OR rework not permitted) | hold_for_review |
| 3.3 | Severity major AND rework permitted AND incidence <= 1% | rework |
| 3.4 | Severity minor AND rework permitted | rework |
| 3.5 | Severity minor AND rework not permitted | use_as_is candidate — REQUIRES deviation authorization and QE sign-off; never self-approving |

## 4. Confidence, ambiguity, and document conflicts
| Rule | Condition | Effect |
|---|---|---|
| 4.1 | Any engine confidence < 0.75 (CONFIDENCE_FLOOR) | force hold_for_review + human review flag |
| 4.2 | Incidence within ±0.25 pp of the 1% MRB threshold (BORDERLINE_BAND) | borderline — escalate; do not let the disposition silently flip on one part |
| 4.3 | A CoC/certificate claims conformity for a characteristic the measurements show out of tolerance | MEASUREMENTS GOVERN. Flag doc_conflict, escalate to supplier quality (SCAR candidate), disposition floor = hold_for_review |
| 4.4 | Missing tolerance, unit mismatch, or revision mismatch | block grading; escalate to spec-ingest owner |
