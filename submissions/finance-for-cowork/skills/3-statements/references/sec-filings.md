# SEC Filings Data Extraction Reference

**When to Use:** Only reference this file when a model template specifically requires pulling data from SEC filings (10-K, 10-Q). For templates that provide data directly or use other data sources, this reference is not needed.

---

## Extracting Data from SEC Filings (10-K / 10-Q)

When populating a model template with public company data, extract financials directly from SEC filings.

### Step 1: Locate the Filing

1. Use available `web_search` / `web_fetch` to locate and read the exact company filing; confirm registrant identity, form, fiscal period and filing date. EDGAR company search example: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=[TICKER]&type=10-K`
2. For quarterly data, use `type=10-Q`. If retrieval is blocked, request the filing or an accessible copy; do not invent figures or silently substitute a search snippet.
3. Record source URL, filing date, statement/note and page where available for each historical hardcode. Do not include private workbook contents in public searches.

### Step 2: Identify Filing Currency

Before extracting data, identify the reporting currency:

- Check the cover page or header for reporting currency
- Look at statement headers (e.g., "in thousands of U.S. dollars")
- Review Note 1 (Summary of Significant Accounting Policies)

#### Common Currency Indicators

| Indicator | Currency |
|-----------|----------|
| $, USD | US Dollar |
| €, EUR | Euro |
| £, GBP | British Pound |
| ¥, JPY | Japanese Yen |
| ¥, CNY, RMB | Chinese Yuan |
| CHF | Swiss Franc |
| CAD, C$ | Canadian Dollar |

Preserve the agreed model currency and scale. If they differ from the filing, use sourced translation rates under the applicable policy and record the conversion; obtain confirmation before changing the model's currency. Document the basis in the existing assumptions area.

### Step 3: Navigate to Financial Statements

Within the 10-K or 10-Q, locate:

- **Item 8** (10-K) or **Item 1** (10-Q): Financial Statements
- Key sections to extract:
  - Consolidated Statements of Operations (Income Statement)
  - Consolidated Balance Sheets
  - Consolidated Statements of Cash Flows
  - Notes to Financial Statements (for schedule details)

### Step 4: Data Extraction Mapping

#### Income Statement (from Consolidated Statements of Operations)

| Filing Line Item | Model Line Item |
|------------------|-----------------|
| Net revenues / Net sales | Revenue |
| Cost of goods sold | COGS |
| Selling, general and administrative | SG&A |
| Depreciation and amortization | D&A |
| Interest expense, net | Interest Expense |
| Income tax expense | Taxes |
| Net income | Net Income |

#### Balance Sheet (from Consolidated Balance Sheets)

| Filing Line Item | Model Line Item |
|------------------|-----------------|
| Cash and cash equivalents | Cash |
| Accounts receivable, net | AR |
| Inventories | Inventory |
| Property, plant and equipment, net | PP&E (Net) |
| Total assets | Total Assets |
| Accounts payable | AP |
| Short-term debt / Current portion of LT debt | Current Debt |
| Long-term debt | LT Debt |
| Retained earnings | Retained Earnings |
| Total stockholders' equity | Total Equity |

#### Cash Flow Statement (from Consolidated Statements of Cash Flows)

| Filing Line Item | Model Line Item |
|------------------|-----------------|
| Net income | Net Income |
| Depreciation and amortization | D&A |
| Changes in accounts receivable | ΔAR |
| Changes in inventories | ΔInventory |
| Changes in accounts payable | ΔAP |
| Capital expenditures | CapEx |
| Proceeds from issuance of common stock | Equity Issuance |
| Proceeds from / Repayments of debt | Debt activity |
| Dividends paid | Dividends |

### Step 5: Extract Supporting Detail from Notes

For schedules, pull from Notes to Financial Statements:

- **Note: Debt** → Maturity schedule, interest rates, covenants
- **Note: Property, Plant & Equipment** → Gross PP&E, accumulated depreciation, useful lives
- **Note: Revenue** → Segment breakdowns, geographic splits
- **Note: Leases** → Operating vs. finance lease obligations

### Step 6: Historical Data Requirements

Follow the template's required historical horizon; do not add periods unasked.

- Many 10-Ks provide 3 years of IS/CF and 2 years of BS, but issuer requirements vary.
- If a third BS year is required, retrieve the appropriate prior filing and check restatements.
- Use 10-Qs for required quarterly granularity. Cash-flow statements are often year-to-date: derive standalone quarters by subtracting comparable cumulative periods, label the derivation, and never treat a year-to-date figure as one quarter.

### Data Extraction Checklist

- Identify reporting currency and scale (thousands, millions)
- Required historical Income Statement periods
- Required historical Cash Flow Statement periods
- Required historical Balance Sheet dates
- For indirect CF only, verify IS Net Income = CF starting Net Income (each year); preserve direct-method receipts/payments when supplied
- Reconcile BS cash to CF ending cash on the same definition and dates; bridge restricted cash and FX effects where relevant
- Extract debt maturity schedule from notes
- Extract D&A detail or useful life assumptions
- Identify non-recurring items separately; do not alter reported historical figures without a clearly labeled adjustment bridge

### Handling Common Filing Variations

| Variation | How to Handle |
|-----------|---------------|
| D&A embedded in COGS/SG&A | Use CFS/notes as a cross-check; do not subtract it again in the IS or add it twice in CFO |
| "Other" line items are material | Check notes for breakdown |
| Restatements | Use restated figures, note in assumptions |
| Fiscal year ≠ calendar year | Label with fiscal year end (e.g., FYE Jan 2025) |
| Reporting currency differs from agreed model currency | Preserve agreed currency; source and document any required translation |

Currency symbols alone can be ambiguous (for example $ and ¥); verify the textual reporting-currency disclosure. Map reported net revenue and each cash-flow sign deliberately. Do not assume a raw balance-sheet movement exactly equals the reported working-capital cash flow.
