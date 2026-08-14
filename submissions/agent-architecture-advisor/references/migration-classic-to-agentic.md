# Classic → Agentic Copilot Studio Modernization

Reference for **Mode C**. This is *not* a platform migration (Copilot Studio → Foundry).
It modernizes a **classic, topic/trigger-phrase** Copilot Studio agent into the new
**agentic, multi-agent** structure on the GitHub Copilot harness — same platform, new
architecture.

- **last-reviewed:** 2026-08-07
- **live sources:** `MIG-CPS-FAQ`, `MIG-CPS-PLUGIN`, `MIG-CPS-SAMPLES` in
  `reference-links.json` — fetch for current upgrade behaviour and tooling before
  asserting what carries over.

## Inputs

- **Classic solution export** (`.zip`) or topic YAML — reuse `scripts/ingest_agent.py`
  and `scripts/analyze_topics.py`; the collision/orchestration/grounding measurements
  become the modernization evidence base.
- **Self-report** when no export exists — topic count, orchestration mode, knowledge
  sources and scoping, actions, auth. Mark findings `low` confidence.

## The mapping model

Map each classic construct to its agentic counterpart. Verify carry-over behaviour
against `MIG-CPS-FAQ` before promising anything — some constructs are reused, some are
superseded.

| Classic construct | Agentic target | Disposition |
|---|---|---|
| Topic + trigger phrases | Intent handled by **Adaptive Orchestration** | Often **superseded** — heavy trigger-phrase graphs collapse into described capabilities |
| Rigid topic branching (dialog tree) | Dynamic planning across turns | **Rebuild** as goals/instructions, not fixed nodes |
| Sub-topics / redirects | **Connected agents** (specialist children) | **Re-architect** where a topic cluster is really a separate specialty |
| Global variables passed between topics | **Memory** | **Reuse intent**, re-express as session memory |
| Power Automate flows / custom connectors | **Tools / MCP servers** | **Reuse** via MCP where possible |
| Adaptive cards | Retained; check FAQ for exact behaviour | **Verify** against `MIG-CPS-FAQ` |
| Computation done via external flow | **Agent Sandbox** (runtime code) | **Simplify** where a flow only computed/transformed |
| Document output via connector | **File Generation** | **Simplify** |
| Knowledge sources | Knowledge + Tools | **Reuse**, re-scope per agent |

## Output

Produce three artifacts, in this order:

### 1. Gap analysis

For each classic construct found in the export/self-report, state: what it maps to, the
disposition (reuse / re-architect / rebuild / superseded), and the evidence
(finding ID or measurement). Call out trigger-phrase collisions and dead-end topics as
**prime rebuild candidates** — they usually dissolve under Adaptive Orchestration and
should not be ported as-is.

### 2. Phased roadmap (effort + risk)

| Phase | Contents | Exit criteria |
|---|---|---|
| **Phase 0** | Inventory + gap analysis; identify the single highest-value flow to modernize first | Agreed target scope, measured baseline |
| **Phase 1** | Rebuild the core flow as an agentic agent (goals, Memory, Tools/MCP); keep classic agent live in parallel | New agent matches or beats baseline on the target flow |
| **Phase 2** | Add Connected agents for specialty clusters; migrate remaining flows; retire classic topics | Classic agent decommissioned; parity + regression checks pass |

Tag every item with effort (low/medium/high) and risk, and note where behaviour change
is expected (dynamic planning replaces deterministic branching — flag any flow that
requires strict determinism).

### 3. Target agentic design spec

- **Agent topology** — the parent agent and any Connected child agents, with the
  responsibility boundary of each.
- **Orchestration** — what Adaptive Orchestration owns vs. what stays explicit.
- **Memory** — what persists across turns and why.
- **Tools / MCP** — external systems, mapped from classic flows/connectors.
- **Runtime capabilities** — Agent Sandbox / File Generation where they replace a flow.
- **Knowledge** — sources and per-agent scoping.
- **Recommended execution path** — cite `MIG-CPS-PLUGIN` as the tooling that upgrades an
  existing agent to the harness, and `MIG-CPS-SAMPLES` for reference patterns.

## Guardrails

- **Do not port collisions.** A classic agent's trigger-phrase overlaps are a reason to
  rebuild, not a spec to replicate.
- **Flag determinism loss.** Where a classic dialog guaranteed a fixed path (e.g.
  compliance scripts), state explicitly that adaptive planning changes this and how to
  constrain it.
- **Verify carry-over from the FAQ**, never from assumption — topics, prompts, adaptive
  cards, and child agents each have specific upgrade behaviour.
- **Cost delta.** Run `scripts/cost_model.py` for both the classic and agentic shapes so
  the modernization case includes a consumption comparison, priced from the live links
  in `reference-links.json`.
