# Formula Reference

**IMPORTANT:** These are illustrative accounting relationships, not a replacement for the template, entity accounting policies or sourced disclosures. Adapt them to the documented sign convention, period, currency, accounting framework and applicable tax rules. Preserve existing formulas unless a justified correction is in scope. Do not double-count expenses or noncash movements.

---

## Core Linkages

```text
Balance Sheet:        Assets = Liabilities + Equity
Net Income:           IS Net Income → indirect CF Operations starting point only
Cash Flow:            ΔCash = CFO + CFI + CFF + FX/other reconciliation effects
Cash Tie-Out:         Ending Cash (CF) = corresponding BS cash definition (bridge restricted cash if needed)
Cash Monthly/Annual:  Final month closing cash = annual closing cash, when both are modeled
Retained Earnings:    Prior RE + Net Income - Dividends + documented RE adjustments = Ending RE
Equity Movements:     ΔCommon Stock/APIC = cash issuance + noncash SBC - issuance costs +/- other supported movements
Opening Equity:       Beginning equity ties to prior closing or documented formation records
```

## Gross Profit Calculation

**IMPORTANT:** Gross Profit must be calculated from Net Revenue, not Gross Revenue.

```text
Net Revenue - Cost of Revenue = Gross Profit
```

| Term | Definition |
|------|------------|
| Gross Revenue | Total revenue before any deductions |
| Net Revenue | Gross Revenue - Returns - Allowances - Discounts |
| Cost of Revenue | Direct costs attributable to production of goods/services sold |
| Gross Profit | Net Revenue - Cost of Revenue |

**Note:** Always use Net Revenue (also called "Net Sales" or simply "Revenue" on most financial statements) as the starting point for profitability calculations. Gross Revenue overstates the true top-line performance.

## Margin Formulas

```text
Gross Margin %      = Gross Profit / Net Revenue
EBITDA              = EBIT + D&A included in EBIT (no double-counting)
EBITDA Margin %     = EBITDA / Net Revenue
EBIT Margin %       = EBIT / Net Revenue
Net Income Margin % = Net Income / Net Revenue
```

## Credit Metric Formulas

Use the covenant or company-specific definition where supplied. Ratios below are illustrative; include leases/restricted cash adjustments only as defined. For zero or negative EBITDA/equity or a missing denominator, report not meaningful and explain. EBITDA-based coverage is not interchangeable with EBIT-based coverage.

```text
Total Debt            = Current Portion of Debt + Long-Term Debt
Net Debt              = Total Debt - Cash
Total Debt / EBITDA   = Total Debt / EBITDA (from IS)
Net Debt / EBITDA     = Net Debt / EBITDA (from IS)
Interest Coverage     = EBITDA / Interest Expense (from IS)
Net Int Exp % Debt    = Net Interest Expense / Long-Term Debt
Debt / Total Cap      = Total Debt / (Total Debt + Total Equity)
Debt / Equity         = Total Debt / Total Equity
Current Ratio         = Total Current Assets / Total Current Liabilities
Quick Ratio           = (Total Current Assets - Inventory) / Total Current Liabilities
```

## Forecast Formulas (% of Net Revenue Method)

Use these only when appropriate to the business and approved drivers. Fixed costs, headcount, unit economics or contract terms may be better. SBC may already be embedded in operating expense; do not subtract it twice.

```text
Cost of Revenue (Forecast) = Net Revenue × Cost of Revenue % Assumption
S&M (Forecast)             = Net Revenue × S&M % Assumption
G&A (Forecast)             = Net Revenue × G&A % Assumption
R&D (Forecast)             = Net Revenue × R&D % Assumption
SBC (Forecast)             = Net Revenue × SBC % Assumption
```

## Working Capital Formulas

Use the actual period length rather than 365 for quarters/stub periods and document whether days metrics use average or ending balances. Purchases may be a better DPO denominator than COGS; use the template's documented basis. Residual collections/purchases/payments below must reconcile an evidenced schedule, not conceal unexplained gaps. Historical CFS working-capital movements can differ from raw BS changes due to acquisitions, FX and reclassifications.

```text
Accounts Receivable
  Prior AR
  + Revenue (from IS)
  - Supported Cash Collections
  +/- Supported noncash/other movements
  = Ending AR
  DSO = (AR / Revenue) × Days in period

Inventory
  Prior Inventory
  + Supported Purchases
  - COGS (from IS)
  +/- Supported noncash/other movements
  = Ending Inventory
  DIO = (Inventory / COGS) × Days in period

Accounts Payable
  Prior AP
  + Purchases (from Inventory calc)
  - Supported Cash Payments
  +/- Supported noncash/other movements
  = Ending AP
  DPO = (AP / documented purchases or COGS basis) × Days in period

Net Working Capital = AR + Inventory - AP
ΔWC = Current NWC - Prior NWC
```

## D&A Schedule Formulas

The simple roll-forward below must also include material disposals, acquisitions, impairment, FX, transfers and accumulated depreciation removed on disposals. Amortization needs a separate intangible-asset schedule when applicable.

```text
Beginning PP&E (Gross)
+ Capitalized additions (reconcile to cash CapEx and noncash additions)
- Gross cost of disposals
+/- Supported acquisitions, FX, transfers and other movements
= Ending PP&E (Gross)

Beginning Accumulated Depreciation
+ Depreciation Expense
- Accumulated depreciation removed on disposals
+/- Supported other movements
= Ending Accumulated Depreciation

PP&E (Net) = Gross PP&E - Accumulated Depreciation
```

## Debt Schedule Formulas

```text
Beginning Debt Balance
+ New Borrowings
- Repayments
+/- Supported noncash movements (FX, conversions, fees/amortization where applicable)
= Ending Debt Balance

Interest Expense = documented balance basis × rate × applicable time fraction
  (Also include supported fees, amortization and other interest components.)
  Use a disclosed beginning-balance approximation only when appropriate.
  Preserve intentional circuit breakers; require approval to change calculation settings.
```

## Retained Earnings Formula

```text
Beginning Retained Earnings
+ Net Income (from IS)
- Dividends
+/- Documented retained-earnings adjustments
= Ending Retained Earnings
```

**SBC treatment:** Expense already reduces net income and therefore retained earnings. Do not add it directly back to retained earnings. Equity-classified awards generally increase APIC; liability-classified awards follow their liability schedule. The noncash expense may be added back in indirect CFO, subject to the actual accounting treatment.

## NOL (Net Operating Loss) and Tax Schedule

Confirm jurisdiction, tax year, NOL vintage, expiry, ownership-change restrictions and applicable law before using a limit. An 80% utilization cap is not universal. The first forecast year is not necessarily business formation: opening tax losses must be sourced, not forced to zero.

```text
Beginning eligible tax-basis NOL (sourced)
+ Current tax losses generated under applicable rules
- Eligible NOL utilized
- Expirations / other supported reductions
= Ending NOL

Taxable income before loss relief = Book EBT +/- supported book-to-tax adjustments
NOL use = limited by eligible available losses and the applicable utilization rules
Taxable income after relief = taxable income before relief less eligible NOL use
Current tax expense = tax determined under applicable rates, credits and rules
Book tax expense = Current tax expense + Deferred tax expense (or benefit)
Net income = Book EBT - Book tax expense
```

Do not deduct NOL use directly from book net income. Cash taxes paid also reflect tax payable/receivable movements, settlements and refunds; they are not automatically equal to tax expense. A book loss can coexist with current tax expense, and a deferred tax benefit is not automatic.

```text
Gross NOL DTA = eligible tax losses x applicable enacted tax rate(s), subject to framework
Net DTA = recognized gross DTA less valuation allowance / recognition adjustments
```

Reconcile the balance-sheet DTA to the tax schedule. Consider realizability and the accounting framework. A DTA increase arising through profit and loss ordinarily produces a noncash tax benefit, reversed by subtraction in indirect CFO; a decrease ordinarily produces a noncash expense, reversed by addition. Do not mechanically use the whole balance-sheet change: isolate acquisition, OCI, FX and other non-P&L movements. Do not count this reversal twice if already included in a deferred-tax adjustment.

## Balance Sheet Structure

```text
ASSETS
  Cash (from CF ending cash)
  Accounts Receivable (from WC)
  Inventory (from WC)
  Total Current Assets

  PP&E, Net (from DA)
  Deferred Tax Asset - NOL (from NOL schedule)
  Total Non-Current Assets
  Total Assets

LIABILITIES
  Accounts Payable (from WC)
  Current Portion of Debt (from Debt)
  Total Current Liabilities

  Long-Term Debt (from Debt)
  Total Liabilities

EQUITY
  Common Stock / APIC
  Other equity components where applicable
  Retained Earnings (from RE schedule)
  Total Equity

CHECK: Assets - Liabilities - Equity = 0
```

## Cash Flow Statement Structure

This is an **indirect-method illustration**, not a required layout. Preserve direct-method templates: populate supported cash receipts and payments, not NI plus add-backs in their place. Complete any required indirect reconciliation separately. Apply the entity's accounting framework to interest/dividend classifications. The limited lines below do not authorize omission of other material cash flows.

```text
CASH FROM OPERATIONS (CFO)
  Net Income (LINK: IS)
  + D&A (LINK: DA schedule)
  + Noncash Stock-Based Compensation included in NI (LINK: source schedule)
  +/- Noncash deferred tax expense / benefit reversal (LINK: tax schedule; not itself a cash flow)
  - ΔAR (LINK: WC)
  - ΔInventory (LINK: WC)
  + ΔAP (LINK: WC)
  = CFO

CASH FROM INVESTING (CFI)
  - CapEx (LINK: DA schedule)
  = CFI

CASH FROM FINANCING (CFF)
  + Debt Issuance (LINK: Debt)
  - Debt Repayment (LINK: Debt)
  + Cash Equity Issuance (LINK: equity schedule; excludes noncash APIC movements)
  - Dividends (LINK: RE schedule)
  = CFF

Net Change in Cash = CFO + CFI + CFF + FX / other reconciliation effects
Beginning Cash
+ Net Change in Cash
= Ending Cash (LINK TO: BS Cash)
```

## Income Statement Structure

```text
Net Revenue
  Growth %
(-) Cost of Revenue
  % of Net Revenue
────────────────
Gross Profit (= Net Revenue - Cost of Revenue)
  Gross Margin %

(-) S&M
  % of Net Revenue
(-) G&A
  % of Net Revenue
(-) R&D
  % of Net Revenue
(-) D&A only if not already included in operating costs
(-) SBC only if not already included in operating costs
  Documented driver
────────────────
EBIT
  EBIT Margin %

EBITDA
  EBITDA Margin %

(-) Interest Expense
────────────────
EBT (Pre-Tax Income)
(-) Book tax expense (current + deferred, from tax schedule)
────────────────
Net Income
  Net Income Margin %
```

## Check Formulas

```text
BS Balance:          Assets - Liabilities - Equity = 0
Cash Tie-Out:        BS corresponding cash - CF ending cash = 0, with definition bridge
NI Link:             IS NI - indirect-CF starting NI = 0
RE Roll-Forward:     Prior RE + NI - Dividends + documented RE adjustments - BS RE = 0
DTA Tie-Out:         Tax schedule net DTA - BS net DTA = 0
Equity Roll-Forward: Beginning equity + all supported cash/noncash movements - Ending equity = 0
Monthly / Annual:   Final month ending cash - annual ending cash = 0, if applicable
NOL Availability:   Eligible loss use <= available eligible losses
NOL Limits:         Eligible loss use complies with sourced jurisdiction/vintage restrictions
NOL Non-Negative:   Ending NOL >= 0
Opening Balances:   Tie to prior closing or formation records, not assumed zero
```

Document a scale-appropriate rounding tolerance. A missing input, absent recalculation or unperformed check is **not verified**, not a pass. Cash presentation and interest/dividend classifications must follow the applicable accounting framework and existing template.
