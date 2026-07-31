# Choosing the AI Building Block (Phase 4)

AI-first design is **not** "add an agent." An agent is only one of several building blocks. For
every step you decide AI should own or augment, pick the *simplest block that delivers the
outcome*. Start at the top of this list and only move down when the step genuinely needs it.

## The ladder — simplest first
1. **Process / workflow change** — no AI at all. Remove the step, re-order it, or change a rule.
   Often the highest-value move; always test this first.
2. **Knowledge** — the data the agent can reference. Use when the need is "answer accurately from
   a source" (policy, spec, past cases). Managed as knowledge sources.
3. **Tool / action** — an action via an external service (connector, API, MCP server, or a Power
   Automate flow). Use when the step must *do* something in a system (create, update, send, look
   up). Managed as connectors/tools.
4. **Skill** — a reusable, task-specific capability defined by a **name, a description, and
   Markdown instructions**. Use when a distinct *type of task or mode* recurs and you want it
   focused, reusable, and shareable across agents. A skill is the right home for "how to handle
   this kind of task" — the orchestration runtime invokes it when a request matches its purpose.
5. **Agent** — a single assistant with its own instructions, knowledge, and tools that holds a
   conversation and orchestrates several skills/tools toward a goal. Use when a whole role needs
   an interactive front end and judgement across multiple steps.
6. **Connected agent** — a *specialist* agent that a primary "front-door" agent delegates to. Use
   only when a capability is a **genuinely separate domain** — different responsibilities, data,
   owner, or team — that deserves to be built, owned, and reused independently.

## Skills vs. the other components (quick reference)
| Component | Purpose | Managed as |
|-----------|---------|-----------|
| **Instructions** | General agent behaviour and personality | Identity configuration |
| **Knowledge** | Data the agent can reference | Knowledge sources |
| **Tools** | Actions via external services | Connectors, APIs, MCP servers |
| **Skills** | Reusable, task-specific capabilities | Markdown skill files or packages |

**Why reach for a skill** (over stuffing everything into one agent's instructions):
*reusability* (write once, add to many agents), *modularity* (focused, maintainable pieces),
*shareability* (export as Markdown or a package), and *clarity* (one clear purpose each).

## Connected agents — when a specialist is worth it
A connected agent is useful when you have multiple specialised agents and want a single front-door
agent that routes users to the right one. They give you **specialisation** (each agent focuses on
one domain), **reusability** (connect one specialist to many primaries), **separation of concerns**
(different teams own different agents), and **scalability** (add capability by connecting a new
agent rather than bloating one). At runtime the primary agent's orchestrator evaluates each
message, delegates to a connected agent when the request matches its domain, passes the relevant
history, and returns the specialist's response to the user.

**Rule of thumb:** don't split into a connected agent just because a capability is big — split when
it is a *different domain with a different owner*. Otherwise a skill inside the same agent is
simpler to build, test, and maintain.

## How this feeds the outputs
- **Summary table (part E):** the "AI Agents & Skills" bucket should say *which* block each item
  is (skill / tool / agent / connected agent), not assume "agent."
- **AI-capability backlog (part F):** for each opportunity, state the **recommended building
  block** and why that block over the alternatives — this is what an agent-builder step needs.
- **Challenge test:** for every proposed agent, ask "could a process change, a tool, or a reusable
  skill do this instead?" Record the answer. Reserve agents/connected agents for where they truly
  earn their keep.
