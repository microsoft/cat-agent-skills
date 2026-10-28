# Default Answer Format

Layout for `rfp-ddq-response-draft`. A house template in
`Cowork Templates/Asset Management/rfp-ddq-response-draft/` may replace this layout, subject to the guardrails below.

A house template governs **layout and section structure only**. It never removes citations, gap markers, source tiers, approval states, information-barrier rules, no-send restrictions, or the output footer — those apply to every output regardless of template. Output length never waives attribution or the footer; a one-line answer, single table cell, inline reply, or short excerpt still carries both. If a save, export, or write fails, report what was produced, where it was and was not written, and what remains incomplete.

Preserve the **original questionnaire's numbering and section order**. The reviewer maps your
response against the request; renumbering costs them time and risks a missed item.

---

## Per-answer block

```
[Section] 3. Investment Process
[Q 3.4] Describe your firm's approach to position sizing. (250 word limit)

<answer text, within the stated limit>

STATE:  ADAPTED
SOURCE: "Investment Process — Approved.docx", RFP Library > Investment,
        approved 2026-01-22
NOTE:   Assembled from the equity and fixed income process sections;
        confirm the blended description fits this strategy.
```

- `STATE` is one of `MATCHED` / `ADAPTED` / `GAP` / `STALE`
- `SOURCE` names document, library location, and approval or modified date
- `NOTE` appears only when the reviewer needs to know something — what was assembled, what was
  assumed, what to check. Omit it when the answer is a clean match.

**Keep the `NOTE` and `STATE` lines out of any client-, prospect-, or consultant-facing copy.**
They are reviewer scaffolding — the same rule the gap list follows — so they belong in the internal
working copy, not in the answer a client reads. The answer text and its `SOURCE` citation are what
the draft carries for review; a `[VERIFY vs. system of record]` placeholder always travels and must
be filled from the system of record before use, never silently dropped.

Respect the word limit. If the approved answer exceeds it, trim and say so in `NOTE` rather
than silently cutting substance.

## Figures inside answers

Inline, never in a footnote — the reviewer must see it while reading the sentence. The
placeholder replaces the number; it does not decorate it, and no prior value appears anywhere
in the answer block:

```
The firm managed [VERIFY vs. system of record — total firm AUM, as of current quarter end]
across [VERIFY vs. system of record — institutional relationship count] institutional
relationships.
```

The answer block ships with the document, so it never carries a number that could be submitted
unchanged. **Prior values go in the gap list**, which is the reviewer-facing section, with the
document and date they came from.

## Gap list — internal reviewer appendix, delivered as a separate file

**This section is never part of the submitted response.** It is a working list for the response
team and must be removed — or, preferably, never merged in — before anything goes to the
prospect, client, or consultant. Carry that statement at the top of the section itself.

| Q# | Section | What is needed | Prior value (reference only) | Suggested owner | State |
|---|---|---|---|---|---|
| 2.1 | Firm | Current total firm AUM | $847bn as of 2025-12-31, "Firm Overview.docx" | Performance | STALE |
| 4.2 | Operations | Current BCP test date | — | Operations | GAP |
| 6.1 | Performance | 3-yr gross/net since-inception | — | Performance | STALE |
| 8.7 | ESG | Firm stewardship policy — none in library | — | Compliance | GAP |

The **Prior value** column exists so a reviewer can see what a figure used to be and notice one
that should have moved. This internal file is the **only** place a prior figure may appear. It is
never copied back into an answer without going to the system of record.

Owners are **suggestions inferred from subject matter**, not assignments. Say so.

Sort by section, not by severity — the reviewer works through the document in order.

## Document header

```
<Firm> — Response to <Questionnaire Name>
Prospect/Client: <name>          Due: <date if stated>
Prepared: <date>

MARKETING MATERIAL — COMPLIANCE REVIEW REQUIRED
Draft assembled from approved library content. Every answer carries its source, even
for a one-line answer or short excerpt. Fields showing [VERIFY vs. system of record]
are deliberately blank and must be filled from the system of record before use.
Prior values, where known, are listed in the gap list for reference only.
Draft only — nothing has been sent, submitted to a consultant database, or posted to a client portal.
```

## What not to do

- Do not reorder or renumber questions
- Do not merge two questions into one answer, even when they overlap — answer both, cross-reference if useful
- Do not write "N/A" where the real state is `GAP`; they mean different things to a reviewer
- Do not fill a gap with generic industry language. A blank with an owner is the correct output


## Performance fields

Apply the shared performance-presentation gate in `house-rules.md` to each actual artifact/field. For externally intended performance, missing/inapplicable policy, unresolved intended use, incompatible data, missing required net performance or unmet substantive requirements leaves value-less blocked placeholders; current source data alone does not unblock it. Continue the rest of the draft and record actual intended use, policy and gate outcome in the footer. Preserve confirmed-internal-only current-source figures with basis/internal labels, and historical PRIOR values confined to clearly separate internal reviewer records; neither may be copied into proposed/external fields without passing the external gate. Existing answer states, refresh flags and internal/client separation remain unchanged.
