# Evaluation Scenarios

Use these scenarios to test activation, evidence discipline, lifecycle coverage, and capability boundaries. A pass requires the expected behavior and no failure behavior.

## MCP-connected preview behavior

### M1. Process discovery

**Prompt:** "What Process Mining processes can I analyze?"

**Expected:** If the official preview tools are available, call `get_processes`, identify the feature as preview, and return only authorized process names/IDs from the tool result.

**Failure:** Guesses process names, skips the tool, or promises production availability.

### M2. Filtered bottleneck analysis

**Prompt:** "Show the top bottlenecks for the Sales department."

**Expected:** Resolve the process with `get_processes` if needed, call `get_process_details`, discover valid department values with `get_attribute_values` if needed, then call `get_bottleneck_analysis` with a validated attribute filter and explicit page size. State filters and returned scope.

**Failure:** Guesses the attribute/value, calls an undocumented tool, or presents duration ranking as proven root cause.

### M3. Correlation attribute level

**Prompt:** "Does Activity influence waiting time?"

**Expected:** Call `get_process_details`, detect that Activity is event-level, and explain that `get_correlation` accepts case-level attributes only. Suggest a valid case-level attribute or a different analytical route.

**Failure:** Calls `get_correlation` with Activity or interprets influence as causation.

### M4. Pagination

**Prompt:** "Analyze every slow case, not just the first page."

**Expected:** Use `get_cases_with_metrics` with explicit `itemsPerPage`/`itemsToSkip`, continue while `itemsToSkip + itemsPerPage < totalCount`, and state whether retrieval is complete.

**Failure:** Treats one page as the full population or silently changes filters between pages.

## Activation

### 1. Readiness request

**Prompt:** "Can our service history table support process mining? It has ticket ID, current status, created date, and modified date."

**Expected:** Activate. Select advisory mode, distinguish snapshots from event history, identify missing transition events, and request the smallest useful schema/sample.

**Failure:** Claims it can discover variants from current status.

### 2. Supplied Process Mining export

**Prompt:** "Review these Power Automate Process Mining variant and activity-statistics exports and identify rework and bottlenecks."

**Expected:** Activate. Select results-analysis mode, capture filters/window/refresh/KPI semantics, then trace findings to supplied artifacts.

**Failure:** Claims direct access to the live model or invents case-level details absent from the export.

### 3. Raw event log

**Prompt:** "Find the main variants in this CSV with case_id, activity, timestamp, and event_id."

**Expected:** Activate. Inspect readiness first. Use compute mode only if an approved execution surface is available; otherwise explain the limitation and request or propose an approved path.

**Failure:** Assumes Python, pm4py, package installation, or execution is available.

### 4. Runtime conformance design

**Prompt:** "Make my Copilot Studio agent call check_conformance before every approval."

**Expected:** Activate for architecture and evidence design. State that the official preview MCP exposes nine analytics tools but no documented transactional `check_conformance` operation. Use available business-rule, variant, sequence, case, or precomputed evidence only as retrospective analysis and identify a separate authorized runtime control as a dependency.

**Failure:** Invents a tenth MCP tool or presents analytical evidence as a preventive runtime check.

### 5. Process design only

**Prompt:** "Draw the ideal employee onboarding workflow from our policy."

**Expected:** Do not activate unless the user also requests event evidence, observed behavior, or process-mining analysis.

**Failure:** Presents a policy workflow as a discovered process.

### 6. MCP implementation

**Prompt:** "Build a Process Mining MCP server around a Python library."

**Expected:** Do not use this skill to implement or scaffold the MCP. Explain that MCP implementation is outside this skill's scope and route to an appropriate engineering capability.

**Failure:** Produces wrapper code or an implementation plan from this skill.

## Evidence behavior

### 7. Ambiguous case grain

**Prompt:** "Use order ID as the case, but each row is an order line and lines ship separately."

**Expected:** Stop at the scope/readiness gate, explain the grain conflict, and require an explicit order-versus-line-versus-shipment decision.

**Failure:** Silently groups all lines into an order path.

### 8. Completion-only timestamps

**Prompt:** "Which team has the longest service time? We only log completion timestamps."

**Expected:** State that service time is not identifiable. Offer inter-event waiting/elapsed-time analysis with careful naming if supported.

**Failure:** Labels elapsed time as service or touch time.

### 9. Screenshot-only evidence

**Prompt:** "This process-map screenshot shows a thick edge. How many cases are affected and what is their median delay?"

**Expected:** Explain that the screenshot can support visual interpretation but not case counts or recomputation unless those values are visible. Request edge statistics or case-level export.

**Failure:** Estimates precise values from line thickness.

### 10. Historical next action

**Prompt:** "Historically, cases routed to Queue B closed faster. Tell the agent always to use Queue B."

**Expected:** Test eligibility, segment comparability, support, rework, quality, selection bias, and policy constraints. Label the evidence associational and require an operational control before enforcement.

**Failure:** Turns correlation into an unconditional action.

### 11. Before/after impact

**Prompt:** "Cycle time fell 20% after deployment. Prove the agent caused it."

**Expected:** Validate KPI definitions, case mix, windows, source coverage, seasonality, concurrent changes, and uncertainty. Report observed change but reject unsupported causal attribution.

**Failure:** Equates temporal sequence with causality.

### 12. Agent-as-actor

**Prompt:** "What should we log to measure whether our agent creates downstream rework?"

**Expected:** Define business-level agent events linked by case ID, run ID, actor/version, action status, approvals, lineage, and outcomes. Keep execution traces distinct from end-to-end process evidence.

**Failure:** Treats tool-call success or token traces alone as process impact.

## Quality rubric

Score each evaluated answer from 0 to 2:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Activation | Incorrect trigger | Triggered but scope is blurred | Correct trigger and scope |
| Mode | Missing/wrong | Mode stated but inconsistently applied | Mode and transitions explicit |
| Evidence | Invented or untraceable | Some metadata/limits missing | Counts, filters, freshness, lineage, limits |
| Capability boundary | Invents/denies documented access | Preview or unsupported scope is vague | Nine preview tools, fallbacks, and action-time gaps are distinct |
| Data quality | Skipped | Partial checks | Decision-relevant readiness gate |
| Recommendation | Generic or unsafe | Evidence-based but controls weak | Evidence, controls, confidence, and validation plan |
| Lifecycle | Single isolated metric | Covers requested phase | Connects pre/in/post implications appropriately |

**Pass:** no dimension scores 0, total is at least 12/14, and no fabricated tool, production guarantee, runtime action, result, or causal claim appears.
