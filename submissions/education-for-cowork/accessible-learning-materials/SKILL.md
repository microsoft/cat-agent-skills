---
name: accessible-learning-materials
description: |
  Maintains instructionally equivalent, accessible variants of a set of learning materials — lessons, readings, slides, and handouts — with parity checks against the original learning goals and recorded approvals. Use when the user asks to "make these materials accessible", "audit this lesson set for accessibility", "create an accessible version of this reading", "check reading level and alt text", or "keep my accessible variants in sync". Do NOT use for individual student accommodation or support-plan decisions (IEP, EHCP, or local equivalent), and do NOT use for generic document formatting (use docx).
metadata:
  category: writing
  icon: AccessibilityCheckmark
---

# Accessible Learning Materials

## Overview
Audits and maintains accessible variants across a material set, preserving the original learning goals. Each run checks parity (same objectives, same assessed content), applies accessibility fixes, and records which variants were approved so later runs only revisit what changed.

## When to Use
- A set of lesson materials needs accessible variants or an accessibility audit
- The user asks about alt text, reading level, structure, contrast, or captions across files
- Source materials changed and the accessible variants must be brought back in sync

## When NOT to Use
- Deciding accommodations for a specific student, or anything relating to an individual learning-support, disability, or accommodation plan — however it is named locally (IEP, 504, EHCP, IPP, ILP, PEI, OPP, SEN/SEND support plan) — that is a qualified human decision
- General document formatting with no accessibility goal — use docx
- Translating third-party copyrighted material in full

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

### Step 1: Define the material set and goals
Identify the files in scope (Glob on input/, SearchDrive) and the stated learning objectives. If objectives are not written down, extract candidates and confirm them — parity depends on this.

### Step 2: Audit
For each file, check structure (headings, lists, tables), alt text on images, link text, colour-contrast and colour-only meaning, reading level, caption/transcript availability, and language tagging. Record findings per file with severity.

### Step 3: Check parity
Confirm each proposed variant teaches and assesses the same objectives as the original. A variant that drops content is a parity failure, not a simplification.

### Step 4: Produce variants
Apply fixes and generate the requested variants (docx for documents, pptx for slides). Keep the original untouched and version the variant.

### Step 5: Handle uncertainty
Where a check cannot be completed automatically — an image whose content you cannot see, a colour judgment, a media file without a transcript — record it as **needs human review** with the reason. Never report an unchecked item as passing, and never guess a reading level you did not compute.

### Step 6: Review and approve
Present the audit and variants for review. Record approved variants and reusable patterns (preferred alt-text style, terminology) for future runs.

## Persistent State (carried between runs)
- Material set, source versions, and stated learning objectives
- Audit findings and their remediation status per file
- Approved variants and their version dates
- Accepted accessibility patterns and approved terminology

## Output
```
# Accessibility Audit and Variants — [material set]

## Summary
Files: n · Blocking issues: n · Advisories: n

## Findings
| File | Issue | Type | Severity | Fix applied |

## Parity check
| Objective | Original | Variant | Equivalent? |

## Variants produced
| File | Variant | Version | Status |

## Not remediated / needs human review
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
- Never reduce instructional content in the name of accessibility — flag a parity failure instead.
- Never generate alt text for an image you cannot see; mark it for human authoring.
- Do not make accommodation decisions for named students; refer those to the qualified team. This covers any individual learning-support, disability, or accommodation plan under any national framework, plus any health, diagnostic, or behavioural record about a named student — such content is special category data under GDPR Article 9 and sensitive personal data under comparable regimes (for example Brazil's LGPD).
- Preserve the original file; every change lands in a versioned variant.
- Report an accessibility check as a check, not as a compliance guarantee.
- Never fabricate a finding, a reading-level figure, a standard reference, or a file's contents — if a file cannot be read, say so and exclude it.
- Cite every finding to a specific file and location (slide, page, or heading); unverified items are marked [verify].
