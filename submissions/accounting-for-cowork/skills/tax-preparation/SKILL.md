---
name: tax-preparation
description: "Prepares tax analyses, workpapers, compliance support, and audit-ready packages using source-linked calculations, jurisdictional rules, documented assumptions, and reviewer controls. Supports filing-readiness checklists, tax projections and estimated payments, entity allocations, tax account analysis, indirect-tax reconciliation, provision and effective-tax-rate analysis, tax-savings comparisons, compensation and Schedule C workbooks, master-data reviews, and transaction-level audit packages. It can also extract issues and due dates from tax notices, identify evidence gaps, and prepare response strategies, checklists, and issue trackers. Use for tax compliance, accounting, planning, reconciliation, filing readiness, or audit support."
metadata:
  version: '1.0.0'
  category: 'analysis'
  icon: 'MoneyCalculator'
  argument-hint: '<tax-workflow> [entity] [period]'
---

# Tax Preparation

**Important**: This skill assists with tax preparation, provision, and compliance workflows but does not provide tax or legal advice. All tax positions, filings, and deliverables must be reviewed and signed off by a qualified tax professional (CPA / Tax Director / Tax Manager) before they are filed, posted, or sent to a requesting stakeholder or taxing authority.

Methodology and best practices across the tax preparation lifecycle: income tax provision and account analysis, tax projections and estimated payments, entity-election and tax-savings analysis, reasonable compensation, indirect tax reconciliation and audit-ready packages, tax authority notice/audit response, and filing readiness.

This skill supplies the tax-specific layer of each deliverable: the tax classification taxonomy (current/deferred, permanent/temporary, valuation allowance, UTB) and the one-discrete-tax-effect-per-entry rule for journal entries; the indirect-tax population, root-cause taxonomy and tax-determination traceability for reconciliations; the ASC 740 rate-reconciliation driver taxonomy for rate bridges; and the jurisdiction due dates, document requirements and Outlook mechanics for a filing-deadline calendar. **Read [Reconciliation Standards](references/reconciliation-standards.md) before you build a workbook**: live formulas, tie-outs, completeness and structure lock.

A tax-authority audit is not SOX 404 internal-controls testing, despite the shared word "audit". Do not substitute a SOX workpaper template for a notice response package; see Tax Authority Notice & Audit Response below.

## Classification-Before-Computation Discipline

Several sections below require testing an item against a classification rule - business vs. nonbusiness income, which rate governs, whether a provision conforms - before that item can correctly enter a computation. Apply this same discipline everywhere a classification test is named below, rather than treating it as one optional step among several:

1. **Test before you compute, for every item in the population.** Run the named classification test for every entity, jurisdiction, or line item before finalizing the computation it feeds - not for a sample, and not only for the item that happens to prompt the question. An untested item is unclassified, not included by default.
2. **Apply the same classification consistently everywhere the same fact pattern appears.** Once an item is classified one way in one entity, jurisdiction, period, or scenario column, the identical fact pattern gets the identical classification everywhere else it appears in the same deliverable - across every scenario/column of a multi-scenario workbook as much as across entities or jurisdictions - never decide the same question differently in two places without a stated, fact-specific reason for the difference.
3. **Resolve using facts the source data already establishes; reserve "flag for review" for genuine ambiguity.** If the provided source data or reference materials already state the governing fact - an enacted rate, a stated conformity position, a documented policy - apply it and complete the computation. Do not log an already-answered question as an open item or a follow-up for someone else to resolve. Flag as an open item only when the source data genuinely doesn't settle the question and a human judgment call is actually required.

## Income Tax Provision & Tax Account Analysis (ASC 740)

Reconcile book income to taxable income, compute current and deferred tax expense, and roll forward every tax balance sheet account to a supported ending balance.

For the Tax Account Analysis Workbook below, apply the tie-out, live-formula and structure-lock discipline in [Reconciliation Standards](references/reconciliation-standards.md) to the workbook. Draft the entries from the supplied template: look up every account code in the supplied chart of accounts rather than guessing it, build one line per item, and confirm total debits equal total credits before posting. This section adds the tax-specific classification taxonomy and the one-effect-per-entry rule. When a Tax JE Posting Policy or a record of prior-period reviewer categorization decisions is provided, use it exactly as given rather than inventing a fresh taxonomy each period.

### Current & Deferred Tax Provision Calculation

Calculate the provision itself before building the rate reconciliation below - the ETR bridge explains and control-checks the provision, it does not replace it. Work the calculation by legal entity and tax jurisdiction, then consolidate:

1. **Current provision**: reconcile pretax book income to estimated taxable income for the period (add back permanent differences, adjust for temporary differences originating/reversing in the period); apply the enacted federal, state/local, and foreign rates that actually govern the period; compute current tax expense by jurisdiction, net of credits and estimated payments; identify any return-to-provision true-up separately from the current-year estimate.
2. **Deferred provision**: compute the period's deferred tax expense/benefit as the net change in deferred tax assets and liabilities - each temporary difference's originating and reversing movement, any enacted-rate remeasurement, and any valuation allowance change (see Deferred Tax Rollforward below for the supporting detail).
3. **Total provision**: current tax expense/(benefit) plus deferred tax expense/(benefit) equals total income tax expense; tie this total to the tax accounts on the balance sheet and to the income statement.
4. **Intraperiod allocation**: where the request involves discontinued operations, OCI, or an equity transaction, allocate tax expense to the applicable category rather than defaulting the entire provision to continuing operations.

Use the Effective Tax Rate Bridge below to explain and control-check the result (why the effective rate differs from statutory) - not as a substitute for the calculation above.

### Effective Tax Rate (ETR) Bridge

Reconcile the statutory rate to the effective rate - this is the standard "rate reconciliation" required by ASC 740-10-50 and is also the fastest way to explain *why* tax expense moved. Flag the reconciling items above a stated materiality threshold, explain each in a sentence, and classify them with the tax-specific driver taxonomy below rather than revenue or opex drivers such as volume, price or mix:

```
ETR RECONCILIATION
                                          Amount        Rate
Income before tax                        $XX,XXX
Tax at statutory rate (federal + state)  $XX,XXX       XX.0%
  Permanent differences (e.g., meals,
    officer comp limits, tax-exempt inc) $X,XXX        X.X%
  State taxes, net of federal benefit    $X,XXX        X.X%
  Tax credits (R&D, foreign tax credit)  ($X,XXX)      (X.X%)
  Valuation allowance change             $X,XXX        X.X%
  Uncertain tax position movement        $X,XXX        X.X%
  Rate change (deferred remeasurement)   $X,XXX        X.X%
  GILTI / FDII / other international     $X,XXX        X.X%
                                          --------      -----
Effective tax rate                       $XX,XXX       XX.X%
```

**Common drivers to check when the ETR moves period over period:**
- A jurisdiction's statutory rate changed - remeasure deferred balances in the period of enactment using the enacted rate expected to apply when each temporary difference reverses, including an enacted future-period rate when the reversal is expected in that future period.
- A discrete item hit this period (an audit settlement, a rate change, a new uncertain tax position) versus the ongoing/recurring rate - separate discrete items from the annual effective rate so the underlying rate trend is visible.
- Permanent differences grew or shrank relative to pre-tax income (permanent items move the ETR more when pre-tax income is smaller).
- A valuation allowance was established or released against deferred tax assets.

Where a PBT/tax-expense variance investigation flags an entity for deeper review, hand off to the Tax Account Analysis Workbook below (same skill) to inspect that entity's underlying journal entries.

### PBT & Effective-Tax-Rate Variance: Period-over-Period Driver Decomposition

The ETR Reconciliation above explains a single period's own rate; explaining why PBT or the group ETR *moved* between two periods is a variance-decomposition problem, not a side-by-side of the two periods. Split the movement into a rate effect (each entity's rate change, weighted by its prior-period share of PBT) and a mix effect (each entity's change in share of PBT, at its current-period rate), and present it as a bridge from the prior-period figure to the current one whose components sum exactly to the total movement. Work through the procedure below first, since a rate-bridge decomposition run directly off consolidated totals will miss exactly the errors it exists to catch.

Apply the Classification-Before-Computation Discipline above throughout this sequence, worked at the entity (or jurisdiction) level first, before touching a consolidated figure:

1. **Entity-level rate test, for every entity.** Compute [PBT x that entity's own enacted statutory rate] and compare it to the entity's actual booked current tax, for every entity in scope - not a sample. Flag any entity where the two don't tie within a normal rounding tolerance - this isolates where a rate variance actually originates before any group-level narrative gets written.
2. **Diagnose each flagged entity - and resolve it, not just flag it.** Either (a) a real temporary/permanent difference explains the gap - a legitimate contributor to jurisdictional mix - or (b) the wrong rate was applied when the tax was booked. Apply the enactment-date test from the Effective Tax Rate (ETR) Bridge above to confirm which rate should actually have governed. If the source data already establishes the governing rate (an enacted-rate schedule, a tax authority notice), apply it and proceed to step 3 - do not log a source-confirmed rate discrepancy as an open item or a follow-up for someone else to resolve.
3. **Restate where (b) applies.** Compute the entity's tax at the correct rate, quantify the correction (booked vs. corrected), and carry both the as-booked and the corrected/underlying figures through the rest of the bridge - never silently replace one with the other, and never leave a computed correction unapplied.
4. **Aggregate.** Entity-level rate corrections from step 3 roll into the statutory-rate-change component; entity-level differences confirmed as case (a) roll into the jurisdictional-mix component; items outside the recurring rate use the same discrete-vs-recurring split as the ETR Reconciliation above.
5. **Net-off check.** Before writing the movement narrative, scan the entity-level components for offsetting pairs - two entities' variances the same size in opposite directions - and call them out explicitly as netting to a smaller or zero group residual, rather than letting a clean-looking consolidated total hide them.
6. **Client policy overrides the generic default.** If the client supplies its own variance/reporting policy document, apply that document's own aggregation and sequencing rules (e.g., grouping movements by common cause before any percentage/dollar test) ahead of any generic materiality threshold.

Only after this sequence is complete, aggregate to the consolidated total and check that the bridge components sum to the total movement at the entity level, not only on the already-consolidated figure - an error hiding in offsetting entity-level movements won't show up if the check is run after they've been netted together. Apply the tie-out discipline in [Reconciliation Standards](references/reconciliation-standards.md) to the accompanying narrative (see Tax Provision / Account Analysis Memo below) the same way it's applied to the workbook itself.

### Deferred Tax Rollforward

Build the rollforward at whatever level of detail is needed to explain and support the recorded balance - the table below is an illustrative layout, not a mandatory template; adapt the columns and grouping to the entity's actual temporary differences, jurisdictions, and source data. At minimum: state the opening balance, separately explain every originating and reversing movement (plus any acquisition/disposal, return-to-provision true-up, or enacted-rate remeasurement), compute the ending balance, and tie it to the ledger - report every unexplained difference rather than absorbing it into a plug.

| Temporary Difference | Opening DTA/(DTL) | Current Year Originating | Current Year Reversing | Rate Change Impact | Ending DTA/(DTL) |
|---|---|---|---|---|---|
| Depreciation (book vs. tax) | $(X,XXX) | $(X,XXX) | $X,XXX | $X,XXX | $(X,XXX) |
| Accrued compensation / bonus | $X,XXX | $X,XXX | $(X,XXX) | N/A | $X,XXX |
| Warranty / bad debt reserve | $X,XXX | $X,XXX | $(X,XXX) | N/A | $X,XXX |
| Stock-based compensation | $X,XXX | $X,XXX | $(X,XXX) | N/A | $X,XXX |
| Capitalized R&D (174) | $X,XXX | $X,XXX | $(X,XXX) | N/A | $X,XXX |
| Net operating loss carryforward | $X,XXX | $X,XXX | $(X,XXX) | $X,XXX | $X,XXX |
| Tax credit carryforward | $X,XXX | $X,XXX | $(X,XXX) | N/A | $X,XXX |
|  |  |  |  |  |  |
| **Valuation allowance** | $(X,XXX) | $(X,XXX) | $X,XXX | N/A | $(X,XXX) |
| **Net deferred tax asset/(liability)** | $X,XXX |  |  |  | $X,XXX |

**Valuation allowance assessment** (ASC 740-10-30): a valuation allowance is required when it's more likely than not that some or all of a deferred tax asset will not be realized. Weigh the four sources of taxable income against the deferred tax asset: (1) taxable income in prior carryback years, (2) reversal of existing taxable temporary differences, (3) tax-planning strategies, and (4) future taxable income exclusive of reversing temporary differences. Weigh negative evidence (cumulative losses in recent years, a history of expiring carryforwards) against positive evidence (a strong earnings history, expiring negative evidence, firm contracts/backlog).

**Uncertain tax positions** (ASC 740-10-25, formerly FIN 48) - apply the two-step model:
1. **Recognition:** only recognize a tax benefit if it is more-likely-than-not (a likelihood of more than 50%) to be sustained on technical merits upon examination.
2. **Measurement:** for positions that pass recognition, measure the benefit as the largest amount that is more than 50% likely of being realized upon settlement - this is often less than the full position, producing an unrecognized tax benefit (UTB) liability for the difference.

### Financial Statement Disclosures

When the deliverable includes period-end financial reporting, prepare the disclosure support alongside the provision - the disclosure requirement doesn't stop at the rate reconciliation and rollforward above:

- **Rate reconciliation disclosure**: present the ETR bridge above (or the statutory-to-effective dollar/percentage reconciliation, depending on the reporting framework) as a stand-alone disclosure, tied to the income statement's reported tax expense.
- **Components of income tax expense**: break out current and deferred expense/benefit by federal, state/local, and foreign, matching the provision calculation above.
- **Deferred tax components**: present the material categories of deferred tax assets and liabilities (by temporary difference or grouped category) and the valuation allowance, from the Deferred Tax Rollforward below.
- **Carryforwards**: disclose NOL and credit carryforward amounts and expiration schedules, with any valuation allowance against them.
- **Uncertain tax positions**: disclose the UTB rollforward (beginning balance, additions/reductions for current and prior-year positions, settlements, lapses of statute, ending balance) when positions exist.
- **Other required items**: address any other disclosure the applicable reporting framework and jurisdiction require for the entity's facts (e.g., indefinite reinvestment assertions on foreign earnings, tax holidays, open tax years) - confirm the specific list against the entity's reporting framework and filer status rather than assuming this list is complete.

Tie every disclosed number back to the provision workbook, the rollforward, or a named source schedule, and log any immaterial or unresolved item explicitly rather than omitting it silently.

### Tax Account Analysis Workbook

Roll every tax balance sheet account (current tax payable/receivable, deferred tax assets/liabilities by jurisdiction, valuation allowance, UTB liability) from opening to ending balance, supported by the underlying tax journal entries:

1. **Account Rollforward tab** - opening balance, each movement (current provision, deferred movement, valuation allowance change, rate remeasurement, prior-year true-up), ending balance agreeing to independently computed support.
2. **Journal Entries tab** - balanced entries (total debits equal total credits) with account codes from the supplied chart of accounts and preparer and approver fields, plus the tax-specific fields: jurisdiction, current/deferred classification, permanent/temporary classification, tax-effect category, and a cross-reference back to the provision/rollforward line it supports. Preserve one discrete tax effect per entry (don't net a research credit, a rate remeasurement, and a valuation allowance movement into a single entry) unless an approved Tax JE Posting Policy specifies a different level of aggregation.
3. **Exception Log tab** - unresolved differences, items passed under a posting/materiality threshold, and items referred for further technical assessment (an uncertain position, a transfer-pricing question).
4. **Review and Sign-Off tab** - preparer, reviewer, and approver, with blank date fields until actual sign-off.

## Multi-Scenario Tax Projections & Estimated Payments

### Scenario Structure

Lay out the scenarios side by side in columns, base case first. Build a base-case projection from current-year financials, then a separate scenario for each planned transaction, election, or timing decision under consideration (an asset sale, a restructuring, an accounting method change). Isolate the incremental tax effect of each scenario against the base case so a decision-maker can see what each option is worth on its own.

### Estimated Payment Safe Harbors (IRC 6654 individuals / 6655 corporations)

To avoid an underpayment penalty, pay the lesser of:

| Taxpayer | Safe Harbor Options |
|---|---|
| Individuals (prior-year AGI ≤ $150K, or ≤ $75K MFS) | 90% of current-year tax, **or** 100% of prior-year tax |
| Individuals (prior-year AGI > $150K, or > $75K MFS) | 90% of current-year tax, **or** 110% of prior-year tax |
| C-Corporations | 100% of current-year tax, **or** 100% of prior-year tax (large corporations - over $1M taxable income in any of the 3 preceding years - generally can't use the prior-year safe harbor after the first installment) |

Where income is earned unevenly through the year, use the **annualized income installment method** to reduce the required payment for early quarters - compute cumulative income through each installment date, annualize it, and apply the marginal rate, rather than assuming a flat 25% of the full-year liability is due each quarter.

### Quarterly Due Dates (calendar-year taxpayer)

| Installment | Corporation | Individual |
|---|---|---|
| Q1 | April 15 | April 15 |
| Q2 | June 15 | June 15 |
| Q3 | September 15 | September 15 |
| Q4 | December 15 | January 15 (following year) |

Confirm taxpayer type before assigning dates. Adjust for the entity's actual fiscal year end - these dates shift for a non-calendar fiscal year, and jurisdictions can define their own installment percentage schedule rather than a flat 25% per quarter.

### Federal Book-to-Tax Adjustments: Current-Law Baseline

Establish the federal starting point correctly before layering any state apportionment or conformity work on top of it - a wrong federal baseline propagates into every state figure derived from it, even when the state-level logic is applied perfectly.

**Research and experimental expenditures (IRC 174 / 174A).** Domestic R&E expenditures paid or incurred in a tax year beginning after December 31, 2024 are fully deductible in the year incurred under IRC 174A (enacted by the One Big Beautiful Bill Act, July 2025) - no capitalization or amortization. Foreign R&E expenditures remain capitalized and amortized over 15 years regardless of when incurred; the domestic/foreign distinction still matters even though domestic treatment changed.

**A specific, common, now-superseded assumption to actively rule out before computing anything here: do not apply a five-year (or any multi-year) domestic R&E amortization schedule to a tax year beginning after December 31, 2024.** That was the correct treatment before IRC 174A, and it is a strong default that gets reached for out of habit even when the current rule is stated right above - it is simply wrong for domestic R&E in any tax year starting after the boundary above. If a computation is about to produce a multi-year amortization schedule, a "current-year amortization percentage" line, or any capitalization-addback-plus-amortization pair for domestic R&E in an in-scope tax year, that is this exact superseded pattern - stop and replace it with a single full current-year deduction instead.

Apply the rule by the beginning date of the taxpayer's tax year, not by splitting expenditures within a fiscal year: a tax year beginning after December 31, 2024 is governed by IRC 174A for its domestic R&E expenditures. Transition relief permits accelerating any remaining unamortized pre-2025 domestic R&E balance; confirm whether the taxpayer has made or is eligible to make that election before assuming a multi-year amortization schedule continues unchanged.

**Fixed-asset additions: placed-in-service boundary test.** Before including any addition in the current tax year's depreciation computation, confirm its placed-in-service date actually falls within that tax year - using the entity's real fiscal year start/end, not a calendar-year default. An addition placed in service before the year begins or after it ends belongs to a different year's computation, not the current one. Apply this test to every addition in the population, not a sample; a system-generated depreciation total that has not been tested against this boundary is not yet a tax-year-specific figure.

**Bonus/first-year depreciation eligibility gate.** Before applying 100% (or any bonus percentage) first-year expensing to an addition, confirm the asset was not acquired from a related party - the anti-churning principle behind IRC 179(d)(2), which also constrains 168(k) bonus eligibility, carves out related-party acquisitions of used property even when the asset would otherwise qualify. Test this for every addition claiming bonus treatment, not only ones that look unusual.

These federal-level determinations are the baseline the State Conformity checklist below tests each state against - resolve them here first.

### Multi-State Apportionment: Factor Construction

Any multi-state scenario projection needs each state's apportioned share of income before it can project that state's tax - get the factor construction right before modeling scenarios on top of it.

**Apportionment method varies by state and changes over time.** Most states have moved toward a single-sales-factor formula, though property/payroll/sales three-factor and other weightings still exist - confirm the specific state's current method and factor weighting before apportioning, rather than assuming one default applies everywhere.

**Sales/receipts factor sourcing.** For services and intangibles, states source receipts either by **market-based sourcing** (where the customer received the benefit) or **cost-of-performance** (the state where the greater share of income-producing activity occurred, historically an all-or-nothing rule in many states) - confirm which method the specific state uses, since the same transaction can source entirely differently under each.

**Business vs. nonbusiness income.** Apportion only business income; nonbusiness income - under the unitary-business-principle line of cases (*Allied-Signal, Inc. v. Director, Div. of Taxation*; *Container Corp. of America v. Franchise Tax Board*) - is allocated instead, directly to a single state, and never enters the apportionment formula at all. Test every material one-off item against this distinction before deciding whether it belongs in the factor.

**Common exclusion categories to test for every apportionment build** - not exhaustive, but the categories most likely to need a judgment call:
- Occasional or non-recurring sales of a fixed asset, business line, or subsidiary, as opposed to sales made in the regular course of business.
- Treasury/investment income earned by a taxpayer whose regular trade or business is not treasury or investment management.
- Intercompany transactions that a combined or consolidated return eliminates before apportionment.
- Income already excluded from the state tax base under that state's own statute (e.g., foreign-source income not subject to state tax, or an item specifically carved out by statute).

**Procedure - apply the Classification-Before-Computation Discipline above throughout:** (1) confirm the state's current apportionment method and factor weighting; (2) classify every material income item as business or nonbusiness, and test it against the exclusion categories above, before it enters any state's factor - an item not yet classified does not default to inclusion; (3) once an item is classified for one state's factor, apply the identical classification to that same item in every other state's factor - never exclude an item's effect in one jurisdiction while still including it in another without a stated, jurisdiction-specific reason; (4) source services/intangible receipts under each state's actual sourcing rule, not a default assumption; (5) document the classification decision and its statutory basis for every item that isn't obviously in the ordinary course of business, so the apportionment build is defensible on review.

### State Conformity to Federal Provisions: Checklist

A state's starting point for taxable income is rarely identical to the federal figure - confirm conformity before assuming a federal figure carries through unmodified.

**Conformity type.** A state either has **rolling conformity** (automatically adopts the IRC as amended) or **fixed-date (static) conformity** (adopts the IRC as of a specific date, requiring its own legislative update to pick up later federal changes) - confirm which applies and, for fixed-date states, whether the conformity date has been updated to include the federal provision in question.

**Provisions that commonly decouple, regardless of jurisdiction** - check each one every period, since decoupling positions change with each state's own legislative cycle:
- Bonus/first-year depreciation (IRC 168(k)) - many states require an addback with a corresponding future-year subtraction.
- The business interest expense limitation (IRC 163(j)).
- Treatment of research and experimental expenditures (IRC 174/174A - see the Federal Book-to-Tax Adjustments baseline above) - a state can decouple from whatever the current federal rule is (including the current full-expensing rule) and require its own capitalization/amortization schedule and addback instead.
- Net operating loss carryforward percentage and duration limits (states frequently cap the NOL deduction at a percentage of income or apply a different carryforward period than the federal rule).
- Any recently-enacted federal provision, simply because a fixed-date-conformity state's adoption date may not yet reach it.

**Procedure - apply the Classification-Before-Computation Discipline above throughout:** (1) identify the state's conformity type and, if fixed-date, its conformity date; (2) list every federal provision material to the specific return, and test every one - not only the provision that happens to prompt the question; (3) check each one against the state's own decoupling statute rather than assuming conformity; (4) apply the resulting addback or subtraction modification before finalizing state taxable income - a decoupling position the state's own statute already confirms gets applied, not logged as an item for someone else to confirm later; (5) treat this as a full re-check every period, not a one-time determination, since states amend their own conformity position independently of the federal government's legislative calendar.

**Required output - Conformity Determination table.** The procedure above is not complete until its results are recorded, one row per provision tested per state, even when the conclusion is "no adjustment required":

| Provision | State | Conforms? (Y/N) | Adjustment (if any) | Basis |
|---|---|---|---|---|
| e.g., IRC 174/174A | e.g., New York | | | |
| e.g., IRC 168(k) | e.g., New York | | | |

A return with a materially affected federal provision and no corresponding row in this table has not completed the conformity checklist, regardless of what the rest of the workbook shows - do not treat the checklist as satisfied by having read it.

### Jurisdiction-Specific Estimated-Payment Safe Harbors

The federal safe harbors above (IRC 6654/6655) govern the federal estimated-payment calculation only - each state sets its own safe-harbor percentage, look-back period, and installment schedule, and these do not necessarily mirror the federal rule or each other.

Build a per-jurisdiction reference (never assume a state's rule from the federal one or from another state) covering, at minimum:

| Element | What to confirm per state |
|---|---|
| Safe-harbor basis | Percentage of current-year tax, percentage of prior-year tax, or both, at the state's own thresholds |
| Look-back period | Whether a prior-year safe harbor is offered at all, and for how many prior years |
| Large-taxpayer carve-out | Whether the state has its own income/tax threshold above which a prior-year safe harbor is unavailable (mirroring, but not necessarily identical to, the federal large-corporation rule) |
| Installment percentages and due dates | Whether the state follows a flat 25%-per-quarter schedule or its own percentage/date schedule |

Source every cell of this table from the specific state's current instructions at the time of the projection - state safe-harbor rules change with each legislative session, so a prior period's reference table should never be assumed current without re-confirming it.

## Entity Election & Tax Savings Analysis

### Entity Choice Landscape

Any entity-election question starts from where the business sits today and what it could elect instead. Use this general landscape for any entity type, not only the sole-proprietor-to-S-Corp case below:

| Entity Type | Default Tax Treatment | Owner-Level Exposure | Election Mechanics |
|---|---|---|---|
| Sole proprietorship | Disregarded; reported on the owner's Schedule C | Self-employment tax on all net profit | Default for a single-owner unincorporated business; no election needed |
| Partnership | Pass-through; Form 1065 + Schedule K-1 per partner | Self-employment tax on general-partner/active-member share; character of income and gains passes through | Default for a multi-owner unincorporated business under check-the-box |
| LLC (single- or multi-member) | Defaults to disregarded or partnership treatment | Follows the default or elected treatment | Form 8832 to elect corporate (C) treatment instead of the default; Form 2553 on top of a corporate election to further elect S status |
| S-Corporation | Pass-through; Form 1120-S + Schedule K-1 | Wages subject to FICA; distributions generally not subject to payroll tax | Form 2553, timely filed with all shareholders' consent; eligibility limits apply (no more than 100 shareholders, one class of stock, eligible shareholder types only) |
| C-Corporation | Entity-level tax; Form 1120 | Dividends taxed again at the shareholder level (double taxation) | Default for an incorporated entity that does not elect S status |

Every comparison below is one illustration of this general landscape, not the only comparison the skill supports - apply the same framework to any pair of entity types the request names.

### Entity Comparison Framework

A Tax Savings Estimator or entity-election workbook should compare, side by side, at minimum: federal tax, state tax, self-employment/payroll tax, net tax savings, and effective tax rate impact - for the current structure versus each potential election.

**Workbook structure** (apply the live-formula and structure-lock discipline in [Reconciliation Standards](references/reconciliation-standards.md) for the linking):

1. **Main Tax Savings Summary (dashboard)** - formula-linked from every input tab below; displays federal and state tax liability by structure, net tax savings, and effective tax rate impact in real time.
2. **Taxable Income Brackets (input tab)**
3. **Current Business Structure (input tab)**
4. **Potential Entity Elections (input tab)** - one row/column per election under consideration
5. **Deduction Categories (input tab)** - major deduction categories, including §199A QBI

**Illustrative comparison: sole proprietor/partnership vs. S-Corp election.** An S-election converts self-employment tax (15.3% on net earnings, uncapped for the 2.9% Medicare portion) into a split between reasonable W-2 wages (subject to FICA) and distributions (not subject to payroll tax) - the tax savings come from the portion of profit taken as distributions rather than wages, which is exactly why the reasonable-compensation determination below has to be defensible.

### 199A Qualified Business Income (QBI) Deduction

- Determine whether the trade or business is a **specified service trade or business (SSTB)** - health, law, accounting, consulting, financial services, and similar fields where the business's principal asset is the reputation or skill of its owners/employees.
- **Below the lower taxable-income threshold**: SSTBs and non-SSTBs both get the full 20% QBI deduction (subject to the taxable-income limitation).
- **Inside the phase-in range** (between the lower and upper thresholds): the deduction phases in/out proportionally using the statutory formula - this is a blend, not a hard cutoff at either end.
- **Above the upper threshold**: SSTBs get no QBI deduction at all; non-SSTBs are instead limited to the greater of 50% of W-2 wages, or 25% of W-2 wages plus 2.5% of the unadjusted basis of qualified property (UBIA).

### Reasonable Compensation (S-Corp Shareholder-Employee)

The IRS and courts weigh a multi-factor ("independent investor") test rather than a single rule - build the S-Corp Reasonable Salary Payroll Matrix against these same factors so the number is defensible if questioned.

**Workbook structure:**

1. **Main Compensation Summary (dashboard)** - the reasonable-salary conclusion, the salary-vs-distribution split, and the resulting payroll-tax impact, formula-linked from the detail tabs below.
2. **Owner-Employee Role Breakdown (input tab)** - one row per factor in the table below, documented for the specific owner-employee.
3. **Industry Wage Benchmarks (input tab)** - third-party comparable compensation data by role/industry/geography.
4. **Business Distribution Data (input tab)** - historical distribution and salary amounts, and the resulting ratio over time.

| Factor | What to document |
|---|---|
| Duties and responsibilities | Hours worked, role, and complexity of the owner-employee's actual work |
| Comparable compensation | Third-party industry/geography wage benchmarks for equivalent roles |
| Training and experience | Owner's qualifications relative to the role |
| Time devoted | Full-time vs. part-time involvement |
| Dividend history | Ratio of distributions to salary, historically |
| Compensation to non-owner employees | Internal pay equity check |
| What the business could pay an outside hire | The independent-investor return test - after paying reasonable salary, does the business still return a reasonable profit to a hypothetical outside investor? |

Shareholder-employee health insurance and fringe benefits follow S-Corp-specific rules (typically added to W-2 wages, then deducted above-the-line by the shareholder) rather than the normal employee exclusion - and unreimbursed home-office/vehicle expenses generally need an **accountable plan** in place before they can be reimbursed and deducted rather than personally absorbed.

## Self-Employment Income, Schedule C & Self-Employment Tax

Applies to any individual reporting business income on Schedule C - a gig-platform driver or courier, a freelancer or consultant billing clients directly, a sole proprietor running a trade or business, or a statutory nonemployee - not only the platform-income case used as the illustrative example below. Build a Main Schedule C Profit Summary formula-linked (per the live-formula discipline in [Reconciliation Standards](references/reconciliation-standards.md)) to input tabs for gross income (1099-NEC/1099-K/1099-MISC or direct invoicing - reconcile total gross receipts and watch for the same payment reported on both a 1099-K and a 1099-NEC when it flows through a platform), business mileage (miles × the IRS standard mileage rate in effect for the trip date, or the actual-expense method - commuting miles are never deductible), equipment (check placed-in-service date and whether 179/bonus depreciation applies), business-use-of-home, contract labor, and other ordinary and necessary business expenses.

**Schedule C line-item mapping** (illustrative set - map whatever expense categories the specific business actually has; confirm the mapping is applied consistently period over period):

| Schedule C Line | Item | Notes |
|---|---|---|
| Line 1 | Gross receipts | All income sources reconciled to gross - 1099-NEC/1099-K/1099-MISC for platform or contract work, invoices for direct billing, other receipts |
| Line 8 | Advertising | Marketing, website, and platform-promotion spend |
| Part II, Line 9 | Car and truck expenses | Mileage log × standard mileage rate, or the actual-expense method |
| Line 11 | Contract labor | Payments to subcontractors; issue Form 1099-NEC when required |
| Line 13 | Depreciation / Section 179 | Equipment, computers, and tools - check placed-in-service date and whether 179/bonus depreciation applies |
| Line 17 or Line 27a | Legal & professional / platform & software fees | Pick one line consistently based on the fee's characterization |
| Line 20b | Rent - vehicles/equipment | Leased equipment or vehicles used in the business |
| Line 22 | Supplies | Consumable materials and small tools |
| Line 25 | Utilities | Business phone, internet, and similar recurring costs |
| Line 30 | Business use of home | Form 8829 - simplified or actual-expense method, based on the applicable square footage |
| Line 27a | Other expenses | Any remaining item not otherwise mapped |
| Line 31 | Net profit | Flows to the Main Schedule C Profit Summary and the self-employment tax calculation below |

**Self-employment tax calculation** (applies to net Schedule C profit regardless of income source):

```
Net profit from Schedule C                          $XX,XXX
× 92.35%                                             = Net SE earnings
Net SE earnings × 12.4% (Social Security, up to
  the annual wage base)                              = $X,XXX
Net SE earnings × 2.9% (Medicare, uncapped)           = $X,XXX
SE Tax                                                = $X,XXX
Less: 50% of SE tax (above-the-line deduction)
```

Flag whether 199A QBI applies to the net Schedule C income (it commonly does for a sole proprietor).

## Indirect Tax (Sales/Use/VAT) Reconciliation & Audit-Ready Packages

Match transactions in tiers - exact, then within a tolerance window, then manual review - and carry what remains to a reconciling-items schedule, applying the materiality and tie-out discipline in [Reconciliation Standards](references/reconciliation-standards.md). This section adds what that does not cover: the indirect-tax-specific population (nexus/jurisdiction), the categorization and root-cause taxonomy, and the tax-determination traceability layer.

### Nexus

Confirm where the business has a filing obligation before reconciling anything: **physical nexus** (property, employees, inventory in a jurisdiction) and **economic nexus** (post-*Wayfair v. South Dakota*, most US states impose nexus based on sales/transaction-count thresholds regardless of physical presence). A reconciliation is only as good as the population of jurisdictions it covers - confirm the jurisdiction list is complete before reconciling within it.

### Tax Engine to GL Reconciliation

**Tax engine** here means whatever system or process actually determines transaction-level tax - a dedicated third-party tax-determination system, ERP-embedded tax logic, or a spreadsheet-based calculation. If the organization has no dedicated tax-determination system, reconcile from whatever source actually calculates the tax instead.

1. Extract the tax engine's calculated tax by transaction, the ERP sales register, and the GL tax accounts (collected and accrued) for the period and entity/country in scope.
2. Match transactions between the engine and the sales register by invoice/transaction ID, date, and amount.
3. Categorize every unmatched or variant item:
   - **In register, not in engine** - a taxable sale that never reached the tax calculation.
   - **In engine, not in register** - a calculated transaction with no corresponding sale record.
   - **Rate variance** - the same transaction taxed at different rates in each system (check whether a jurisdiction rate changed mid-period and the correct rate was applied by the transaction's own date, not a blanket quarterly rate).
   - **Exemption variance** - exempt in one system, taxable in the other (check that any exemption certificate was actually effective on the transaction's date, not merely on file).
   - **GL-only balances** - amounts sitting in a GL tax control account (e.g., accrued use tax) that were never reported on any filed return.
   These five categories reflect what commonly shows up in a tax-engine-to-GL reconciliation; they are not necessarily exhaustive for every ERP/tax-engine population. Where the organization has not previously validated its reconciliation categories with a sales/use tax or VAT specialist, treat this list as a starting point and confirm it against the actual population and system landscape before relying on it as complete.
4. Quantify each variance, assess the compliance/reporting risk it represents, and identify the likely root cause (system interface failure, rate table not updated, certificate expired) rather than stopping at "these don't match."
5. Route findings into the filing-deadline calendar (see Tax Organizer & Filing Readiness) so risk items surface before the return is due, not after.

### Audit-Ready Source-to-Filing Package

For a full traceability package (as opposed to a routine monthly reconciliation), build so that **any single transaction** can be picked up and traced end-to-end: source record → tax determination → ERP posting → filed return line. Include, for each transaction: the source document, the tax engine's calculation and rate applied, supporting documentation (exemption certificate, contract, or invoice), and the specific return line it was reported on (or the documented reason it wasn't). Treat supporting documentation as sufficient evidence only when it is dated and carries an identifiable approver or a system log; undated or uncorroborated documents are not sufficient on their own. Let the exception categories that show up (a document dated in the wrong period, a missing certificate, an unfiled use-tax accrual) emerge from tracing the actual population rather than assuming a fixed list up front - real populations produce exception types a predefined list won't anticipate. Before delivering, confirm every formula feeding the return-line tie-out actually evaluates; a broken or blank cell defeats the purpose of the package regardless of the narrative around it. Tracing a transaction to its filed return line establishes traceability and audit evidence; it does not by itself constitute or authorize return preparation, form population, or filing - route those activities to the entity's return-preparation process and retain the appropriate reviewer/preparer sign-off.

## Tax Authority Notice & Audit Response

### Examination Types

Apply the same response discipline below regardless of which type of engagement generated it:

| Examination Type | Scope | Typical Channel |
|---|---|---|
| Correspondence exam | A single issue or a small number of line items | Mail only |
| Office exam | Multiple issues, moderate complexity | In-person or virtual meeting at a local IRS/state office |
| Field exam | Complex returns, multiple years, or higher-dollar entities | Auditor works on-site or reviews records directly with the taxpayer/representative |
| Appeals | Disputing a proposed adjustment after an exam | Independent review, separate from the original examiner |

### Common Notice / Request Types

| Type | Typical Trigger | Response Urgency |
|---|---|---|
| IRS CP2000 | Income reported to IRS doesn't match the return | Moderate - respond by the stated date, can often be resolved by mail |
| IRS Information Document Request (IDR) | Active audit, requesting specific records | High - track due date and negotiate extensions if needed |
| 30-day letter | Proposed adjustment following an exam, appeal rights attached | High - appeal window is time-limited |
| Statutory Notice of Deficiency ("90-day letter") | Formal proposed assessment | Urgent - Tax Court petition deadline is jurisdictional and cannot be extended |
| State nexus questionnaire / VDA outreach | State believes the business has an unregistered filing obligation | Moderate-High - assess exposure before responding |
| Refund examination / assessment | State or IRS reviewing a filed refund claim or return | Moderate - depends on dollar exposure |

### Response Process

1. **Extract the facts from the notice itself**: notice/request type, issuing authority, tax year(s), entities, specific issues raised, items requested, due date, and any penalty/interest already assessed.
2. **Search prior work** (workpapers, prior correspondence, technical memos) for the same or a similar issue - reuse a previously accepted position where the fact pattern still matches, but confirm it before reusing rather than assuming it transfers automatically.
3. **Assess risk and exposure** for each issue: estimate the dollar exposure (tax, penalty, interest), and separate documentation gaps (recoverable by producing better records) from genuine technical disagreements (which need a substantive position, not just paperwork).
4. **Build the package**: an action plan sequenced to the due date with owners, an evidence/document checklist cross-referenced to each specific request item, a draft response addressed to the correct authority and organized to answer the notice point-by-point, and an issue tracker (status, owner, exposure, next action) so the team can see every open item at a glance.

Keep due dates prominent throughout - a technically strong response delivered late doesn't help, and a Tax Court petition deadline in particular cannot be extended.

## Tax Organizer & Filing Readiness

Lay out the tracker with task, owner, deadline, status and blocker columns; the tax-specific content - jurisdiction due dates, document requirements, and Outlook invite mechanics - is defined here.

### Organizer & Missing-Document Checklist

Build a per-entity organizer tracking prior-year data on file, current-year data received, and outstanding items, plus a checklist naming exactly what's still needed to complete each return. Work the population's actual facts rather than assuming every entity follows the standard path - a meaningful share of any real book will have a fact that changes the default treatment: a late extension that doesn't actually extend anything, an entity classification election that was never filed, an ownership change that splits a tax year, or a document filed under the wrong year or entity.

### Filing Deadline Reference (US federal, calendar-year entities)

| Return | Original Due Date | Extended Due Date |
|---|---|---|
| Form 1040 (individual) | April 15 | October 15 (Form 4868) |
| Form 1120 (C-Corp) | April 15 | October 15 (Form 7004) |
| Form 1120-S (S-Corp) | March 15 | September 15 (Form 7004) |
| Form 1065 (Partnership) | March 15 | September 15 (Form 7004) |
| Form 990 (Exempt org) | May 15 | November 15 (Form 8868) |

Anchor every deadline to the entity's actual fiscal year end, not a blanket calendar-year assumption, and carry forward any already-filed extension so the calendar reflects the real deadline. A late-filed extension is generally ineffective - the original due date still governs, and any penalty clock starts there. State and local due dates vary by jurisdiction and conformity to the federal calendar - confirm each jurisdiction's own date rather than assuming it mirrors the federal one.

The table above covers the most common entity income-tax return types; apply the same anchor-to-fiscal-year-end and extension-tracking methodology to any other filing obligation the organizer needs to track - payroll returns (Forms 941/940), information returns (the 1099 series, W-2/W-3), estate and trust returns (Form 1041), exempt-organization unrelated business income (Form 990-T), and excise tax returns each have their own due-date and extension-form pairing to look up and anchor the same way.

### Filing Deadline Calendar Invitations

Sequence each review meeting ahead of its statutory due date (not on it), with the responsible partner and senior staff as required attendees, the relevant checklist attached, and an agenda covering returns due, current preparer/reviewer status, and any extensions or open items. Flag any deadline at risk explicitly so partners can prioritize review time and decide on extensions.

## New / Newly-Active Master Data for Tax Scoping

Apply the completeness principle in [Reconciliation Standards](references/reconciliation-standards.md) (work the full population, state exactly what's excluded and why) - the tax-specific addition is treating a new or newly-active master data element as a potential filing-obligation or apportionment trigger, not just a data anomaly. Before running a provision, reconciliation, or organizer cycle, check for master data (entities, accounts, products, profit centers) that is new this period or that existed but had no prior-period activity. New entities may carry their own filing obligation; newly active accounts or product lines can carry indirect-tax or apportionment implications that existing workpapers don't yet cover. Compare current- and prior-period activity by the element's unique identifier (not name, since names get reused or renamed), and report both periods' balances side by side for anything flagged - a flag with no supporting numbers doesn't let a reviewer judge materiality.

## Tax Provision / Account Analysis Memo

The narrative that accompanies a provision or tax account analysis for a reviewer who hasn't seen the underlying workpapers (structured like an account reconciliation memo). The memo must stand alone.

```
TAX PROVISION / ACCOUNT ANALYSIS MEMO

Entity:             [Legal entity]
Period:             [Period end date]
Prepared by:        [Name]            Date: [Date]
Reviewed by:        [Name]            Date: [Date]

CONCLUSION
[Lead with the bottom line: "ETR of XX.X%, consistent with prior
period" / "ETR increased X.X pp driven by [discrete item]" /
"Provision reflects a new valuation allowance of $X,XXX against
the [jurisdiction] deferred tax asset."]

ETR SUMMARY
Statutory rate:                                XX.0%
Effective rate:                                 XX.X%
Discrete items this period:                     $X,XXX

KEY MOVEMENTS
| # | Item | Amount | Driver | Recurring? |
|---|------|--------|--------|------------|
| 1 | [Item] | $X,XXX | [Cause] | Yes / No - discrete |

UNCERTAIN TAX POSITIONS
[Any new or changed UTBs this period, the technical basis, and
the measurement conclusion. State if none.]

EXCEPTIONS / ITEMS REFERRED
[Anything not recorded this period and why - passed under
threshold, held for approval, or referred for further technical
assessment. State if none.]

SIGN-OFF
[Preparer / Reviewer / Approver - names and blank date fields
until actual sign-off.]
```

**Writing guidance:**
1. **Lead with the ETR and the conclusion**, not the mechanics - a reviewer's first question is always "did the rate move, and why."
2. **Separate discrete from recurring** - a one-time item (a settlement, a rate change) explains a rate movement very differently than a shift in the ongoing effective rate.
3. **Justify every position with its technical basis** - cite the ASC 740 recognition/measurement conclusion for any uncertain position, not just the dollar amount.
4. **Write for audit** - a provision memo is frequently reviewed months later by an external auditor or a new preparer; spell out account numbers, entry numbers, and source schedules rather than assuming context.

## Tax Preparation Best Practices

For general Excel-workbook and reconciliation discipline - live formulas, materiality tie-outs, disclosed-vs-derived sourcing, structure lock - follow [Reconciliation Standards](references/reconciliation-standards.md). The items below are the tax-specific additions on top of it:

1. **Rate discipline:** measure deferred balances using the enacted rate expected to apply when each temporary difference reverses, including an enacted future-period rate only when the reversal is expected in that period.
2. **One tax effect per entry:** never net multiple discrete tax effects (a credit, a rate remeasurement, a valuation allowance movement) into a single journal entry - this is stricter than general journal-entry line-item granularity.
3. **Discrete vs. recurring, always separated:** every driver table and memo splits one-time items (a settlement, a rate change, a one-time UTB movement) from the ongoing effective rate - a generic variance or reconciliation workpaper has no equivalent concept.
4. **Technical basis over conclusion:** every uncertain tax position needs its two-step ASC 740-10-25 recognition/measurement conclusion written down, not just the recorded dollar amount.
5. **Jurisdiction awareness:** nexus, apportionment, and filing obligation are entity- and jurisdiction-specific - confirm the population of jurisdictions before reconciling or projecting within it.
6. **Deadlines are jurisdictional, not organizational:** unlike an internal close-calendar task, a missed tax deadline (a Tax Court petition, a lapsed extension) can be legally unrecoverable - surface at-risk dates explicitly rather than folding them into a generic status tracker.

## Document Output

Create tax account-analysis and provision workbooks, tax savings / reasonable-compensation / gig-worker Schedule C tie-out estimators, and indirect-tax reconciliation or audit-ready packages as an `.xlsx` using `xlsx` if it is offered in this conversation, or the available workbook tools otherwise. For provision memos, notice/audit response packages, and companion user guides, create a `.docx` using `docx` if it is offered in this conversation, or the available document tools otherwise.
