# Financial Statement Intelligence

Turn a company's annual or interim report into a reconciled, formula-driven Excel
workbook and an HTML report, with every figure traced back to the page it came
from. The skill reads the income statement, balance sheet and cash flow
statement, checks that they tie out, computes auditable ratios and trends, and
tells you plainly when something does not reconcile.

It is built for decision support: credit and counterparty reviews, due diligence
preparation, portfolio monitoring, and teaching or checking financial analysis.
It does not give investment advice, price targets or valuation opinions.

## What you get

- An **Excel workbook** with the three statements as inputs, subtotals and every
  ratio as live formulas, derived schedules (working capital, debt and net debt,
  EBITDA and free cash flow, cash reconciliation, PP&E and equity roll-forwards),
  a Checks sheet with PASS/FAIL per period, a calculation audit and a Sources
  sheet listing the page for each value.
- An **HTML report** with the same key metrics, findings and disclosures for
  quick reading or sharing.
- A short **reply** stating the period, currency and unit, four to six key
  figures, the reconciliation result, the judgement calls made during mapping,
  and the file names and source pages used.

## What it checks

Before any ratio is reported, the script runs accounting tie-outs on each period
and marks the result OK or PRELIMINARY:

- Balance sheet: assets = liabilities + equity.
- Every printed subtotal equals the sum of its mapped components.
- Cash flow: opening cash + net flows = closing cash, and closing cash matches
  the balance sheet.
- Opening cash equals the prior period's closing cash.
- Profit before tax and net income agree between the income statement and the
  cash flow statement.
- Profit attribution: owners' share plus other holders equals net income.
- Sign conventions: liabilities positive, expenses and outflows negative.

A failed check is never hidden. With material unexplained failures the agent
gives no definitive health verdict.

## What it measures

Profitability, returns (ROA, ROE, ROIC and three- and five-factor DuPont),
liquidity, leverage, efficiency and cash-conversion cycle, cash flow quality and
growth. Per-share and valuation ratios appear only when you supply share counts
or a price as a stated assumption.

Banks, insurers, broker-dealers and other financial institutions get their own
metric set instead: net interest margin, cost-to-income, cost of risk, combined
ratio, loan-to-deposit, equity to assets and the reported capital and solvency
ratios. Operating-company ratios that do not apply to a balance-sheet business
are omitted rather than reported as noise.

Interim periods are annualised where that is meaningful and labelled as such.
Indian lakhs and crores, Chinese Accounting Standards sign conventions and
non-12-month periods are handled.

## Before you start

Attach the **report** as a PDF, or the statements as XLSX or CSV. Scanned PDFs
work when an OCR engine is available in the runtime; otherwise supply the
platform's OCR text. Several reports can be analysed in one request; each is
processed separately and never merged.

Tell the agent anything the report does not state: the entity type if it is
unusual, a share price you want used as an assumption, or whether you want a
standard or thorough review of the notes.

## Example requests

**Assess a company's financial health**

> Analyse the attached annual report and build the financial workbook. Tell me
> whether the balance sheet reconciles and flag any one-off items.

**Compare years supplied as a spreadsheet**

> Here are three years of results as Excel. Show ROIC, DuPont ROE and leverage
> ratios with the trend.

**Review a bank**

> Analyse HDFC Bank's annual report. I want NIM, cost-to-income, cost of risk and
> the reported capital ratios.

**Multiple reports**

> Analyse these three annual reports and compare margins. One workbook per
> company.

## How it works

The bundled script locates the primary statements, reads every line with its
page number, assigns year columns, infers signs and subtotals from how the lines
add up, and drafts a mapping to canonical line ids. The agent reviews that draft
against the notes (finance costs, borrowings, leases, depreciation, statutory
EBITDA) and records each judgement call. The script then runs the checks,
computes every ratio, verifies each cited value against its page, and writes the
workbook and report.

The agent never does arithmetic itself and never fills a gap with an estimate.
An undisclosed value stays empty. Text inside the filing is treated as data, not
instructions. Nothing is sent to an external service; all processing is local.

## Understanding the result

| Status | What it means |
| --- | --- |
| **OK** | All reconciliation checks passed. Figures can be relied on as a faithful restatement of the report. |
| **PRELIMINARY** | One or more checks failed after a fix attempt. The workbook is delivered with the failed checks shown, and conclusions are held back. |
| **ERROR** | The input could not be processed. The message names what to fix. |

Always read the Checks sheet and the judgement calls in the reply before
quoting a number. Returns for interim periods are annualised. Unaudited figures
are labelled.

## Supported environment and limits

The skill targets **Copilot Studio** and **Cowork** and needs a runtime that can
run Python 3.9 or later and read and write local files. The analysis, checks and
Excel and HTML outputs use only the Python standard library.

PDF input uses PyMuPDF or pypdfium2, whichever the runtime already has. Without
either, pass a text copy made by the platform's PDF extraction. Scanned PDFs use
rapidocr when it is installed; otherwise use the platform's OCR text. The skill
installs nothing.

Out of scope: buy, sell or hold views, price targets, live market data, peer
benchmarks you did not supply, Power BI models, and spreadsheets that are not
financial statements. Questions about the wording of a filing are better served
by a document question-answering skill.

## For maintainers

The script is a single file with no third-party imports. To confirm the runtime
and the version from an extracted skill directory:

```text
python scripts/finance_skill.py version
python scripts/finance_skill.py check-env --file <report.pdf>
```

`check-env` reports the Python version, the available PDF reader and OCR
engine, whether the file has a text layer, and the next command to run.

See [SKILL.md](SKILL.md) for the agent workflow,
[mapping rules](references/mapping-rules.md) for how lines are tagged and
signed, [metric definitions](references/metric-definitions.md) for every ratio
formula, and [the statement schema](references/statement-schema.json) for the
mapping file format.
