# Requirement Model

The normalised schema both modes converge on. Mode A elicits it; Mode B infers it from
artifacts and asks about the gaps.

This schema is the interlingua that lets one reasoning core serve two platforms and two
modes. Every ceiling rule tests against fields defined here.

## Schema

```yaml
requirement_model:

  interaction:
    turn_complexity: single | multi_turn | long_running
    state_scope: stateless | session | cross_session | persistent
    determinism_need: strict | guided | open
    channels: [teams, web, m365_copilot, custom, voice]

  knowledge:
    sources: [sharepoint, dataverse, web, api, files, custom_index, none]
    volume_gb: <number>
    freshness_sla: realtime | hourly | daily | static
    grounding_strictness: citation_required | preferred | none
    document_homogeneity: uniform | mixed | highly_varied

  actions:
    side_effects: read_only | write | irreversible
    tool_count: <int>
    orchestration: linear | branching | multi_agent | dynamic_planning
    human_in_loop: none | approval | escalation
    output_consumer: human | system | both

  model_control:
    needs_model_choice: true | false
    needs_finetune: true | false
    needs_custom_eval: true | false
    needs_prompt_versioning: true | false
    needs_reproducibility: true | false

  scale:
    conversations_per_month: <int>
    peak_concurrency: <int>
    latency_p95_target_ms: <int>
    growth_trajectory: flat | linear | steep

  governance:
    auth_model: none | sso | obo | service_principal
    data_residency: [<region codes>] | unconstrained
    content_safety_tier: standard | strict | regulated
    auditability: none | conversation_log | full_trace
    budget_monthly: <number> | unstated

  memory:
    persistence_need: none | session | cross_session
    per_user_isolation: required | not_required
    retention_policy: defined | none | unknown
    sensitive_in_memory: excluded | present | unknown

  safety_feedback:
    guardrail_coverage: input_output | plus_tool_io | none | unknown
    evaluation: gating | baseline | manual | none
    user_feedback_channel: present | absent

  handoff:
    targets: [connected_agent, human, other_agent, none]
    context_carried: full | partial | none
```

## Field notes that matter

Several fields carry more analytical weight than their brevity suggests.

**`interaction.determinism_need`** — the strongest single signal for DSN-01
(orchestration mode mismatch). A `strict` requirement on generative orchestration is
almost always wrong; an `open` requirement on classic orchestration produces the "my
agent can't handle how people actually ask" complaint.

**`actions.orchestration: dynamic_planning`** — the primary trigger for CEIL-01. Probe
this carefully in Mode A. Users say "it should figure out what to do" when they mean
"it should pick from these five things", which is not a ceiling. Ask: *can you write
down every path in advance?*

**`knowledge.document_homogeneity`** — the discriminator between CFG-06/DSN-04 and
CEIL-02. `highly_varied` sources with structured documents genuinely need custom
chunking. `uniform` sources with retrieval complaints are almost always a scoping
problem.

**`actions.output_consumer: system`** — triggers CEIL-06. Humans tolerate format
variation; parsers do not.

**`scale.*` and `governance.*` are never present in an export.** In Mode B these must be
asked or flagged as assumptions. A cost projection built on a guessed volume is worse
than no cost projection, because it looks authoritative.

**`governance.budget_monthly: unstated`** — do not invent a threshold. Present the cost
projection and let the user judge viability. COST-01 requires a stated budget to fire.

**`memory.*`, `safety_feedback.*`, `handoff.*`** — the operational dimensions covered in
`agent-quality-dimensions.md`. `memory.per_user_isolation: required` with no per-user
scope triggers GOV-08; `memory.persistence_need: cross_session` with memory off triggers
CFG-09; `safety_feedback.guardrail_coverage` gaps trigger CFG-10; `handoff.context_carried:
none`/`partial` triggers DSN-10. Distinguish `cross_session` continuity (fixable memory
config) from true durability *beyond* a session (CEIL-05).

## Elicitation (Mode A)

Six rounds, 3–5 questions each, each with a recommended default so the user can accept
and move rather than deliberating over every field. Batching matters — question-by-question
interrogation causes abandonment, and users answer later questions worse as fatigue sets in.
Round 6 (operational readiness) can be skipped for a simple single-turn FAQ agent.
### Round 1 — Purpose and users
- What job does this agent do for the person using it?
- Who uses it — employees, customers, or both?
- Which channels? *(default: Teams + web)*
- What does success look like in three months?

### Round 2 — Knowledge
- What sources must it draw on?
- Roughly how much content, and how often does it change?
- Must answers cite their source? *(default: preferred, not required)*
- Are the documents similar in structure, or varied?

### Round 3 — Actions and orchestration
- What can it *do*, beyond answering?
- Do any actions write data or trigger something irreversible?
- Can you write down every path in advance, or must it work out steps as it goes?
- Where should a human approve or take over? *(default: escalation on repeated failure)*

### Round 4 — Scale and performance
- Expected conversations per month? *(default: ask for an order of magnitude)*
- Peak concurrency?
- Acceptable response time? *(default: 3s p95)*
- Is volume expected to grow sharply?

### Round 5 — Governance
- How do users authenticate, and does the agent access user-specific data?
- Any data residency constraints?
- What content safety posture does the domain need? *(default: standard)*
- What must be auditable?
- Is there a monthly budget ceiling? *(default: unstated — do not invent one)*

### Round 6 — Operational readiness (memory, safety, handoff)
Ask only what the earlier rounds did not already settle; each has a safe default so the
user can accept and move.
- Should the agent **remember** anything between turns or sessions, and must that be
  isolated per user? *(default: session-only, per-user isolated)*
- If it remembers, is there a **retention** limit, and should sensitive data be excluded?
  *(default: exclude sensitive; set a TTL)*
- What **guardrails** must cover it — input/output only, or tool calls too?
  *(default: input/output; add tool I/O if it calls tools)*
- How will you know if quality **regresses**, and can users report a bad answer?
  *(default: baseline eval + a feedback channel)*
- On **handoff** to another agent or a human, what context must travel with the user?
  *(default: full history + key parameters)*

## Inference (Mode B)

What an export reliably yields, and what it does not:

| Field group | From export | Confidence |
|---|---|---|
| `interaction.*` | Topic structure, variable scope | medium |
| `knowledge.sources` | Knowledge configuration | high |
| `knowledge.volume_gb` | Not present | — must ask |
| `actions.tool_count`, `orchestration` | Tool definitions, graph shape | high / medium |
| `actions.side_effects` | Tool semantics | medium — verify with user |
| `model_control.*` | Not present | — must ask |
| `scale.*` | Not present | — must ask |
| `governance.auth_model` | Auth configuration | high |
| `governance.*` (rest) | Not present | — must ask |
| `memory.*` | Memory toggle / store config if in export; else ask | medium / — |
| `safety_feedback.guardrail_coverage` | Guardrail/moderation config | high |
| `safety_feedback.evaluation`, `user_feedback_channel` | Not present | — must ask |
| `handoff.*` | Connected-agent + escalation config; context-passing rarely explicit | medium |

Mark every inferred value as an assumption in the report's requirement-model summary.
Never present an inference as a fact — the report's credibility depends on the reader
being able to tell which is which.
