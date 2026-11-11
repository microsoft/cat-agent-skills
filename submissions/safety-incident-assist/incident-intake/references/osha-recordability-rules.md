# OSHA Recording & Reporting — candidate rules

**EHS REVIEW REQUIRED / COWORK RE-EVAL PENDING — 2.0.0-rc.5.**
This is a draft decision aid, not an approved EHS policy or comprehensive regulatory engine.
Inherited source states OSHA 1904.7 and 1904.39 were read on 2026-10-02; this candidate has not reverified them. State-plan requirements and special
recording criteria need human review. The bundled raw PDF excerpts are immutable, incomplete
synthetic demo evidence, not authoritative interpretations; this candidate supersedes their
overbroad "first aid is not recordable" and unconditional hospitalization reporting summaries.

## 1. Near-miss vs injury

1.1 A near miss requires explicit near_miss type, cited absence_confirmed=true and a complete no-injury screen (no treatment/outcome/days/diagnosis/LOC evidence). Missing facts never establish absence.
1.2 Injury evidence combined with near_miss/property/environmental is a contradiction:
near_miss and recordability are undetermined, with review reasons. No label overrides evidence.
Property/environmental events are not automatically near misses.

## 2. Treatment and evidence

2.1 `none`/`first_aid` alone do NOT establish nonrecordability.
2.2 `medical_treatment` is a positive criterion only with cited facts and established recording
applicability. Distinguish clinical examination/diagnostic testing from medical treatment.
2.3 `hospitalization` alone does NOT prove medical treatment, days away, or reportability.
The actual treatment, formal admission for care, timing and reporting exclusions require review.

## 3. Recording criteria (1904.7)

The engine requires cited work-relatedness, new-case status, recordkeeping coverage, federal OSHA
scope and cited treatment/outcome facts. Missing or conflicting material facts yield
`recordable.value=null`, not false. Explicit non-federal/unknown applicability is routed to review.

| Section | Positive criterion | OSHA 300 column |
|---|---|---|
| 3.1 | Fatality | G — death |
| 3.2 | Positive days_away, or supported days-away outcome | H — days away |
| 3.3 | Restricted duty or job transfer | I — restriction/transfer |
| 3.4 | Medical treatment, loss of consciousness, physician/PLHCP-diagnosed significant injury/illness | J — other |
| 3.5 | Complete cited negative screen, zero days, no outcome, none/first aid | Blank — draft negative |

Most-severe supported column wins. Severe outcome alone does not imply H.
Recognized significant diagnoses: fracture, cracked bone, punctured eardrum, cancer and chronic
irreversible disease, each requiring diagnosed_by=physician_or_plhcp and diagnosis_citation.
Other/unknown diagnoses require clarification. Fracture and days-away criteria cannot be
overridden by first aid. The negative screen requires loss_of_consciousness=false,
significant_diagnosis=none, and other_recording_criteria_reviewed=true; these are evidence claims,
not authenticated clinical decisions. Never invent negative evidence to obtain a low classification.

## 4. Reporting (1904.39) — unresolved release blocker

Candidate reportability is ALWAYS `value=null`, status=review_required; deadline_hours=null.
`routing.regulatory_clocks=[]` is accompanied by clock_status=review_required and an explicit
warning. An empty clock is NOT "no duty to report." No deadline is calculated.

Inherited, not freshly verified, public rule constraints informing this hold (not incident-specific advice or a deadline calculation):
- 1904.39(a): eight hours for death, twenty-four for qualifying hospitalization/amputation/eye loss.
- (b)(6): death within 30 days of the work incident; other severe events within 24 hours.
- (b)(7)-(8): delayed knowledge of the event or work-relatedness can control the clock.
- (b)(9)-(10): formal inpatient admission for care/treatment, not observation/testing only.
- (b)(3)-(4): transportation exceptions; (b)(11): qualifying amputation definition.

The candidate does not implement a complete adjudicated timing/applicability model, even when
reporting_facts are supplied. Occurrence, event/admission, employer/agent knowledge, work-relatedness,
jurisdiction, qualifying conditions, exceptions and evidence must be reviewed by EHS/Regulatory.
Severe events prompt URGENT review; do not wait for an automated deadline. No operational use
until the reporting blocker is resolved and independently approved.

## 5. Severity (internal draft triage, not a legal determination)

5.1 Severe outcome or hospitalization evidence -> critical, including unresolved applicability.
5.2 Days-away evidence -> high, even where recordability still requires review.
5.3 Other supported positive recording criteria -> medium.
5.4 Supported negative recording screen -> low; otherwise review_required (EHS-manager routing).

## 6. Evidence and governance

6.1 confidence=null and confidence_basis=not_estimated; completeness is not a probability.
6.2 Surface all review_reasons; missing facts never become "none" or zero.
6.3 Downgrade requests/prior positive determinations place an explicit governance hold and
EHS-manager draft review. No input can authenticate an approval, filing confirmation, release,
notification or closure. All packets remain draft_review_required and closure_allowed=false.
Only an external, authenticated human workflow may resolve these gates; none is implemented here.

Official sources:
- https://www.osha.gov/laws-regs/regulations/standardnumber/1904/1904.7
- https://www.osha.gov/laws-regs/regulations/standardnumber/1904/1904.39

rc.2 uses a bounded conservative lexical contradiction tripwire against structured negative screens; it is not a validated clinical NLP model and never infers diagnosis. Negated/ambiguous markers may require review.

## rc.3 reconciliation and numeric limits

Explicit cited source_conflicts force recording and near-miss review without interpreting unrecognized wording. Shared bounded markers cover clinical time off, qualitative accounts, significant-disease and harm/absence conflicts; none infer diagnosis, exact days or source trust. Negation can over-escalate; unmatched language still needs careful raw-grounded intake and human review. Exact days use 0..9007199254740991 only as a portable integer transport bound, not an OSHA cap; unrepresentable calendar windows fail validation without output. No automatic input migration is performed.
