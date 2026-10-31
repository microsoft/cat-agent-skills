---
name: "forecast-review-prep"
description: >-
  Builds a one-page pre-read for an upcoming forecast review, business review,
  or operating review by pulling the calendar event, recent email and chat
  discussion, attendee roles, and last cycle's open items into a structured
  brief. Use when the user asks to "prep me for the forecast review", "build the
  pre-read for the QBR", "brief me for the business review", "get me ready for
  the operating review", or "what is still open from last cycle". Do NOT use for
  anticipating specific questions (use stakeholder-qa-prep), building the
  forecast itself, or general meeting prep.
metadata:
  icon: ChartMultiple
---

# Forecast / Business Review Prep

A single-screen brief for an upcoming review: what it is, who's in the room, what they'll likely
focus on, the numbers to have ready, and what's still open from last cycle.

## When NOT to Use

- **General meeting prep for any meeting type** → outside this skill's scope
- **Building the forecast or model itself** → spreadsheet or BI work, do that first
- **Anticipating and pre-answering specific questions** → use `stakeholder-qa-prep`
- **1:1 prep** → outside this skill's scope

## Related Skills

Hand off rather than overlap:

- Anticipating and pre-answering questions — use stakeholder-qa-prep instead.
- A slide-format prep pack — use pptx instead.
- Writing the variance narrative itself — use variance-commentary instead.
- Close-cycle status — use close-status-digest instead.
- General meeting prep of any type — outside this skill's scope.

## Workflow

### 1. Find the meeting

`outlook_calendar-ListCalendarView` from now through the next seven days, matched on the subject
keywords the user used. If they named it exactly, use that. If several candidates remain, list
them with `core-AskUserQuestion` — never guess between two plausible reviews.

Capture subject, start time in the user's local time zone, organizer, and attendees.

### 2. Identify the senior attendee

Scan the attendee list and resolve unfamiliar names with `me_profile-GetUserDetails` or
`me_profile-SearchPeople` to surface role and team. The most senior person in the room is
effectively who the user is preparing for — anchor the focus areas around them.

Never infer seniority from a name or email pattern; resolve it from the directory or leave it
unstated.

### 3. Gather context — run these in parallel

- `m365_search-SearchM365` with `sources=["email","teams"]` on the meeting subject and its key
  metrics, last 14 days
- `m365_search-SearchM365` with `sources=["files"]` for pre-read documents referenced in those
  threads
- `outlook-ListMessages` filtered to the senior attendee, last 7 days
- If the meeting recurs, find the prior occurrence with `outlook_calendar-ListEvents` and pull its
  follow-up thread for open action items

### 4. Draft the brief

Fixed structure, capped at roughly one screen:

- **Meeting** — subject, time, organizer, attendees with roles
- **Likely focus** — what's top of mind based on retrieved discussion
- **Key numbers to know** — only figures found in retrieved context
- **Questions to anticipate** — 3-5 the senior attendee is likely to raise
- **Open items from last cycle** — outstanding follow-ups with owners
- **Materials** — bracketed links to documents found, e.g. `[file_1]`

## Output Format

Inline markdown. Write a file only if the user asks for one.

## When Things Fail

- **No matching meeting found** — say so and ask for the meeting name; do not brief on a guessed event.
- **Attendee lookup fails** — list the attendee without a role rather than inferring seniority.
- **Search returns nothing** — deliver the brief with the sections you have and state plainly that no recent discussion was found. An empty "Likely focus" is a valid answer.
- **Prior occurrence missing** — omit the open-items section and say the prior cycle wasn't found.
- **A tool errors** — retry once, then continue and disclose the gap in plain language.

### Example output

```text
Meeting    Q3 Business Review - Thu 14 May, 9:00-10:00 PT
           Organizer: J. Alvarez - 7 attendees
           Most senior: M. Chen (VP Finance)

Likely focus   Renewal timing and the services margin dip flagged twice
               in last week's thread

Key numbers    Revenue $42.1M vs $40.3M plan (+4.5%)
               Services margin 61% vs 64% prior quarter
               Pipeline coverage [Verify before review]

Anticipate     1. Is the renewal pull-forward timing or run-rate?
               2. What recovers the 300bps of services margin?
               3. Does coverage support next quarter's number?

Open items     Pricing exception policy - due from last cycle, still open
```

## Guardrails

- **Never invent a metric.** If a number isn't in retrieved context, write `[Verify before
  review]` rather than supplying a plausible figure. A brief with visible gaps is useful; a brief
  with invented numbers is dangerous in front of an executive.
- If no relevant context surfaces, say so honestly — do not pad with generic preparation advice.
- For meetings marked private or confidential, surface the time block only, not subject details.
- Surface disagreements between attendees' recent positions rather than smoothing them over.
- Never evaluate an individual's performance, even by implication.
- If the brief would run past one screen, cut the least decision-relevant section rather than truncating mid-list.
- Never infer a person's role, seniority, or reporting line from their name or email address.
- Confirm before writing any file — the default is inline.
