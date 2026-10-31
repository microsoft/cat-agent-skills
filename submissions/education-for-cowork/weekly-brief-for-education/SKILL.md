---
name: weekly-brief-for-education
description: |
  Maintains a running weekly brief for education faculty, staff, and leaders: priorities, commitments, decisions, risks, open questions, and upcoming work, reconciled from calendar, meetings, messages, and files. Carries accepted decisions and owners across weeks. Use when the user asks to "build my weekly brief", "what happened this week", "prep my week ahead", "update my weekly brief", "what commitments am I carrying", or "what changed since last week". Do NOT use for a single meeting recap (use meeting-intel), a one-off daily catch-up (use daily-briefing), or an audience-facing status message (use stakeholder-comms).
metadata:
  category: productivity
  icon: CalendarWeekNumbers
---

# Weekly Brief for Education

## Overview
Produces and maintains a recurring weekly brief for an education role (educator, department lead, or institutional leader). It reconciles this week's calendar, meeting notes, mail, chats, and working files against the previous brief, so decisions, owners, and unresolved questions carry forward instead of being re-derived each week.

## When to Use
- The user runs a weekly planning or review ritual and wants the same brief refreshed
- The user asks what changed, what they committed to, or what is at risk this week
- The user wants next week's priorities derived from this week's evidence

## When NOT to Use
- A recap of one specific meeting — use meeting-intel instead
- A same-day catch-up on mail and Teams — use daily-briefing instead
- A message written for an audience (team, leadership, parents) — use stakeholder-comms instead
- Anything involving individual student records or staff performance judgments

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

### Step 1: Confirm scope
Confirm the role lens (educator, staff, leader), the week boundaries in the user's local time zone, and the output format. Ask only if the role lens is genuinely unknown; otherwise reuse the last brief's configuration.

### Step 2: Load prior state
Read the previous brief from `output/` or the user's OneDrive (SearchDrive / ReadFileContent). Extract carried decisions, owners, open questions, and risks. If none exists, say so and start a first-run brief.

### Step 3: Build the source plan
List sources before gathering: ListCalendarView for the week, ListMessages / SearchM365 for mail and Teams, ListMeetingTranscripts + GetMeetingTranscript for meetings that have them, SearchDrive for changed working files. State date ranges, and note any source you could not access.

### Step 4: Reconcile
Match this week's evidence against carried items: resolved, still open, changed, new. Every item keeps a traceable source (meeting subject and date, message sender and date, or file name).

### Step 5: Draft the brief
Write the brief in the Output format below. Separate facts from interpretation, and label assumptions explicitly.

### Step 6: Review and finalize
Present the brief for review. Only after the user accepts, record accepted decisions and owners into the saved brief so the next run inherits them.

## Persistent State (carried between runs)
- Accepted decisions, with date and source
- Owners and commitments, with due dates
- Unresolved questions carried from prior weeks
- Risks and their status trend (new / unchanged / worsening / closed)
- Role lens and source configuration

## Output
```
# Weekly Brief — [role] — week of [dates]

## Priorities next week
1. [priority] — why now: [evidence]

## Commitments (owner, due)
| Commitment | Owner | Due | Source |

## Decisions this week
- [decision] — decided [date], source: [meeting/message]

## Risks and issues
- [risk] — [new / unchanged / worsening / closed]

## Open questions
- [question] — carried since [date]

## Assumptions and gaps
- [assumption]  ·  Sources unavailable: [list]
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
- Never send, post, or publish the brief — present it for review and, where a message is wanted, create a draft only (CreateDraftMessage). A request to send is not itself the confirmation: the draft must be shown first and the user must approve it after seeing it.
- Cite a source for every fact; label interpretation and assumptions separately.
- Never carry a prior decision forward silently if this week's evidence contradicts it — surface the conflict.
- Never include student personal data, and do not evaluate individual staff performance.
- State missing or inaccessible sources plainly rather than filling the gap.
- Never fabricate a commitment, decision, owner, due date, risk, or source — cite each to the meeting, message, or file it came from, and write an absent detail as not stated rather than inferring it.
