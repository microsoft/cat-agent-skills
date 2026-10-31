# Workbook Spec

Fixed tab order. The workbook **must open on Summary** — never on a raw calculation tab.

| # | Tab | Contents |
|---|---|---|
| 1 | **Summary** | Header, first-read status block, valuation summary, rating, drivers, open items |
| 2 | **Assumptions & Sources** | Every input with value, source, retrieval date, confidence |
| 3 | **Historicals** | Revenue through FCF, 4 years plus LTM, with margins and growth |
| 4 | **FCF Build** | Revenue projection and the full unlevered FCF build, by forecast year |
| 5 | **WACC** | CAPM build-up, cost of debt, capital structure, resulting WACC |
| 6 | **TV & Bridge** | Both terminal-value methods, cross-check, EV-to-equity bridge |
| 7 | **Sensitivities** | WACC x g grid, scenario table, reverse-DCF solve |
| 8 | **Comps** | Comparable trading multiples with median and target (context, not conclusion) |
| 9 | **Checks** | Full check battery with pass/fail/warn and the failing detail |

## The first-read status block (Summary, top of tab)

Two labeled fields that are allowed to disagree, side by side:

```text
Calculation integrity:  PASS / FAIL — <count> checks, <n> failures
Decision readiness:     Senior-ready / Screen-grade — <reason>
```

Directly beneath, in this order:

1. **Valuation range** — low / base / high per share
2. **Current price** and premium/discount to base case
3. **Rating** with its readiness qualifier
4. **Market-implied assumption** from the reverse-DCF
5. **TV as % of EV**, flagged when above 75%
6. **Top three value drivers** from the sensitivity grid
7. **Open items** — every placeholder and stale input, named
8. Standing line: *Analytical support, not investment advice.*

## Formatting conventions

- **Live formulas, not hardcoded values**, everywhere downstream of an input. A banker must be
  able to change a cell on Assumptions and watch the whole model move.
- Input cells in blue, formulas in black, cross-tab links in green — standard banker convention.
- Negatives in parentheses. Currency in millions unless the user specifies otherwise, with the
  unit stated in every table header.
- Multiples to one decimal with an `x`. Percentages to one decimal.
- Sensitivity grid: base case bolded and boxed at the center; conditional color scale across the
  grid; row and column headers showing the actual WACC and g values, not offsets.
- **Grid dimensions are odd — 5x5 or 7x7, never 4x4 or 6x6.** Only odd dimensions have a true
  center cell. Axis values run symmetrically around the base case
  (`base-2d, base-d, base, base+d, base+2d`).
- **The center cell must equal the model's actual base-case per-share value.** That equality is the
  proof the grid recalculates the model rather than approximating it. It is a check, not a
  formatting nicety — it appears in the check battery and on the Checks tab.
- Every cell is a full recalculation at that assumption pair, and no two cells should be identical.
  No linear interpolation, no placeholder text, no manual steps left for the reader.
- Every tab has a title row naming the company, the analysis date, and the currency/unit.

## Scenario blocks

Where the model carries Bear / Base / Bull cases, give each case its own assumption block rather
than scattering case logic through the projection.

- Each block holds the full set of assumptions across the projection years, with a **year header
  row immediately below the block title** — without it, a reader cannot tell which value belongs to
  which year.
- A single case-selector cell drives the model (1 = Bear, 2 = Base, 3 = Bull).
- A **consolidation column** pulls the active case's values with an `INDEX` against that selector,
  and every projection formula references the consolidation column — not the case blocks directly.

Centralizing the case logic in one column keeps it auditable. Scattering nested `IF` statements
across the projection means a reviewer has to check every formula to know which case is live.

## Provenance

Every headline output on Summary carries a note pointing to the tab and cell that produced it —
e.g. *"EV from 'TV & Bridge'!C18"*. Internal workspace paths, tool names, and session identifiers
never appear anywhere in the workbook.

**The source note is written as each input is entered, never deferred.** Finish a section only when
every hardcoded value in it carries its note. "TODO: add source" is not a source, and a note
gathered at the end is a note reconstructed from memory.

Cite the specific location rather than the publication:

- *"FY24 10-K, page 42, line item 'Total Revenue'"* — not *"annual report"*
- *"10-year Treasury, retrieved 14 Sep 2026 (web-sourced)"* — not *"market data"*
- *"Street consensus EPS $3.45, average of 12 estimates, as of 14 Sep 2026"*

Where a value is an assumption rather than a retrieved fact, the note carries the reasoning instead
of a source — *"EBITDA margin held at the peer median; company does not disclose segment margin"* —
so a reader can tell sourced fact from analyst judgment at a glance. Record source URLs in the note
or on the Assumptions tab; never replace a cell's value with a URL.

## Companion artifacts

Generated **from the Checks tab and workbook cell values**, never from chat recollection.

- **PPTX** — title slide carries the readiness stamp; then valuation range, FCF and WACC
  assumptions, sensitivity grid, reverse-DCF, risks. Regenerated on every run, never hand-edited.
- **HTML** — same content, standalone, on explicit request only.
