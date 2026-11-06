---
name: policy-change-pack-for-education
description: |
  Carries an approved education policy through local procedures, audience communications, owners, and deadlines, comparing policy versions to establish what changed and which audiences, procedures, and forms are affected, traced across Microsoft 365. Use when the user asks to "build a policy change pack", "roll out this policy update", "what changes with the new policy", "draft the policy communications", or "who needs to know about this policy change". Do NOT use for drafting the policy itself, for a generic announcement with no source policy (use stakeholder-comms), for reviewing AI tools and connectors (use governance-review-for-education), or for AI rollout training and cohort communications (use ai-rollout-education).
metadata:
  category: communication
  icon: ClipboardTaskListLtr
---

# Policy Change Pack for Education

## Overview
Turns an approved policy or policy revision into an implementation pack: what changed, which local procedures are affected, which audiences must hear it, who owns each action, and by when. It preserves the source policy version and approval trail so later runs can detect drift.

## When to Use
- A policy or handbook section has been approved or revised and must be implemented
- The user needs the downstream procedure, communication, and owner list for a change
- The user asks what changed between two policy versions and who is affected

## When NOT to Use
- Authoring the policy text itself — that is a drafting task, not this workflow
- A general announcement with no governing source document — use stakeholder-comms
- Reviewing agents, plugins, or connectors — use governance-review-for-education

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

### Step 1: Identify the authority
Locate the approved policy and its version with SearchDrive / SearchM365 / ReadFileContent. Record file name, version, approval date, and approver. If more than one candidate matches, list up to 10 and confirm before proceeding.

### Step 2: Diff the change
Compare the approved version against the prior version or the current local procedure. Quote the operative wording that changed and cite the section by its heading or number.

### Step 3: Map the impact
Identify affected local procedures, forms, handbooks, and systems. Search files and messages for each; mark items as confirmed-affected, likely-affected, or unknown.

### Step 4: Assign audiences and owners
List each audience (staff, faculty, families, students, vendors) with the required message, the accountable owner (resolve names with SearchPeople), and a deadline.

### Step 5: Draft the artifacts
Draft audience communications and a procedure-update checklist. Keep drafts separate from facts about the policy.

### Step 6: Review and stage
Present the whole pack for review. Create drafts only (CreateDraftMessage) — never send. On acceptance, record the approved pack state for change tracking.

## Persistent State (carried between runs)
- Source policy name, version, approval date, and approver
- Change log: which sections changed and how
- Affected procedures and their update status
- Audiences, owners, deadlines, and communication status
- Approvals recorded and exceptions granted

## Output
```
# Policy Change Pack — [policy name] v[version]

## Source and authority
Policy: [file] · Version: [v] · Approved: [date] by [approver]

## What changed
| Section | Before | After | Impact |

## Affected procedures
| Procedure/Doc | Owner | Change required | Status |

## Audience plan
| Audience | Message | Channel | Owner | Deadline |

## Draft communications
[draft per audience — unsent]

## Open items and assumptions
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
- Never send communications or change records without explicit confirmation — draft only.
- Never paraphrase policy language where the exact wording is operative; quote it and cite the section.
- If the approved version cannot be confirmed, stop and say so rather than inferring what changed.
- Do not assign an owner you could not resolve in the directory — mark it as unassigned.
- Flag any legal, accessibility, or compliance implication for human review; never adjudicate it.
