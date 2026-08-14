# Agent Architecture Advisor

Reviews an existing Copilot Studio or Azure AI Foundry agent for architectural
problems — or designs the architecture for a new one. One reasoning core, two
entry points.

## Supported hosts

This skill can be used across Copilot Studio, Copilot Cowork, Scout, and GitHub
Copilot. The same architecture-review reasoning applies regardless of which
host invokes it.

## What it answers

The gallery already helps you pick a platform, blueprint topics, and test
behaviour. The gap this skill fills is the question every team hits *after* they
have shipped an agent:

> **Is my architecture right — and when do I outgrow this platform?**

It answers that without vendor bias. Every finding is classified as a
configuration issue, a design issue, or a genuine platform ceiling, and
migration is only ever recommended when a real ceiling (or a blocking cost) is
proven. If nothing is wrong with the platform, the report says so.

## Where it fits

The gallery covers the agent lifecycle at three points; this skill fills the fourth —
architecture review and evolution, the question teams hit *after* they ship.

| Stage | Existing skill | Answers |
| --- | --- | --- |
| Platform selection | Microsoft AI Platform Advisor | "Which platform?" |
| Agent design | Copilot Studio Topic Blueprint | "How do I structure a new agent?" |
| Behavioural testing | Copilot Studio Test Planner | "Does it behave correctly?" |
| **Architecture review & evolution** | **this skill** | **"Is it right — and when do I outgrow the platform?"** |

To stay in its lane it is **not** a platform selector, test generator, topic-authoring
tool, or implementation guide — it hands those back to the skills above.

## Modes

- **Review (brownfield).** Point it at a Copilot Studio solution export, agent
  YAML, or Foundry definition. It ingests the artifact, measures trigger
  collisions, orchestration health, and configuration gaps, and produces a
  verdict backed by simulated production failures.
- **Design (greenfield).** Answer a few short rounds of questions and it produces
  a target-state architecture, with the same failure analysis run as a
  pre-mortem.
- **Modernize (classic → agentic).** Point it at a classic topic-based Copilot
  Studio agent and it maps each construct onto the new agentic building blocks
  (Adaptive Orchestration, Connected agents, Memory, Tools/MCP) with a phased
  roadmap.

## Example prompts

You don't run the skill directly — you just describe your situation and the agent
invokes it. Any of these will trigger it:

**Review an existing agent**

- "Review this Copilot Studio agent and tell me if it's built correctly."
  *(attach a solution export, agent YAML, or Foundry definition)*
- "Audit my agent's architecture and give me a verdict."
- "Should I move from Copilot Studio to Azure AI Foundry?"
- "How much will my agent cost at 40,000 conversations a month?"

**Describe a symptom (no jargon needed)**

- "My agent keeps escalating to a human — why?"
- "Answers are wrong even though the knowledge is there."
- "My agent misroutes between two topics."
- "Our Copilot credits are burning way too fast."

**Design a new agent**

- "Help me architect a new customer-support agent."
- "Design a Foundry agent that does retrieval over our policy docs."
- "Plan an agent that can take actions but needs approval before anything irreversible."

**Modernize a classic agent**

- "Upgrade this classic Copilot Studio agent to the new agentic structure."
- "Map my topic-based bot onto Adaptive Orchestration and connected agents."

## How the verdict is reached

| Verdict | Meaning |
| --- | --- |
| `OPTIMIZE` | No platform ceiling reached — stay put and fix what was found. |
| `EXTEND` | Narrow ceilings — add a Foundry component behind a hybrid boundary. |
| `MIGRATE` | Ceilings span several capability areas — move platform. |
| `REDESIGN` | The requirements themselves are unsound. |

The three Python helpers in `scripts/` do the deterministic measurement
(ingest → analyze → cost). The instructions in `SKILL.md` and the rulesets in
`references/` do the judgment.

## Attachment handling by mode

The artifact workflow differs between the two host modes:

- **Agent mode:** provide the Copilot Studio export as a `.zip` file. Agent mode can
  pass the ZIP path directly to `scripts/ingest_agent.py`; a separate extraction step
  is not required.
- **Ask mode:** extract the ZIP first, then share the extracted export folder or its
  files with the conversation. An attachment name or chat reference alone is not a
  readable filesystem path for the parser.

If the export is not available as a local path or shared extracted files, the review
must be reported as incomplete rather than inferred from the attachment name.

## Installing the skill

The skill is a self-contained folder. The agent host discovers it by reading the
`SKILL.md` frontmatter, so installation is just placing the folder where your
host looks for skills.

1. Keep the folder together — `SKILL.md` must sit at the top with `scripts/`,
  and `references/` beside it:

    `agent-architecture-advisor/` with `SKILL.md`, `scripts/`, and `references/`.

2. Copy that folder into your agent host's skills directory (for a local
   Cowork / Copilot / Scout setup this is typically a `skills/` folder, e.g.
   `~/.agents/skills/agent-architecture-advisor/`).

3. Make sure **Python 3** is available.

    Optional for higher-fidelity parsing of real Copilot Studio solution exports
    (`bots/` + `botcomponents/` layout): run `pip install -r scripts/requirements.txt`.

    If PyYAML is not installed, extract the exported solution first and run the
    analysis on the extracted files. The scripts still run with regex fallback
    and will flag reduced-fidelity parsing in `parse_report`.

4. Restart or reload the host so it re-indexes skills, then invoke it with any of
   the [example prompts](#example-prompts) above.

## Contributors

- Anamika Kumari: https://github.com/Annamika
- Shilpa Gangaramani: https://github.com/shilpa1417
