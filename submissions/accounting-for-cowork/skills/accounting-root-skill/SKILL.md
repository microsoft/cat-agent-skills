---
name: accounting-root-skill
description: "Read this BEFORE building or editing any finance or accounting deliverable. Applies the shared build contract across journal entries, reconciliations, financial reporting, presentations, budgeting and forecasting, and tax preparation. It selects the appropriate workflow and output format, preserves the requested structure, and requires source-linked calculations, control totals, documented assumptions, exception handling, and preparer/reviewer evidence. It ensures accounting deliverables are traceable, reviewable, and ready for the intended process. This is not a standalone workflow and does not replace a specialized skill. Used whenever a request creates or materially changes an accounting deliverable."
metadata:
  version: '1.0.0'
  category: 'analysis'
  icon: 'Organization'
---

# Accounting Root Skill

The shared build contract for the finance and accounting work in this package — financial statements, finance presentations, reconciliation, journal entries, budgets and forecasts, and tax. Whichever workflow skill matched this request supplies the domain method; this skill governs how the deliverable is scoped, built and checked.

> **Important**: This skill assists with finance and accounting workflows but does not provide financial, tax, or audit advice. All outputs should be reviewed by qualified financial professionals before use in financial reporting, regulatory filings, or audit documentation.

## Workbook implementation gate

**STOP before routing to a finance workflow or touching the files. Determine the requested output type first.**

- If the request names an Excel workbook, spreadsheet, workpaper, schedule, tracker, `.xlsx` file, workbook tab, worksheet, or Excel template, load `xlsx` first if it is offered in this conversation.
- After the dedicated workbook skill loads, read the finance workflow. Use the finance workflow for accounting decisions and the dedicated skill for workbook implementation and validation. If no such skill is offered, proceed with the workbook tools this conversation does provide — never abandon the deliverable or switch the requested file type because an implementation skill is unavailable.
- For mixed-output requests, load every applicable dedicated format skill that is offered before constructing the deliverables, and use the available format-specific tools for any requested format without one. Never route a requested Word or PowerPoint output to Excel merely because the task is financial.

## Available finance workflows

Identify the workflow the request calls for and load that skill before building:

| Workflow | Skill | Use when |
|----------|-------|----------|
| Journal Entry | `journal-entry` | Booking accruals (AP, payroll, prepaid), depreciation, or revenue recognition; documenting entries for audit; or building batch journal entries|
| Reconciliation | `reconciliation` | Comparing GL to subledger, bank recs, intercompany recs, lease and debt roll-forwards, categorizing reconciling items, or drafting reconciliation memos and review packs |
| Financial Statements & Reporting | `financial-statements` | **Any financial-reporting deliverable except a slide deck** — income statement, balance sheet, or cash flow (with period comparisons/variance); trial-balance workbooks; monthly/quarterly reporting packages and management summaries; footnotes and disclosures; technical accounting memos and position papers (goodwill/asset impairment, capitalization, revenue recognition — citing the governing ASC and showing the required comparison); MD&A / management commentary; and GAAP presentation / period-end requirements (ASC 220/210/230) |
| Budget and Forecast | `budget-and-forecast` | **Building the plan itself** — loading ERP or GL actuals into a planning baseline, mapping accounts to planning lines, rolling department submissions into one company model, reconciling submissions to control totals, or cascading a company-level budget, savings, margin or investment target across departments |
| Finance Presentations | `financial-presentations` | **Any finance slide deck (.pptx)** — quarterly or board financial-review decks, investment-committee / board / deal / M&A recommendation decks, AP/AR process-documentation slides, or department close / status meeting slides |
| Tax Preparation | `tax-preparation` | Preparing income-tax provisions, ASC 740 analyses, effective-tax-rate reconciliations, deferred-tax rollforwards, estimated-tax payments, tax organizers, indirect-tax reconciliations, or tax-authority response packages |

> **Financial reporting spans many deliverables — read the workflow that fits what you're producing.** Financial statements (P&L, balance sheet, cash flow), trial balances, disclosures and footnotes, technical accounting memos (impairment, capitalization, revenue recognition, lease/debt), management commentary, reporting packages, and review or board decks are all financial reporting — start from `financial-statements`; use `budget-and-forecast` to build the plan, budget or forecast itself; and draw on `financial-presentations` only when the requested output is a slide deck. Follow the deliverable you must produce, not a keyword in the request.
>
> Reporting memos and narratives are graded on **substance, not brevity** — describe the actual conditions and drivers and present the GAAP comparison the standard requires (e.g. fair value vs. carrying amount for impairment), rather than a one-line conclusion.

## How to use

1. **Determine every requested file type and pass the implementation-skill gate above.** Do not defer this until after workflow selection or analysis.
2. **Identify the finance workflow the request calls for, and read that workflow skill** — required, before building. Use the table above. Follow the deliverable you must produce, not a keyword in the request. Do not build from this skill alone; it carries the contract, not the method.
3. **Read the standards file the workflow skill points to, if it has one.** It adds the checks specific to that skill's deliverables on top of this contract.
4. **Lock the requested structure before designing.** Record the exact deliverable count, file types, tab names, tab order, template rows/columns, and any words such as "only," "exactly," "do not add," or "preserve." These are hard constraints and override every example, best practice, standard format, or audit-ready convention in any skill. If a template is supplied, preserve its tab roster, order, names, row layout, headers, and formulas unless the user explicitly authorizes a change. Do not add, rename, delete, reorder, or replace structure to make the workpaper more reusable or audit-ready.
5. **Pre-register the requirements internally.** Before building, extract every explicitly requested item — each file, tab, section, column, period, metric, and named figure — into working notes. The checklist is a verification aid, not a deliverable. **Never create a `Requirements`, `README`, `Cover`, `Controls`, `Source`, `Notes`, `Memo`, `Index`, or similar supplemental tab unless the user explicitly requested that tab or the supplied template already contains it.** If no structure is prescribed, use the fewest tabs needed to hold the requested work; prefer a compact section on an existing requested tab over a new tab.
6. **Gather source data** — prompt the user for financial data (trial balance, GL exports, bank statements) or use data from attachments.
7. **Execute the workflow** following its detailed instructions, trimming every optional methodology step the request does not need.
8. **Create the output document** using the available format-specific implementation skill or tools appropriate to the requested file type. Put necessary controls, provenance, assumptions, or reviewer notes inside the requested structure; do not create extra deliverables or tabs for them.
9. **Verify against the request, not your plan.** Re-open the delivered file with the available format-specific implementation skill or tools and first compare its file count, tab count, exact tab names, tab order, and template layout to the structure lock. For `.xlsx`, verify formulas, cached/recalculated values, visible error cells, and rendered layout using the available workbook validation workflow. Then verify every requested item and every tie/check cell. Re-derive each expected value from the request and source data — not from your build script, which shares your build's blind spots. Never clear a failing check by hardcoding a value, making a check circular, or repointing dependents: a formula the renderer can't compute gets a documented fallback in an existing requested location plus an exception note, and a control that won't tie is concluded "not reconciled", visibly. Fix and re-verify (at most twice); route what still can't tie to exceptions with its most-likely cause.

## Scope & structure fidelity

- **Build only what the request names.** Lock the entity, source files, period, account population, deliverable count, and requested structure. Treat every "only," "just," "single," or "exactly" as a hard boundary.
- **Quality language does not expand scope.** "Audit-ready," "professional," "controller-ready," and "reusable" describe the quality of the requested work; they do not authorize extra tabs, files, schedules, dashboards, memos, covers, source copies, or control packs.
- **The latest explicit user structure wins.** A suggested structure from an earlier assistant message is not a user requirement. If the user specifies exact tabs or supplies a template, perform internal analysis in working files or notes and deliver only the specified structure.
- **Reproduce supplied figures exactly.** Data given in the prompt or an attachment must appear as provided — same values, labels, account captions, signs. Do not re-scale, re-round, re-caption, re-order or "correct" a supplied figure. If one looks wrong, reproduce it unchanged and note the concern separately. A restated input reads as an error even when the restatement is defensible.

## Evidence authority

A figure, status or conclusion is only as good as the record it rests on. Compliance and review work often turns on the difference between what a record shows and what a note says about it.

1. **Record fields beat indicators.** Rest every figure, tier, threshold test, status and conclusion on the system-of-record field for it: the register, ledger or subledger, billing or order system, receiving record, contract, signed approval, or third-party confirmation named in the inputs. Trackers, progress or status notes, coordinator or PMO notes, emails, meeting notes, pipeline figures, estimates, and anything labelled "approx." are **indicators**: they tell you what to investigate, never what to book. Only when the inputs designate a tracker or log as the authoritative record, or no other record exists, use it — and say so.
2. **An indicator creates an open item, not an adjustment.** When an indicator says something the records do not (for example "tracker indicates …", "approx.", "per the progress report"), keep the recorded value in every calculation and conclusion, and log the indicator as an open item or follow-up that cites its source. Do not move a tier, cross a threshold, recognise, capitalise, accrue, close, or clear anything on an indicator alone.
3. **Pending is not done.** "Pending", "awaiting", "update pending", and "not yet received / approved / signed" mean the required evidence does not exist yet: report the item as open or unsupported, not as completed or effective.
4. **Surface conflicts; never resolve them silently.** When two sources give different values for the same thing — a quantity field and a description, a figure stated in the conversation and the documented schedule, two schedules — rely on the authoritative record, state the conflict where the requested structure allows, and carry the unresolved difference as an open item.
5. **A partial extract is not a population.** Do not reconcile an extract the inputs describe as partial, filtered, or incomplete to a full-population total, and do not report the gap as an exception or misstatement; report the limitation instead.
6. **Before you finalise, name the record behind every adjustment, reclassification, and conclusion.** If the only support is an indicator, turn it back into an open item.

## Output format guidelines

- **Excel (.xlsx)** — journal entries, reconciliation workpapers, trial balances, variance schedules, SOX testing workpapers, close checklists
- **Word (.docx)** — financial narrative reports, variance analysis memos, management commentary, audit documentation
- **PowerPoint (.pptx)** — financial review presentations, board decks, close status reports

Use the dedicated format implementation skills for file creation whenever they are offered. If a requested format has no dedicated skill, use the format-specific tools available in the conversation rather than blocking the work or changing the requested file type. This skill carries the build contract, not file-format implementation guidance. When the deliverable is a slide deck, follow the `financial-presentations` skill for deck structure and chart selection — do not build a finance deck from generic slide craft alone.

## Common accounting concepts

### Chart of accounts structure

| Range | Category | Normal Balance |
|-------|----------|---------------|
| 1000-1999 | Assets | Debit |
| 2000-2999 | Liabilities | Credit |
| 3000-3999 | Equity | Credit |
| 4000-4999 | Revenue | Credit |
| 5000-5999 | Cost of Revenue | Debit |
| 6000-7999 | Operating Expenses | Debit |
| 8000-8999 | Other Income/Expense | Varies |
| 9000-9999 | Tax/Extraordinary | Varies |

### Debits and credits

- **Assets** increase with debits, decrease with credits
- **Liabilities** increase with credits, decrease with debits
- **Equity** increases with credits, decreases with debits
- **Revenue** increases with credits, decreases with debits
- **Expenses** increase with debits, decrease with credits
- Every journal entry must balance: total debits = total credits

### Materiality thresholds (general guidance)

| Line Item Size | Dollar Threshold | Percentage Threshold |
|---------------|-----------------|---------------------|
| > $10M | $500K | 5% |
| $1M–$10M | $100K | 10% |
| < $1M | $50K | 15% |

Materiality is context-specific and must be determined by qualified professionals.
