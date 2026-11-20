# Default Change Log / Redline Format

Layout for `consultant-database-refresh`. A house wrapper in
`Cowork Templates/Asset Management/consultant-database-refresh/` may replace this layout, subject to the guardrails below.

A house template governs **layout and section structure only**. It never removes citations, gap markers, source tiers, approval states, information-barrier rules, no-send restrictions, or the output footer — those apply to every output regardless of template. Output length never waives attribution or the footer; a one-line answer, single table cell, inline reply, or short excerpt still carries both. If a save, export, or write fails, report what was produced, where it was and was not written, and what remains incomplete.

The filled questionnaire follows **the uploaded template's own format**. This file governs the
accompanying change log, which is where the reviewer actually spends their time.

---

## Summary block (top of the change log)

```
Questionnaire:      Mercer Manager Profile — Q3 2026
Prior submission:   "Mercer Profile Q2 2026.docx", Consultant Relations > Mercer,
                    submitted 2026-07-15
Questions by state:  142 total
                      26  GAP
                       9  NEW
                      12  UPDATED
                      95  UNCHANGED
Flags (overlap states, not additive):
                      31  REFRESH REQUIRED
                       4  REVIEW — QUESTION CHANGED

Retrieval failures: 2 NOT RETRIEVED (listed separately, not counted above)
Template changes vs. prior cycle: 9 new, 2 removed, 4 reworded
```

## Ordering

Retrieval failures are listed **first**, before any question states — a reviewer needs to know
what could not be read before trusting any count below it.

Then sort questions by **answer-resolution state**, most attention-demanding first:

1. `GAP`
2. `NEW`
3. `UPDATED`
4. `UNCHANGED`

Within each state, put items carrying flags above items carrying none, `question-changed`
before `figure-refresh-required` where both apply.

A reviewer should be able to stop once they reach unflagged `UNCHANGED` items and trust the rest.

## Per-item block

State and flags are **separate lines**. A question can carry a state and both flags at once, and
all of them must be visible.

```
[Q 2.7]  Total firm assets under management
STATE:   UNCHANGED
FLAGS:   figure-refresh-required

PRIOR:    $847bn (as of 2025-12-31, submitted 2026-01-15)
PROPOSED: [REFRESH REQUIRED — confirm total firm AUM vs. system of record,
           as of current quarter end]

NOTE:     Prior figure shown above for reference only. It has NOT been carried
          into the proposed answer and must be re-sourced before submission.
```

```
[Q 4.2]  Describe your firm's approach to ESG integration
STATE:   GAP
FLAGS:   question-changed

PRIOR:    "Describe your ESG policy" — answered from "ESG Policy 2025.docx"
PROPOSED: [GAP — prior answer addresses policy, not integration. Nothing in the
           approved library covers integration as now asked. Owner: Compliance]

NOTE:     Wording change shown for the reviewer. No substantive change has been
          inferred from it.
```

**The prior value is always shown** in the `PRIOR` line, with its as-of date, so the reviewer
sees exactly what is being replaced and can spot a figure that should have moved but didn't.
**It is never repeated in the `PROPOSED` line.** A reader must not be able to lift a number out
of the proposed column and submit it without going to the system of record first — a flag next
to a usable number does not achieve that.

For a reworded question whose approved answer still responds:

```
[Q 5.2]  Describe how ESG factors are incorporated into security selection
STATE:   UNCHANGED
FLAGS:   question-changed

QUESTION WAS:  "Describe your firm's approach to ESG integration."
QUESTION NOW:  "Describe how ESG factors are incorporated into individual
                security selection decisions."

CARRIED ANSWER: <prior answer text>

NOTE: The question narrowed from firm-level to security-level. Confirm the
      carried answer still responds to what is being asked. If it does not,
      this becomes STATE: GAP — the flag alone is not enough.
```

## Fields that always age

Treat every one of these as `figure-refresh-required` on every cycle, even when they look static:

- AUM — firm, strategy, and vehicle level
- Performance, in any period or basis
- **Fees, expense ratios, fee schedules, breakpoints, and waivers** — always carry `figure-refresh-required`
- Headcount, team size, and named personnel
- Average team tenure
- Client and account counts
- Office locations and addresses
- Ownership percentages
- Capacity and soft-close status
- Any "as of" date anywhere in the document

## What not to do

- Do not present a carried-forward figure as current, or repeat it in the `PROPOSED` line
- Do not drop a flag because a state was already assigned — they are independent
- Do not mark an item `UNCHANGED` without the `question-changed` flag when only the wording changed
- Do not present a fee or expense-ratio answer without the `figure-refresh-required` flag, whatever its state
- Do not drop a question because the prior submission had no answer. Mark it `NEW` **only if approved library content was actually found to draft from**; if nothing responsive exists, mark it `GAP` with a suggested owner
- Do not report a source that could not be opened as absent — that is `NOT RETRIEVED`, listed separately and never counted as a question state
- Do not submit anything. The human submits


## Performance fields

Apply the shared performance-presentation gate in `house-rules.md` to each actual artifact/field. For externally intended performance, missing/inapplicable policy, unresolved intended use, incompatible data, missing required net performance or unmet substantive requirements leaves value-less blocked placeholders; current source data alone does not unblock it. Continue the rest of the draft and record actual intended use, policy and gate outcome in the footer. Preserve confirmed-internal-only current-source figures with basis/internal labels, and historical PRIOR values confined to clearly separate internal reviewer records; neither may be copied into proposed/external fields without passing the external gate. Existing answer states, refresh flags and internal/client separation remain unchanged.
