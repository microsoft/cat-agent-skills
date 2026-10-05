# HIPAA Safe Harbor — reference (as implemented by this skill)

The **Safe Harbor** method (45 CFR §164.514(b)(2)) de-identifies protected
health information by removing 18 categories of identifiers of the individual
and of their relatives, employers, and household members. This file documents
how each is handled by `scripts/deidentify.py`, and where human review is still
required.

> This is an engineering reference, not legal advice. Safe Harbor also requires
> that the covered entity has no actual knowledge the residual information could
> identify the individual. Only a qualified human can make that determination.

## The 18 identifiers

| # | Identifier | Handling | Confidence |
|---|------------|----------|-----------|
| 1 | Names | Titled ("Dr. X") + labelled ("Patient: X") patterns, plus a bundled offline name lexicon for bare names; spaCy used only if already present | Review |
| 2 | Geographic subdivisions < state (street, city, county, ZIP) | Street address + "city ST" (comma/ZIP-anchored) via regex; ZIP truncated to 3 digits, restricted prefixes → 000 | High / Partial |
| 3 | Dates (except year) directly related to an individual; ages 90+ | Dates → year only; ages 90+ → `90+` | High |
| 4 | Telephone numbers | Regex | High |
| 5 | Fax numbers | Regex (labelled) | High |
| 6 | Email addresses | Regex | High |
| 7 | Social Security numbers | Regex | High |
| 8 | Medical record numbers | Regex (labelled MRN / "medical record no.") | High |
| 9 | Health plan beneficiary numbers | Regex (labelled member/beneficiary) | High |
| 10 | Account numbers | Regex (labelled account/policy) | High |
| 11 | Certificate / license numbers | Regex (labelled license/cert/DEA/NPI) | High |
| 12 | Vehicle identifiers (VIN, plates) | Regex (VIN) | High |
| 13 | Device identifiers / serial numbers | Regex (labelled serial/device) | High |
| 14 | Web URLs | Regex | High |
| 15 | IP addresses | Regex | High |
| 16 | Biometric identifiers | **Out of scope** (not text) | — |
| 17 | Full-face photographs | **Out of scope** (not text) | — |
| 18 | Any other unique identifying number, characteristic, or code | Labelled numeric IDs caught; novel patterns need human review | Partial |

## ZIP code rule

Keep only the **first three digits** of a ZIP, and set them to **000** for the
restricted 3-digit prefixes whose population is 20,000 or fewer:

`036, 059, 063, 102, 203, 556, 692, 790, 821, 823, 830, 831, 878, 879, 884, 890, 893`

## Dates & ages

- Remove all date elements more specific than the **year** when tied to an
  individual (birth, admission, discharge, death, service dates).
- Ages **≤ 89** may be retained; all ages/elements indicating **90 or older**
  must be aggregated into a single "90+" category.

## Safe Harbor vs Limited Data Set

A **Limited Data Set** (§164.514(e)) is *not* fully de-identified but may be
used for research, public health, or operations under a data use agreement. It
**may retain**: dates (admission, discharge, service, birth, death) and
**city, state, and full ZIP** — but must still exclude names, street address,
phone/fax, email, SSN, MRN, account/health-plan numbers, certificate/license
numbers, vehicle/device identifiers, URLs, IPs, and biometrics/photos.

Run `--mode limited` to keep dates and geography while stripping the direct
identifiers.

## Residual-risk reminders

- Rare diagnoses, quasi-identifier combinations, and free-text context can
  re-identify even after the 18 categories are removed. Human review required.
- Name recall depends on the bundled lexicon plus title/label cues — it runs
  fully offline (no `pip`/network needed), but names outside the lexicon can be
  missed. Extend `assets/name_lexicon.txt` for your population and review the
  `needs_human_review` list every time.
