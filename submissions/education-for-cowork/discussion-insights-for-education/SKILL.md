---
name: discussion-insights-for-education
description: |
  Maintains group-level patterns from classroom discussions, exit checks, and learner questions — themes, misconceptions, and shifts across cycles — using notes, transcripts, and summaries, never individual student judgments. Use when the user asks to "what patterns are showing in class discussions", "analyze this exit ticket set", "what misconceptions are coming up", "compare this week's discussion to last", or "did my teaching response work". Do NOT use for grading, individual student assessment, or ranking learners.
metadata:
  category: analysis
  icon: PeopleTeam
---

# Discussion Insights for Education

## Overview
Aggregates discussion and formative-check evidence into group-level patterns: recurring misconceptions, unanswered questions, and shifts between cycles. It preserves counterevidence and tracks whether the teaching response chosen last cycle actually moved the pattern.

## When to Use
- The user wants themes and misconceptions across a discussion, exit ticket, or question set
- The user asks whether a teaching change from a prior cycle had an effect
- The user wants to compare patterns between two class sessions or cycles

## When NOT to Use
- Grading, scoring, or assessing any individual learner
- Ranking or comparing students in any way
- One-off summarization of a single meeting transcript — use meeting-intel

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

### Step 1: Set the scope
Confirm the class or cohort, the cycle boundaries, and the sources (notes, transcripts, exit-check files). Never request or accept identifiable student records.

### Step 2: Gather evidence
Collect the sources: Glob/SearchDrive for uploaded response sets, ListMeetingTranscripts + GetMeetingTranscript for recorded sessions, notes files. State the date range and any missing source.

### Step 3: De-identify
Strip names and identifiers before analysis. Work only in aggregate; report counts and proportions, never a named example.

### Step 4: Extract patterns
Cluster into themes, misconceptions, and open questions. For each, give frequency, an anonymized illustrative phrasing, and the source.

### Step 5: Preserve counterevidence
Explicitly record evidence that contradicts each pattern. A pattern with no counterevidence check is reported as tentative.

### Step 6: Compare cycles and test responses
Compare against the prior cycle's patterns and state whether the recorded teaching response is associated with a shift — carefully, without claiming causation.

If two sources disagree about whether a response worked, fill the Conflicting sources block: present both with their dates, and end that block by asking the user which source governs. Do not pick one, average them, or prefer the more recent — and do not close the run with the question unasked.

### Step 7: Recommend next moves
Offer 2-3 instructional responses tied to specific patterns. On acceptance, record them so the next run can test them.

## Persistent State (carried between runs)
- Cohort and cycle definitions (no student identifiers)
- Prior patterns with frequency and status
- Counterevidence recorded per pattern
- Selected teaching responses and the cycle they were applied in

## Output
```
# Discussion Insights — [cohort] — [cycle]

## Patterns
| Theme / misconception | Frequency | Trend vs last cycle | Counterevidence |

## Open learner questions
## Effect of last cycle's response
[response applied] — [observed shift, with the uncertainty stated]

## Conflicting sources (omit only if there are none)
| Source A (name, date) | Source B (name, date) | What they disagree on |
**Which source governs this cycle's record? — [ask the user; do not resolve it yourself]**

## Suggested next moves
1. [move] — addresses [pattern]

## Sources and gaps
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
- Never assess, score, rank, or characterize an individual learner — group level only.
- De-identify all evidence before analysis; never quote a student by name.
- State association, never causation, when comparing cycles.
- Report a pattern's frequency and source; never infer a pattern from a single response.
- If sources are too thin to support a pattern, say so instead of generating one.
- When two sources disagree, present both with their dates and then put the governing question to the user explicitly; the run is complete only once that question has been asked. Surfacing a conflict and leaving it unresolved is an incomplete run, not a neutral one.
- Never fabricate a pattern, frequency, illustrative phrasing, trend, or source — cite each to the file or transcript and date it came from, and report an unevidenced item as absent rather than filling the gap.
