---
name: instructional-retrospective
description: |
  Maintains a private, evidence-backed teaching retrospective across course cycles for higher-education faculty: what was planned, what changed, what the evidence suggests, and which next-cycle actions were accepted, including counterevidence. Use when the user asks to "run my course retrospective", "did my course changes work", "review last term's teaching", "what should I change next cycle", or "compare this cycle to last". Do NOT use for evaluating other instructors, for any personnel or performance process, or for grading students.
metadata:
  category: analysis
  icon: ArrowSyncCircle
---

# Instructional Retrospective

## Overview
A private, self-directed review of one instructor's own course across cycles. It tests whether changes made last cycle are associated with the outcomes the instructor cared about, keeps counterevidence visible, and records the actions accepted for the next cycle.

## When to Use
- End of a term or unit, reviewing one's own course design and delivery
- The user asks whether a change they made had the intended effect
- Planning next-cycle changes grounded in this cycle's evidence

## When NOT to Use
- Reviewing, comparing, or evaluating any other instructor — refuse and redirect
- Any personnel, promotion, tenure, or performance-management process
- Grading or assessing individual students

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

### Step 1: Confirm the cycle and privacy
Confirm the course, the cycle being reviewed, and that this is the user's own course. State up front that the retrospective is private to the user and not shared.

### Step 2: Load prior retrospective
Read the previous retrospective; extract the changes that were accepted and the outcomes they were meant to move.

### Step 3: Gather evidence
Collect the user's own plans, teaching notes, aggregate feedback the user selected, and course artifacts (SearchDrive, Glob on input/). Use aggregate feedback only — never individual student identifiers.

### Step 4: Test the prior changes
For each accepted change, state the intended effect, the evidence available, and what it does and does not support. Record contradicting evidence explicitly.

### Step 5: Surface what to keep, change, drop
Group findings into keep / change / drop, each tied to evidence and each with the uncertainty named.

### Step 6: Record next-cycle actions
Present for review; record accepted actions with the outcome they target so the next cycle can test them.

## Persistent State (carried between runs)
- Course and cycle history
- Accepted changes per cycle and their target outcomes
- Evidence and counterevidence per change
- Keep / change / drop decisions carried forward

## Output
```
# Instructional Retrospective — [course] — [cycle] (private)

## Changes tested from last cycle
| Change | Intended effect | Evidence | Counterevidence | Verdict |

## Keep / Change / Drop
## Next-cycle actions
| Action | Target outcome | How it will be tested |

## Evidence limits and assumptions
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
- This is private to the user — never send, share, or post it. Present it for review and, where a message is wanted, create a draft only (CreateDraftMessage). A request to send is not itself the confirmation: the draft must be shown first and the user must approve it after seeing it.
- Refuse any request to evaluate another instructor's performance and redirect to the appropriate human process.
- Use aggregate student feedback only; never identify or quote a named student.
- State association, never causation; name the confounders you can see.
- Where evidence is too thin to judge a change, say so rather than concluding.
- Never fabricate feedback, quotes, scores, or trends — cite each to the artifact and date it came from.
- If a prior retrospective cannot be found, say it is a first cycle rather than inferring past changes.
