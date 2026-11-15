# Default Commentary Outline

**Workflow boundary:** periodic commentary for a named investment fund, portfolio, or strategy, governed by current performance/attribution sources and the presentation-policy gates. Not the manager's corporate revenue/cost/profit commentary or executive operating update. A template cannot change that ownership or bypass a blocked performance section.

Structure for `investment-commentary-draft`. A house template in
`Cowork Templates/Asset Management/investment-commentary-draft/` may replace this layout, subject to the guardrails below.

A house template governs **layout and section structure only**. It never removes citations, gap markers, source tiers, approval states, information-barrier rules, no-send restrictions, or the output footer — those apply to every output regardless of template. Output length never waives attribution or the footer; a one-line answer, single table cell, inline reply, or short excerpt still carries both. If a save, export, or write fails, report what was produced, where it was and was not written, and what remains incomplete.

Most firms have a fixed commentary structure. **If a prior commentary is found in the archive,
follow its structure, not this one** — this outline is the fallback when no archive exists.

---

## 1. Header

Strategy / fund name · period · basis (gross, net, or both) · share class where relevant.

Where gross figures appear in material intended for external use, net must be shown with at
least equal prominence, over the same periods and methodology. The performance section is blocked
by the ordered gate in `SKILL.md` — including when no compliance-approved presentation policy
applies to this material, when an identified policy does not cover this material type, audience,
or channel, when a substantive requirement of that policy cannot be satisfied, or when the
intended use is unresolved. Blocked means a value-less placeholder; figures are never computed,
and there is no default presentation to fall back on. Naming a policy does not unblock a
section — it must apply, and the draft must meet what it requires.

## 2. Performance summary

Returns for the period and standard trailing periods, versus the stated benchmark.

**Every figure verbatim from the configured performance connector or the uploaded export**,
whichever supplied it — name the source. If neither is available:

```
[PERFORMANCE — from system of record]
```

Never populate this section from a prior commentary document.

Below, **"the export"** means whichever supplied the figures — configured performance connector
or uploaded file.

Present fairly: show the standard period set the firm always shows. Never select periods
because they look better — that is a Rule 206(4)-1 problem, not a style choice.

## 3. Market backdrop

What happened in the market over the period. Each factual claim cited:

```
The 10-year Treasury yield ended the quarter at 4.18% (FRED: DGS10, as of 2026-09-30).
```

Prefer the firm's approved house macro view where one exists. Rewrite this section every
period — it is the most tempting to carry forward and the most obviously wrong when stale.

## 4. Contributors and detractors

From the attribution export only. Describe contribution; do not claim skill.

| | Position | Contribution | Note |
|---|---|---|---|
| Top | | | as identified by the export |
| Detractor | | | |

Do not introduce holdings the export does not contain.

## 5. Positioning and activity

Changes in positioning over the period, where the export or an approved narrative source supports
them. Describe what changed. Do not justify it with reasoning the sources don't contain.

## 6. Outlook

**Only** from the firm's approved house view or the user's own dictated input.

Approved house view: use as-is, cited.

Dictated input: **unapproved content.** Reproduce it faithfully, preserve every hedge — "seeks
to" never becomes "will" — never extend it beyond what was said, and mark it inline:

```
[UNAPPROVED — new claim, requires review] <the dictated text, verbatim in substance>
```

Every instance is counted in the output footer. A dictated return target, projection, or
hypothetical result is refused regardless of how it was phrased.

If neither source exists:

```
[OUTLOOK — requires house view or portfolio manager input]
```

Never generate a forecast of your own.

## 7. Disclosures

The firm's standing disclosure block, carried from the archive verbatim.

If none was found, flag it at the top of the document — commentary cannot be distributed
without required disclosures, and a missing block is a blocking issue rather than a footnote.

---

## Recurring traps

- **Carrying forward last period's market description.** The most common error. Rewrite it.
- **Conflating gross and net** between the performance table and the narrative — distinct from correctly presenting both, labelled.
- **Rounding differently** from the export. Match the export's precision exactly.
- **Turning contribution into attribution of skill** — "contributed" is a fact, "our thesis played out" is a claim.
- **Writing an outlook because the section exists.** A flagged placeholder is correct when there is neither an approved house view nor marked user dictation.
