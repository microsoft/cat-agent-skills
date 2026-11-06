---
name: ai-rollout-education
description: |
  Coordinates a phased AI rollout across schools, colleges, universities, trusts, districts, or an education ministry: staff cohorts, prerequisites, role-based learning paths mapped to professional development windows, communications, support readiness, and wave gates checked against the academic calendar, with state carried between waves. Use when the user asks to "plan our AI rollout", "set up the training cohorts", "are we ready for the next wave", "what training does this role need", or "how is the rollout tracking". Do NOT use for any learner- or student-facing enablement wave, which is always referred out; for approving the tools themselves (use governance-review-for-education); for rolling out an approved policy document (use policy-change-pack-for-education); or for a single announcement (use stakeholder-comms).
metadata:
  category: productivity
  icon: Rocket
---

# AI Rollout and Role-Based Training

## Overview
Runs a multi-wave AI enablement programme: who is in each cohort, what they must complete first, which learning path fits their role, what communications go out when, and whether support capacity is sufficient to open the next wave.

## When to Use
- Planning or running a phased AI rollout across roles, sites, or sectors (school-age or higher education)
- The user asks about wave readiness, cohort status, prerequisites, or academic-calendar fit
- A request may put the capability in front of learners and needs referring out (Step 6 tripwire)
- Adjusting the programme between waves based on feedback and capacity

## When NOT to Use
- Approving or risk-reviewing the AI tools — use governance-review-for-education
- A single announcement or update message — use stakeholder-comms
- Individual staff performance or competency judgments, including appraisal and lesson observation
- Authoring the academic-integrity or AI-use policy itself — that is a drafting task
- Planning or gating a learner-facing wave, or determining any consent requirement

## Shared Skill Contract

This skill follows the institution's shared contract for every run:

1. **Intent check** — confirm outcome, audience, timeframe, and format before working.
2. **Source plan** — show the sources selected, their date ranges, access gaps, and freshness.
3. **Clarification gate** — ask only for missing information that would change the result.
4. **Staged execution** — keep discovery, synthesis, creation, review, and finalization separate.
5. **Reviewable output** — separate facts, interpretation, recommendations, assumptions, and open questions.
6. **Human approval** — require confirmation before sending, publishing, or changing any record.
7. **Reusable state** — carry accepted decisions forward without silently reusing stale assumptions.
8. **Quality check** — run the checks below before presenting final output.
9. **Telemetry** — log workflow signals only; never sensitive content.
10. **Failure behavior** — explain missing access, unsupported sources, uncertainty, and partial completion.

## Core Instructions

### Step 1: Frame the programme
Confirm the capability being rolled out, the sector (school-age education or higher education), the organisational unit (single school or college, campus, trust or academy chain, district, diocese, department or ministry of education), the roles in scope, and the success measures. Confirm the capability has an approved governance review; if not, flag it as a blocker.

Load the academic calendar before proposing any wave date: term, semester or trimester boundaries, examination and assessment periods, marking and reporting windows, admissions or enrolment cycles, and holiday or half-term breaks. Wave dates are constrained by this calendar, not chosen freely.

Success measures describe adoption, capability, and support load — completion rates, confidence, use in practice, ticket volume. Do not accept a success measure that attributes changes in learner outcomes to the rollout; that is an attribution the evidence cannot support. Record it as an aspiration, not a measure.

### Step 2: Load prior wave state
Carry forward cohort membership, completion status, support load, and changes accepted after the last wave.

### Step 3: Define cohorts and prerequisites
Group by role, site, and readiness. Site is a first-class cohort dimension wherever the institution spans more than one location — schools in a trust or district, colleges in a group, campuses in a university, regions under a department or ministry of education.

Use the sector's role taxonomy rather than inventing roles per run:

- **School-age education:** classroom teacher, teaching assistant or classroom support staff, subject or department lead, inclusion / special educational needs lead (SENCO, learning support coordinator, or local equivalent), senior leadership, office and administrative staff, technology lead
- **Higher education:** faculty or lecturing staff, adjunct / sessional / hourly-paid teaching staff, teaching assistant or graduate instructor, instructional or learning designer, department chair or head of school, professional services staff, technology staff
Cohorts are staff cohorts. Learners are out of scope — see the learner-facing tripwire in Step 6.

List prerequisites per cohort: licensing and account provisioning, policy acknowledgement, baseline training, data-protection training currency, safeguarding or child-protection training currency where the cohort works with learners, and academic-integrity guidance for any cohort using the capability in teaching or assessment. Resolve owners with SearchPeople.

### Step 4: Build role-based paths
For each role, list the learning path — sessions, self-paced material, practice scenarios — with effort and sequence.

Map each path to the professional development windows the institution actually has, not to abstract hours. Confirm which windows apply: professional development or in-service training days (INSET, staff development days, or the local equivalent), directed or allocated time, staff and department meeting slots, twilight or after-hours sessions, and self-paced time. Where release from teaching is required, name the cover or substitute cost as a constraint. A path that cannot be scheduled into an available window is not ready, however good its content.

### Step 5: Plan communications and support
Map the message calendar per cohort (draft only) and confirm support capacity: channels, hours, named responders, expected ticket load.

State the support model explicitly — central service desk, distributed champions or digital leads per site, or hybrid — and name responders per site rather than reporting capacity in aggregate only. Many school-age settings have no on-site technology staff; if a site has no named responder, that site is not supported, whatever the central capacity says. Expect demand to peak at term or semester start and size capacity against that peak, not the average.

### Step 6: Gate the wave
Give an explicit go / no-go for the next wave against the gates: prerequisites met, support capacity confirmed, communications ready, prior wave feedback addressed, and the academic calendar clear.

**Academic calendar gate.** Fail the wave if its window collides with an examination or assessment period, a marking or reporting window, the first days of a term or semester, or an admissions or enrolment peak. Name the colliding window and propose the next clear one.

**Learner-facing tripwire.** This skill plans staff waves only. If a request would put the capability in front of learners, stop and say so rather than gating it as a staff wave. Name what such a wave would require — age-appropriateness for every age band, parental or guardian notification and any consent the governing framework requires, a recorded safeguarding or child-protection review, age-appropriate account provisioning, and published academic-integrity guidance — and route the consent and safeguarding questions to governance-review-for-education and a named human owner. Do not determine any consent requirement yourself, and never issue a GO for a learner-facing wave.

### Step 7: Record and adjust
Record the wave outcome, feedback themes, and accepted changes for the next wave.

## Persistent State (carried between runs)
- Sector, organisational unit, and sites in scope
- Academic calendar constraints and protected windows
- Staff cohorts, membership, and completion status
- Prerequisites and their verification status
- Role-based learning paths, their professional development windows, and revisions
- Communication calendar and send status
- Support model, named responders per site, capacity, feedback themes, and wave gate decisions
- Learner-facing requests referred out, with the date and the owner they were routed to

## Output
```
# AI Rollout — [capability] — wave [n]

## Wave gate: [GO / NO-GO]
| Gate | Status | Evidence |
Prerequisites · Support capacity · Communications · Prior feedback · Academic calendar

## Cohorts
| Cohort | Role | Site | Size | Prerequisites | Status | Owner |

## Learning paths
| Role | Path | Effort | Professional development window | Sequence |

## Communications (drafts, unsent)
## Support readiness
| Site | Support model | Named responder | Peak capacity |
## Feedback and changes for the next wave
```

## Quality Checks (run before final output)

- Every fact carries a source: file name, meeting subject and date, or sender and date.
- Interpretation, assumptions, and open questions are labelled separately from facts.
- Carried state is reconciled against this run's evidence; contradictions are surfaced, not overwritten.
- Inaccessible or missing sources are named explicitly.
- No personal or sensitive data appears that the workflow does not require.
- Nothing is sent, posted, or published without explicit user confirmation.

## Failure Behavior

- **Missing access:** name the source and what is missing; continue with the rest and mark the gap.
- **No prior state:** say it is a first run and proceed without inventing history.
- **Thin evidence:** report low confidence rather than producing a confident-sounding result.
- **Conflicting sources:** present both, with dates and sources, and ask which governs.
- **Partial completion:** state exactly what was and was not covered.

## Guardrails
- Never send rollout communications without explicit confirmation — draft only.
- Never open a wave gate on incomplete prerequisites or unconfirmed support capacity; report NO-GO with reasons.
- Do not roll out a capability without an approved governance review — flag it as a blocker.
- Never evaluate individual staff competence; track cohort completion only.
- Never supply rollout, completion, or feedback data into teacher or faculty appraisal, lesson observation, probation, tenure, or any performance-management process. Refuse the request and say why, whoever asks.
- Report participation and feedback in aggregate, without attributing comments to named individuals.
- Never attribute a change in learner outcomes to the rollout; report adoption and capability, and state association at most.
- Never plan or gate a learner-facing wave here — refer it out under the Step 6 tripwire, and never determine a consent requirement or apply any jurisdiction's rules.
- Never schedule a wave into a protected academic window to meet a programme deadline; report the collision and propose the next clear window.
- Never fabricate a cohort size, completion figure, prerequisite status, support-capacity number, feedback theme, or wave date — cite each to the record it came from, and report an unverified item as unverified rather than filling the gap.
