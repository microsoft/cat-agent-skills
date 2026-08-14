# Platform Capability Envelopes

Reference for C2. Describes where each platform's capability boundary sits and — more
usefully — *why* it sits there, so the classification holds up when a specific feature
name changes.

- **capability-date:** 2026-08
- **review-cadence:** quarterly

Platform features move fast. Treat specific feature claims as provisional and verify
before asserting a ceiling in a report. The *shape* of the boundaries below is stable
even when the details are not.

---

## Currency note — Copilot Studio's agentic shift (capability-date 2026-08)

Copilot Studio has been rebuilt from a single chatbot into an **agentic, multi-agent
platform on the GitHub Copilot harness** — the agent reasons, acts, and adapts in a
continuous loop. This moves several boundaries that older reviews treated as fixed
Copilot Studio ceilings. **Re-test the requirement against these in-platform capabilities
before asserting the corresponding CEIL rule.**

Source: Copilot Studio technical guide (Microsoft CAT team),
https://microsoft.github.io/new-copilot-studio-tech-guide/ — treat as provisional and
confirm regional/tenant availability.

| New building block | What it does | Boundary it narrows |
|---|---|---|
| **Adaptive Orchestration** | Plans dynamically across turns, asks for clarification, revises the plan when the request changes | **CEIL-01** — dynamic multi-step planning is now partly in-platform |
| **Connected agents** | A parent agent delegates to specialist child agents and merges their answers | **CEIL-05** — multi-agent coordination |
| **Memory** | Context and earlier results persist across the conversation | **CEIL-05** — cross-turn / session state |
| **Agent Sandbox** | Generates and runs code at runtime to compute and transform | reduces reliance on external tools for computation |
| **AI Skills** | Reusable runtime procedures that can reference scripts and templates | orchestration structure (DSN) |
| **File Generation** | Produces real PDFs, images, and documents | new capability, not previously modelled |
| **Tools / MCP servers** | Calls external systems and APIs as tools via MCP | tool integration standardised |

**Consequence for the anti-bias rule:** because Copilot Studio now covers dynamic
planning, multi-agent, memory, and runtime computation, a review must re-test CEIL-01 and
CEIL-05 against these in-platform capabilities *before* recommending EXTEND or MIGRATE.
The most likely 2026-07-era error is recommending Foundry for planning or multi-agent work
that current Copilot Studio does natively. The boundaries that still hold most reliably
are **model-level control (CEIL-03)**, **engineered retrieval (CEIL-02)**, and
**CI-gated evaluation (CEIL-04)**.

---

## Copilot Studio — designed strengths

Copilot Studio optimises for **speed to a governed conversational agent**. Its
abstractions are deliberate, and most of what looks like a limitation is a trade the
platform made on purpose.

| Strength | Why it matters architecturally |
|---|---|
| Channel integration | Teams, M365 Copilot, web, voice with no per-channel work |
| Identity and auth | SSO and on-behalf-of flows against M365 without custom code |
| Maker accessibility | Non-developers can build and maintain topics — this is a real, frequently discounted asset |
| Governed by default | DLP, tenant policy, admin visibility inherited from Power Platform |
| Built-in grounding | Point at SharePoint/Dataverse/web and get working retrieval quickly |
| Generative orchestration | Dynamic tool selection across defined topics and actions |

**The architectural consequence:** when a review recommends migration, these are what
gets lost. A `MIGRATE` verdict that does not account for rebuilding channel integration,
auth, and governance is understating the cost by a wide margin — often by more than the
engineering effort of the agent itself.

## Copilot Studio — boundary shape

The boundaries cluster in four areas. Understanding the *category* matters more than
tracking individual features.

**1. Model abstraction.** The model is managed. No selection, temperature control,
fine-tuning, or version pinning. → CEIL-03

**2. Orchestration is selection, not composition.** Generative orchestration chooses
among things you defined. It does not compose novel multi-step plans where the plan
shape depends on intermediate results. → CEIL-01

**3. Retrieval is configured, not engineered.** Grounding works well on
reasonably-structured sources. Custom hybrid weighting, re-ranking, query decomposition,
and structure-aware chunking are outside the envelope. → CEIL-02

**4. Evaluation is manual.** The test panel validates behaviour interactively. Automated,
quantitative, threshold-gated evaluation in a pipeline is not available. → CEIL-04

Secondary boundaries: durable cross-session state (CEIL-05), strict structured output
guarantees (CEIL-06).

---

## Azure AI Foundry — designed strengths

Foundry optimises for **engineering control over AI systems**.

| Strength | Enables |
|---|---|
| Model choice and parameters | CEIL-03 resolution; cost/quality tuning |
| Custom orchestration | CEIL-01 resolution; genuine multi-step planning |
| Azure AI Search integration | CEIL-02 resolution; full retrieval pipeline control |
| Evaluation SDK | CEIL-04 resolution; CI-gated quality regression |
| Agent Service | CEIL-05 resolution; durable and multi-agent workflows |
| Structured output | CEIL-06 resolution |
| Full tracing | GOV-05 resolution at reasoning-step granularity |

## Azure AI Foundry — costs

State these plainly whenever recommending Foundry. A recommendation that presents only
upside reads as advocacy and gets discounted accordingly.

- **Channel work is yours.** Teams, web, and voice surfaces must be built and maintained.
- **Auth is yours.** OBO flows, token handling, and scope management become code.
- **Governance is yours.** DLP and tenant policy inheritance does not come for free.
- **Developer skills required.** Makers who maintained topics cannot maintain this.
- **Operational burden.** Deployment, monitoring, versioning, and on-call become real.
- **Cost model shifts** from predictable per-message Credits to consumption-based Azure
  spend, which is cheaper at volume but harder to forecast and easier to overrun.

---

## The hybrid boundary — where EXTEND lives

The most useful architectural insight in this reference: **these platforms are
complementary, not competing.** Their strengths are close to disjoint.

Copilot Studio owns channel, identity, governance, and conversation management.
Foundry owns reasoning, retrieval, model control, and evaluation.

The hybrid pattern keeps each where it is strong: Copilot Studio as the conversational
front door, invoking a Foundry agent behind a tool call for the specific capability that
exceeded the ceiling.

This is correct more often than either extreme, and it is systematically
under-recommended — teams tend to frame the question as "should we move?" rather than
"what should move?" Prefer `EXTEND` whenever CEILING findings are confined to one or two
capability areas.

See `hybrid-patterns.md` for reference architectures and the boundary contract to specify.

---

## Applying this in a review

1. **Identify which boundary category a requirement crosses**, not which feature is
   missing. Features change; the four boundary categories have been stable.
2. **Check the cheap explanation first.** Most retrieval complaints are scoping
   (CFG-06/DSN-04), not pipeline ceilings. Most latency problems are serial calls
   (DSN-06), not platform floors.
3. **Count distinct capability areas crossed**, since that drives EXTEND vs MIGRATE.
4. **When recommending Foundry, enumerate what is lost** from the Copilot Studio strengths
   table above.
5. **When a feature claim is load-bearing for a ceiling assertion, verify it** or record
   it as an open question rather than asserting it.
