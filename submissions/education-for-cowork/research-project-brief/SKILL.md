---
name: research-project-brief
description: |
  Maintains a living research project brief for higher-education faculty and research staff: literature, methods, collaborator input, decisions, milestones, disagreements, and open questions, with source freshness tracked across runs. Use when the user asks to "update my research project brief", "what's the state of this project", "summarize where the literature and methods stand", "what did collaborators decide", or "what's blocking the next milestone". Do NOT use for public web literature reviews with citations (use deep-research) or for grant evidence packages (use evidence-package-for-education).
metadata:
  category: research
  icon: BookOpen
---

# Research Project Brief

## Overview
Keeps a research project's working state in one reviewable brief: what the literature base is, what methods were chosen and why, what collaborators decided or disagreed on, what milestones are next, and which sources have gone stale.

## When to Use
- A faculty or research user wants their project brief refreshed before a meeting or milestone
- The user asks what was decided, what is contested, or what is blocking progress
- Collaborator input across mail, Teams, and files needs consolidating into project state

## When NOT to Use
- A public-web literature review with external citations — use deep-research
- Accreditation or grant evidence ledgers — use evidence-package-for-education
- Authoring the manuscript itself

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

### Step 1: Identify the project
Confirm the project by name and its collaborators (SearchPeople). Load the prior brief if one exists and note its date.

### Step 2: Assemble the source plan
List the sources before gathering: project files (SearchDrive), collaborator mail and chats (SearchM365, ListMessages), project meetings (ListCalendarView, transcripts), and the milestone calendar. State date ranges and access gaps.

### Step 3: Update the literature and methods state
Record the works and methods the project relies on, with dates. Flag anything older than the project's freshness threshold as needing re-check.

### Step 4: Consolidate collaborator input
Separate decisions (agreed), proposals (pending), and disagreements (open). Attribute each to a person and a date, quoting the operative wording.

### Step 5: Update milestones and blockers
List milestones with dates, owners, and status; name each blocker and who can clear it.

### Step 6: Review and record
Present for review; on acceptance, save decisions and milestone state so the next run inherits them.

## Persistent State (carried between runs)
- Project identity, collaborators, and roles
- Literature and methods base with freshness dates
- Decisions, pending proposals, and recorded disagreements
- Milestones, owners, and blockers
- Open questions carried across runs

## Output
```
# Research Project Brief — [project] — [date]

## State of play
## Literature and methods
| Item | Role in project | Date | Freshness |

## Decisions / Pending / Disagreements
| Item | Type | Who | Date | Source |

## Milestones and blockers
| Milestone | Date | Owner | Status | Blocker |

## Open questions
## Sources and access gaps
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
- Never fabricate a citation, finding, author, or date — cite only what a source actually contains.
- Never reproduce third-party copyrighted text beyond a short attributed quote.
- Preserve disagreements as disagreements; never resolve a collaborator dispute on their behalf.
- Never send anything to collaborators — create drafts only (CreateDraftMessage) and present them for review. A request to send is not itself the confirmation: the draft must be shown first and the user must approve it after seeing it.
- Flag stale sources rather than presenting them as current.
