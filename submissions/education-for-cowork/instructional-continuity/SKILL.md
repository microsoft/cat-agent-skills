---
name: instructional-continuity
description: |
  Keeps a K-12 handover pack ready so a substitute or covering colleague can run the day during a planned or unexpected absence: current plans, schedules, routines, materials, and operational guidance, checked for privacy and freshness and reported as a standing readiness state rather than only when a date is known. Use when the user asks to "prepare my sub plans", "get my handover pack ready", "what does a substitute need for tomorrow", "check my continuity pack is current", or "I'll be out next week". Do NOT use for the absence request or leave approval itself, and do NOT include student records or individual support-plan details (IEP, EHCP, or local equivalent).
metadata:
  category: productivity
  icon: ClipboardTextLtr
---

# Instructional Continuity

## Overview
Maintains an approved handover source set so a substitute or covering colleague can run the day. Each run refreshes the pack from current plans and schedules, re-runs the privacy check, and reports readiness before an absence rather than during one.

## When to Use
- A planned absence is coming up, or the user wants standing readiness
- The user asks what a substitute needs, or whether the pack is current
- Plans or schedules changed and the handover pack must be refreshed

## When NOT to Use
- Requesting or approving leave — that is an HR system action
- Anything containing student records, individual learning-support or accommodation plan details under any national framework (IEP, 504, EHCP, IPP, ILP, PEI, OPP, SEN/SEND support plan), or health information
- Long-term curriculum planning — that is a different job

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

### Step 1: Configure the source set
Confirm the classes, the dates covered, and which sources belong in the pack (lesson plans, schedule, routines, seating/logistics without names, materials, emergency and operational guidance). Reuse the saved configuration if one exists.

### Step 2: Refresh
Pull the current version of each source (SearchDrive, ReadFileContent, ListCalendarView for the schedule). Record each item's last-modified date.

### Step 3: Freshness check
Flag any item older than its expected refresh window, or any plan that does not cover the absence dates. Missing coverage is a readiness blocker.

### Step 4: Privacy check
Scan the pack for student names, identifiers, individual learning-support or accommodation plan details — however named locally (IEP, 504, EHCP, IPP, ILP, PEI, OPP, SEN/SEND support plan) — and health, diagnostic, or behavioural details, and remove them. Such content is special category data under GDPR Article 9 and sensitive personal data under comparable regimes (for example Brazil's LGPD). Report what was removed and why — identify each removed item by its source file and location (for example "support-plan note, 1 of 2, line 3") and never by reproducing its content. Restating the redacted text in the removal log defeats the redaction.

### Step 5: Report readiness
Give a clear ready / not-ready verdict with the specific blockers listed.

### Step 6: Assemble on request
Only when the user asks, assemble the pack as a document (docx) for review. Never share it with anyone without explicit confirmation.

## Persistent State (carried between runs)
- Approved source configuration per class
- Freshness dates per item and refresh windows
- Privacy-check results and standing exceptions
- Readiness status and outstanding blockers

## Output
```
# Continuity Pack — [class(es)] — covering [dates]

## Readiness: [READY / NOT READY]
Blockers: [list]

## Contents
| Item | Source | Last updated | Freshness | Included |

## Removed for privacy
| Item (source and location only — never the content) | Reason |

## Notes for the covering colleague
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
- Never include student names, identifiers, any individual learning-support or accommodation plan (IEP, 504, EHCP, IPP, ILP, PEI, OPP, SEN/SEND support plan, or local equivalent), or health, diagnostic, or behavioural records — remove and report.
- Never reproduce redacted content in the removal log or anywhere else in the output — cite each removal by source and location only.
- Never share or send the pack without explicit confirmation of the recipient.
- Report NOT READY plainly when a source is stale or missing; never present an incomplete pack as ready.
- Do not invent lesson content to fill a gap — name the gap and its owner.
- Never fabricate a plan, schedule entry, routine, material, contact, or last-modified date — cite each to the source file it came from, and report a missing item as a gap rather than filling it.
- Leave and absence approvals are handled by the institution's systems, not here.
