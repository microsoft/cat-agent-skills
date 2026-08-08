# Copilot Agent Advisor

Not sure whether a scenario needs a full custom agent, a lightweight standard agent, or nothing more than Microsoft 365 Copilot as it ships? This skill makes that call for you.

Describe the scenario and it recommends **one of three options**:

| Option | What it is |
|--------|-----------|
| **Use Microsoft 365 Copilot as-is** | The built-in Copilot experience over your Microsoft 365 data — no build. |
| **Standard agent (declarative)** | Copilot tailored with your instructions, knowledge, and actions, running on Copilot's own orchestrator and models, inside Microsoft 365 apps. |
| **Custom agent (custom engine)** | A fully custom agent — your own orchestrator and models, custom workflows, its own hosting, and reach beyond Microsoft 365. |

It also advises **which Copilot Studio authoring experience** to use — the new (modern) instruction-based experience vs the classic topic/flow experience — and always flags that there's no migration path between the two.

## How it works

It weighs the factors that actually drive the decision:

- Where the **knowledge/data** lives (Microsoft 365 vs external systems)
- Whether you need **your own or fine-tuned models**
- Whether you need **custom orchestration** or deterministic business logic
- **Channels** (inside Microsoft 365 only, or external too)
- **Autonomy** (user-initiated vs proactive/triggered)
- **Audience** (individual vs group collaboration)
- **Compliance** (inherit Microsoft 365's, or own it)
- **Speed & skill** (fastest low-code, or full pro-code control)

Then it returns a clear recommendation with the reasoning tied to your specifics, a runner-up and the single factor that would flip the decision, how to build it, and the trade-offs (cost, hosting, compliance ownership).

## Example

> **You:** "We want a Teams helpdesk assistant that answers from our SharePoint IT policies. Which agent should I build?"
>
> **It recommends:** a standard (declarative) knowledge agent in Microsoft 365 Copilot Agent Builder (new experience) — because the knowledge already lives in Microsoft 365, it runs inside Teams, it's user-initiated, and it inherits Microsoft 365 compliance. Runner-up (custom engine agent) only if you later add external-system write-back, your own model, or proactive behavior.

## Good to know

- **It advises — it doesn't build.** It recommends the choice; it won't provision, configure, or deploy the agent.
- **It stays current.** Agent capabilities and previews move fast, so it verifies fast-moving specifics against Microsoft Learn before asserting them.
- Grounded in Microsoft Learn's declarative-vs-custom-engine decision guidance and the Copilot Studio "classic vs new agent experience" documentation.
