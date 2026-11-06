---
name: journal-entry
description: "Prepares posting-ready adhoc journal entries and supporting schedules with traceable calculations, balanced debits and credits, documented business purpose, and release controls. Supports recurring entries, reversals, corrections, reclassifications, allocations, close batches, accruals, deferrals, depreciation true-ups, payroll, intercompany activity, AP/AR clearing, suspense resolution, and FX revaluation. Reconciles entries to source records and control totals, flags unmapped accounts or cost centers, and produces line-level posting detail, narration, supporting evidence, adjustment rationale, and preparer/reviewer documentation. Use to calculate, draft, validate, correct, allocate, reverse, clear, or document a journal entry."
metadata:
  version: '1.1.0'
  category: 'analysis'
  icon: 'BookNumber'
  argument-hint: '<type> <period>'
---

# Journal Entry: Evidence to Release

Use this workflow to prepare entries for qualified financial review, not to provide financial advice or to certify that an entry is approved or posted. It includes its own accounting and review guidance; no separate JE standards skill is needed.

**Provenance and modification notice:** This experimental Microsoft revision consolidates the Microsoft Journal Entry and Journal Entry Standards baseline. That baseline incorporates guidance from Anthropic's Finance & Accounting plugin, distributed under Apache-2.0. This revision reorganizes and rewrites the explanations and examples while retaining accounting coverage and Microsoft invoice controls. The accompanying `LICENSE.txt` retains the upstream license; new wording does not remove provenance or imply legal independence.

## 1. Establish the posting context

Accept `/journal-entry <type> <period>`, or the same information in natural language. Preserve these type identifiers: `ap-accrual`, `fixed-assets`, `prepaid`, `payroll`, and `revenue`. A period can be a month (`2026-09`), quarter (`2026-Q3`), or year (`2026`). Determine the entity, period end, transaction and functional currencies, accounting policy, chart of accounts, required dimensions, requested output, and authorization requirements before calculating.

With an authorized ERP or warehouse connection, obtain the period trial balance, affected GL balances, relevant subledger or schedules, and comparable prior-period entries. Otherwise request pasted data or uploaded spreadsheets containing the affected balances and supporting detail; suggest connecting the ERP when useful, but do not require a connection. Prior entries are optional references, not evidence that today's amount is correct. Identify missing or contradictory inputs and request the specific records needed rather than inventing account codes, amounts, rates, policy, or approval.

Preserve exact user identifiers, figures, file counts, tab names and order, headers, template rows/columns, and formulas. Apply `accounting-root-skill` when offered. Use `xlsx` if it is offered in this conversation, or the available workbook tools otherwise. Do not add supplemental tabs or files for controls or evidence. Fit supporting detail into the requested structure; if it has no suitable location, report the limitation in the handoff instead of altering the template.

**Before constructing a cloud workbook, read [reference.md](reference.md).** Map every authentic request requirement and supported source locator to the expected population, grouping, amounts, control quantity/rule and preservation constraints before building. Derive expectations from source detail, not the delivered aggregate or hidden reference answers. Unknown mappings/policy/amounts remain holds or unavailable checks, not invented expected values. Keep working notes internal, never extra deliverable tabs.

## 2. Determine treatment and measurement

First identify the economic event and its recognition date, then establish the measurement basis. Use the applicable policy and evidence, not a desired balancing amount. The debit/credit patterns below are starting points; validate actual accounts and dimensions against the entity's ledger.

| Type | Account effect |
| --- | --- |
| `ap-accrual` | Debit the relevant expense, or an asset when capitalization criteria are met; credit accrued liabilities |
| `fixed-assets` | Debit depreciation or amortization expense allocated to department/cost center; credit accumulated depreciation or amortization |
| `prepaid` | Debit the benefiting expense; credit prepaid expense |
| `payroll` | Debit salary, bonus, benefits or payroll tax expense; credit the corresponding accrued payroll, bonus, benefits or payroll tax liability |
| `revenue` | Earned deferred amounts: debit deferred revenue, credit revenue. New earned receivable: debit accounts receivable, credit revenue. Receipts/billings before earning: debit cash or accounts receivable, credit deferred revenue |

Apply only the relevant type's checks:

### `ap-accrual`

- **Evidence:** Goods received or services performed before close but not invoiced: receipt-confirmed open POs, unbilled contract work, recurring utilities/subscriptions/professional services, and unprocessed employee expense reports.
- **Measurement:** Document the PO, contract, or historical run-rate estimate. Keep the estimation method consistent; explain changes.
- **Follow-through:** Plan the following-period reversal, preferably automatic; confirm policy/date to avoid duplicate expense when invoiced, and compare actual invoices with the accrual to improve estimates.

### `fixed-assets`

- **Evidence:** Asset register and depreciation/amortization schedule: cost, salvage value, useful life, method, in-service date and period.
- **Measurement:** Straight-line expense is `(Cost - Salvage) / Useful life`, adjusted to the supported period convention. Declining balance applies the supported fixed rate to opening net book value; units of production allocates the depreciable base by actual usage/output divided by total expected usage/output.
- **Follow-through:** Keep method, rate, units and period aligned to the register; check additions and life/method, disposals, impairments and write-offs. Reconcile book and tax tracking without assuming identical expense.

### `prepaid`

- **Evidence:** Benefit-period schedules for insurance, software licenses/subscriptions, rent where lease terms permit, maintenance contracts, and conference/event deposits.
- **Measurement:** Record start/end dates and monthly amounts, including any partial-period convention.
- **Follow-through:** Add new items promptly; assess expensing of immaterial items under policy and cancellation/termination requiring accelerated amortization or other treatment.

### `payroll`

- **Evidence:** Payroll registers, pay calendars, bonus plans, benefit schedules, employer tax bases/rates and PTO rules.
- **Measurement:** Multiply eligible compensation by earned working days / pay-period working days; allocate by department. Apply bonus target, performance metrics and payout timing; separately support employer FICA/FUTA, health benefits and 401k match.
- **Follow-through:** Include all related costs; accrue PTO/vacation when policy or jurisdiction requires.

### `revenue`

- **Evidence:** Contract terms, delivery/service evidence and contract-level recognition schedules.
- **Measurement:** Under ASC 606, identify the customer contract, identify distinct performance obligations, determine transaction price including variable consideration, allocate the price to obligations, and recognize revenue as/when each is satisfied.
- **Follow-through:** Retain contract-level audit support for the recognition date, allocation and account effect.

For each calculation, cite a precise source locator, formula, period basis, assumptions and rounding. Do not silently change supplied figures to make totals tie. If source records disagree, identify the conflict and leave the unsupported treatment unresolved.

**Validate period measurements before applying rates:** Establish endpoints, inclusion/exclusion and day-count basis from the explicit user requirements and applicable policy; do not invent a missing convention. Recompute derived counts/fractions using that convention (actual/365, actual/actual, or the specified 30/360 variant), not an embedded duration claim. For inclusive actual days, use `end - start + 1`; do not substitute calendar days for a contractual 30/360 basis. Retain a contradictory supplied count as source evidence and disclose the difference. If endpoints/convention are agreed, use their independently checked result for calculations; if authority or convention conflicts, pause the affected calculation for clarification. Link downstream expense, balances and entry lines to the checked duration/basis and revalidate propagation, not just the displayed day count.

## 3. Construct the entry and evidence trail

Use the supplied ERP upload layout or template when provided. Otherwise use the following compact entry format:

```text
Journal Entry: [Type] - [Period]
Prepared by: [Identified preparer]
Date: [Period end date]

| Line | Account Code | Account Name | Debit | Credit | Department | Memo |
| ---- | ------------ | ------------ | ----- | ------ | ---------- | ---- |
| 1    | [Code]       | [Account]    | [Amount] |     | [Department] | [Reason] |
| 2    | [Code]       | [Account]    |       | [Amount] | [Department] | [Reason] |
|      |              | Total        | [Debit total] | [Credit total] | | |

Supporting Detail: [Calculation basis, assumptions, schedule/source references]
Reversal: [Yes/No; supported date if Yes]
```

Maintain a link from every amount, account and department/cost center/project dimension to the supporting record or mapping and calculation. Include an audit-sufficient memo explaining the event and rationale; the applicable accounting period; the real preparer and preparation timestamp; source identifiers such as PO, invoice, contract or payroll register; and reversal status/date. Distinguish the period-end entry date from the actual preparation date. Record review/approval evidence under the authorization matrix when available; otherwise label approval as pending. Never fabricate a preparer identity, signature or sign-off.

**Check output coverage, not only totals:** Read the actual OneDrive workbook through the available cloud Excel tools, using the real workbook and canonical tool context. Follow [reference.md](reference.md) to compare every required population, debit/credit grouping, account/dimension, amount and control status against independently supported expectations. Balanced totals do not clear missing requested groups or wrong control bases. Do not replace actual range readback with model-retyped data or download a workbook for validation.

## 4. Apply release-control gates

Treat these as independent gates: an arithmetically balanced entry can still be incorrectly recognized or unauthorized. Record failed checks and their consequence, not just a completed checklist.

| Gate | Required checks before release |
| --- | --- |
| Arithmetic integrity | Recompute amounts from support, reconcile totals and confirm total debits equal total credits. Verify signs and debit/credit direction; do not hide imbalance in a plug line. Explain estimates that are suspiciously round rather than treating rounding as evidence. |
| Accounting validity | Confirm the accounting period is correct and open; test delivery/service cut-off, valid and appropriate account codes (especially similar codes), capitalization versus expense, and department/cost center/project coding. Check policy and prior-period consistency, changes in circumstances behind stale accruals, FX rate and rate date, and intercompany counterpart entries and necessary consolidation eliminations. Explain unusual or large amounts. |
| Completeness | Confirm the memo is specific enough for audit, calculations and source documents are complete and referenced, no transaction is duplicated in existing entries, and reversal settings/date are appropriate. In particular, an accrual without the required reversal can double-count when the invoice arrives. |
| Authorization | Check preparer authority and route the entry to the required reviewer. Approval requires actual review evidence, not a calculated amount below a threshold. An out-of-period or consolidation adjustment needs the applicable higher-level review. |

Use the organization's approval matrix, materiality and risk tolerance. If none is supplied, the following is an **illustrative routing reference, not authorization to post**:

| Classification | Illustrative reviewer |
| --- | --- |
| Recurring standard entry, any amount | Accounting manager |
| Manual/non-recurring, less than $50,000 | Accounting manager |
| Manual/non-recurring, $50,000 through $250,000 | Controller |
| Manual/non-recurring, more than $250,000 | CFO or VP Finance |
| Top-side/consolidation or out-of-period, any amount | Controller or higher |

Confirm the operative matrix with the organization. Reviewers must assess all four gates; delegation or an amount threshold does not replace supporting evidence or expand the preparer's authority.

## 5. Resolve exceptions and hand off

Separate **missing evidence**, **failed checks**, and **approval pending**. For each unresolved item state its source, affected line/amount/period, what cannot yet be concluded, the action needed, and owner when known. Do not claim to have resolved a discrepancy by merely listing it. Resolve or prominently flag every exception before giving posting guidance.

Deliver the formatted journal entry as an `.xlsx` workbook, its supporting calculations, a comparison with the same type of prior-period entry when available, review/follow-up items, and manual posting instructions or the user's ERP upload mapping. Keep all five components within the requested artifact structure and handoff. Do not route a specifically requested Word or PowerPoint deliverable into Excel solely because it is accounting work.

**Validate -> correct -> revalidate:** Compare actual cloud rows, formulas and control results with the full requirement/evidence checklist before handoff; record passed, failed and unavailable checks, not just a grand total or Excel error count. Also verify rendered layout with available workbook tools. Correct supported defects and re-read the current output to repeat affected comparisons (at most two correction/revalidation cycles within the accounting-root limit). Never clear a failure by changing expected groups, dropping rows, plugging values or inventing evidence. Missing/truncated results, unavailable reads or calculation results are not passed. Preserve a labeled draft and disclose exact unresolved checks; no posting-ready/approval claim when mandatory checks fail or remain unavailable. This is a procedural workflow, not a bundled executable validator or a guarantee of model compliance.

### Worked examples (illustrative, not user data)

**Supported accrual input:** PO-81 confirms 6 service days received by September 30 at $400/day, not yet invoiced. The supplied ledger maps expense to `6105` and accrued liabilities to `2105`, department `OPS`; policy requires October 1 reversal. The user requests only a `JE` tab. No approval is supplied.

**Expected output:** In `JE`, debit `6105` $2,400 and credit `2105` $2,400, both `OPS`; memo references PO-81 and September services. Show support `6 * $400 = $2,400`, period-end date September 30, and reversal October 1 in the requested layout or handoff. Report approval pending; do not claim posting or add a support tab.

**Conflicting-evidence input:** The same PO lists 6 days, but the receiving record lists 4; neither is designated authoritative, and account mapping is absent.

**Expected response:** "Unresolved: PO-81 implies $2,400; receiving support implies $1,600, a difference of $800. Confirm accepted service days and provide GL mapping before a posting-ready entry can be prepared. Approval remains pending." Preserve both inputs; do not average them, invent codes or mark the entry approved.

## 6. Invoice-batch branch: daily completeness and reconciliation

When the request concerns invoice batches, use this branch instead of inventing a journal entry for every invoice. Summarize by batch and retain the connection from processed invoices to the posting register and AP GL. Use the requested layout; otherwise include:

| Batch ID | Batch Date | Entry Count | Gross Amount | Tax | Discounts | Net Payable | Control Total | Difference | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ID] | [Date] | [Count] | [Gross] | [Tax] | [Discount] | [Net] | [System total] | [Net minus control] | Verified / Exception |

Also report counts posted, pending approval, on hold and rejected for each batch. Recompute gross, tax, discounts and net payable from invoice data using its documented sign and tax conventions; avoid adding tax twice when gross already includes it. Tie the batch net to the system control total/posting register. A nonzero difference is an exception. Reconcile the amount actually posted to AP in the GL and identify partial postings separately from unposted items.

Search within the batch and recently posted batches for the same vendor plus invoice number. Hold a suspected duplicate pending confirmation against the vendor statement. Inspect invoice/batch numbering gaps and determine whether records were voided, held or lost; a sequence gap is an investigation trigger, not proof of a missing posting.

For a control-total mismatch, isolate the affected entries and require correction or reprocessing before close. Escalate approval items past their SLA to the approver and assess whether an unposted period-end item requires an AP accrual based on receipt/service evidence. For wrong-period postings, propose an authorized reverse-and-repost or documented cut-off treatment; do not execute or declare a correction without authorization.

Produce the summary on the posting day. Carry unresolved exceptions forward with an owner and age until verified clear. At period end, feed unposted approved invoices into AP accrual review and batch-to-GL differences into AP reconciliation. A batch cannot be called Verified merely because its invoice sum equals a control total while posting or completeness checks remain unresolved.
