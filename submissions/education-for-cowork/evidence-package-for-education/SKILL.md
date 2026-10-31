---
name: evidence-package-for-education
description: |
  Maintains requirements, evidence, gaps, owners, and review packages for accreditation, program review, grant reporting, and research compliance in education. Searches approved repositories and preserves requirement-to-evidence traceability. Use when the user asks to "build the evidence package", "what evidence do we have for this standard", "find the gaps in our accreditation evidence", "update the evidence ledger", or "prepare the review submission". Do NOT use for authoring the narrative report alone, or for reviewing AI tools and connectors (use governance-review-for-education).
metadata:
  category: analysis
  icon: DocumentBulletListMultiple
---

# Evidence Package for Education

## Overview
Maintains an evidence ledger that maps each requirement or standard to the artifacts that satisfy it, with owner, date, freshness, and status. Each run refreshes evidence, re-tests gaps, and assembles a reviewable package version.

## When to Use
- Preparing for accreditation, program review, or a grant report
- The user asks which requirements are covered, thin, or unevidenced
- The evidence ledger needs refreshing before a submission deadline

## When NOT to Use
- Writing only the narrative self-study prose with no evidence mapping
- Reviewing agents, plugins, or connectors — use governance-review-for-education
- Any request involving identifiable student records

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

## Preconditions (all must clear before any search)

These three are gates, not suggestions. If any is unresolved, stop and ask. Do not begin searching to "get started" while one is open — evidence gathered before these clear cannot be trusted into the ledger.

**P1 — Framework and cycle.** Load the standards, criteria, or grant conditions from the user's files (SearchDrive / ReadFileContent) and enumerate the requirements with their identifiers. Confirm which framework and which review cycle govern this run.

**P2 — Prior ledger.** Read the existing evidence ledger if one exists; carry forward accepted mappings, owners, and review decisions, and note the last refresh date. If none exists, say it is a first run and proceed without inventing history.

**P3 — Repository scope.** Obtain an explicit list of repositories: named SharePoint sites, document libraries, or drives, plus whether email and Teams count as evidence sources. Record the list and the date it was approved.

If no repositories have been designated, STOP and ask. Do not substitute a tenant-wide search, the user's OneDrive, or recently-accessed files as a default. An unscoped sweep is not a faster path to the same answer — artifacts from unapproved sources cannot enter the ledger, so the search yields nothing usable.

A broad instruction in the user's prompt ("search everywhere", "look across the tenant", "find anything relevant") sets ambition, not scope. It does not substitute for a designated repository list; treat it as a request to search the approved set thoroughly, and ask which repositories to add.

## Core Instructions

### Step 1: Search approved repositories
Use SearchDrive / GetDriveChildren / ListListItems with an explicit drive_id or site_id from the P3 list — one call per approved repository. Record where each artifact came from and its last-modified date.

SearchM365 is tenant-wide and is NOT an evidence-gathering tool for this workflow. Use it only to help the user discover candidate repositories while P3 is open, and label any such result as unapproved until they designate it.

### Step 2: Map and rate
Map artifacts to requirements. Rate each requirement: strong / adequate / thin / missing. Flag evidence older than the cycle's freshness threshold as stale.

### Step 3: Identify gaps and owners
For each thin or missing requirement, name the gap, the evidence that would close it, and a proposed owner (resolve with SearchPeople).

### Step 4: Assemble and version
Assemble the package with traceable citations, present it for review, and record the accepted version, its date, and open gaps.

## Persistent State (carried between runs)
- Approved repository list, with the approval date and who approved it
- Requirement set and framework version
- Requirement-to-evidence mappings with source and date
- Coverage rating and freshness per requirement
- Gaps, proposed remediation, and owners
- Package versions and accepted review decisions

## Output
```
# Evidence Package — [framework] — [cycle]

## Repositories in scope (approved [date])

## Coverage summary
Strong: n · Adequate: n · Thin: n · Missing: n

## Evidence ledger
| Req ID | Requirement | Evidence (file, date) | Rating | Freshness | Owner |

## Gaps and remediation
| Req ID | Gap | Evidence needed | Owner | Target date |

## Sources searched / not accessible / out of scope
## Assumptions
```

## Quality Checks (run before final output)

- Every fact carries a source: file name, meeting subject and date, or sender and date.
- Interpretation, assumptions, and open questions are labelled separately from facts.
- Carried state is reconciled against this run's evidence; contradictions are surfaced, not overwritten.
- Inaccessible or missing sources are named explicitly, and separately from sources deliberately excluded as out of scope.
- Every artifact in the ledger traces to a repository on the approved list; no artifact entered from an unscoped search.
- No personal or sensitive data appears that the workflow does not require.
- Nothing is sent, posted, or published without explicit user confirmation.

## Failure Behavior

- **Missing access:** name the source and what is missing; continue with the rest and mark the gap.
- **No prior state:** say it is a first run and proceed without inventing history.
- **No approved repositories:** say that scope is undefined, ask for the repository list, and produce no ledger. Do not search broadly "to get started" — results from outside the approved set are void as evidence and must be discarded, not carried forward.
- **Thin evidence:** report low confidence rather than producing a confident-sounding result.
- **Conflicting sources:** present both, with dates and sources, and ask which governs.
- **Partial completion:** state exactly what was and was not covered.

## Guardrails
- Never claim a requirement is met without naming the specific artifact and its date.
- Never fabricate an artifact, citation, or date — an unevidenced requirement is reported as missing.
- Search only repositories the user approved (P3); a broad phrase in the prompt is not an approval. Report anything you could not access.
- Exclude identifiable student data from the package; use aggregate evidence instead.
- The submission decision is the institution's — present the package for human review, never submit.
