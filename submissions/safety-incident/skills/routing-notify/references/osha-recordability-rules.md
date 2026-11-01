# OSHA Recordability & Severity Rules — Incident Classification

Deterministic classification rules consumed by `recordability_classify.py`. Given the structured
incident intake (incident type, injury nature/body part, treatment given, outcome, days away),
these rules assign a **severity tier**, a **near-miss** flag, an **OSHA recordability**
determination (with the OSHA 300 column), and a **reportability** determination (with the
regulatory clock). Cited in contract payloads as `osha-recordability-rules.md #<section>`.

Grounded in **OSHA 29 CFR 1904** (recording & reporting occupational injuries and illnesses) and
`ehs-policy-excerpts.md`. This is a **classification aid** that applies published criteria to the
facts on the intake; a physician's or EHS manager's professional judgment always governs the final
record.

## 1. Near-miss vs. injury/illness

| Section | Condition | Effect |
|---|---|---|
| 1.1 | `incident_type = near_miss`, **or** there is no injury/illness and no property/environmental loss | `near_miss = true`. A near miss is **not** OSHA recordable, but it is logged and investigated (leading indicator). |
| 1.2 | An employee sustained an injury or illness (any `body_part` + `nature`) | `near_miss = false`; proceed to the recordability test (Sec 2-3). |

## 2. First aid vs. medical treatment (the recordability hinge)

OSHA **1904.7(b)(5)** — an injury treated **only** by first aid is **not** recordable. Treatment
beyond first aid **is** medical treatment and makes an otherwise-qualifying case recordable.

| Section | `treatment_given` | Meaning |
|---|---|---|
| 2.1 | `none` or `first_aid` | First aid only (bandage, cleaning, non-prescription meds at non-prescription strength, hot/cold therapy, etc.). **Not** recordable on treatment grounds. |
| 2.2 | `medical_treatment` | Treatment beyond first aid (sutures, prescription meds, physical therapy, etc.). **Recordable.** |
| 2.3 | `hospitalization` | In-patient hospitalization. **Recordable** and also **reportable** (Sec 4). |

## 3. Recordability determination + OSHA 300 column

A case is **recordable** if `near_miss = false` **and** any of the following is true:
death; days away from work; restricted work or job transfer; medical treatment beyond first aid;
loss of consciousness; or a significant injury/illness diagnosed by a physician.

Set `recordable.value` and the OSHA 300 classification column (most-severe applicable wins):

| Section | Condition | `recordable.value` | `osha_300_column` |
|---|---|---|---|
| 3.1 | `outcome = fatality` | true | `G` (Death) |
| 3.2 | `outcome = in_patient_hospitalization`/`amputation`/`loss_of_eye`, or `days_away > 0` | true | `H` (Days away from work) |
| 3.3 | `outcome = restricted_duty`/`job_transfer` (and not 3.1/3.2) | true | `I` (Job transfer or restriction) |
| 3.4 | `treatment_given` in {`medical_treatment`,`hospitalization`} with no days-away/restriction | true | `J` (Other recordable cases) |
| 3.5 | `near_miss = true`, **or** `treatment_given` in {`none`,`first_aid`} **and** `outcome = none` | false | `` (blank — not recorded) |

## 4. Reportability to OSHA (1904.39) — the regulatory clock

Severe events must be **reported to OSHA** on a hard clock, independent of recordability:

| Section | `outcome` | `reportable.value` | `type` | `deadline_hours` |
|---|---|---|---|---|
| 4.1 | `fatality` | true | `fatality` | **8** |
| 4.2 | `in_patient_hospitalization` | true | `in_patient_hospitalization` | **24** |
| 4.3 | `amputation` | true | `amputation` | **24** |
| 4.4 | `loss_of_eye` | true | `loss_of_eye` | **24** |
| 4.5 | anything else | false | `none` | `null` |

The clock starts at the **time the event occurred / became known** (`occurred_at`). The
`routing_notify` engine turns a reportable determination into a `regulatory_clock` with a computed
`due_by`.

## 5. Severity tier

Fold the determination into a single severity (most-severe wins):

| Section | Condition | `severity` |
|---|---|---|
| 5.1 | `reportable.value = true` (fatality/hospitalization/amputation/eye) | `critical` |
| 5.2 | Recordable **and** `outcome = days_away` / `days_away > 0` | `high` |
| 5.3 | Recordable (medical treatment or restricted/transfer), not 5.1/5.2 | `medium` |
| 5.4 | Near-miss or first-aid-only | `low` |

## 6. Confidence & governance

| Section | Condition | Effect |
|---|---|---|
| 6.1 | `treatment_given` **and** `outcome` are both present on the intake | confidence `0.92`. |
| 6.2 | Either field missing/ambiguous | confidence `0.75`; add an escalation to confirm the treatment/outcome with the treating clinician before the record is finalized. |
| 6.3 | A recordable or reportable determination fires | It **cannot be silently downgraded** to first-aid. Any request to reclassify downward is surfaced as an open item for EHS-manager sign-off (audit trail intact). |

The classification (severity, near-miss, recordable + column, reportable + clock) travels to
`routing-notify`, which assigns the investigator, builds the notification list, and starts any
regulatory clock.
