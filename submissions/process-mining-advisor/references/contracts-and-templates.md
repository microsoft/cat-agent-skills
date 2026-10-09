# Contracts and Templates

Read this reference when gathering process-mining inputs or producing a deliverable.

## Input contracts

### MCP invocation evidence

Use this envelope for every preview MCP-backed finding:

```yaml
mcp_evidence:
  feature_status: preview
  process_id: <authorized process GUID>
  process_name: <name returned by the tool>
  process_metadata_checked_at: <timestamp>
  tools_invoked:
    - name: <one of the nine documented tools>
      invoked_at: <timestamp>
      parameters: {<filters, sort, page size, offset>}
      status: <Succeeded|FailedClientError|FailedAnalyticsError>
  pagination:
    retrieved_items: <n>
    total_count: <n or unknown>
    complete: <boolean>
  evidence_freshness: <source refresh if available, otherwise unknown>
  limitations: [<preview, access, partial pages, unavailable metadata>]
```

Do not infer source refresh time from invocation time. Do not combine pages with different filters or metadata versions.

### Process definition

```yaml
process:
  name: <stable process name>
  business_object: <object represented by one case>
  objective: <decision or improvement this analysis must support>
  start_condition: <observable event that starts a case>
  end_condition: <observable event that completes a case>
  included_scope: [<business units, channels, products, systems>]
  excluded_scope: [<explicit exclusions>]
  case_id_semantics: <what one identifier represents>
  expected_outcomes: [<completed, rejected, cancelled, ...>]
  known_rules: [<required order, forbidden transition, SLA, segregation rule, ...>]
  analysis_window: <start/end and rationale>
  timezone: <IANA timezone or documented source timezone>
  owner: <business owner>
```

Reject ambiguous case semantics. An order, order line, shipment, invoice, and support interaction are different case grains.

### Event log

Required:

| Field | Requirement |
|---|---|
| `case_id` | Stable, non-null identifier for one process instance |
| `activity` | Business-meaningful, consistently normalized event name |
| `timestamp` | Parseable event time with documented timezone and precision |

Conditionally required:

| Field | Use |
|---|---|
| `event_id` | Deterministic deduplication and traceability |
| `start_timestamp`, `end_timestamp` | Separate service time from waiting time |
| `lifecycle` | Distinguish scheduled/start/complete states |
| `actor_id`, `actor_type` | Resource, role, human/system/agent analysis |
| `source_system`, `source_record_id` | Lineage and drill-through |
| `outcome` | Success, rejection, cancellation, or another terminal result |
| `cost` | Cost-per-event or cost-per-case analysis |
| `automation_flag` | Manual versus automated execution |
| `agent_id`, `agent_run_id`, `tool_name` | Agent-as-actor telemetry |
| case attributes | Stable segmentation values such as region or product class |
| event attributes | Event-specific values such as queue, channel, or decision reason |

Use a deterministic tie-breaker when multiple events share a timestamp:

```text
sort_key = (case_id, timestamp, lifecycle_order, event_id)
```

If no defensible tie-breaker exists, mark path ordering as uncertain.

### Precomputed results

```yaml
mining_result:
  engine: <product and experience>
  generated_at: <timestamp>
  source_refresh_at: <timestamp>
  analysis_window: <start/end>
  filters: [<all active filters>]
  case_count: <included cases>
  event_count: <included events>
  completed_case_policy: <included/excluded/how censored cases are handled>
  process_definition_version: <version>
  kpi_definitions_version: <version>
  artifacts:
    - type: <process_map|variant_table|activity_stats|edge_stats|case_table|conformance>
      format: <csv|xlsx|image|json|other>
      scope: <what the artifact contains>
```

Do not compare outputs whose filters, case policy, or definitions differ until they are normalized.

### Runtime case state

Use only when discussing a conformance decision or next-action recommendation:

```yaml
case_state:
  case_id: <identifier>
  observed_events: [<ordered event records>]
  current_state: <derived state and derivation time>
  eligible_actions: [<actions allowed by the operational system>]
  prohibited_actions: [<policy constraints and reasons>]
  case_attributes: {<decision-relevant fields>}
  evidence_fresh_at: <timestamp>
```

Historical frequency never overrides policy, authorization, or eligibility.

## Output templates

### Readiness report

```markdown
## Event-log readiness
- Mode:
- Decision supported:
- Process/case definition:
- Window, refresh, and filters:
- Required fields: present/missing
- Blockers:
- Material limitations:
- Monitors:
- Ordering confidence:
- Coverage assessment:
- Governance assessment:
- Verdict: Ready | Conditionally ready | Not ready
- Minimum remediation:
- Claims currently supported:
- Claims not supported:
```

### Finding

```yaml
finding:
  id: <stable id>
  title: <one-line evidence statement>
  type: <variant|bottleneck|rework|conformance|outcome|drift>
  mode: <mcp_connected_preview|results_analysis|event_log_compute|advisory>
  scope: <window, filters, segment>
  evidence:
    cases: <n>
    case_share: <percent>
    events: <n>
    metrics: {<named values with units>}
    comparison: <target or cohort>
  interpretation: <what the evidence indicates>
  alternative_explanations: [<plausible confounders>]
  data_limitations: [<limitations>]
  confidence: <high|medium|low with reason>
  drill_through: <artifact/source lineage>
```

### Automation candidate

```yaml
candidate:
  activity_or_pattern: <target>
  evidence_summary: <volume, delay, rework, outcomes>
  proposed_intervention: <trigger/action/outcome>
  score: <value>
  positive_weights: {<dimension: weight>}
  penalty_scales: {risk: <scale>, complexity: <scale>}
  normalization: {<dimension: method>}
  data_confidence: <high|medium|low>
  exception_rate: <value>
  controls: [<authorization, approval, audit, reversal>]
  dependencies: [<systems, data, owner>]
  expected_kpi_effect: [<metric and directional hypothesis>]
  validation_plan: <pilot and measurement>
  recommendation: <proceed|investigate|defer>
```

### Conformance verdict

```yaml
conformance:
  scope: <case or cohort>
  reference_version: <model/rules version>
  evaluated_at: <timestamp>
  evidence_fresh_at: <timestamp>
  result: <conformant|nonconformant|indeterminate>
  deviations:
    - rule_id: <id>
      severity: <severity>
      evidence: <events/attributes>
  limitations: [<missing or stale evidence>]
  allowed_action: <only if an authorized runtime control exists>
  escalation: <owner and reason>
```

Use `indeterminate` when evidence is missing, stale, or ambiguous. Never convert uncertainty into approval.

### Next-action evidence

```yaml
next_action:
  case_id: <id>
  state_as_of: <timestamp>
  recommendation: <action or no-recommendation>
  eligibility_basis: <policy/tool evidence>
  cohort_definition: <historical comparison>
  support: <n>
  expected_outcomes: {<metric: value>}
  alternatives: [<action and evidence>]
  confidence: <high|medium|low>
  limitations: [<bias, freshness, sample, missing data>]
  human_decision_required: <boolean>
```

### Baseline comparison

| KPI | Direction | Definition version | Baseline | Current | Absolute change | Relative change | Baseline n | Current n | Confidence/limitation |
|---|---|---|---:|---:|---:|---:|---:|---:|---|

Conclude with:

- process changes observed;
- outcome changes observed;
- what can and cannot be attributed;
- controls that held or degraded;
- next measurement date.

### Drift alert

```yaml
drift_alert:
  detected_at: <timestamp>
  drift_type: <input|control_flow|performance|conformance|actor|outcome>
  baseline_window: <window>
  current_window: <window>
  metric: <name and definition>
  baseline_value: <value>
  current_value: <value>
  sample_sizes: {baseline: <n>, current: <n>}
  practical_threshold: <value>
  persistence: <number of windows>
  likely_scope: <segments/variants>
  data_quality_status: <pass|warning|fail>
  recommended_response: <inspect|remediate|rebaseline|no_action>
  owner: <role>
```
