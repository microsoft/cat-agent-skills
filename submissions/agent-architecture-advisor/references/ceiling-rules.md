# Capability Ceiling Rules

Classification ruleset for the reasoning core (C2). Rate-independent.

- **capability-date:** 2026-08
- **review-cadence:** quarterly

> **Currency (2026-08):** Copilot Studio's agentic rebuild (Adaptive Orchestration,
> Connected agents, Memory, Agent Sandbox, MCP) narrows CEIL-01 and CEIL-05. Re-test
> those against in-platform capabilities before asserting them. See the currency note in
> `platform-capabilities.md`.

## Contents

1. How to apply this file
2. Classification taxonomy and the anti-bias rule
3. GOVERNANCE rules (GOV-01 … GOV-08)
4. CEILING rules (CEIL-01 … CEIL-08)
5. COST rules (COST-01 … COST-04)
6. DESIGN rules (DSN-01 … DSN-10)
7. CONFIG rules (CFG-01 … CFG-11)
8. Verdict derivation
9. Validation fixtures
10. Extension protocol

> Rules GOV-08, DSN-09, DSN-10, and CFG-09–CFG-11 cover the cross-cutting operational
> dimensions (guardrails, feedback loops, access, memory, context, session handoff).
> Their domain detail lives in `agent-quality-dimensions.md`.

---

## 1. How to apply this file

For each requirement in the requirement model and each finding from artifact analysis
(Mode B) or elicitation (Mode A):

1. Test in order: **GOVERNANCE → CEILING → COST → DESIGN → CONFIG.** First match wins.
   Order matters — a governance blocker that is also a config error is a GOVERNANCE
   finding, because the remediation urgency differs.
2. Record: rule ID, evidence, confidence, severity.
3. If no rule matches, emit nothing. Do not invent findings to fill a report.

### Confidence

| Level | Meaning | Permitted sources |
|---|---|---|
| `high` | Deterministically measured | Script output: collision scores, graph analysis, config presence/absence, arithmetic |
| `medium` | Inferred from artifact pattern plus domain rule | Topic structure implying orchestration need; transcript patterns |
| `low` | User-stated only, unverified | Interview answers with no artifact backing |

A finding may never be rendered as a failure simulation below `medium`.

### Severity

| Level | Meaning |
|---|---|
| `blocking` | Ship-stopper: compliance breach, data exposure, or auth bypass |
| `high` | Will cause user-visible failure or material cost overrun at stated scale |
| `medium` | Degrades quality or increases cost without being immediately visible |
| `low` | Hygiene — worth fixing, no urgency |

---

## 2. Classification taxonomy

| Class | Definition | Implies |
|---|---|---|
| `GOVERNANCE` | Security, compliance, residency, or auditability requirement unmet | Blocking; resolve before platform decisions |
| `CEILING` | Requirement exceeds the platform's capability envelope | Platform change or hybrid required |
| `COST` | Technically achievable, economically unviable at stated scale | Re-architecture for cost, not capability |
| `DESIGN` | Available primitives used incorrectly | Restructure in place |
| `CONFIG` | Setting wrong, missing, or left at default | Fix in place |

### The anti-bias rule — mandatory

**Migration (`MIGRATE` or `EXTEND`) may only be recommended when at least one `CEILING`
finding or one blocking `COST` finding exists.**

Any number of CONFIG, DESIGN, or non-blocking COST findings — even dozens — must produce
verdict `OPTIMIZE`. A platform is not "wrong" because it was used poorly.

**Corollary:** when the analysis produces zero CEILING findings, the report must state:

> No platform ceiling was reached. The current platform is the correct one for these requirements.

This sentence is required. It is the ruleset's primary credibility signal — a tool that
always recommends migration is a sales pitch, not an advisor, and readers detect that
immediately.

---

## 3. GOVERNANCE rules

Evaluated first. Any match is `blocking` regardless of other findings.

### GOV-01 — Unbounded generative response on regulated content
**Detect:** `content_safety_tier == regulated` AND a topic uses generative answers
without citation enforcement.
**Evidence:** topic config — generative mode on, grounding strictness not `citation_required`.
**Confidence:** high (Mode B), low (Mode A).
**Why:** regulated domains require traceable provenance for every assertion.
**Resolution:** enforce citation-required grounding, or place the topic behind a
retrieval layer with mandatory source attribution.

### GOV-02 — Data residency violation via knowledge source or model endpoint
**Detect:** residency constraint exists AND a knowledge source or model endpoint
resolves outside the permitted region.
**Evidence:** source URI region; model deployment region.
**Confidence:** high if the endpoint is inspectable, medium if inferred.
**Resolution:** regional deployment. If a required capability has no in-region
deployment, escalate to CEIL-08.

### GOV-03 — Missing on-behalf-of auth for user-scoped data
**Detect:** the agent reads user-scoped data (mailbox, personal files, user-owned
records) AND auth model is `service_principal` or `none`.
**Evidence:** connector/tool scope compared against configured auth.
**Confidence:** high.
**Severity:** blocking.
**Why:** service-principal access to user-scoped data bypasses per-user authorization —
the agent can surface records the asking user has no right to see. This is the most
common serious finding in real agents and it is rarely noticed until an audit.
**Resolution:** on-behalf-of auth flow. If the data source has no OBO path, escalate to CEILING.

### GOV-04 — Irreversible action without human approval
**Detect:** `side_effects == irreversible` AND `human_in_loop == none`.
**Evidence:** tool definitions with write/delete semantics; no approval node in the graph.
**Confidence:** high.
**Resolution:** insert an approval gate. Non-negotiable for financial transactions,
deletions, and outbound external communication.

### GOV-05 — Audit trail insufficient for stated need
**Detect:** `auditability == full_trace` AND config lacks transcript retention or
tool-invocation logging.
**Confidence:** high (Mode B).
**Resolution:** enable tracing. If per-decision reasoning traces are required rather
than just transcripts, this is a CEILING for classic orchestration.

### GOV-06 — Unreviewed MCP tool or connector scope
**Detect:** the agent invokes an external MCP server / connector whose scope grants access
beyond the task, or that has not passed DLP / tenant-policy review.
**Evidence:** tool / MCP definitions with broad or write scopes; connectors outside the
tenant DLP policy.
**Confidence:** high when scopes are inspectable, medium when inferred.
**Severity:** blocking when the scope reaches regulated or user-scoped data (see GOV-03).
**Distinguishing test:** is the tool inside tenant governance (DLP, admin visibility) and
scoped to the task? If yes → CONFIG at most, not GOVERNANCE.
**Why:** the agentic build calls external systems through MCP; an over-scoped connector is
the new form of the classic over-privileged integration.
**Resolution:** scope the connector to least privilege, bring it under DLP, remove unused tools.

### GOV-07 — Runtime code execution on sensitive data
**Detect:** Agent Sandbox (runtime code generation/execution) operates on regulated,
user-scoped, or write-capable data without execution constraints or human review.
**Evidence:** sandbox enabled AND data sources include sensitive/user-scoped content, or
generated code can trigger irreversible actions.
**Confidence:** medium; high if transcripts show generated code touching such data.
**Severity:** blocking for irreversible/regulated data; high otherwise.
**Distinguishing test:** does the sandbox run only on ephemeral, non-sensitive data for
computation or formatting? If yes → not a governance finding.
**Resolution:** constrain sandbox inputs, forbid write/irreversible actions from generated
code, add review where regulated data is in scope.

### GOV-08 — Cross-user memory or thread-state leakage
**Detect:** the agent uses memory or persisted thread state that is not isolated per user,
or a connected/child agent grants the parent access to data the parent's own identity is
denied.
**Evidence:** memory enabled with no per-user `scope` (Foundry low-level memory API
requires `scope` per request; the memory search tool needs `scope={{$userId}}`); shared
thread reused across users; a connected agent with broader data privileges reachable from a
lower-privileged parent.
**Confidence:** high when scope/isolation config is inspectable, medium when inferred.
**Severity:** blocking — cross-user data exposure.
**Distinguishing test:** is every memory/thread read bound to the asking user's identity,
and does each connected-agent call stay within the parent's own authorization envelope?
If yes → not a finding.
**Why:** memory and multi-agent delegation are the new surfaces for the classic
over-privilege bug — one user's context surfacing to another, or a parent escalating via a
child. See `agent-quality-dimensions.md` §3.
**Resolution:** set memory `scope` per user; isolate threads per user; govern and audit
connected agents so delegation cannot bypass the parent's restrictions.

The core IP. Each rule states the boundary being crossed and the minimum evidence
required to assert it.

### CEIL-01 — Dynamic multi-step planning
**Detect:** the task requires a plan whose *shape* is not knowable at design time —
step count, order, or selection depends on intermediate results.
**Distinguishing test:** can the full decision tree be enumerated in advance? If yes,
this is not a ceiling (DESIGN at most). If the agent must decide *what to do next* based
on what it just learned, it is.
**Evidence (Mode B):** topic graph with conditional nesting beyond ~4 levels, or a topic
looping back on itself with variable-driven branching; transcripts showing goals that
require variable step counts.
**Evidence (Mode A):** stated requirements for research, investigation, diagnosis, or
"figure out how to…" tasks.
**Confidence:** medium unless transcripts confirm.
**Why it is a ceiling:** classic topic orchestration executes a designed graph.
Generative orchestration selects among defined tools but does not compose novel
multi-step plans with intermediate reasoning.
**Currency (2026-08):** current Copilot Studio ships **Adaptive Orchestration**, which
plans dynamically across turns and revises the plan when the request changes. Before
asserting this ceiling, confirm the tenant is on the older classic/generative model and
not the agentic build — on the new build this is frequently *not* a ceiling. See
`platform-capabilities.md` currency note.
**Resolution:** Foundry Agent Service for the planning portion. Frequently EXTEND rather
than MIGRATE — keep the conversation in Copilot Studio and call out for planning.

### CEIL-02 — Custom retrieval pipeline
**Detect:** grounding requires hybrid search with custom weighting, semantic re-ranking,
query decomposition or rewriting, multi-index federation with custom merge logic,
metadata-filtered retrieval with complex predicates, or chunking tuned to document
structure.
**Distinguishing test:** does built-in grounding over the connected source produce
acceptable results? Only when retrieval quality is the problem *and* no configuration
change fixes it does this become a ceiling.
**Evidence:** transcripts showing correct-source-wrong-passage failures; heterogeneous
document structure; grounding failures concentrated in long or structured documents.
**Confidence:** medium; high with transcript evidence.
**Caution — check CFG-06 and DSN-04 first.** Most grounding complaints are source
scoping or chunking defaults, not capability limits. This rule over-fires more than any
other in the set; the cheap explanation is usually the right one.
**Resolution:** Azure AI Search index with a custom pipeline; Foundry or hybrid.

### CEIL-03 — Model-level control required
**Detect:** requirement for specific model selection, temperature or sampling control,
fine-tuning, distillation, version pinning for reproducibility, or model-level A/B testing.
**Evidence (Mode A):** stated in model-control requirements.
**Evidence (Mode B):** transcripts showing tone or format inconsistency that prompt
iteration has not resolved.
**Confidence:** high when stated, medium when inferred.
**Why:** Copilot Studio abstracts the model deliberately. That is a feature for most
users and a hard boundary for the rest.
**Resolution:** Foundry. If only some interactions need it, EXTEND.

### CEIL-04 — Systematic offline evaluation with CI gating
**Detect:** requirement for reproducible eval runs against a fixed dataset, quantitative
quality metrics with thresholds, regression gating in a deployment pipeline, or
eval-driven prompt iteration.
**Distinguishing test:** manual test-panel validation sufficient → not a ceiling.
Automated pass/fail gates on metrics → ceiling.
**Evidence:** stated requirement, or DevOps maturity signals (multiple environments,
existing solution pipeline, regular release cadence).
**Confidence:** high when stated.
**Note:** Copilot Studio Test Planner covers behavioural test *design*. This rule is
about quantitative, automated, gating evaluation — a different capability. Do not
double-report against that skill's territory.
**Resolution:** Foundry evaluation SDK. Hybrid is viable — evaluate the Foundry
component, manually test the conversational layer.

### CEIL-05 — Durable long-running or multi-agent state
**Detect:** workflow spans hours or days, survives session end, requires checkpointing
or resumption, or coordinates multiple specialised agents over shared mutable state.
**Distinguishing test:** does a session boundary destroy required context? If yes, ceiling.
**Evidence:** variables written and expected across sessions; transcripts showing users
re-supplying context they already gave.
**Confidence:** high when session-boundary loss is observable.
**Currency (2026-08):** current Copilot Studio ships **Memory** (context persists across
the conversation) and **Connected agents** (multi-agent delegation). Re-test the
requirement against these before asserting the ceiling; true durability *beyond* a
conversation, or coordination over shared mutable state, may still exceed them.
**Resolution:** durable orchestration behind the agent; the conversational layer may
remain in Copilot Studio.

### CEIL-06 — Deterministic output contract
**Detect:** downstream systems consume agent output and require strict schema
conformance.
**Distinguishing test:** is the consumer human (tolerant) or a system (intolerant)?
System consumer with no schema enforcement → ceiling.
**Evidence:** tool definitions passing agent output into APIs; stated integration requirements.
**Confidence:** high.
**Resolution:** structured output enforcement at the model layer, or a
validation-and-repair layer between agent and consumer.

### CEIL-07 — Latency floor unreachable
**Detect:** the p95 latency target cannot be met by the required chain of grounding,
generation, and tool calls.
**Assessment:** sum minimum realistic stage latencies and compare against target. Never
assert without showing the stage-level reasoning.
**Confidence:** medium — latency is environment-dependent. State assumptions explicitly.
**Caution:** frequently a DESIGN issue instead — serial calls that could run in parallel,
or grounding invoked on deterministic topics. Rule out DSN-06 and COST-04 first.
**Resolution:** architecture changes (caching, parallelisation, smaller model,
pre-computation) before any platform change.

### CEIL-08 — Required capability unavailable in required region
**Detect:** escalation from GOV-02 — a needed capability has no deployment in the
mandated region.
**Confidence:** high only if verified against current availability; otherwise record as
an open question rather than asserting it.
**Resolution:** architecture change or requirement renegotiation. Present honestly as a
constraint, not as a platform failing.

---

## 5. COST rules

Technically possible, economically questionable. Arithmetic comes from
`scripts/cost_model.py`; these rules interpret it.

### COST-01 — Generative turn ratio above viability threshold
**Detect:** projected generative-message share combined with volume exceeds the stated budget.
**Evidence:** turn-type classification from topic analysis × volume.
**Confidence:** medium — always render with a sensitivity band.
**Severity:** `blocking` only above ~3× budget; otherwise `high`.
**Resolution, in order:** convert deterministic topics from generative to classic;
reduce grounding scope; cache frequent answers. Consider platform change only after
these. Most cost problems are design problems wearing a cost costume.

### COST-02 — Retry and escalation loop burn
**Detect:** findings that cause repeated turns (trigger collisions, missing fallback, no
disambiguation) combined with volume.
**Evidence:** collision matrix + missing-config detection + volume.
**Confidence:** high — deterministic inputs make this the most defensible cost finding.
**Note:** this is a CONFIG root cause with a COST consequence. Report as CONFIG with the
cost impact attached rather than double-counting as a separate finding.

### COST-03 — Break-even crossed
**Detect:** projected volume exceeds the computed break-even point by more than ~2×.
**Evidence:** `cost_model.py` output.
**Confidence:** medium — depends on rate-card currency and token estimates.
**Important:** cost advantage alone is a weak migration argument. With no CEILING
finding present, present this as *information*, not a recommendation, and state the
operational cost of migration as a counterweight.

### COST-04 — Over-grounding
**Detect:** knowledge grounding invoked on topics that do not need it.
**Evidence:** grounding enabled on topics with deterministic answers or pure action topics.
**Confidence:** high.
**Severity:** medium. Cheap fix, meaningful savings at volume.

---

## 6. DESIGN rules

Right platform, wrong use of it.

### DSN-01 — Orchestration mode mismatch
**Detect:** generative orchestration on a strictly deterministic process, or classic
orchestration on a domain with wide intent variance.
**Evidence:** orchestration mode compared against topic structure and trigger diversity.
**Confidence:** medium.
**Resolution:** switch mode. Often the single highest-leverage change available.

### DSN-02 — Monolithic topic
**Detect:** a topic exceeding ~25 nodes or handling more than two distinct user intents.
**Evidence:** node count and branch analysis.
**Confidence:** high.
**Resolution:** decompose; extract shared sub-topics.

### DSN-03 — Unreachable or orphaned topics
**Detect:** graph analysis — topics with no inbound edge and no trigger phrases.
**Evidence:** orchestration graph.
**Confidence:** high.
**Why it matters:** usually indicates abandoned work that still consumes maintenance
attention and can confuse generative orchestration's tool selection.

### DSN-04 — Grounding scope too broad
**Detect:** a single knowledge source spanning multiple domains without metadata
filtering, producing cross-domain retrieval noise.
**Evidence:** source scope vs topic diversity; transcripts showing wrong-domain answers.
**Confidence:** medium.
**Resolution:** scope sources per topic or add metadata filters. **Check this before
asserting CEIL-02.**

### DSN-05 — Variable lifecycle errors
**Detect:** variables set but never read, read but never set, or scope leakage across topics.
**Evidence:** variable dataflow analysis.
**Confidence:** high.
**Severity:** medium — read-without-set produces user-visible empty responses.

### DSN-06 — Serial tool chain where parallel is possible
**Detect:** independent tool calls executed sequentially.
**Evidence:** graph dependency analysis.
**Confidence:** medium.
**Resolution:** parallelise. **Check before asserting CEIL-07.**

### DSN-07 — Connected-agent delegation without a boundary contract
**Detect:** a parent agent delegates to child / connected agents with no defined contract —
unclear ownership, overlapping responsibilities, or no payload / latency / error / fallback
semantics between them.
**Evidence:** multiple connected agents with overlapping trigger coverage; undefined handoff.
**Confidence:** medium.
**Severity:** medium.
**Distinguishing test:** is each child agent's responsibility, input, and failure behaviour
specified? If yes → sound design, not a finding.
**Resolution:** define the boundary contract per `hybrid-patterns.md` (payload schema,
latency budget, timeout, error semantics, fallback). Prefer fewer, well-scoped child agents.

### DSN-08 — Tool or skill sprawl degrading selection
**Detect:** so many MCP tools / AI Skills are registered that adaptive orchestration's
tool selection degrades — wrong-tool calls or added latency.
**Evidence:** tool count high relative to distinct intents; transcripts showing wrong-tool selection.
**Confidence:** medium.
**Resolution:** consolidate overlapping tools, group by task, remove unused. **Check before
asserting a CEILING on orchestration quality — this is usually the cheaper explanation.**

### DSN-09 — Context or thread window mismanagement
**Detect:** conversation state is allowed to grow past the model context window so early
context is silently truncated, or deep chained tool calls exhaust the window; the fix is
thread/window hygiene, not a platform change.
**Evidence:** single ever-growing thread rather than a new thread per topic/user
(Foundry threads auto-truncate to fit the window); transcripts showing the agent
"forgetting" earlier turns on long conversations; multi-tool runs stalling at depth.
**Confidence:** medium; high with transcript evidence.
**Severity:** medium.
**Distinguishing test:** is required context lost because of *windowing/thread hygiene*
(fixable) or because the requirement needs durability *beyond a session*? The latter is
`CEIL-05`, not this rule.
**Resolution:** start a new thread per topic/user; summarise rather than carry raw history;
budget chained tool-call depth. See `agent-quality-dimensions.md` §5.

### DSN-10 — Session handoff loses continuity
**Detect:** on delegation to a connected/child agent, handoff to another agent, or human
escalation, the conversation context (history + key parameters) is not carried across the
boundary, forcing the user to repeat themselves.
**Evidence:** connected-agent calls that pass no parameters; escalation nodes that drop
collected variables (e.g. a created case number); handoff without conversation history.
**Confidence:** medium.
**Severity:** medium.
**Distinguishing test:** does the target receive enough context to continue without
re-asking? Copilot Studio passes conversation history by default on connected-agent
calls — if history *and* the needed parameters cross the boundary, this is not a finding.
**Resolution:** pass history plus known parameters on delegation; carry context variables
through escalation; use contextual/A2A handoff that forwards `contextId` + history. Pairs
with `DSN-07` (boundary contract). See `agent-quality-dimensions.md` §6.

---

## 7. CONFIG rules

Deterministic, high-confidence, usually quick to fix. These dominate real findings registers.

### CFG-01 — Trigger phrase collision
**Detect:** pairwise similarity between trigger phrases of different topics exceeds
threshold (default 0.75; report all pairs ≥0.70).
**Evidence:** collision matrix from `analyze_topics.py`, including the measured score.
**Confidence:** high — fully deterministic.
**Severity:** high.
**Why it matters:** root cause of most misrouting and the primary driver of COST-02.
This is the single most valuable finding the skill produces. Render as a failure
simulation whenever severity is high.
**Resolution:** consolidate colliding topics behind a disambiguation slot, or
differentiate the phrases. Prefer consolidation — near-duplicate topics usually should
have been one topic.
**Threshold note:** 0.75 is a starting point. Tune against real agents — too low floods
the register, too high misses collisions that actually cause misroutes.

### CFG-02 — Missing fallback
**Detect:** no system fallback topic configured, or a fallback with no recovery path.
**Confidence:** high. **Severity:** high.

### CFG-03 — Missing escalation path
**Detect:** no human handoff configured, or a handoff unreachable from the orchestration graph.
**Confidence:** high.

### CFG-04 — No mid-conversation correction handling
**Detect:** topics with slot filling but no path for the user changing their mind
("no, I meant…").
**Evidence:** slot-filling nodes without an interruption or restart branch.
**Confidence:** high.
**Why it matters:** a top contributor to user frustration and escalation. Pairs
naturally with CFG-01 in failure simulations — a misroute the user cannot correct is
far worse than a misroute they can.

### CFG-05 — Content moderation not configured
**Detect:** moderation level unset or minimum where the domain warrants more.
**Confidence:** high.
**Escalates to GOV-01** when the safety tier is `strict` or `regulated`.

### CFG-06 — Knowledge source scope misconfiguration
**Detect:** grounding enabled with no source bound, or a source configured but not bound
to any topic.
**Confidence:** high.
**Check before CEIL-02.**

### CFG-07 — Session timeout mismatch
**Detect:** timeout shorter than realistic task completion time.
**Evidence:** timeout vs longest topic path length.
**Confidence:** medium.

### CFG-08 — Missing conversation-start guidance
**Detect:** no welcome message or no capability disclosure at conversation start.
**Confidence:** high. **Severity:** low, but materially affects containment rate.

### CFG-09 — Memory not configured for the continuity need
**Detect:** memory is off where the requirement needs cross-turn/cross-session continuity,
or memory is on with no retention/TTL policy, or sensitive data is not excluded from what
memory extracts.
**Evidence:** `state_scope` requires continuity but Copilot Studio Memory toggle is off /
no Foundry memory store; memory store with no default TTL; `user_profile_details` not
scoped to exclude sensitive data.
**Confidence:** high when config is inspectable, low from self-report.
**Severity:** medium; high when unbounded retention holds regulated/PII data.
**Distinguishing test:** does the task actually need continuity? If it is single-turn,
memory-off is correct — not a finding (and it saves Copilot Credits).
**Resolution:** turn memory on where continuity adds value; set a store-level TTL and use
item-level CRUD for deletion; exclude sensitive fields from extraction. See
`agent-quality-dimensions.md` §4.

### CFG-10 — Guardrail intervention points incomplete
**Detect (Foundry):** a tool-using agent's guardrail does not scan `tool call` /
`tool response` intervention points, severity thresholds are left too permissive/restrictive,
or the agent is inheriting the model's guardrail instead of an explicitly assigned agent
guardrail.
**Evidence:** guardrail config lacking tool-call/tool-response controls; no guardrail
assigned to the agent; hosted agent with no network egress allowlist where outbound calls
are made.
**Confidence:** high when the guardrail is inspectable.
**Severity:** high when tool I/O reaches sensitive data or actions; otherwise medium.
**Escalates to GOV-01** when the domain safety tier is `strict`/`regulated`.
**Distinguishing test:** are all *active* intervention points for this agent's shape
covered? A no-tool agent needs only input/output. Copilot Studio equivalent is `CFG-05`.
**Resolution:** assign an agent-level guardrail covering tool call/response; tune severity
per category; add network egress controls on hosted agents. See
`agent-quality-dimensions.md` §1.

### CFG-11 — No feedback loop or evaluation baseline
**Detect:** no evaluation exists (baseline, threshold, or gate), or there is no user
channel to report bad answers, or no production tracing to detect drift.
**Evidence:** no rubric/built-in evaluators configured; no acceptance threshold; no
tracing/monitoring; no user feedback path.
**Confidence:** high when stated/inspectable, low from self-report.
**Severity:** medium.
**Distinguishing test:** this is the *lightweight hygiene* version. A requirement for
automated, gating, reproducible evaluation in a pipeline is `CEIL-04`, not this rule; do
not double-report, and do not stray into Copilot Studio Test Planner's behavioural-test
territory.
**Resolution:** establish a baseline evaluator + threshold; add a user feedback channel
with human oversight; enable tracing so production telemetry feeds re-evaluation. See
`agent-quality-dimensions.md` §2.

---

## 8. Verdict derivation

Apply after all findings are classified.

```
if any GOVERNANCE finding with severity == blocking:
    resolve governance first
    verdict = OPTIMIZE (or REDESIGN if the requirement itself is unsound)
    # never recommend migration as an escape from a governance gap —
    # moving platforms relocates the gap, it does not close it

elif no CEILING findings and no blocking COST:
    verdict = OPTIMIZE
    # MANDATORY: state that no platform ceiling was reached

elif CEILING findings confined to <= 2 capability areas
     and the conversational, channel, and auth layers are sound:
    verdict = EXTEND
    # hybrid: keep the front door, offload the ceiling

elif CEILING findings span >= 3 capability areas
     or CEIL-01 + CEIL-02 + CEIL-03 occur together:
    verdict = MIGRATE

elif the requirement model is internally contradictory:
    verdict = REDESIGN
```

### Guardrails

- **`EXTEND` is under-recommended in practice.** When CEILING findings are narrow, prefer
  it over `MIGRATE`. Migration cost is real and rarely modelled by the teams asking.
- **`MIGRATE` requires stating what is lost** — channel integrations, M365 auth, maker
  accessibility, elapsed time, and the risk of a parallel-run period. A migration
  recommendation without a stated downside is not credible.
- **`OPTIMIZE` is a legitimate and common outcome.** Verify it remains reachable (fixture 2).

---

## 9. Validation fixtures

Run before shipping changes to this file. All must pass.

| # | Fixture | Expected verdict | Guards against |
|---|---|---|---|
| 1 | Well-built simple FAQ agent | OPTIMIZE, zero findings | False positives |
| 2 | 6 CONFIG findings, no ceiling | OPTIMIZE | Migration bias |
| 3 | Dynamic planning need only | EXTEND | Over-migration |
| 4 | Planning + retrieval + model control | MIGRATE | Under-migration |
| 5 | OBO auth gap present | GOVERNANCE blocking, no migration | Escaping governance via platform change |
| 6 | Empty or minimal export | Graceful low-confidence output | Fabrication under sparse input |
| 7 | Memory shared across users (no per-user scope) | GOVERNANCE blocking (GOV-08), no migration | Treating an isolation bug as a ceiling |
| 8 | Handoff drops context; memory off when continuity needed | DESIGN/CONFIG (DSN-10, CFG-09), verdict OPTIMIZE | Operational gaps inflating to migration |

Fixtures 2 and 5 matter most. They test the rules that protect credibility rather than
the rules that find problems — and credibility is what the whole ruleset trades on.

---

## 10. Extension protocol

A new rule requires: unique ID, deterministic detection criterion, required evidence,
confidence ceiling, a distinguishing test against adjacent classes, and a fixture showing
it fires correctly and does not fire spuriously.

Reject rules without a distinguishing test. They tend to over-fire into CEILING, which
breaks the anti-bias property and turns the whole ruleset into a migration recommender.
