# Hybrid Patterns (EXTEND verdict)

Reference architectures for keeping Copilot Studio as the conversational front door
while delegating a specific capability to Azure AI Foundry.

## Why EXTEND is usually right

When CEILING findings are confined to one or two capability areas, the question is not
*"should we move?"* but *"what should move?"* — and the answer is almost never
"everything."

Copilot Studio and Foundry have close to disjoint strengths. Copilot Studio owns channel
integration, identity, governance inheritance, and conversation management. Foundry owns
reasoning, retrieval engineering, model control, and evaluation. A full migration
discards the first set to acquire the second, when a tool-call boundary acquires the
second while keeping the first.

Teams under-choose this because the framing they arrive with is binary. Name that framing
explicitly when recommending EXTEND — it is usually the moment the recommendation lands.

---

## Pattern A — Planning delegate

**Resolves:** CEIL-01 (dynamic multi-step planning)

```
User ── Copilot Studio ──┬── classic topics (FAQ, forms, deterministic paths)
                         │
                         └── "complex request" topic
                                    │
                                    ▼  tool call
                         Foundry Agent Service
                            plans and executes N steps
                                    │
                                    ▼  structured result
                         Copilot Studio renders response
```

**When:** most interactions are simple; a minority need genuine multi-step reasoning
(research, diagnosis, investigation).

**Routing:** send only what needs planning across the boundary. The most common
implementation error is routing everything through the Foundry component, which
reproduces MIGRATE's cost profile with EXTEND's added complexity — the worst of both.

**Watch:** planning is slow. Set user expectations in the Copilot Studio layer with an
acknowledgement turn before the call.

---

## Pattern B — Retrieval delegate

**Resolves:** CEIL-02 (custom retrieval pipeline)

```
User ── Copilot Studio ──┬── built-in grounding (simple, uniform sources)
                         │
                         └── complex knowledge topic
                                    │
                                    ▼  tool call: query
                         Foundry + Azure AI Search
                            hybrid search, re-rank, decompose
                                    │
                                    ▼  passages + citations
                         Copilot Studio generates grounded answer
```

**When:** retrieval quality is the bottleneck on a subset of sources, and CFG-06/DSN-04
have already been ruled out.

**Two variants:**
- *Retrieval-only* — Foundry returns passages; Copilot Studio generates. Cheaper, keeps
  response style consistent, preserves the conversational layer's voice.
- *Full answer* — Foundry retrieves and generates. Better when the answer needs
  reasoning across passages.

Prefer retrieval-only unless the reasoning genuinely requires it. It is simpler, cheaper,
and leaves the conversational experience intact.

**Watch:** citation fidelity across the boundary. Pass source metadata through and
render it in Copilot Studio, or grounding strictness (GOV-01) breaks silently.

---

## Pattern C — Evaluation sidecar

**Resolves:** CEIL-04 (systematic offline evaluation)

```
Copilot Studio agent (production, unchanged)
         │
         ▼  conversation logs
Foundry evaluation pipeline
   groundedness, relevance, coherence scoring
         │
         ▼  metrics + regression alerts
Deployment gate / dashboard
```

**When:** the agent is architecturally sound but the team needs quantitative quality
measurement and regression gating.

**Distinguishing feature:** this pattern does not change the runtime path at all. The
agent is untouched; evaluation runs alongside. That makes it the lowest-risk hybrid and
frequently the right first step even when other CEILING findings exist — it gives the
team measurement before they change anything else.

**Watch:** this is analysis of production traffic, so confirm logging retention and
privacy posture before recommending it.

---

## Pattern D — Structured output validator

**Resolves:** CEIL-06 (deterministic output contract)

```
Copilot Studio ── generates ──┬──> human-facing response
                              │
                              └──> Foundry structured-output call
                                        schema-enforced extraction
                                               │
                                               ▼
                                     downstream system
```

**When:** the agent serves both a human and a machine consumer.

**Watch:** define behaviour when schema validation fails — retry, fall back to human
confirmation, or fail closed. An unhandled validation failure here surfaces as silent
data corruption downstream, which is worse than a visible error.

---

## The boundary contract

Every hybrid recommendation must specify the interface. An EXTEND verdict without a
boundary contract is an idea, not an architecture — and it is where hybrid
implementations actually fail.

Specify all six:

| Element | Must define |
|---|---|
| **Payload schema** | Request and response shape; what conversation context crosses the boundary |
| **Latency budget** | Maximum acceptable round trip, and what the user sees while waiting |
| **Timeout behaviour** | What happens at the ceiling — degrade, escalate, or retry |
| **Error semantics** | Distinguish retryable from terminal; define retry policy |
| **Fallback path** | What the agent does when the Foundry component is unavailable |
| **Auth propagation** | How user identity crosses the boundary; whether OBO is preserved |

**Auth propagation is the one most often missed and most consequential.** If the Copilot
Studio layer authenticates the user but the Foundry component queries data as a service
principal, per-user authorization is silently bypassed — reintroducing GOV-03 at the
boundary. Flag this explicitly in every hybrid recommendation that touches user-scoped data.

**The fallback path is the second most missed.** Teams design the happy path and discover
at 3am that the Foundry component being down means the entire agent is down, including
the simple FAQ topics that never needed it. Specify graceful degradation: the classic
topics should keep working.

---

## Anti-patterns

Worth naming explicitly, because each one shows up regularly.

**Everything through the delegate.** Routing all traffic through the Foundry component
because it is "the smart one." Reproduces MIGRATE cost with added latency and network
failure modes, and gains nothing. If most traffic crosses the boundary, the verdict
should have been MIGRATE.

**Chatty boundary.** Multiple round trips per user turn. Each hop adds latency and
failure surface. Design for one call per turn.

**Duplicated state.** Conversation state maintained on both sides drifts. Keep it
authoritative in Copilot Studio and pass what is needed.

**Silent auth downgrade.** Covered above. The most dangerous of the four because nothing
visibly breaks.

**Hybrid as indecision.** Choosing EXTEND to avoid making a call, then migrating
piecemeal without a plan. EXTEND is a deliberate architecture with a defined boundary,
not a staging area. If the evidence supports MIGRATE, say MIGRATE.
