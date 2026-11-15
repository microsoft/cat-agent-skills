# Default Research Brief Outline

**Workflow boundary:** a matched two-filing risk-factor/MD&A/guidance language diff with retrieval coverage. Include metric movements only as context for those compared passages, never as a separate corporate financial-variance narrative. A house template cannot remove the diff or expand the job.

Structure for `security-research-brief`. A house template in
`Cowork Templates/Asset Management/security-research-brief/` may replace this layout, subject to the guardrails below.

A house template governs **layout and section structure only**. It never removes citations, gap markers, source tiers, approval states, information-barrier rules, no-send restrictions, or the output footer — those apply to every output regardless of template. Output length never waives attribution or the footer; a one-line answer, single table cell, inline reply, or short excerpt still carries both. If a save, export, or write fails, report what was produced, where it was and was not written, and what remains incomplete.

The brief answers one question: **what changed?** Anything that did not change belongs in a
profile, not here.

---

## 1. Header

Issuer, ticker, and the **two filings being compared** — form, period end, accession number
for each. State this before anything else; every finding below depends on it.

## 2. What changed — the summary

Five to eight bullets, most material first. Each one states the change and cites where it came
from. No interpretation of what it means for the investment case.

Write: *"Guidance for FY revenue narrowed from $4.2–4.6bn to $4.4–4.5bn (8-K, 2026-07-22)."*
Not: *"Management appears more confident."*

## 3. Metric context for the compared passages

Include only metrics supporting a matched filing-language comparison. Do not fill a standard
financial table for its own sake or add standalone operating-variance narrative.

| Metric | Prior | Current | Change | Basis (prior / current) | Period ends | Compared passage / language change |
|---|---|---|---|---|---|---|
| <source-supported metric> | | | | prior / current | prior / current | <matched passage and citation> |

Segment metrics follow the same passage-linked rule.

Always show **period end dates**, never fiscal-year labels alone.

**Prior and Current each carry their basis** — `as-reported (filing, accession)` or
`standardized (<connector>, as-of)`. Where they differ, `Change` reads `NOT COMPARABLE — mixed
basis`, not a number. A change computed across a standardized figure and an as-reported figure is
not a real change.

## 4. Risk factor diff

The highest-value section. Three lists:

**Added** — quote the new risk factor, or its opening sentence where long.
**Removed** — quote what the prior filing said, and note that the language **is not present** in
the current filing. Do not say why; consolidation and incorporation by reference look identical
to removal.
**Reworded** — prior and current language side by side.

```
PRIOR (10-K FY2025): "We may experience supply constraints..."
CURRENT (10-K FY2026): "We have experienced, and expect to continue to experience,
                        supply constraints..."
```

Report the change. Do not grade its severity.

**Completeness gates are symmetric — both lists require both Item 1A sections in full.**

| List | Requires |
|---|---|
| `Added` | Complete retrieval of **both** sections — an unread part of the prior filing looks exactly like a new risk |
| `Removed` | Complete retrieval of **both** sections — an unread part of the current filing looks exactly like a deletion |
| `Reworded` | Both passages actually retrieved and matched |

If either section was partial:
- Omit **both** the `Added` and `Removed` lists, mark them `NOT RETRIEVED`, and say so **here**,
  not in a footnote.
- For a risk present in the current filing whose novelty you cannot establish, write
  **"currently disclosed; novelty unverified"** — never `new` or `added`.
- Report wording comparisons only for passages retrieved from both periods, and state that the
  comparison is **not an exhaustive diff**.

Carry the coverage status next to the lists, where the reader sees the claim.

## 5. MD&A and guidance language

Paired quotes showing what changed in how management explains the business. Topics **not present**
in the current filing may be included only when both MD&A sections were retrieved in full —
otherwise mark that comparison `NOT RETRIEVED`. Absence is a signal, but only when you are certain
you actually read the whole section.

## 6. Earnings call

Prepared-remarks summary and notable Q&A with speaker/source attribution; quote only brief necessary excerpts where permitted, otherwise summarize.

If no public transcript exists: `NOT FOUND — no public transcript`, and note that the 8-K
release was used instead.

## 7. Continuity with prior firm research

Where the firm's prior research note is available in SharePoint: what it flagged to watch, and
whether this filing resolved it. Cite the note by name and date.

Omit the section entirely if no prior note exists — do not speculate about the firm's view.

## 8. Open questions

Things the filing raises but does not answer, phrased as questions for the analyst. Not
predictions, not recommendations.

---

## What this brief never contains

A rating, a price target, a valuation, a recommendation, a forecast, or a judgment that the
security is attractive or unattractive. Those are the analyst's, and this document is an input
to that judgment.
