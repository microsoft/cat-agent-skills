---
name: reconciliation
description: "Reconciles balances and transactions across the general ledger, subledgers, bank or loan statements, supporting schedules, vendor records, and third-party data. Supports GL-to-subledger, bank, cash, loan, trial-balance, AP/vendor, and invoice-batch reconciliations, plus explanatory memos and supervisor review packs. Matches transactions, calculates adjusted balances, and classifies timing items, missing support, posting errors, duplicates, cutoff issues, disputes, and FX differences. Produces control totals, materiality flags, proposed corrections, owners, aging, resolution dates, and reviewer evidence. Use to tie out accounts, investigate discrepancies, or prepare close-review packages."
metadata:
  version: '1.0.0'
  category: 'analysis'
  icon: 'ArrowSyncCheckmark'
  argument-hint: '<account> [period]'
---

# Reconciliation

**Important**: This skill assists with reconciliation workflows but does not provide financial advice. All reconciliations should be reviewed by qualified financial professionals before sign-off.

Methodology and best practices for account reconciliation, including GL-to-subledger, bank reconciliations, and intercompany. Covers reconciling item categorization, aging analysis, escalation, and the deliverables that package reconciliation work: reconciliation memos, vendor correspondence, AP discrepancy trackers, and supervisor review packs.

**Read [Reconciliation Standards](references/reconciliation-standards.md) before you build** — the cross-cutting output discipline, applied as checks on your own work (not a template): reconcile within the account's materiality threshold and show the computed difference (tight for cash/bank, looser for estimate-heavy accounts like accruals — it need not be exactly $0); tie support to the official GL / trial-balance figure that ties to the ERP, and show the difference; use live formulas, never hardcoded balances; cover the complete population; label each material figure disclosed-vs-derived with its source and period, and never present a guess as disclosed; document the inputs, methodology, exceptions above threshold, and a definitive conclusion — cross-tie related accounts for reasonableness (e.g., AR vs revenue given the payment terms) and propose the most-likely cause of each exception; and never guess silently — state the assumption you took wherever the inputs left a choice open. Apply the treatment the task calls for and don't impose structure it doesn't need; the sections below add the *type-specific* mechanics.

## Structure precedence — apply before the methodology

The user's requested deliverable structure and any supplied template are authoritative. The formats below are examples of content, not required tabs or layouts.

- Preserve exact tab count, names, order, template rows/columns, headers, and formulas when specified. Do not insert a cover, README, requirements checklist, controls sheet, source index, copied source-data tab, memo, reviewer-notes tab, or exception tab unless explicitly requested or already present in the template.
- Keep the requirements checklist and detailed analysis in working notes. Put only requested output into the workbook.
- "Audit-ready," "controller-ready," "professional," and "reusable" never expand scope. Achieve those qualities with formulas, labels, and concise notes inside the requested tabs.
- If the request says "only," "exactly," "do not add/rename/delete/reorder," or "template exactly as supplied," treat that as a hard failure boundary. Do not apply a standard format that conflicts with it.
- When no layout is prescribed, choose the smallest structure that fully satisfies the request. Add a separate schedule or memo only when its content cannot fit clearly in an already-required tab and the user has not limited the structure.

## Spreadsheet implementation handoff — required

When any requested reconciliation deliverable is an Excel workbook (`.xlsx`), load `xlsx` first if it is offered in this conversation. If no such skill is offered, proceed with the workbook tools this conversation does provide — never abandon the reconciliation or change the requested file type because an implementation skill is unavailable.

After building, re-open and validate the delivered workbook using the loaded implementation skill or the available workbook tools. Confirm that live formulas recalculate, tie/check cells reference independent source and detail cells, no visible formula errors remain, and the rendered workbook preserves the user's exact tab roster and layout. Do not add tabs or change the requested file type as part of this handoff.

## Reconciliation Types

### GL to Subledger Reconciliation

Compare the general ledger control account balance to the detailed subledger balance.

**Common accounts:**
- Accounts receivable (GL control vs AR subledger aging)
- Accounts payable (GL control vs AP subledger aging)
- Fixed assets (GL control vs fixed asset register)
- Inventory (GL control vs inventory valuation report)
- Prepaid expenses (GL control vs prepaid amortization schedule)
- Accrued liabilities (GL control vs accrual detail schedules)

**Process:**
1. Pull GL balance for the control account as of period end
2. Pull subledger trial balance or detail report as of the same date
3. Compare totals — they should match if posting is real-time
4. Investigate any differences (timing of posting, manual entries not reflected, interface errors)

**Common causes of differences:**
- Manual journal entries posted to the control account but not reflected in the subledger
- Subledger transactions not yet interfaced to the GL
- Timing differences in batch posting
- Reclassification entries in the GL without subledger adjustment
- System interface errors or failed postings

### Bank Reconciliation

Compare the GL cash balance to the bank statement balance.

**Process:**
1. Obtain the bank statement balance as of period end
2. Pull the GL cash account balance as of the same date
3. Identify outstanding checks (issued but not cleared at the bank)
4. Identify deposits in transit (recorded in GL but not yet credited by bank)
5. Identify bank charges, interest, or adjustments not yet recorded in GL
6. Reconcile both sides to an adjusted balance

**Standard format:**

```
Balance per bank statement:         $XX,XXX
Add: Deposits in transit            $X,XXX
Less: Outstanding checks           ($X,XXX)
Add/Less: Bank errors               $X,XXX
Adjusted bank balance:              $XX,XXX

Balance per general ledger:         $XX,XXX
Add: Interest/credits not recorded  $X,XXX
Less: Bank fees not recorded       ($X,XXX)
Add/Less: GL errors                 $X,XXX
Adjusted GL balance:                $XX,XXX

Difference:                         $0.00
```

**Book balance comes from the transaction detail — never the running balance alone.** Recompute the ending book balance as the opening GL balance plus the sum of period transaction activity, and show it beside the official GL ending balance; any gap between the two is its own exception line. If the supplied detail covers a different date range, use the corresponding opening control balance and state the range. Linking the running-balance cell as "the book balance" without independently recomputing it is a methodological failure reviewers reject.

**Which side does an item adjust — and does it get a journal entry?** Classify every reconciling item by who must act:

- **Bank-side add-backs — NO journal entry:** anything the bank got wrong or hasn't finished processing — encoding/amount errors, checks charged to the account that are not in the company's check register (out-of-series or another company's checks), bank errors pending reversal. These adjust the bank column only.
- **Book-side items — JE at the full cleared amount to the correct account:** fees, interest, NSF returns, transfers, and collections the bank processed that the books lack. An interbank/intercompany cash movement is a transfer between cash accounts, never an expense; an NSF customer check reinstates the receivable for the check amount, while the bank's returned-item fee is recorded separately as an expense unless a contractual or legal basis permits charging it to the customer; a note collected by the bank splits principal (note receivable) from interest income.
- **Timing — NO journal entry:** an item already recorded on one side and dated within the normal processing lag (typically 1–5 business days around period end) is an outstanding check / deposit in transit — a routine reconciling item, not an error to investigate.

**Transaction matching workflow:**

When working from transaction-level detail (bank statement export + GL cash detail or cash journal):

1. Match transactions between bank and book by amount, date, and reference number (check number, wire reference, deposit ID)
2. Use tiered matching: exact match on all three fields first, then amount + date within a tolerance window (e.g., ±3 business days), then amount-only for manual review
3. Categorize every unmatched item by exception type:
   - **Outstanding check** — in book, not in bank
   - **Deposit in transit** — in book, not in bank
   - **Bank fee / interest / adjustment** — in bank, not in book
   - **Duplicate** — same transaction recorded twice on one side
   - **Missing entry** — cleared at bank with no book entry
   - **Misdated** — recorded in the wrong period on one side
   - **Amount mismatch** — same transaction, different amounts (possible keying error)
4. Calculate the adjusted bank balance and adjusted book balance; both must agree
5. Produce a reconciling items schedule listing each exception with type, amount, date, reference, and proposed correction (record entry, reverse duplicate, investigate)

**Reconciling items schedule format:**

| # | Exception Type | Date | Reference | Amount | Side (Bank/Book) | Proposed Correction | Status |
|---|---------------|------|-----------|--------|------------------|--------------------|--------|
| 1 | [Type] | [Date] | [Ref] | $X,XXX | [Side] | [Action or JE] | Open / Cleared |

When the user asks for a reusable template and has not prescribed a conflicting layout, organize inputs, matching, exceptions, and a summary so they flow clearly. Otherwise preserve the requested/template structure and place only the necessary calculations within it.

### Intercompany Reconciliation

Reconcile balances between related entities to ensure they net to zero on consolidation.

**Process:**
1. Pull intercompany receivable/payable balances for each entity pair
2. Compare Entity A's receivable from Entity B to Entity B's payable to Entity A
3. Identify and resolve differences
4. Confirm all intercompany transactions have been recorded on both sides
5. Verify elimination entries are correct for consolidation

**Common causes of differences:**
- Transactions recorded by one entity but not the other (timing)
- Different FX rates used by each entity
- Misclassification (intercompany vs third-party)
- Disputed amounts or unapplied payments
- Different period-end cut-off practices across entities

### FX / CTA Reconciliation

Foreign-currency translation reconciliations use the **current-rate method, with every leg modeled quantitatively**: assets and liabilities at the period-end spot rate; income-statement amounts at appropriate transaction-date rates (a period-average rate when it reasonably approximates them); contributed equity at historical rates; and retained earnings rolled forward from its translated opening balance using translated net income and historical-rate dividends. The balancing translation adjustment is recorded in CTA within OCI/AOCI. State the method by name on the face of the work. A balance-sheet-only proxy or a model that translates equity at the closing rate is incomplete — show each translation leg and the entity-level net income/loss actually used.

### Lease Reconciliation (ASC 842 / GASB 87 / IFRS 16)

Reconcile the right-of-use (lease) asset and lease liability via formula-driven rollforwards (type-specific mechanics on top of the Reconciliation Standards), under whichever framework the task specifies:

- **ROU asset rollforward** and **lease-liability rollforward** as separate schedules (beginning + additions/remeasurements − amortization/principal = ending), each tying to the trial balance.
- **Current vs long-term split** of the lease liability — compute the current portion (principal due within the next 12 months) by formula; never show the current portion as $0 when principal is due within a year.
- Apply recognition exemptions only under the governing framework and elected policy: short-term lease elections exist under ASC 842, GASB 87, and IFRS 16, while the explicit low-value-asset exemption is specific to IFRS 16. Do not exclude a lease merely because another framework would permit an exemption.
- **Drive the movements from a rate — and get the direction right.** When you must *derive* the schedule (rather than follow one the source already provides), put the annual discount/borrowing rate in a labeled input cell and compute by formula: periodic interest = annual rate ÷ periods-per-year × opening liability; principal = payment − interest; **ending liability = opening + interest − payment** (equivalently opening − principal). Validate that the full schedule reaches ≈ $0 at lease end; the liability may increase during a rent-free or deferred-payment period when interest exceeds payment, so do not treat every period-over-period increase as a sign error. Never plug the lease *term* (a count of periods) in where the *rate* belongs. Keep this **liability** rollforward separate from the **ROU/lease-asset** reduction and apply the framework and classification specified by the task: for an ASC 842 operating lease, ROU reduction equals straight-line single lease cost minus liability interest; for ASC 842 finance leases, IFRS 16 lessee leases, and GASB 87 leases, amortize the asset separately under the applicable ownership, purchase-option, lease-term, and useful-life rules. Do not apply the liability recurrence to the asset. Typed interest/amortization columns, or no rate input cell, is not formula-driven. If the source already provides a payment or amortization schedule, follow it rather than re-deriving.
- **Rollforward residuals are derived component-wise, never plugged.** The "other/residual" line = disclosed ending − (beginning + disclosed additions − disclosed reductions), computed separately per component (operating vs finance; ROU vs liability). Show the derivation formula, its inputs, and the assumptions for EACH residual — a residual presented without its component derivation and assumptions fails review.
- **Surface leases not yet commenced as explicit scoped-out lines.** When reconciling to a filing that discloses commitments for leases not yet commenced, carry that amount as its own labeled off-balance-sheet line in the extracted inputs, the maturity schedule, AND the reviewer conclusion (recognized vs unrecognized explained) — never silently omit it.
- **Tie to every GL account the leases touch** — a tie-out block with one line per account (ROU asset, current lease liability, long-term lease liability, accumulated amortization, interest expense, lease/rent expense), each showing the control balance, the rollforward total, and the formula difference. Give the per-lease detail a GL-account column. Don't leave the current/long-term split or accumulated amortization as an "open item" when the inputs to compute them are present.

### Debt Reconciliation

Reconcile borrowings via a rollforward that ties to ending debt — the tie-out *difference* to the disclosed / TB balance is what reconciles to $0; add the debt-specific mechanics:

1. **Rollforward to ending debt; tie-out difference to $0:** beginning (prior-FY ending) + issuances − repayments ± exchanges/FX = rollforward ending; then reconcile that rollforward ending to the disclosed / TB debt balance, with the difference computed as a live formula that must tie to $0.
2. **Face → carrying-value bridge:** face/principal ± unamortized discount/premium − unamortized debt-issuance costs = carrying value; show the bridge explicitly.
3. **Tranche-level rows:** one row per instrument/tranche (e.g. notes by coupon/maturity), summing to the total — not a single lump line.
4. **Cash-flow financing tie-out:** issuances and repayments in the rollforward tie to the financing section of the statement of cash flows.
5. **Debt-exchange treatment:** assess extinguishment vs modification (10% cash-flow test) and flag the conclusion; do not silently pick one.
6. **Amortize from a rate on the stated convention:** discount/premium, debt-issuance costs, and commitment fees accrue by formula from a labeled rate/term input. Amortize discount/premium and debt-issuance costs by the **effective-interest method** — it is required under IFRS 9, and under US GAAP (ASC 835-30-35-2) straight-line is permitted *only* when the result is not materially different from the interest method. Simplicity is not a basis for choosing it: if you use straight-line (annual amount ÷ 12, or total cost ÷ term-in-months), state the framework and the not-materially-different conclusion that supports it in a labeled cell, and default to effective-interest whenever the instrument has material discount/premium, uneven payments, or you cannot support that conclusion. Do not prorate by actual days in the period unless the instrument specifies it. Derive the term / number of periods by formula from the facility's start and end dates — never type the period count as a constant. Commitment fees accrue each period as that period's *unfunded* commitment balance × the commitment-fee rate. State the convention in a cell, and generate the recurring per-period ledger entries from the schedule rather than only the inception entry — each generated JE row carrying a GL account code and a one-line memo describing the item.

When the authoritative source (e.g. the 10-K debt footnote) is not attached, populate the rollforward with a labeled **derived reconstruction** from public figures (mark each balance as *derived*, state the basis and limitations in the memo) rather than leaving an empty schedule.

## Reconciling Item Categorization

### Category 1: Timing Differences

Items that exist because of normal processing timing and will clear without action:

- **Outstanding checks:** Checks issued and recorded in GL, pending bank clearance
- **Deposits in transit:** Deposits made and recorded in GL, pending bank credit
- **In-transit transactions:** Items posted in one system but pending interface to the other
- **Pending approvals:** Transactions awaiting approval to post in one system

**Expected resolution:** These items should clear within the normal processing cycle (typically 1-5 business days). No adjusting entry needed.

### Category 2: Adjustments Required

Items that require a journal entry to correct:

- **Unrecorded bank charges:** Bank fees, wire charges, returned item fees
- **Unrecorded interest:** Interest income or expense from bank/lender
- **Recording errors:** Wrong amount, wrong account, duplicates
- **Missing entries:** Transactions in one system with no corresponding entry in the other
- **Classification errors:** Correctly recorded but in the wrong account

**Action:** Prepare adjusting journal entry to correct the GL or subledger.

### Category 3: Requires Investigation

Items that cannot be immediately explained:

- **Unidentified differences:** Variances with no obvious cause
- **Disputed items:** Amounts contested between parties
- **Aged outstanding items:** Items that have not cleared within expected timeframes
- **Recurring unexplained differences:** Same type of difference appearing each period

**Action:** Investigate root cause, document findings, escalate if unresolved.

## Aging Analysis for Outstanding Items

Track the age of reconciling items to identify stale items requiring escalation:

| Age Bucket | Status | Action |
|-----------|--------|--------|
| 0-30 days | Current | Monitor — within normal processing cycle |
| 31-60 days | Aging | Investigate — follow up on why item has not cleared |
| 61-90 days | Overdue | Escalate — notify supervisor, document investigation |
| 90+ days | Stale | Escalate to management — potential write-off or adjustment needed |

### Aging Report Format

| Item # | Description | Amount | Date Originated | Age (Days) | Category | Status | Owner |
|--------|-------------|--------|-----------------|------------|----------|--------|-------|
| 1      | [Detail]    | $X,XXX | [Date]          | XX         | [Type]   | [Status] | [Name] |

### Trending

Track reconciling item totals over time to identify growing balances:

- Compare total outstanding items to prior period
- Flag if total reconciling items exceed materiality threshold
- Flag if number of items is growing period over period
- Identify recurring items that appear every period (may indicate process issue)

## Accounts Receivable Aging Report

An AR aging report categorizes outstanding customer invoices by due-date bucket and customer, supporting collections prioritization and reserve assessment.

### Invoice-Level Detail Format

| Customer | Invoice # | Invoice Date | Due Date | Amount | Current | 1-30 | 31-60 | 61-90 | 90+ | Last Payment | Collection Status |
|----------|-----------|--------------|----------|--------|---------|------|-------|-------|-----|--------------|-------------------|
| [Name] | [#] | [Date] | [Date] | $X,XXX | $X,XXX | — | — | — | — | [Date] | Current / In contact / Promise to pay / Disputed / Escalated |

Age from the **due date** (not invoice date) so terms differences don't distort buckets.

### Customer Summary Format

| Customer | Total Outstanding | Current | 1-30 | 31-60 | 61-90 | 90+ | % Past Due | Credit Terms | Flag |
|----------|-------------------|---------|------|-------|-------|-----|------------|--------------|------|
| [Name] | $X,XXX | $X,XXX | ... | ... | ... | $X,XXX | XX% | Net 30 | [See flags] |

**Flags to apply:**
- Any invoice over 90 days or above the materiality threshold
- Customer with past-due percentage above a set level (e.g., > 25%)
- Concentration: customer representing more than a set share of total AR (e.g., > 10%)
- No payment activity in 60+ days on an active balance
- Disputed invoices (exclude from routine dunning; route to dispute resolution)

### Summary Metrics

- **Total AR by bucket** with prior-period comparison (is aging improving or deteriorating?)
- **DSO (Days Sales Outstanding):** `(Ending AR / Revenue for period) × days in period` — trend over 6-12 periods
- **Collection priorities:** top 10 past-due balances by dollar, each with collection status and next action
- **Reserve implications:** balances 90+ days and disputed items feed the allowance for credit losses assessment — summarize the exposure by reserve category

## Accounts Payable Aging Report

An AP aging report categorizes open vendor invoices by vendor and due-date bucket, supporting payment planning, cash forecasting, and close review.

### Invoice-Level Detail Format

| Vendor | Invoice # | Invoice Date | Due Date | Amount | Current | 1-30 | 31-60 | 61-90 | 90+ | Payment Terms | Status |
|--------|-----------|--------------|----------|--------|---------|------|-------|-------|-----|---------------|--------|
| [Name] | [#] | [Date] | [Date] | $X,XXX | $X,XXX | — | — | — | — | Net 30 / 2-10 Net 30 | Approved / Pending approval / On hold / Disputed |

### Vendor Summary Format

| Vendor | Total Payable | Current | 1-30 | 31-60 | 61-90 | 90+ | Early-Pay Discount Available | Flag |
|--------|---------------|---------|------|-------|-------|-----|------------------------------|------|
| [Name] | $X,XXX | $X,XXX | ... | ... | ... | $X,XXX | $XXX by [date] | [See flags] |

**Flags to apply:**
- Overdue balances (past due date and not on hold) — late-payment and vendor-relationship risk
- Payment holds and disputed invoices, with the hold reason and owner
- Concentration: vendor representing more than a set share of total AP
- Available early-payment discounts expiring within the payment window
- Invoices pending approval near period end (accrual candidates)

### Summary Metrics

- **Total AP by bucket** with prior-period comparison
- **DPO (Days Payable Outstanding):** `(Ending AP / COGS or total spend for period) × days in period` — trend over 6-12 periods
- **Near-term cash requirements:** payables due in the next 1-2 weeks by due date, for payment-run planning
- **Discount opportunity:** total early-pay discounts available vs forfeited this period
- **Close review items:** held, disputed, and pending-approval invoices that affect accruals or cut-off

## Escalation Thresholds

Define escalation triggers based on your organization's risk tolerance:

| Trigger | Threshold (Example) | Escalation |
|---------|---------------------|------------|
| Individual item amount | > $10,000 | Supervisor review |
| Individual item amount | > $50,000 | Controller review |
| Total reconciling items | > $100,000 | Controller review |
| Item age | > 60 days | Supervisor follow-up |
| Item age | > 90 days | Controller / management review |
| Unreconciled difference | Any amount | Cannot close — must resolve or document |
| Growing trend | 3+ consecutive periods | Process improvement investigation |

*Note: Set thresholds based on your organization's materiality level and risk appetite. The examples above are illustrative.*

## Account Reconciliation Memos

A reconciliation memo is a separate narrative deliverable **only when the user requests a memo, correspondence, or review pack**. Do not add a memo file or workbook tab merely because the reconciliation is described as audit-ready or controller-ready. When no memo is requested, include only the minimum conclusion and material-item explanations in an existing requested reconciliation location. When requested, the memo explains discrepancies and justifies adjustments for a reviewer who has not seen the underlying detail and must stand alone.

### Memo Structure

```
ACCOUNT RECONCILIATION MEMO

Account:            [Account number — Account name]
Period:             [Period end date]
Prepared by:        [Name]            Date: [Date]
Reviewed by:        [Name]            Date: [Date]

CONCLUSION
[Lead with the bottom line: "Reconciled with no exceptions" /
"Reconciled with X items carried forward totaling $X,XXX" /
"Unreconciled difference of $X,XXX pending investigation"]

BALANCE SUMMARY
Balance per general ledger:                    $XX,XXX
Balance per [subledger/statement/schedule]:    $XX,XXX
Net difference:                                $X,XXX

RECONCILING ITEMS
| # | Description | Amount | Category | Root Cause | Owner | Expected Resolution |
|---|-------------|--------|----------|------------|-------|---------------------|
| 1 | [Item]      | $X,XXX | Timing / Adjustment / Investigation | [Cause] | [Name] | [Date] |

EXPLANATION OF DIFFERENCES
[One short paragraph per material item: what happened, why, and what
happens next. Reference the item # from the table above.]

PROPOSED ADJUSTING ENTRIES
[For each proposed JE: accounts, amounts, and the justification —
the business reason and authoritative basis (policy, GAAP reference,
or management approval). State if no adjustments are needed.]

CARRYFORWARD ITEMS
[Items not resolved this period: why they remain open, aging status,
and the expected resolution date. State if none.]
```

### Memo Writing Guidance

1. **Lead with the conclusion.** The first thing a reviewer reads should be whether the account reconciles and the size of any open exposure.
2. **Quantify everything.** "Three timing items totaling $4,230" — never "some small differences."
3. **Explain cause, not just existence.** "Difference of $12,500 due to a manual JE posted directly to the control account on [date] without a corresponding subledger entry" — not "GL doesn't match subledger."
4. **Justify each adjustment.** Every proposed entry needs a business rationale and a basis: accounting policy, GAAP treatment, or documented management approval. An adjustment without justification is a red flag in review.
5. **Make carryforwards accountable.** Each open item needs an owner and an expected resolution date — items without owners get carried forward indefinitely.
6. **Write for audit.** Assume the memo will be read 12 months later by someone reconstructing what happened. Spell out references (JE numbers, invoice numbers, statement dates).

## Vendor Correspondence

Reconciliation work often surfaces discrepancies with vendor statements or triggers payment inquiries. These require external-facing responses that are professional, factual, and specific enough for the vendor to act on.

### Statement Reconciliation Process

Before drafting a response, reconcile the vendor statement to the AP subledger:

1. Match open invoices on the vendor statement to the AP subledger by invoice number and amount
2. Match payments and credits the vendor shows against company remittance records
3. Classify each discrepancy:
   - **Payment in transit** — paid by company, not yet applied by vendor
   - **Missing invoice** — on statement, not in AP system (request a copy)
   - **Unapplied credit** — credit memo on one side only
   - **Amount difference** — pricing, tax, or freight discrepancy
   - **Disputed item** — quantity/quality dispute, on hold
   - **Duplicate billing** — invoice appears twice on the statement

### Payment Inquiry Response Template

```
Subject: Re: Payment status — [Vendor name], [invoice number(s)]

[Vendor contact],

Thank you for your inquiry regarding [invoice number(s)].

Our records show the following status:

| Invoice # | Invoice Date | Amount | Status | Payment Date | Reference |
|-----------|-------------|--------|--------|--------------|-----------|
| [#]       | [Date]      | $X,XXX | Paid / Scheduled / Under review / On hold | [Date] | [Check/ACH ref] |

[For paid items: remittance detail — date, method, reference number.]
[For scheduled items: expected payment date per terms.]
[For items under review or on hold: the reason and what is needed
to release them, with expected resolution timing.]

Please let us know if your records differ, and include remittance
detail or invoice copies for any items above so we can resolve
them promptly.

[Name, title, contact]
```

### Statement Discrepancy Response Structure

For a vendor statement that does not match company records:

1. **Acknowledge** the statement date and total under review
2. **Confirm what matches** — items both sides agree on, briefly
3. **Address each discrepancy** with the company's records: invoice number, amount on file, payment status, and the reason for the difference
4. **Request what's missing** — invoice copies, credit memo documentation, remittance application detail
5. **State next steps and timing** — what the company will do, what the vendor needs to do, and when to expect resolution

**Tone guidance:** factual and cooperative, never defensive. State what the records show, not who is at fault. Do not commit to payment dates for disputed items until the dispute is resolved internally.

## AP Collaboration Workflow

Reconciliations frequently surface invoice discrepancies and coding questions that the reconciler cannot resolve alone. Resolution runs through AP, purchasing, or receiving — the reconciler's job is to package each exception so the owning team can act on it.

### Common Invoice Exceptions

| Exception Type | Typical Root Cause | Resolving Team |
|----------------|--------------------|----------------|
| Price mismatch (invoice vs PO) | Price change not reflected on PO; vendor billing error | AP + Purchasing |
| Quantity mismatch (invoice vs receipt) | Partial shipment; receiving not posted | AP + Receiving |
| Duplicate invoice number | Vendor re-sent invoice; keying error | AP |
| Missing PO reference | Invoice sent without PO; maverick purchase | AP + Purchasing |
| Incorrect GL account coding | Wrong expense category at entry | AP (reconciler proposes correct coding) |
| Incorrect cost center / department | Coding default applied incorrectly | AP (reconciler proposes correct coding) |

### Exception Resolution Tracker

Assign every exception an owner, a recommended action, and a due date:

| # | Vendor | Invoice # | Amount | Issue Type | Detail | Recommended Action | Owner | Due Date | Status |
|---|--------|-----------|--------|-----------|--------|--------------------|-------|----------|--------|
| 1 | [Vendor] | [#] | $X,XXX | [Type] | [Current vs expected coding, or mismatch detail] | [Specific fix] | [AP owner] | [Date] | Open / In progress / Resolved |

### Escalation Package Format

When sending exceptions to AP, include everything needed to act without a follow-up question:

- Invoice number, vendor, amount, and invoice date
- The specific issue, with both sides of the mismatch (e.g., "invoice $5,200 vs PO $4,800")
- Current coding and proposed coding (account, cost center, project) for coding fixes
- The recommended corrective action and why
- Any blocker requiring purchasing, receiving, or vendor follow-up — flagged explicitly

### Shared Responsibility Model

- **Reconciler owns:** GL-side reclassifications, accrual adjustments, proposing corrected coding, documenting the exception
- **AP owns:** invoice corrections, duplicate removal, vendor credits, payment holds/releases, vendor master updates
- **Escalate jointly** when an item is blocked on purchasing, receiving, or the vendor — summarize the blocker and what is needed, rather than letting the item age silently

## Reconciliation Review Meetings

Periodic review meetings with supervisors walk through open exceptions and agree on resolution approaches. The preparer's job is to arrive with a meeting-ready review pack — not raw reconciliation detail.

### Pre-Meeting: Review Pack Contents

**1. Status summary (one page):**

| Metric | This Period | Prior Period |
|--------|-------------|--------------|
| Accounts reconciled / total | X / X | X / X |
| Open reconciling items (count) | X | X |
| Open reconciling items (total $) | $X,XXX | $X,XXX |
| Items > 60 days old | X | X |
| Items above materiality threshold | X | X |

**2. Exception detail, sorted by risk** (materiality, then age):

| Account | Item | Amount | Age | Risk | Category | Proposed Resolution | Decision Needed? |
|---------|------|--------|-----|------|----------|--------------------|------------------|
| [Acct]  | [Description] | $X,XXX | XX days | High / Med / Low | [Type] | [Recommendation] | Yes — [what] / No |

**3. Items requiring supervisor judgment**, each framed as a decision:
- The item, its amount, and why it cannot be resolved at preparer level
- Options considered, with the preparer's recommendation
- What happens if no decision is made this week (aging, close impact)

### Meeting Agenda Structure

1. **Status summary** — counts and totals vs prior period (2 minutes; trends, not detail)
2. **Clean accounts** — confirm and move on; no walkthrough
3. **Exceptions requiring decisions** — highest materiality first; present the item, the recommendation, and the decision needed
4. **Aged items update** — status of previously escalated items; flag anything that aged past a threshold since last review
5. **Proposed adjustments** — entries above the preparer's approval authority needing sign-off
6. **Recurring/systemic issues** — exceptions appearing multiple periods that need a process fix, not another one-off resolution

### Post-Meeting: Action Log

Capture every decision and follow-up in an action log circulated after the meeting:

| # | Item | Decision / Action | Owner | Due Date | Status |
|---|------|--------------------|-------|----------|--------|
| 1 | [Exception ref] | [Approved adjustment / Investigate further / Escalate to controller] | [Name] | [Date] | Open |

Carry unresolved actions into the next review pack's aged items section — the action log from one meeting seeds the agenda for the next.

## Reconciliation Best Practices

1. **Timeliness:** Complete reconciliations within the close calendar deadline (typically T+3 to T+5 business days after period end)
2. **Completeness:** Reconcile all balance sheet accounts on a defined frequency (monthly for material accounts, quarterly for immaterial)
3. **Documentation:** Include preparer, reviewer, and date fields only when requested or already present in the supplied template. Always explain material reconciling items, but use an existing requested location rather than adding a cover, controls, sign-off, memo, or notes tab.
4. **Segregation:** The person who reconciles should not be the same person who processes transactions in that account
5. **Follow-through:** Track open items to resolution — do not just carry items forward indefinitely
6. **Root cause analysis:** For recurring reconciling items, investigate and fix the underlying process issue
7. **Standardization:** Standardize calculation quality and terminology, not workbook structure. A user-specified layout or supplied template overrides house formats and cross-account consistency.
8. **Retention:** Maintain reconciliations and supporting detail per your organization's document retention policy
