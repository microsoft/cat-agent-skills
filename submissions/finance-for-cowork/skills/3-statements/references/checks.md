# Reconciliation and Scenario Checks

Read before final QA. Apply only to schedules, periods and scenarios actually in scope. These are tests of a completed template, not a mandate to create new tabs or accounting policies. Record results in the check register specified by SKILL.md.

## Evidence and tolerance gates

Before a numeric check can pass, its inputs must be resolved, its formulas recalculated and its scope/date/definition aligned. A cached value, a blank treated as zero or a rounded display is not evidence. Document rounding tolerance in the model's units, appropriate to source precision; never widen it to conceal a discrepancy. State which checks were not run and why.

## Statement-level checks

| Check | Test | Applicability / interpretation |
|---|---|---|
| Historical source mapping | Cell value agrees to cited evidence after documented units/sign conversion | Every historical hardcode; trace adjusted figures to a separate bridge |
| IS subtotals | Revenue/costs reconcile through gross profit, EBIT, EBT and NI | Follow actual layout; D&A/SBC included in operating costs must not be deducted twice |
| BS balance | Assets − liabilities − equity = 0 within tolerance | Every modeled period and tested scenario |
| Cash roll-forward | Beginning CF cash + CFO + CFI + CFF + FX/other evidenced effects − ending CF cash = 0 | Same cash definition throughout; noncash financing is excluded from cash flows |
| CF-to-BS bridge | Ending CF cash − corresponding BS cash components = 0 | Identify cash equivalents, restricted cash and other included/excluded balances explicitly |
| Beginning cash | Current opening CF cash − prior closing CF cash = 0 | Bridge any changed definition/reclassification; first period needs source evidence |
| NI link | IS NI − indirect-CF starting NI = 0 | Indirect method only; direct method uses receipts/payments with any required reconciliation separately |
| RE | Prior RE + NI − dividends +/- documented RE adjustments − ending RE = 0 | Use the NI attributable to the relevant equity holders; consider supported NCI allocations |
| Equity | Opening stock/APIC + documented cash/noncash movements − closing stock/APIC = 0 | Separate SBC, issuance costs, repurchases and conversions as relevant; do not equate all equity changes with cash financing |
| Opening balances | Opening balance − prior close/formation evidence = 0 | First modeled year is not automatically company formation |
| Monthly/annual | Final month closing balance − annual closing balance = 0 | Only when both frequencies exist; sum flows across matched periods, not balance-sheet stocks |

### Cash bridge discipline

Record each component of the CF and BS definitions and both dates. For example, where CF covers cash, cash equivalents and restricted cash, reconcile it to those BS components rather than comparing it with unrestricted cash alone. Explain any other classification difference explicitly. FX on cash is part of the CF roll-forward where applicable; it is not an invented balancing item and must not be counted twice. Investigate remaining differences; never change reported values to force a tie.

## Supporting schedules

- **Working capital:** opening + supported operating/noncash movements = closing. Tie AR, inventory and AP to BS and cash movements to CF. Acquisition, FX and reclassification effects can make raw BS changes differ from reported cash changes. Use actual period days, documented average/ending balance conventions and a defensible purchases/COGS basis for DPO.
- **PP&E/intangibles:** reconcile additions, disposals, impairments, acquisitions, FX and transfers. Remove accumulated depreciation associated with disposals. Tie D&A to both IS classification and CF noncash adjustments; distinguish cash CapEx from noncash additions.
- **Debt:** reconcile opening balances, borrowing, repayments and noncash changes to current/long-term BS balances. Tie cash movements to CFF, interest to IS and relevant cash classifications to company policy. Inspect convergence if the template is circular.
- **Tax/NOL:** loss use cannot exceed eligible available losses or sourced jurisdiction/vintage limits; ending NOL is nonnegative. Tie gross DTA, valuation allowance and net DTA to BS. Separate current tax expense, deferred expense/benefit and cash payments. Reconcile non-P&L DTA movements rather than reversing the entire BS change in CFO.
- **Equity/SBC:** expense already enters NI and RE. Equity-classified awards generally enter APIC; liability awards follow their own schedule. Only genuinely noncash expense is an indirect-CFO add-back, once. Source opening balances rather than assuming zero.

## Formula and scenario checks

Inspect formulas across forecast columns for shifted references, wrong absolute/relative anchors, inconsistent periods, embedded assumptions, stale external links and broken ranges. Trace precedents when results are surprising. Check that repeated figures link to one source and that every unresolved input blocks dependent verification.

For each existing or approved scenario, verify selector validation and its exact mapping (including CHOOSE or INDEX/MATCH logic), confirm intended drivers reach all statements, recalculate and repeat accounting checks. Restore the original selector after tests. Explain unexpected NI, EBITDA, FCF, margin or leverage ordering; growth investment and financing can reverse apparent hierarchies. Do not force a ranking.

Calculate margins/credit metrics only when requested or required. Use sourced covenant definitions and thresholds, not universal traffic lights. Mark missing, zero or inappropriate negative denominators not meaningful. Unexpected margins are investigation prompts, not automatic formula failures.

## Final status and debugging

Trace any failed check to its source or formula, correct only in-scope causes and rerun affected checks. Log approved logic changes. Remove scratch-test values and verify preservation of workbook features. Stop at the spreadsheet workflow's retry limit; disclose remaining errors.

- All required inputs resolved, recalculation complete and all applicable checks passed: **ALL APPLICABLE CHECKS PASS**.
- Any failed test: **ERRORS DETECTED - REVIEW BELOW**.
- Missing inputs, unavailable recalculation or unperformed required tests: **INCOMPLETE / NOT VERIFIED**; show alongside failures when both apply.

A reconciliation pass is not an accounting audit or assurance opinion.
