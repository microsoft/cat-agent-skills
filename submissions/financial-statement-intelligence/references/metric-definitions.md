# Metric reference

## Sign convention (v2 input)
Values are entered as presented on the statement: revenue, assets, liabilities and equity positive; **expenses and cash outflows negative** (cost of sales, opex, interest expense, tax expense, capex, dividends, buybacks, debt repaid). Subtotals are therefore plain sums of their `total_of` components. Formulas below that use an expense or outflow negate it (e.g. interest coverage = EBIT / −interest_expense). A sign check fails if revenue, total assets, COGS, interest expense, capex, dividends or buybacks have the wrong sign.

## Canonical line ids
Ratios look up lines by id. Use these ids when the line exists; other ids are displayed but not used by ratios.

| Statement | Required for core ratios | Recommended / optional |
|---|---|---|
| Income statement | `revenue`, `cogs`, `gross_profit`, `operating_income`, `interest_expense`, `pretax_income`, `tax_expense`, `net_income` | `sga`, `r_and_d`, `interest_income`, `ebitda` (reported; otherwise EBIT + D&A) |
| Balance sheet | `cash`, `receivables`, `inventory`, `current_assets`, `total_assets`, `payables`, `current_liabilities`, `total_liabilities`, `equity`, debt lines tagged `debt` | `short_term_investments`, `ppe`, `intangible_assets`, `goodwill`, `non_current_assets`, `short_term_debt`, `long_term_debt`, `lease_liabilities`, `non_current_liabilities`, `share_capital`, `retained_earnings`, `total_liabilities_and_equity` |
| Cash flow | `ocf`, `capex`, `icf`, `financing_cf`, `cash_begin`, `cash_end` | `cf_net_income`, `d_and_a`, `change_receivables`, `change_inventory`, `change_payables`, `dividends_paid`, `share_buybacks`, `fx_cash` |
| Shareholder basis (optional) | — | `net_income_attributable` (profit attributable to shareholders), `shareholders_equity` (equity attributable to shareholders), `perpetual_bonds` (perpetual bonds / other equity instruments inside it), `perpetual_distributions` (positive; amount attributable to perpetual holders, if disclosed). Ordinary equity = shareholders_equity − perpetual_bonds. When present, ROE = (attributable profit − perpetual distributions) / average ordinary equity, and EPS/BVPS use them. |
| Other optional | — | `ebit` (reported EBIT, overrides the derivation), `restricted_cash` (balance-sheet cash that is not a cash equivalent), lines tagged `debt_like` (e.g. notes payable). |
| Supplementary | — | `shares_outstanding` (same scale as `unit`), `share_price` (currency ones) |

Liabilities are entered as **positive** numbers even when the report prints them in brackets. Sign checks fail for negative `payables`, `short_term_debt`, `long_term_debt`, `lease_liabilities`, `current_liabilities`, `non_current_liabilities` or `total_liabilities`. When a report uses a net-current-liabilities or net-assets layout and prints no total assets or total liabilities, declare those lines with `total_of` and no reported value.

## Definitions
Ratios use consistent fiscal-period currencies and units. Average balances = (opening + closing) / 2; if the prior-year balance is missing the result is N/A, never a substitute ending value. Any ratio with a zero or negative denominator is N/A.

**Intermediate:** total debt = sum of lines tagged `debt`; net debt = total debt − cash; net debt incl. debt-like items = net debt + lines tagged `debt_like` (sensitivity only); EBIT = reported `ebit` line, else per `ebit_method`: `operating_income`, or profit before tax + interest expense (`pretax_plus_interest`, default for CAS, where 营业利润 is after finance costs); EBITDA = reported EBITDA, else EBIT + D&A; effective tax rate = −tax_expense / pretax_income; NOPAT = EBIT × (1 − effective tax rate), N/A when the rate is outside 0–100%; invested capital = equity + total debt − cash.

**Profitability:** gross, EBITDA, operating and net margin = respective profit / revenue.

**Returns:** ROA = net income / avg total assets; ROE = attributable profit to ordinary shareholders / avg ordinary equity when the shareholder-basis lines are supplied, otherwise net income / avg total equity; ROIC = NOPAT / avg invested capital. DuPont 3-factor = net margin × asset turnover × (avg assets / avg equity). 5-factor = tax burden (NI / PBT) × interest burden (PBT / EBIT) × EBIT margin × asset turnover × equity multiplier. DuPont ROE is on the total-equity basis, so it can differ from shareholder-basis ROE.

**Liquidity:** current ratio = current assets / current liabilities; quick ratio = (cash + short-term investments + receivables) / current liabilities; cash ratio = cash / current liabilities; working capital = current assets − current liabilities.

**Leverage:** debt/equity = total debt / equity; debt/assets = total debt / total assets; net debt/EBITDA; interest coverage = EBIT / −interest_expense.

**Efficiency:** asset turnover = revenue / avg total assets; DSO = avg receivables / revenue × days; DIO = avg inventory / −COGS × days; DPO = avg payables / −COGS × days; CCC = DSO + DIO − DPO. `days` comes from each period; do not assume 365 for non-standard periods.

**Cash flow quality:** free cash flow = OCF + capex (capex negative); FCF margin = FCF / revenue; cash conversion = OCF / net income; capex intensity = −capex / revenue; dividend payout = −dividends_paid / net income; accrual proxy = (net income − OCF) / avg total assets.

**Growth:** current / prior − 1 where the prior value is positive, and only when both columns have the same period type and length (±5 days). Avoid growth percentages across sign changes.

## Interim periods
For `period_type: interim` columns, flow-over-balance ratios are annualised by ×365/days: ROA, ROE, ROIC, asset turnover, accrual proxy, FCF yield; net debt/EBITDA, EV/EBITDA and P/E annualise the flow. Margins, cash conversion and payout ratios are not annualised. Days ratios (DSO/DIO/DPO) use the period's own days. The cash-vs-balance-sheet check runs only when the balance sheet date equals the flow period end; the opening-cash continuity check runs only between consecutive annual periods.

**Per share and valuation** (only when supplementary data is supplied): EPS = net income / shares; BVPS = equity / shares; market cap = price × shares; EV = market cap + net debt; P/E, P/B, EV/EBITDA, FCF yield = FCF / market cap.

## Schedules (derived tables)
Working capital, debt and net debt, EBITDA and free cash flow, cash reconciliation, PP&E roll-forward and equity roll-forward. Roll-forward "other movements" rows are **derived balancing figures**, not source data; label them as such in any narrative.

Missing required inputs yield N/A, not extrapolations. Different company conventions may require adjusted EBITDA or alternate definitions; do not call these statutory metrics.

## Financial institutions (`entity_type` bank, insurer, broker_dealer, other_financial)
All entity types are in scope. For these types the balance sheet is the business, so current/quick/cash ratios, working capital, DSO/DIO/DPO, EBITDA, net debt and interest coverage are **omitted**, and the working-capital, debt, EBITDA/FCF and PP&E schedules are dropped. `revenue` = total operating income (banks) or total revenue / insurance revenue.

| Id | Statement | Meaning |
|---|---|---|
| `net_interest_income` | Income statement | Net interest income |
| `operating_expenses` | Income statement | Operating expenses (negative) |
| `impairment_losses` | Income statement | Credit impairment / expected credit loss charge (negative) |
| `insurance_revenue`, `insurance_service_expenses` | Income statement | IFRS 17 insurance revenue and insurance service expenses (negative) |
| `loans`, `deposits`, `interest_earning_assets` | Balance sheet | Customer loans (net), customer deposits, interest-earning assets |
| `cet1_ratio`, `total_capital_ratio`, `solvency_ratio` | Supplementary | Reported regulatory ratios as decimals (0.145 = 14.5%) |

Metrics: net margin; cost-to-income = −operating_expenses / revenue; NIM = net interest income / average interest-earning assets (average total assets if not supplied); cost of risk = −impairment / average loans; combined ratio = −insurance service expenses / insurance revenue; ROA; ROE; equity / total assets; loan-to-deposit; loans / total assets; reported capital and solvency ratios; operating income, net income, loan and deposit growth. Flow-based ratios are annualised for periods that are not 12 months.

`asset_manager` and `payment_institution` use the operating-company metric set, with a note that the balance sheet may include client or safeguarded funds.

## Period length
Any period that is not 360–371 days (interim, or e.g. an 18-month comparative) has returns and turnover annualised (×365/days); growth is computed only between periods of the same type and length (±5 days).

## Conglomerates (`entity_type` conglomerate)
Operating-company metrics plus the financial-services metrics above where inputs exist. Debt = borrowings tagged `debt` outside the financial businesses (never bank deposits). Net debt = that debt − `cash_non_financial` (cash excluding the banking/securities/insurance businesses); if `cash_non_financial` is not supplied, net debt and net debt / EBITDA are N/A rather than distorted by the bank's cash. `loans` = all customer loans and card receivables of the financial businesses; `deposits` = customer deposits.

## Cost of sales
`cogs` is mapped only from a cost-of-sales line (function-of-expense presentation). Nature-of-expense income statements have no gross margin; inventory and payables days are then N/A.

## Added in 0.7.0
- **Net cash.** Net debt = debt − cash; negative means net cash. Net debt / EBITDA is N/A when net debt ≤ 0 (the findings state the net cash). Interest coverage is N/A when debt is 0. Gross debt / EBITDA is shown as a fallback (conglomerates without non-financial cash).
- **EBITDA.** Reported `ebitda` if supplied; else EBIT + D&A − lines tagged `impairment` (+ `share_of_associates_itda`), labelled "derived".
- **Tax rate and NOPAT.** Effective tax rate = −tax / (pretax − `share_of_associates`) when associates are mapped; N/A outside 0–100%. NOPAT = (EBIT − associates if inside EBIT) × (1 − rate) + associates.
- **Averages.** Average balances are N/A when the balance moves more than 5× between opening and closing (large dividends, capital reductions). `opening_*` supplementary lines provide first-year opening balances.
- **One-offs.** Net income before one-off items = net income − lines tagged `non_recurring` / `impairment` (pre-tax; tax effect not adjusted).
- **Cash.** Net debt and invested capital use cash excluding shown restricted deposits; otherwise the cash flow statement's cash equivalents at the same balance sheet date (or the next period's opening cash for a prior year end); else balance sheet cash.
- **Coverage incl. perpetuals** = EBIT / (interest + `perpetual_distributions`). **Current ratio excl. client funds** = (CA − `client_funds`) / (CL − `client_liabilities`).
- **Conglomerates.** OCF and FCF excluding lines tagged `fs_operating`.
- **Checks.** Profit attribution (owners + `attribution` lines = net income); profit before tax income statement vs cash flow (`cf_pretax_income`); interim opening cash vs prior year-end balance sheet cash (REVIEW when the gap is restricted cash).
