# DCF Method Reference

## 1. Free cash flow (FCFF / unlevered)

```text
EBIT
  less: taxes on EBIT (EBIT x effective tax rate)
= NOPAT
  plus: D&A
  less: CapEx
  less: increase in net working capital
= Unlevered Free Cash Flow
```

Use FCFF with WACC to reach enterprise value. Use FCFE with cost of equity to reach equity value
directly. **Never mix them** — discounting FCFF at cost of equity is the single most common
structural error in a DCF; the checks battery tests for it.

Forecast horizon defaults to 5 years. Extend to 7-10 when the business has not reached a steady
state by year 5 — a terminal value applied to an un-normalized final year overstates value.

**Drive operating expense off revenue, not off gross profit**, unless the business genuinely works
that way. Expense lines modeled as a percentage of gross profit compound an error through every
forecast year and are a frequent cause of implausible terminal margins.

Margin expansion needs an operational reason stated next to it. A forecast that widens margins
every year without one is an assertion, not a projection.

## 2. Discounting

Default to **mid-year convention** for operating companies: discount factor = 1 / (1 + WACC)^(t - 0.5).
Use end-of-year (t) when the user's existing model does, or when cash flows are genuinely lumpy
and back-loaded. State which convention is in use on the Assumptions tab — the two differ by
roughly half a year of discounting, which is material.

## 3. WACC

```text
WACC = E/(D+E) x Cost of Equity  +  D/(D+E) x Cost of Debt x (1 - tax rate)
```

Cost of equity via CAPM build-up:

| Component | Typical source | Notes |
|---|---|---|
| Risk-free rate | 10-year government bond | Match currency and tenor to the cash flows |
| Equity risk premium | Published market data | Label the source and vintage |
| Levered beta | Regression or comps unlever/relever | Relever at target capital structure, not current |
| Size premium | Published data | Only for smaller-cap targets; say so if applied |
| Company-specific risk | Analyst judgment | Always flag as judgment, never as sourced data |

Weights use **market values**, not book. Using book equity weights is a check failure.

Cost of debt is taken after tax — the statutory or effective rate applied once, to the cost of debt
term only. Applying it twice, or applying it to the cost of equity, understates WACC and inflates
the valuation.

## 4. Terminal value — run both methods

**Perpetuity growth:** `TV = FCF_terminal x (1 + g) / (WACC - g)`

Constraints that are hard errors: `g >= WACC` (infinite/negative value), and `g` above long-run
nominal GDP for the relevant economy without an explicit, stated justification.

**Exit multiple:** `TV = terminal-year EBITDA x exit EV/EBITDA multiple`

The multiple should be defensible against where comparable businesses actually trade, and should
generally not exceed the entry multiple absent a stated re-rating thesis.

**Cross-check both ways.** Back out the implied exit multiple from the perpetuity method and the
implied growth rate from the exit-multiple method. If they disagree materially, at least one is
wrong — surface it rather than averaging.

**TV concentration** is a first-class output. Terminal value above ~75% of enterprise value means
the DCF is mostly an assertion about year 6 onward; report the percentage on the Summary tab and
call it out above that threshold.

## 5. Enterprise value to equity bridge

```text
Enterprise Value
  less: total debt
  plus: cash and equivalents
  less: minority interest
  less: preferred equity
  plus/less: other claims (pension deficit, operating leases if not already in FCF, etc.)
= Equity Value
  divided by: diluted shares outstanding (treasury stock method)
= Value per share
```

Diluted share count must use the treasury stock method for in-the-money options and include
RSUs and convertible dilution. A basic share count in a per-share valuation is a check failure.
Be explicit about lease treatment — double-counting leases in both FCF and net debt is common.

## 6. Reverse-DCF

Mandatory whenever the rating is Buy or Sell. Hold the framework constant and solve for the one
input that reconciles model value to the current market price:

- **Solve for terminal growth** — holding operating assumptions and WACC constant
- **Solve for WACC** — holding operating assumptions and terminal growth constant
- **Solve for a revenue CAGR or steady-state margin** — holding the discount framework constant

Report as: "at the current price, the market is implying ~X% terminal growth; our base case
assumes Y%." Only change one input at a time — a composite scenario that happens to land near the
market price proves nothing.

## 7. Rating thresholds (fixed mapping)

Applied to base-case value per share versus current price:

| Upside/downside to base case | Rating |
|---|---|
| Above +20% | Buy |
| -10% to +20% | Hold |
| Below -10% | Sell |

These thresholds are the default. If the user specifies their own, use theirs and state the
mapping on the Summary tab. The same numbers must always produce the same verb — never adjust
the verb by feel.

**Readiness qualifier:** when decision readiness is Screen-grade, the rating renders as
"Indicative — Screen-grade" with the unresolved inputs named directly beneath it.

## 8. Check battery

| Check | Fails when |
|---|---|
| Discount-rate consistency | FCFF discounted at cost of equity, or FCFE at WACC |
| Terminal growth bound | g >= WACC, or g above stated long-run nominal GDP |
| Capital structure weights | Weights do not sum to 1, or book values used |
| Bridge completeness | Net debt, minority interest, or preferred missing without a stated reason |
| Share count basis | Basic shares used for a per-share value |
| TV concentration | TV above 75% of EV (warning, not failure) |
| Placeholder count | Any placeholder remains — forces Screen-grade readiness |
| Market input staleness | Price or rate older than the stated staleness window |
| Formula error scan | Any Excel error value in the workbook |
| Sensitivity monotonicity | Value fails to move monotonically with WACC or g |
| Sensitivity grid wiring | Grid center cell does not equal the model's base-case per-share value |
| Grid dimensions | Grid has even dimensions, so there is no true center cell |
| Grid variation | Axis dependencies do not reach live model calculations; inspect unrounded results and explain economically flat regions. Equal rounded outputs alone are not a failure |
| Cost of debt tax treatment | Tax applied twice, or applied to the cost of equity |
| Opex driver base | Operating expense modeled off gross profit without a stated reason |
| Source note completeness | A hardcoded input carries no source or assumption note |
