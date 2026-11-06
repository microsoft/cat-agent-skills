---
name: budget-and-forecast
description: "Plans budgets and forecasts from source-system actuals and departmental inputs through consolidated outlooks and leadership decisions. Supports loading actuals into planning templates, establishing baselines, mapping accounts and owners, consolidating P&L, balance-sheet, and cash-flow forecasts, validating assumptions, creating waterfall and driver analyses, allocating company targets across departments, comparing plans with targets, and preparing budget presentations. Produces refreshable models, scenarios, allocation logic, variance commentary, data-quality exceptions, tradeoffs, and required decisions. Use for annual budgets, rolling forecasts, reforecasts, consolidation, driver-based forecasting, target setting, variance analysis, or strategic planning reviews."
metadata:
  version: '1.0.0'
  category: 'analysis'
  icon: 'DataTrending'
  argument-hint: '<intake|consolidation|allocation> [period]'
---

# Budget and Forecast

Turn source actuals into a planning baseline in which every row is traceable and every unresolved item is visible.

> **Important**: This skill assists with planning data preparation but does not provide financial advice. Budget owners and finance should review mappings, baselines, and exceptions before the planning cycle opens.

**Load the `accounting-root-skill` skill before constructing any artifact.** Its requested-file and requested-structure constraints override the example layouts below. Load the implementation skill for each requested file type before touching deliverables. Consolidate department plans without allowing a partial population, duplicate version, or dropped line to masquerade as a complete company plan.

> **Important**: This skill assists with planning consolidation but does not provide financial advice. FP&A should review the consolidated plan and its exceptions before management use.

Create a target allocation in which every amount traces to a driver, a weight, a constraint, or a named human override.

> **Important**: This skill assists with target-setting mechanics but does not provide financial advice and does not decide what a department's target should be. Leadership must approve, adjust, or reject the proposal.

## Scope

Use this skill for the whole planning cycle: account-to-planning-line mapping, YTD-to-full-year baseline construction, period phasing, populating departmental templates and intake exceptions; the submission register, version and completeness controls, central-assumption checks and rollup by account and period; and driver selection, weighting, normalization, floors, caps, residual handling, target-versus-ask analysis and allocation governance.

Acquire and clean source actuals with whatever data connectivity and cleanup capabilities are available in the current workspace. Use `financial-statements` for legal-entity consolidation and intercompany eliminations. For a bridge, show each driver's contribution from the starting figure to the ending figure, and check that the contributions sum exactly to the total change. Build any leadership deck with the presentation capability available in the current workspace.

## Core invariant

Every source row ends in exactly one reported state:
1. **Mapped**: it has a planning line, owner, and period.
2. **Excluded by rule**: the named rule explains why it is outside planning scope.
3. **Exception**: a human decision is required.
Never absorb an unmapped row into `Other` merely to make the total tie. A consolidated total is only as complete as the submission list behind it. Establish who was asked, who submitted, and which version is authoritative before rolling up any number. Every final number is computed or explicitly overridden with a named owner and reason. A value that is neither is an unexplained plug.


## Track: Intake

### 1. Profile the extract

Determine and record:

- Whether period columns are period-to-date or year-to-date. Never sum cumulative YTD columns.
- The sign convention for revenue, expenses, debits, credits, and reversals.
- Whether amounts include commitments as well as actuals; separate them when both are present.
- The hierarchy version and effective date for departments and cost centers.
- Whether the latest period is closed and whether adjustments or reclasses are complete.
- Currency type and rate basis: transaction, functional, or reporting currency.

If the source cannot establish one of these facts, mark it as an assumption or exception rather than guessing.

### 2. Build and validate the crosswalk

Represent mappings as data, one row per source account, with these fields when the requested structure permits: source account, source account name, planning line, planning category, mapping basis, and status. Preserve account codes as text so leading zeros survive.

Carry every supplied organizational dimension through the mapping, including cost center, profit center, internal order, WBS, project, activity, and initiative. If activity or initiative is absent, do not invent a taxonomy unless the request explicitly asks for one; identify the missing dimension instead.

Distinguish mappings supplied by the user from mappings inferred from account names or prior-year files. Label every inferred mapping and route it for confirmation.

Validate all of the following:

| Check | Exception |
|---|---|
| Every source account appears in the crosswalk | Unmapped account, with amount |
| One source account maps to no more than one planning line | Duplicate mapping |
| Every expected planning line has a feed | Empty planning line |
| Cost center exists and is open in the current hierarchy | Closed or unknown cost center |
| Every populated template has an owner | Missing owner |
| Used account exists in the supplied chart of accounts | Account not in COA |

Sort exceptions by absolute amount descending so material items appear first.

### 3. Build the remaining-year baseline

Choose the method from the strongest supplied evidence, in this order:

1. **Contractual or driver-phased** when contracts, hire dates, volumes, or calendars are supplied.
2. **Prior-year shape on a supplied annual total** when seasonality is supported by history.
3. **Seasonality-adjusted run rate** when prior-year shape is representative but no annual total is supplied.
4. **Straight run rate** only for stable recurring lines with complete closed periods.

If evidence does not support a method, use straight run rate only as a clearly labeled provisional baseline for stable recurring items and flag all other lines for finance review. Never silently select a method.

For every line, show YTD actuals, remaining-year baseline, full-year total, and method. Make the full-year total a formula over YTD plus remaining year. Do not run-rate partial periods, one-time items, or known annual payments. For headcount, use supplied start dates; absent dates, state that the baseline assumes existing headcount only.

### 4. Phase annual values

- Preserve a supplied monthly or quarterly shape exactly.
- Otherwise use a supported historical or driver-based shape.
- Use equal phasing only when no better evidence exists, label it as an assumption, and make the residual period absorb rounding so periods reconcile exactly to the annual total.
- Keep weights visible and verify that they sum to 100%.

### 5. Populate templates safely

Before writing, inventory input cells, formulas, named ranges, validation, protection, and check rows. Locate inputs by headers and labels rather than fixed addresses. Write values only into cells that are demonstrably inputs. Never overwrite a formula, unprotect a sheet, insert or delete rows, or change the locked tab roster.

If writable inputs cannot be identified confidently, produce the mapped and validated dataset in the requested output structure and surface the blocked write as an exception. Do not take a risky template edit merely to complete the population step.

After writing, re-open the workbook and verify that formulas remain formulas, existing checks still evaluate, no new formula error is visible, and written totals equal intended totals.

### 6. Report exceptions

For each exception, preserve: type, affected account/cost center/template, amount, department or owner, action taken, decision needed, and whether it blocks planning. Phrase the decision needed as a question a named owner can answer.

If the request fixes the workbook structure, place this information in an existing requested area without adding a tab. If structure is not prescribed and exceptions are requested, use the minimum additional structure necessary. State explicitly when no exceptions were found.


## Track: Consolidation

### 7. Establish the population

Create a submission register in the requested structure with one record per in-scope department: department, owner, requested, received, source file and date, version, status, and inclusion status.

State the population summary wherever the consolidated result is presented, for example: `22 requested; 19 received; 3 missing; total excludes Legal, Facilities, and IR.`

Resolve versions explicitly:

- Default to the latest received timestamp only when no version-of-record instruction exists.
- Record every superseded file and the rule used.
- Never sum two versions for one department.
- Flag a post-deadline resubmission for a scope decision rather than replacing it silently.
- Do not estimate a missing department unless instructed. If instructed, label every derived line as estimated in both detail and totals.

### 8. Standardize submissions

Match sheets and data blocks by labels and structure, not filenames, tab names, or fixed addresses. Normalize the master calendar and identify fiscal-versus-calendar mismatches. Preserve supplied account, department, project, initiative, and period dimensions.

Handle deviations visibly:

| Condition | Treatment |
|---|---|
| Renamed tab | Match by structure and record the source tab |
| Invented line | Map if defensible and list it for FP&A review |
| Inserted or deleted rows | Anchor on labels; never rely on addresses |
| Annual value where periods were requested | Flag incomplete granularity; phase only if instructed |
| Hard-coded override on a formula line | Preserve and flag the override |
| Unit mismatch | Compare magnitudes and surface the suspected scale; do not silently rescale |

The invented-line list is required review information because repeated invented lines can show that the template itself is incomplete. When structure is locked, place it in an existing requested review area rather than adding a tab.

### 9. Test central assumptions

For each supplied central assumption, derive the implied rate from each submission where possible, compare it with the issued rate, and report the department, implied rate, issued rate, and dollar effect. Mark an assumption as unverifiable when source detail cannot support the test; do not treat unverifiable as compliant.

Do not average deviations away in the consolidated total. A department-level exception may be approved, but it still needs to remain visible.

### 10. Roll up

- Aggregate detail to subtotal to total. Never sum totals that already include the same detail.
- Roll up by account and period while retaining the department dimension for drill-back.
- Preserve supplied initiative, project, and activity dimensions.
- Make subtotals formulas over delivered child rows rather than typed constants.
- Reconcile every department's consolidated slice to its authoritative submission.
- For balance sheet and cash flow views, distinguish department-submitted lines from centrally derived lines, and state the linkage and working-capital assumptions used.

### 11. Run controls

Always run internal consistency checks:

| Check | Failure meaning |
|---|---|
| Sum of included department totals = consolidated total | Dropped or double-counted submission |
| Consolidated department slice = authoritative submission | Mapping loss or duplication |
| Sum of periods = annual amount for every line | Phasing or normalization error |
| Every submitted line is included or explicitly excluded | Silent data loss |
| Current round vs prior round, when supplied | Unexplained movement |

Use the user-supplied board envelope, approved target, or prior-round control total when one exists. When none exists, do not invent an external tie-out: label the controls as internal consistency only. Show each check as a formula with visible pass/fail when the output format supports formulas.

### 12. Produce the FP&A review list

Surface missing submissions, duplicates, superseded versions, assumption deviations, invented lines, incomplete granularity, outliers, unit-scale suspicions, and hard-coded overrides. Sort by absolute dollar effect, with blockers first. Include the specific decision or follow-up owner needs.


## Track: Target allocation

### 13. Define the target

Record on the face of the requested output:

- What is being allocated: total budget, incremental increase, savings, investment, or margin.
- Amount, currency, period, and source or authority.
- In-scope departments and any excluded or ring-fenced amounts.
- Whether the total is fixed or a starting point.

Remove ring-fenced amounts from the allocatable pool before weighting. For a fixed envelope, reconcile exactly. For a starting point, show the resulting gap as an output.

### 14. Select drivers and weights

Use user-supplied drivers and weights when provided. For each driver, show its definition, source, as-of date, rationale, and department-level values.

When no method is supplied, use this conservative operational default:

1. For a savings target, allocate provisionally in proportion to prior-period **controllable** spend after excluding protected and contractual amounts.
2. For a recurring operating budget, use prior-period controllable spend unless a more causal supplied driver such as headcount, transactions, or units explains the cost.
3. For an investment pool, use a supplied strategic-priority or demand measure. If none exists, do not fabricate a priority score; use an equal-share provisional scenario and flag driver selection for leadership.

Label every default-based result `Provisional`. Prefer one defensible driver to several arbitrary weights.

Normalize each driver across the in-scope population:

```text
department_share = department_driver / sum(in_scope_driver)
composite_share = sum(driver_weight * department_share)
raw_allocation = allocatable_pool * composite_share
```

Weights must be visible, editable, and sum to 100%. If a department lacks a driver value, either assign zero or re-normalize its remaining weights, but state the choice and show its effect.

### 15. Apply constraints mechanically

Represent floors, caps, protected amounts, and contractual minimums as visible inputs. Apply them with formulas and show a binding flag for each department.

After constraints:

1. Calculate displacement from the unconstrained allocation.
2. Redistribute displacement across unconstrained departments in proportion to composite share.
3. Re-apply constraints because redistribution can make another constraint bind.
4. Repeat until no new constraint binds or the stated iteration limit is reached.
5. If the constraints are infeasible, report the shortfall or excess. Never hide non-convergence.

Round only after the constrained allocation is stable. Show unrounded and rounded amounts when material, then assign the rounding residual to one named department or central line using a stated rule. Verify final rounded allocations reconcile exactly to the fixed target.

### 16. Compare target with submitted ask

Where submissions exist, preserve one row per department with: prior-year basis, driver contributions, composite share, raw allocation, binding constraint, final target, submitted ask, currency and percentage gap, required adjustment, status, and escalation flag.

Sort by absolute or unfavorable gap according to the decision being made. Translate the adjustment into the department's own supplied units only when the source supports it; otherwise report the currency gap without inventing an operational equivalent.

### 17. Document governance

Within the requested structure, preserve:

1. Target, authority, scope, and ring-fenced amounts.
2. Drivers, weights, rationales, sources, and as-of dates.
3. Constraints and which departments they bind.
4. Departments materially moved by constraints rather than drivers.
5. Overrides, owner, date, and reason.
6. Escalation items requiring leadership judgment.
7. Scenario and version of record, including what changed from the prior version when supplied.

### 18. Run defensibility checks

Surface rather than silently resolve:

- A department below a supplied viable run rate.
- A stated strategic priority receiving a reduction.
- One driver effectively dominating the result.
- Material instability under small, disclosed weight changes.
- Constraints binding for so much of the population that constraints, not drivers, determine the outcome.
- A fixed target that does not reconcile after rounding.

If the source shows that allocation is negotiated rather than formula-driven, use the computed allocation only as an opening position. Preserve the opening position, each ask and justification, approved changes, decision owner, escalation outcome, and final position as the audit trail.


## Output discipline

- Produce exactly the requested files and formats. Do not add a workbook behind a requested deck or memo unless the user asked for it.
- For a workbook, make mappings, methods, assumptions, formulas, and checks visible within the requested structure.
- For a presentation, apply this method in working analysis and show the requested conclusions, sources, assumptions, and material exceptions in the deck.
- Reconcile source total = mapped + excluded + exceptions, and baseline annual total = YTD + remaining year, before delivery.
- Produce exactly the requested files, tabs, sections, and formats. The register and review list are required information, not permission to add unrequested tabs or companion files.
- For a workbook with no prescribed structure, use the fewest tabs needed to hold the requested model, population status, controls, and exceptions.
- For a presentation, perform the consolidation as working analysis, then include the population summary, material exceptions, and requested financial views in the deck only.
- Before delivery, reconcile all included submissions, period totals, annual totals, and the stated population count.
- Produce exactly the requested files and formats. Do not add an allocation workbook behind a requested deck unless the user asks for both.
- For a workbook, keep drivers, weights, constraints, overrides, and reconciliation visible within the requested structure.
- For a presentation, show the target, allocation basis, material movements, binding constraints, requested decision, and reconciliation in the deck.
- Recalculate and verify weights = 100%, shares = 100%, and final allocation = fixed target before delivery.


## Do not

- Do not silently drop or bucket an unmapped account.
- Do not overwrite a formula or protected cell.
- Do not deliver a full-year number without its components and method.
- Do not run-rate one-time items or unclosed periods without an explicit caveat.
- Do not infer a mapping without labeling it as inferred.
- Do not drop supplied dimensions or reorder supplied figures.
- Do not publish a total without its submission-population summary.
- Do not sum duplicate or superseded versions.
- Do not substitute a missing department unless explicitly instructed and visibly labeled.
- Do not average away an assumption deviation.
- Do not present centrally derived lines as department submissions.
- Do not rely on cell addresses, filenames, or tab names as the only locator.
- Do not perform legal-entity elimination logic in this workflow.
- Do not create an unexplained plug.
- Do not bury weights or constraints inside opaque formulas.
- Do not derive a driver from a post-allocation figure.
- Do not apply constraints or overrides silently.
- Do not hide infeasible constraints or non-convergence.
- Do not spread a rounding residual invisibly.
- Do not present a model result as an approved decision.
