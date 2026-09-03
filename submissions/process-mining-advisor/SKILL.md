---
name: process-mining-advisor
description: >-
  Use this skill whenever the user asks about process mining, process
  intelligence, event-log readiness, process discovery or variants,
  bottlenecks, rework, conformance, automation candidates, evidence-based next
  actions, process KPIs, baseline comparison, process drift, or measuring an
  agent's process impact. Use it before calling the official preview Power
  Automate Process Mining MCP tools, or before interpreting supplied event logs
  or exported/precomputed results. Do not use it to implement an MCP or to
  present a designed workflow as a mined process.
---

# Process Mining Advisor

Turn Process Mining MCP analytics, event data, and supplied mining results into evidence-backed process decisions across the **pre-change, in-process, and post-change** lifecycle.

Use the official Power Automate Process Mining MCP connector when its preview tools are available. Otherwise, fall back to advisory work, supplied exports/precomputed results, or optional event-log compute on an approved execution surface. This skill makes the existing tools useful and safe; it does not build or replace the MCP server.

## Activate for

- Assessing whether operational data is ready for process mining.
- Defining a process, event-log contract, source mapping, or baseline.
- Interpreting process maps, variants, activity/edge statistics, dashboards, or exports.
- Finding bottlenecks, queues, rework, loops, deviations, and automation candidates.
- Designing conformance or next-best-action evidence.
- Comparing baseline and post-change performance.
- Monitoring process drift.
- Modeling agents as first-class process actors and measuring downstream effects.

Do not activate merely to draw a desired-state workflow with no event evidence. Use process design or architecture guidance instead.

## Non-negotiable capability boundary

Select and declare the operating mode currently in effect before analysis. An engagement may move between modes as new evidence or an approved execution surface becomes available; label each finding with the mode that produced it.

| Mode | Evidence available | What the agent can do now | What it must not claim |
|---|---|---|---|
| **1. MCP-connected preview** | Official Process Mining connector with documented MCP tools, authenticated environment context, and process access | Discover processes and metadata; query overall metrics, bottlenecks, variants, edges, cases, attribute values, and correlations | Production readiness, unsupported tools, or transactional action guardrails |
| **2. Results analysis** | Exports or precomputed outputs from Power Automate Process Mining or another approved engine | Interpret process maps, variant tables, statistics, filters, KPI tables, conformance outputs, and case-level findings | Direct or live access to the underlying mining model |
| **3. Event-log compute** | Event-level data plus an approved execution surface | Validate and transform the log; compute supported statistics and mining results with existing approved SQL/Python/mining tools | That Power Automate Process Mining itself was invoked, or that unavailable dependencies are present |
| **4. Advisory** | Process description, schemas, or stakeholder knowledge only | Frame the process, define the event-log contract, map sources, design KPIs, plan analyses, and assess feasibility | That discovery, conformance, bottlenecks, or variants were computed |

Copilot Studio does not provide a local Python runtime merely because this skill is installed. Event-log compute is optional and platform-dependent; never require it for the core skill.

### MCP-connected preview mode

The official Process Mining MCP server and prebuilt Power Platform connector are **preview** features. Preview features are subject to change, may have restricted functionality, and are not meant for production use. Never give production guarantees.

Prerequisites documented by Microsoft:

- active Process Mining license;
- Power Platform environment configured with at least one ingested process;
- Microsoft Entra ID authentication;
- an MCP-compatible client such as Copilot Studio with the Process Mining connector configured;
- user access to the process. For Copilot Studio setup, Microsoft documents Process Mining Contributor or Viewer access plus the required maker/agent-creator permissions.

Use only these nine documented tools:

| User intent | Tool | Discipline |
|---|---|---|
| List accessible processes and obtain IDs | `get_processes` | Call first when the process ID is unknown |
| Inspect attributes, custom metrics, and business rules | `get_process_details` | Call before constructing filters; identify case-level versus event-level attributes |
| Discover valid values for an attribute | `get_attribute_values` | Page through values; do not guess labels |
| Summarize process-level performance | `get_process_overall_metrics` | State filters and included metric definitions |
| Find activities with highest duration | `get_bottleneck_analysis` | Treat returned duration ranking as bottleneck evidence, not proven cause |
| Compare unique paths and their metrics | `get_variants_with_metrics` | Choose and state sort metric/order |
| Analyze activity-to-activity transitions | `get_edges_with_metrics` | Use for flow, routing, and handover evidence |
| Inspect individual cases and outliers | `get_cases_with_metrics` | Limit personal data and preserve access controls |
| Analyze attribute influence on metrics | `get_correlation` | Case-level attributes only; correlation is not causation |

Tool sequence:

1. Call `get_processes` to resolve an authorized `processId`.
2. Call `get_process_details` before any filtered or correlation query.
3. Call `get_attribute_values` when valid filter values are unknown.
4. Select the narrowest analytics tool for the question.
5. State the tool, process, filters, sort, page coverage, and returned counts in the finding.

Filter and pagination discipline:

- Use only the documented filter types: attribute value, timeframe, metric condition, subprocess, and attribute sequence.
- Different filter types combine with **AND**; multiple filters of the same type combine with **OR**. Confirm inclusivity/exclusivity.
- Validate attribute names against `get_process_details` and values against `get_attribute_values`.
- Validate ISO 8601 timeframe order, metric/data-type compatibility, nonempty arrays, and custom metric ID when required.
- Set `itemsPerPage` and `itemsToSkip` explicitly for list operations. Continue while `itemsToSkip + itemsPerPage < totalCount`; if not all pages are retrieved, label the result partial.
- Apply timeframe and attribute filters early to reduce data volume. Do not over-filter silently.
- The server handles long-running analytics and progress notifications; do not invent client-side polling behavior.
- Surface `InvalidParams`, `InvalidRequest`, and `InternalError` outcomes rather than replacing them with success-shaped answers.

### Remaining product gap

The nine preview tools expose process discovery and read/analytics operations. They do not document transactional `check_conformance` or `next_best_action` tools. They also do not provide a dedicated continuous drift-monitoring operation.

Use variants, edges, cases, business rules, sequence filters, correlations, or repeated timeframe queries as retrospective/analytical evidence where appropriate. Do not present those analyses as a preventive runtime guardrail. Production maturity and action-time process controls remain separate product and solution-design concerns.

### Evidence fallback paths

- Power Automate Process Mining exports can provide process maps, variants, metrics, cases, and other precomputed evidence when MCP tools are unavailable.
- Dataverse, SQL, CSV, and other accessible sources can provide event-level data. Exact query and compute capabilities depend on the environment.
- Agent and workflow telemetry can be shaped into event records and included in later mining.

## Minimum-artifact rule

Ask only for the smallest artifact that unlocks the requested analysis:

| Requested outcome | Minimum artifact |
|---|---|
| MCP analytics | Configured preview connector, authorized process access, and the documented tool needed for the question |
| Readiness assessment | Source schema, sample rows, process boundary, and data dictionary |
| Discovery or variants | Event log with case ID, activity, and timestamp |
| Bottleneck analysis | Event log or activity/edge performance export; start/end timestamps if service time must be separated from waiting time |
| Rework analysis | Event log or variant/rework export with case-level drill-through |
| Conformance | Reference model/rules plus event log or precomputed conformance output |
| Automation candidates | Volume, time, rework, manual effort, exception, outcome, and risk evidence |
| Next-action evidence | Current state, eligible actions, historical sequences, outcomes, and policy constraints |
| Baseline comparison | Frozen KPI definitions plus baseline and current cohorts/windows |
| Drift | Baseline distribution/model plus comparable current-window data |

When MCP tools are unavailable or unsuitable, request the relevant export or screenshot plus:

- analysis window and active filters;
- refresh timestamp;
- process and case definition;
- KPI definitions and units;
- variant/activity/edge/case-level tables needed for the question.

Never imply that a screenshot alone supports case-level recomputation.

Use the canonical process, event-log, precomputed-result, and runtime case-state contracts in [references/contracts-and-templates.md](references/contracts-and-templates.md). Reject ambiguous case semantics and do not compare outputs whose filters, case policy, or definitions differ until they are normalized.

## Workflow

### Step 1 - Declare mode, question, and evidence

State:

1. selected operating mode and whether the preview connector is available;
2. decision the analysis supports;
3. artifacts received and missing;
4. freshness and filters;
5. claims that are and are not possible.

In MCP-connected mode, begin with metadata discovery and then invoke the narrowest documented tool. In fallback modes, request the minimum artifact instead of simulating certainty.

### Step 2 - Frame the process

Define the case, start, end, scope, terminal outcomes, expected happy path, known exceptions, and business objective.

Separate:

- **normative process**: what policy or design says should happen;
- **observed process**: what event evidence shows happened;
- **target process**: the proposed future behavior.

Never use the observed majority path as the compliance standard unless the process owner explicitly approves it.

### Step 3 - Map sources to events

Create a source map:

| Activity | Source | Trigger/record change | Case key | Event time | Actor | Lineage | Known gap |
|---|---|---|---|---|---|---|---|

Prefer immutable audit/history records over current-state tables. A current status column does not reconstruct the transitions that led to it.

For Dataverse/SQL/CSV-accessible logs:

- use available read-only tools to inspect schemas and retrieve only needed fields;
- preserve source identifiers for traceability;
- perform basic counts and aggregations at source when supported;
- export ordered event records to an approved analysis surface when path reconstruction needs unsupported window, sequence, or graph operations;
- never write back to operational records unless the user separately requests and approves that action.

### Step 4 - Gate event-log readiness

Run and report these checks:

| Dimension | Checks |
|---|---|
| Identity | Null case IDs, reused IDs, unstable composite keys, cross-object collisions |
| Activity | Null/blank labels, aliases, technical noise, over-aggregation, label changes |
| Time | Parse failures, timezone mismatch, future dates, impossible order, insufficient precision, timestamp ties |
| Uniqueness | Duplicate events, duplicate source records, retry-generated duplicates |
| Lifecycle | Missing start/complete pairs, overlapping events, negative durations |
| Coverage | Missing start/end events, incomplete systems, censored/open cases, late-arriving events |
| Grain | Mixed header/line/item cases, merged subprocesses, one event representing multiple activities |
| Attributes | Missingness, changing case attributes, post-outcome leakage, inconsistent units |
| Representativeness | Seasonality, migration periods, outages, pilots, partial business units |
| Governance | Personal/sensitive data, retention, access, purpose limitation, lineage |

Classify every issue:

- **Blocker**: invalidates the requested analysis.
- **Material limitation**: permits analysis but changes interpretation.
- **Monitor**: acceptable now, track over time.

Do not use universal readiness thresholds. Agree thresholds based on process risk, volume, and decision importance.

**Readiness gate:** proceed to computed findings only when case identity, event ordering, scope coverage, and lineage are adequate for the question. Otherwise remain in advisory mode.

### Step 5 - Freeze KPI definitions and baseline

Define each KPI before calculating it:

| KPI | Required definition |
|---|---|
| Case volume | Included cases and counting rule |
| Throughput/cycle time | Start event, end event, calendar, open-case handling |
| Waiting time | Boundary between events or lifecycle timestamps |
| Service/touch time | Start-to-complete duration; unavailable from completion-only logs |
| Rework rate | Rework rule and denominator |
| First-pass yield | Success path and allowed exceptions |
| Conformance rate | Reference model, severity, and denominator |
| Automation rate | Automated event/case definition |
| Touch count | Which human or system interactions count |
| Cost per case | Included costs and allocation method |
| Outcome rate | Terminal outcome taxonomy |

Report distributions, not averages alone. Prefer median plus P75/P90/P95 for skewed durations, alongside case counts.

Baseline metadata must include window, refresh timestamp, filters, process version, KPI version, and case-mix segments.

### Step 6 - Discover process and variants

In results-analysis mode, read the supplied map and variant artifacts. In compute mode, reconstruct ordered activity sequences only after the readiness gate passes.

For every process or variant finding, report:

- cases and percentage of cases;
- event count;
- median and tail duration;
- completion/outcome rate;
- rework or deviation evidence;
- segment concentration;
- freshness and filters.

Do not call the most frequent path the "happy path" unless its outcome and conformance evidence support that label.

Collapse or group activities only with a documented mapping. Preserve the original event label for drill-through.

### Step 7 - Analyze bottlenecks and rework

Distinguish:

- **waiting time** between events;
- **service time** within an activity, if lifecycle timestamps exist;
- **queue accumulation** from arrival versus completion rates;
- **handoff delay** around actor/system transitions;
- **rework** from repeated activities or backtracking;
- **legitimate recurrence** such as scheduled reviews.

Rank a bottleneck by affected volume and delay contribution, not duration alone:

```text
delay_contribution = affected_cases * excess_time_per_case
```

Use a documented reference for `excess_time_per_case` such as target, conforming cohort, or comparable segment. Do not imply causation from a slow transition without corroborating evidence.

For rework, define the rule explicitly:

```text
case_rework = repeated_activity OR repeated_transition OR return_to_prior_state
rework_rate = reworked_cases / eligible_cases
```

Identify which definition was used and exclude expected loops where appropriate.

### Step 8 - Assess conformance

Conformance requires an explicit reference:

- approved process model;
- ordered/precedence rules;
- required and forbidden activities;
- SLA and timing rules;
- segregation-of-duties or approval rules;
- precomputed conformance output.

Classify deviations by rule, severity, case count, business impact, and evidence. Keep policy violations separate from uncommon but permitted variants.

In advisory or basic query mode, the agent may validate explicit rules that the available data and tools can reliably express. It must not label this a full conformance-mining result.

The preview MCP has no documented transactional conformance tool. A runtime conformance guardrail requires a separate authorized action/tool that can evaluate the live case before commitment. Variant, sequence, business-rule, report, materialized-flag, or export evidence is retrospective analysis, not a transactional guardrail.

### Step 9 - Prioritize automation candidates

Build candidates from specific friction evidence, not activity volume alone.

Score only after stakeholders approve dimensions and weights:

```text
candidate_score =
  w_volume * normalized_volume
  + w_delay * normalized_delay_contribution
  + w_rework * normalized_rework
  + w_manual * normalized_manual_effort
  + w_standard * normalized_rule_stability
  + w_outcome * normalized_outcome_opportunity
  - w_risk * normalized_operational_risk
  - w_complexity * normalized_delivery_complexity
```

Positive-driver weights must sum to 1. State risk and complexity penalties separately with their scale, and document every normalization method. Include data confidence separately; do not hide low confidence inside the score.

For every candidate identify:

- trigger, action, and intended outcome;
- affected cases and friction evidence;
- rule stability and exception rate;
- required systems and permissions;
- human-in-the-loop point;
- failure, reversal, and escalation path;
- control and audit requirements;
- expected KPI movement and measurement window;
- implementation dependency and confidence.

Do not recommend automating a poorly understood or nonconformant process merely because it is slow.

### Step 10 - Develop next-action evidence

Treat next-best-action as a decision analysis, not a magic verb.

For each current state and eligible action, compare:

- historical support (`n`);
- completion/success rate;
- median residual time to outcome;
- rework and escalation rate;
- cost or risk outcome;
- relevant segment and case-mix differences;
- confidence and freshness.

Label results as **associational** unless a causal design supports stronger language. Guard against:

- policy-ineligible actions;
- selection bias in who historically received an action;
- leakage from attributes recorded after the decision;
- sparse cohorts;
- outdated behavior;
- optimizing speed while harming quality, compliance, or fairness.

The preview MCP has no documented `next_best_action` tool. Without a separate authorized decision and action surface, produce an evidence-backed recommendation only. Do not claim an in-process recommendation was enforced.

### Step 11 - Compare baseline with post-change

Freeze the change date and identify ramp-up, pilot, or mixed-operation periods.

Compare like with like:

- same KPI definitions and units;
- comparable completed/open-case policy;
- equivalent filters and source coverage;
- aligned seasonal periods where possible;
- segmented case mix;
- change in volume, complexity, and actor mix;
- sufficient observation time for late outcomes.

For each KPI report:

```text
absolute_change = current - baseline
relative_change = (current - baseline) / baseline
```

Define whether higher or lower is better for each KPI. If the baseline is zero or too close to zero for a stable ratio, report absolute change and mark relative change as not meaningful.

Include baseline/current values, case counts, distribution shifts, confidence or uncertainty, and known concurrent changes. Do not attribute the effect to an agent or automation solely because it followed deployment.

### Step 12 - Monitor drift

Monitor multiple drift classes:

| Drift | Examples |
|---|---|
| Input | New/missing activities, schema changes, timestamp quality, source coverage |
| Control-flow | Variant share, new transitions, path entropy, start/end changes |
| Performance | Cycle time, waiting time, service time, SLA breach |
| Conformance | Deviation rate or severity mix |
| Actor | Human/system/agent share, handoffs, workload concentration |
| Outcome | Completion, rejection, rework, cost, quality |

The preview MCP can support repeated filtered window comparisons, but it has no documented continuous drift-monitoring tool. Define:

- baseline window and current window;
- minimum sample size;
- practical significance threshold;
- statistical method where available;
- persistence requirement before alerting;
- owner and response playbook.

Do not alert on percentage changes without counts or on small samples without uncertainty.

### Step 13 - Model the agent as an actor

Emit process events for consequential agent behavior, not every internal token or reasoning step.

Recommended telemetry:

```yaml
agent_event:
  event_id: <unique immutable id>
  case_id: <business case>
  activity: <business-meaningful action>
  timestamp: <UTC or documented timezone>
  actor_type: agent
  actor_id: <stable agent identity/version>
  agent_run_id: <execution correlation id>
  tool_name: <tool/action used>
  action_status: <proposed|executed|failed|escalated|reversed>
  decision_reason_code: <controlled taxonomy>
  human_approval_required: <boolean>
  human_approval_result: <approved|rejected|modified|not_required>
  policy_or_model_version: <version>
  source_system: <system of record>
  source_record_id: <lineage id>
  error_code: <controlled value when applicable>
```

Keep agent observability and process mining distinct:

- execution traces explain what one agent run did;
- process mining explains patterns across complete business cases and all actors.

Link them with `case_id`, `agent_run_id`, and source lineage. Measure downstream rework, handoffs, conformance, and outcomes—not tool-call success alone.

## Output discipline

Use the readiness, finding, automation-candidate, conformance, next-action, baseline-comparison, and drift templates in [references/contracts-and-templates.md](references/contracts-and-templates.md). Use `indeterminate` when conformance evidence is missing, stale, or ambiguous; never convert uncertainty into approval.

## Guardrails

- Do not fabricate events, variants, process maps, KPI values, Microsoft APIs, connectors, tools, or runtime access.
- Do not claim MCP-connected analysis unless the official preview Process Mining tool was actually invoked and its output is cited.
- Use only the nine documented preview tools; do not invent conformance, next-action, simulation, write, or monitoring operations.
- Treat preview availability, schemas, limits, and behavior as subject to change; do not provide production guarantees.
- Do not install mining libraries, upload event logs, or move sensitive data to another environment without authorization.
- Keep raw personal data out of narrative outputs; aggregate or pseudonymize when possible.
- Preserve lineage from every finding to source rows or supplied artifacts.
- Separate evidence, interpretation, hypothesis, and recommendation.
- State filters, windows, refresh time, denominator, units, and case counts.
- Prefer read-only acquisition. Treat operational writes and automated actions as separate, approval-controlled work.
- Never use historical prevalence to legitimize a policy violation.
- Never infer service time from completion-only timestamps.
- Never present retrospective conformance or next-action evidence as a live preventive control.
- Never claim causal impact from a simple before/after comparison.
- Surface sparse data, censoring, selection bias, seasonality, and source changes.
- Use human review for high-impact, regulated, irreversible, or low-confidence decisions.

## Quality gates

Do not advance past a failed gate:

1. **Scope gate** - case, start, end, outcomes, owner, and decision are explicit.
2. **Evidence gate** - operating mode, artifacts, filters, freshness, and lineage are declared.
3. **Readiness gate** - identity, ordering, coverage, grain, and governance support the question.
4. **Definition gate** - KPI, rework, conformance, and segment definitions are frozen.
5. **Analysis gate** - findings include counts, denominators, distributions, comparisons, and limitations.
6. **Recommendation gate** - candidate controls, exceptions, dependencies, risk, and validation are explicit.
7. **Change gate** - baseline and current populations are comparable and attribution is qualified.
8. **Operational gate** - no runtime decision or action is implied from read/analytics MCP evidence without a separate real authorized control and fresh evidence.

Before delivery verify:

- all findings trace to evidence;
- unsupported analyses are listed as requests, not results;
- preview MCP-connected, precomputed, compute, advisory, and unsupported runtime capabilities are unmistakable;
- no customer-specific assumptions or examples remain;
- recommendations include confidence and a measurable validation plan.

## Official references

Use these for product grounding and re-check them before making exact availability, licensing, region, or UI claims:

- [Overview of process mining in Power Automate](https://learn.microsoft.com/en-us/power-automate/process-mining-overview)
- [Prepare processes and data](https://learn.microsoft.com/en-us/power-automate/process-mining-processes-and-data)
- [Get started with process mining](https://learn.microsoft.com/en-us/power-automate/process-mining-tutorial)
- [Process map overview](https://learn.microsoft.com/en-us/power-automate/minit/process-map)
- [Custom metrics](https://learn.microsoft.com/en-us/power-automate/minit/custom-metrics-how-to)
- [Business rules](https://learn.microsoft.com/en-us/power-automate/minit/business-rules)
- [Process Mining MCP server reference (preview)](https://learn.microsoft.com/en-us/power-automate/process-mining-mcp-server-reference)
- [Create a Copilot Studio agent with process mining (preview)](https://learn.microsoft.com/en-us/power-automate/process-mining-mcp-create-cps-agent)

The two MCP pages are prerelease documentation dated April 2026 and are subject to change. Re-check them before deployment or exact capability claims.

## Skill references

- [Contracts and templates](references/contracts-and-templates.md) - canonical inputs and outputs; read when gathering evidence or delivering an analysis.
- [Evaluation scenarios](references/evals.md) - activation, capability-boundary, evidence-discipline, and lifecycle test cases; use when evaluating or revising this skill.
