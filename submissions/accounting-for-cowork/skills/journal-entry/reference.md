# Cloud workbook validation reference

Use this procedure with the Journal Entry workflow before handing off a OneDrive workbook. It is guidance for using existing cloud Excel tools, not a bundled executable validator, automatic enforcement or proof of accounting correctness.

## Establish expectations before construction

Record an internal requirement-to-evidence checklist before building the output. For each requested schedule or entry, identify the authentic source and its workbook, sheet and range; required population; grouping dimensions; account and entity mapping; supported amounts; dates; control rule; and preservation requirements. Expected results must come from the request and source detail, not the delivered totals, a human exemplar or hidden reference answers.

Cover every requested schedule, not just the journal entry or sheet names. Distinguish source populations, recurring debit and credit lines, acquisition/opening entries, offsets, subtotals, corrections and unresolved items. Establish which dimensions each role actually requires. Do not hide missing mappings by selecting only rows with populated dimensions. Keep working notes internal, not extra deliverable files or tabs.

Preserve the cloud template's exact identifiers, sheet names/order, headers, rows/columns, formulas and requested layout. Capture the original cloud values/formulas needed for comparison before editing. Do not download a workbook or assume a local XLSX exists.

## Read the actual cloud output

Use the existing cloud workbook tools with the real OneDrive/SharePoint workbook and the tool's canonical document context. If the tool resolves the current workbook from its context, verify that it is the intended cloud document. Do not invent authorization or override the tool context.

Read actual sheet names, bounded ranges, headers, values and formulas for every required population. Load the needed range properties and let each read complete before inspecting results. Use the existing tool's supported execution and returned-result contract; no new tool, connector or permission bypass is implied. Any task-specific calculations use the available tools, not a shipped helper.

Inspect detailed rows and control cells, not only grand totals, an error count, preview/search snippets or a model-retyped summary. Use explicit headers and distinct physical debit/credit columns; do not alias two meanings to the same cell. If a result is truncated, partition reads into explicit populations and inspect every partition, including the remaining tail. Missing sheets, partial reads, sync/transport failures or unreadable results mean the affected check is unavailable, not passed.

## Compare the full requirement set

| Area | Required comparison |
| --- | --- |
| Population and structure | Reconcile source records to each required schedule and entry population. Check sheet names/order and contents, not names alone. Explain exclusions, duplicates, extra rows and missing records. |
| Grouping | Compare all required group keys, row multiplicities and amounts against independently supported expectations on both debit and credit sides. Equal grand totals do not clear missing, merged, swapped or phantom groups. |
| Identity and mapping | Verify account codes, entity, department, cost center and other requested dimensions for each applicable role. Null, empty or whitespace-only required identities remain unresolved; numeric zero can be a valid code. Preserve meaningful nonblank identifiers exactly rather than trimming them into agreement. Legitimate offsets need only their required dimensions. |
| Amounts and balances | Reperform supported calculations with the stated units, currency, precision and rounding. Compare per-group amounts and each entry's debits/credits, signs and direction. Do not infer currency conversion or treat a missing formula result as zero. Overflow or unsupported precision prevents a reliable check. |
| Dates and periods | Check entry dates separately from preparation dates. Recompute duration from the agreed endpoints, inclusion/exclusion and day-count convention; trace the checked basis through expense, balances and entry lines. Retain and disclose contradictory source counts. |
| Controls and statuses | Test each status against its own named source quantity and policy: correction, conditional adjustment and held exposure are different bases. Establish units, signed versus absolute magnitude, threshold, comparison operator and equality treatment from authority. Numeric tolerance must not conceal crossing a policy boundary. |
| Holds and preservation | Check that actual held rows retain their supported identities, amounts and honest status. Compare preserved cloud values, text, formulas and structure with the original readback. A global hold does not excuse omitted supported dimensions or a falsely cleared control. |

Evaluate formula results as well as formulas. Missing or unavailable calculation results, Excel errors and incomplete readback cannot support a passed check. An explicit empty-string formula result is not automatically a missing cache, but it still cannot satisfy a required identity. Recalculate using available cloud tools when appropriate, then read again.

Keep valuation, mapping, recognition and source authority distinct from arithmetic agreement. A provisional calculation may reconcile under a disclosed assumption without proving the assumption correct. Do not invent account mappings, policy, approval or a zero expected amount for an unknown item. Preserve conflicting evidence and identify the specific clarification needed.

## Correct, reread and hand off honestly

Record each check as passed, failed or unavailable, with the actual observed range, expected basis and relevant limitation. Do not call the whole workbook verified because one total balances or a subset of checks passes. Also inspect rendered layout with available cloud tools; cell comparisons alone do not establish styles, print layout, protection or other template requirements.

Correct supported defects, read the current cloud output again and repeat the affected comparisons within at most two correction/revalidation cycles under the accounting-root limit. Any subsequent edit invalidates the earlier affected check. Never clear a failure by dropping rows, plugging balances, weakening tolerances or redefining expectations to match the output.

Separate missing evidence, observed failures and pending approval. Retain a complete labeled draft when possible, including supported work and explicit unresolved items; source gaps do not automatically prohibit every workpaper. State the affected line/amount/period, source, needed action and known owner in the requested structure or handoff. Do not add unsolicited control tabs. Do not claim a completed workbook when none was produced, or posting readiness, approval or completed validation when mandatory checks fail or remain unavailable.

This prose-only reference does not guarantee deterministic execution, model compliance, full requirement interpretation or no regression. Report what the actual cloud reads and comparisons establish, and disclose what was not checked.
