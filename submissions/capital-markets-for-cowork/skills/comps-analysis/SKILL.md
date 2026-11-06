---
name: "comps-analysis"
description: >-
  Builds a comparable company analysis: selects a defensible peer set with
  stated inclusion criteria, pulls trading multiples and operating metrics,
  calculates the median and quartiles, and applies the range to a target to
  produce an implied valuation. Use when the user asks to "build a comps
  table", "run comparable company analysis", "trading comps for this company",
  "what multiple do peers trade at", "who are the comps", or "value this
  against its peers". Do NOT use for a company profile — use
  company-profile-pack instead; deal accretion — use merger-model instead; or
  discounted cash flow, LBO, or precedent transaction analysis.
metadata:
  icon: ArrowTrendingLines
---

# Comparable Company Analysis

Builds a trading comps set where the peer selection is defensible, the multiples are calculated
consistently, and the implied range carries its assumptions in the open.

## When NOT to Use

- **Intrinsic valuation from cash flows** — outside this skill's scope.
- **Leveraged buyout returns analysis** — outside this skill's scope.
- **Precedent M&A transactions** — a different dataset with control premiums
- **Post-results company research with no multiples** — use earnings-note instead.
- **Pre-results research or initiating coverage** — outside this package; request a verified
  host research destination or identify the workspace administrator as dependency owner.

## Related Skills

Hand off rather than overlap:

- Cash flow valuation and terminal value — outside this skill's scope.
- Sponsor returns and capital structure — outside this skill's scope.
- Investment committee recommendation — use ic-memo instead.
- Company profile or tear sheet — use company-profile-pack instead.
- Rendering metrics as a table or card — use render-ui instead.
- Demand and supply planning review — outside this skill's scope.
- Contract clause comparison — outside this skill's scope.
- Budget or target consolidation — outside this skill's scope.

## Workflow

### 1. Define the target and the screening criteria

Establish the target company and the basis for the peer set **before** naming any peers. State the
criteria explicitly — industry and sub-sector, size range, geography, growth profile, margin
profile, and business model.

**Peer selection is the entire analysis.** A comps table whose selection rule is unstated is not
reviewable, so write the rule down first and let the names follow from it.

State the question the table has to answer, because it decides which columns earn their place:

| Question | Lead with | Leave out |
|---|---|---|
| Which company is undervalued? | EV/Revenue, EV/EBITDA, P/E, market cap | Operating detail, growth metrics |
| Which is most efficient? | Gross, EBITDA and FCF margin, asset turnover | Size metrics, absolute dollars |
| Which is growing fastest? | Revenue growth, EBITDA CAGR, customer growth | Margin metrics, leverage |
| Which generates the most cash? | FCF, FCF margin, FCF conversion, capex intensity | EBITDA, P/E |

### 2. Build the peer set

Propose 5-10 peers, each with a one-line justification tied to the stated criteria. Mark any peer
that fails part of the criteria as an outlier candidate rather than quietly dropping it.

Check `input/` and `sharepoint_onedrive-SearchDrive` for an existing peer set or house screen
first — many firms have one, and diverging from it needs saying.

### 3. Choose the metrics deliberately

**The 5-10 rule:** five operating metrics (revenue, growth, two or three margin and efficiency
measures) and five valuation metrics (market cap, enterprise value, three multiples). Ten columns
tell the story; past fifteen you are adding noise, not rigor. Edit ruthlessly.

Sector determines which metrics are meaningful and which are actively misleading:

| Sector | Must have | Do not use |
|---|---|---|
| Software / SaaS | Revenue growth, gross margin, Rule of 40 | Asset turnover, inventory metrics |
| Manufacturing / industrials | EBITDA margin, asset turnover, capex/revenue | Rule of 40, SaaS metrics |
| Financial services | ROE, ROA, efficiency ratio, P/E | Gross margin, EBITDA — not meaningful for banks |
| Retail / e-commerce | Revenue growth, gross margin, inventory turnover | Heavy R&D or capex metrics |

Optional additions where the data supports them — ARR, net dollar retention and CAC payback for
SaaS; backlog and inventory turns for industrials; net interest margin for financials; same-store
sales for retail.

### 4. Gather the data

Source priority: user-supplied data, then internal files, then any connected market-data provider,
then `host-web_search` for public filings and current prices.

**Label every figure with its source and date.** Where market data comes from a web search rather
than a data feed, say so — a comps table sourced from search results and one sourced from a
terminal are not the same artifact, and the reader must know which they hold.

**Record the source as you capture each figure, never at the end.** A deferred source note becomes
a missing one. Cite the specific location, not the publication: "FY24 10-K, page 42, line item
'Total Revenue'" or "street consensus as of 14 Sep 2026", not "annual report". Where a figure is an
assumption rather than a retrieved fact, record the reasoning in the same place — "EBITDA margin
assumed at the peer median; company does not disclose" — so a reader can tell the two apart.

For each company capture: share price, diluted shares, market cap, net debt, enterprise value,
revenue, EBITDA, EBIT, net income, and growth and margin metrics for the periods in scope.

### 5. Calculate multiples consistently

EV/Revenue, EV/EBITDA, EV/EBIT, and P/E, on a stated basis — last twelve months or forward, but
**the same basis for every company in the table.** Mixing LTM for one peer and forward for another
is the most common error in a comps set.

Report **median and quartiles, not just the mean** — one outlier drags a mean badly at this sample
size. Show the target's own multiples against the set.

**Never average a set of percentages or multiples as if they were levels** — margins, growth rates
and multiples are ratios, and their median is the honest central measure.

### 6. Sanity-check before the range goes anywhere

Run these against the finished table. Each one catches a real error class:

- **Margin hierarchy diagnostic** — compare gross, EBITDA and net margins on consistent
  definitions. Exceptions can arise from non-operating income, tax benefits or line-item
  classification; investigate and explain them rather than declaring an error by definition.
- **Multiple plausibility** — EV/Revenue typically 0.5-20x (varies widely by sector), EV/EBITDA
  typically 8-25x (fairly consistent across sectors), P/E typically 10-50x depending on growth. A
  figure outside its band is either a genuine outlier worth naming or a bad input.
- **Growth-multiple relationship** — higher growth normally carries a higher multiple. A
  fast-growing peer on the lowest multiple in the set needs an explanation, not a footnote.
- **Numerator and denominator agree** — enterprise value over an equity metric, or market cap over
  an enterprise metric, is the error that silently invalidates a whole column.
- **Period alignment** — the numerator's date and the denominator's period must match; LTM revenue
  under a current EV is right, quarterly revenue under it is not.

### 7. Apply the range and build the output

Apply the peer median and quartile multiples to the target's metrics to derive an implied
enterprise value, equity value, and per-share range.

Use the `xlsx` skill: a summary tab with the implied range, a comps table tab, and a
sources-and-criteria tab recording the screening rule and every figure's provenance. Confirm the
file exists before reporting it.

**Every derived cell is a live formula, not a pasted result.** Margins, multiples, medians and
quartiles reference their input cells so the table moves when a price or an estimate is corrected.
The only hardcoded values are raw inputs — price, share count, revenue, EBITDA — and each of those
carries the source note from step 4. A pasted-in margin is a silent bug waiting for the next
update.

Keep inputs visually distinct from calculations — inputs in blue, formulas in black, cross-tab
links in green is the convention a banker will expect.

### 8. Check in as you go, not at the end

Do not build the whole table and then present it. Stop at each of these and confirm before
continuing:

- **After the peer set** — show the names and the criteria each one satisfies, before pulling data
- **After the raw inputs** — show the input block with sources and periods, before building formulas
- **After the operating metrics** — show the calculated margins and growth, before adding multiples
- **After the multiples** — show them against the statistics block, before applying the range

A wrong basis caught at the input block costs a minute; the same error found after the implied
range is built means rebuilding everything downstream of it.

### Example

```text
Peer set - criteria: enterprise software, $500M-$3B revenue, North America,
15-30% growth, positive EBITDA. 6 peers; 1 excluded as an outlier.

                    EV/Rev   EV/EBITDA    P/E    Growth   EBITDA margin
  Peer A             4.2x       18.1x    31.2x     22%        23%
  Peer B             3.1x       14.6x    26.8x     17%        21%
  Peer C             5.8x       24.3x    44.1x     29%        24%
  Peer D             2.9x       13.2x    22.4x     15%        22%
  Peer E             4.6x       19.8x    35.0x     24%        23%
  ---
  Median             4.2x       18.1x    31.2x     22%        23%
  Q1 / Q3      3.1x-4.6x  14.6x-19.8x
  TARGET             3.4x       15.9x    27.1x     19%        21%
  (excluded: Peer F at 11.2x EV/Rev - 61% growth, outside the criteria)

IMPLIED (median applied)   EV $1.26B   Equity $1.09B   $27.40/share
IMPLIED (Q1-Q3 range)      $20.10 - $29.80/share   vs current $22.60

Basis: LTM for all companies. Prices as of 17 Aug 2026 (web-sourced).
```

## When Things Fail

- **If fewer than 4 credible peers exist** — say so and state that the sample is too small for a
  reliable median rather than padding with poor fits.
- **If a metric is unavailable for a peer** — leave it blank and note it; never interpolate a
  multiple from the others.
- **If market data cannot be retrieved** — build the structure with clearly marked placeholders and
  state that the table is unpriced.
- **If the target's own basis differs** from the peers' (different fiscal year end, different
  reporting standard) — flag it prominently; it can invalidate the comparison.
- **If a sanity check fails** — fix the input or name the peer as a genuine outlier with the
  reason. Never leave a broken margin hierarchy or an out-of-band multiple sitting unremarked in a
  table someone else will read as clean.
- **If the data is stale** — state the age. An undisclosed old price is worse than a disclosed one.
- **If a tool errors** — retry once, then continue and name what is missing.

## Output Format

A workbook in `output/` with the implied range on the first tab; an inline table when the user just
wants the numbers. Always state the multiple basis and the price date.

## Guardrails

- **Never fabricate a peer's multiple, price, or financial metric.** Blank and noted beats invented.
- **Never present a peer set without its selection criteria** — an unstated rule is not reviewable.
- **Never mix multiple bases** within one table; state the basis explicitly.
- **Never leave a hardcoded input without its source note**, and never defer the note to the end —
  it is written as the figure is captured or it does not get written.
- **Never mix an enterprise-value numerator with an equity denominator**, or a numerator and
  denominator covering different periods.
- Date-stamp all market data and label web-sourced figures as such.
- Report median and quartiles alongside any mean; disclose exclusions and why.
- Keep derived cells as live formulas; the only hardcoded values are raw inputs.
- Cap the table at ten columns unless the user asks for more; more metrics is not more insight.
- This is analytical support, not investment advice — state that on the output.
