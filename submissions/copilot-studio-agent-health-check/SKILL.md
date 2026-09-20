---
name: copilot-studio-agent-health-check
description: "Statically lints an exported Copilot Studio agent for structural defects, across both the classic topic-based experience and the new agentic (skill-based) experience. For topic agents it finds trigger-phrase collisions that cause misrouting, unreachable topics, missing fallback and escalation paths, slot-filling with no correction path, and variable-lifecycle bugs. For agentic agents it finds skill-description collisions that confuse routing, missing or thin skill descriptions, empty skill instructions, and references to unwired tools. It also runs cross-cutting checks on both experiences: unsafe or unrecognised Power Fx expressions, dead-end dialog branches, orchestration-mode-aware trigger/description quality, inconsistent OData parameter quoting, variable names that look like leaked secrets, and connected-agent handoff integrity. Use this whenever someone uploads a Copilot Studio agent export (solution .zip or the botcomponents folder) and wants it checked, or asks why their agent misroutes, gives empty answers, gets stuck, or might be leaking a secret — even when they only describe the symptom. Deterministic and evidence-backed: it reports defects in the artifact, it does not test security, model cost, or recommend a platform."
---

# Copilot Studio Agent Health Check

Static structural analysis of an exported Copilot Studio agent. One job: read the
export, detect which kind of agent it is, run the deterministic checks that apply,
and return a findings report where every item is a structural fact about the
artifact with a severity and a concrete fix.

The design principle that keeps this skill honest and durable: **every check is
decidable from the export alone, and stays true regardless of what ships in the
platform next quarter.** A trigger collision is a trigger collision forever; a
skill description two other skills could equally match is a routing problem
forever. That is why this is a linter and not an advisor — it does not reason
about fast-moving platform capabilities, pricing, or migration, so it does not go
stale.

## Two modes, detected automatically

Copilot Studio exports come in more than one shape, and this skill handles both
without the user having to say which is which:

- **Classic / topic-based agents** — the agent is a graph of `AdaptiveDialog`
  topics with trigger phrases, nodes, and `Topic.` variables. The classic checks
  apply.
- **Agentic / skill-based agents (new experience)** — the agent is a set of
  `InlineAgentSkill` components, each a natural-language description plus markdown
  instructions and tool references, routed by an LLM. The agentic checks apply.
- **Hybrid / modernized agents** — both at once (classic system topics plus a
  generative core, or topics plus skills). Both check sets run on the parts they
  apply to.

The ingest step reports the detected `mode` and exactly what it analyzed
(topics, skills, tools), so the report is always explicit about which checks ran.

## What this skill is not

State these boundaries and point elsewhere rather than half-doing them:

- **Not a security red-teamer.** It does not run adversarial probes, compute
  attack-success rates, or harden guardrails. That is a separate security workflow.
- **Not a cost model.** It does not price Credits or tokens. Cost depends on rates that
  change; that is a different, separately-maintained concern.
- **Not a platform advisor.** It does not recommend Copilot Studio vs Foundry, migration,
  or modernization. It lints the agent in front of it.
- **Not a test generator or design tool.** It analyses an existing agent's structure; it
  does not author topics, write skills, or generate a test suite.

**Privacy:** the report describes structure and size — topic and skill names, description
and instruction *lengths*, tool references, similarity scores. It never reproduces the
text of skill instructions or descriptions, which in a real agent can carry
business-sensitive prompt content.

### Guardrail & instruction-quality signals (advisory)

The linter also reports a set of **guardrail-presence and instruction-quality signals** as
*advisory notes*, never as hard defects:

- **G-NOCONFIRM** — the agent can change state (a wired tool exposes create/update/delete/
  action) but its instructions contain no confirmation/approval gate.
- **G-NOGROUNDING** — instructions contain no anti-fabrication / grounding rule
  ("do not invent", "answer only from…").
- **Q-NOOUTPUT** — instructions define no output or format constraint.
- **Q-NOSCOPE** — instructions state no scope limits or prohibitions.
- **Q-SKILL-NOSTRUCTURE** — a skill's instructions have no output-format or scope structure.
- **Q-SKILL-NOGROUNDING** — a skill's instructions have no grounding rule of their own,
  independent of whatever the main instructions state.

These are deliberately **advisory by default**. They detect the *structural absence* of a
control (something a script can be certain of); they do **not** judge whether the prose is
well-written, nor whether a guardrail is *sufficient* — that is a security/red-team concern
and the scope of the guardrails/red-team skills, not this linter. Teams that want these to
gate a build can opt in with `--guardrails-strict`, which promotes them to hard findings.

### What this skill does NOT check (and why)

- **Guardrail sufficiency / security red-teaming.** The linter reports whether a
  confirmation gate or grounding rule is *present*, not whether the agent is *safe*.
  Adversarial testing and guardrail adequacy belong to dedicated security skills.
- **Semantic instruction quality / hallucination risk.** Whether an instruction is
  well-phrased or will avoid hallucination is a model-judgement that changes over time. The
  linter stays durable by checking structure, and surfaces quality only as advisory signals.

## How to run it

### 1. Ingest the export

```bash
python scripts/ingest_agent.py <path-to-export> --out normalized.json
```

Accepts a Copilot Studio solution `.zip`, an unzipped solution directory
(including the `botcomponents/` layout used by current exports), a directory of
loose topic YAML, or a single topic/agent YAML file. The parser detects the
format and the agent mode. If parsing is incomplete, the script says so — do not
fill the gap by guessing at the agent's contents.

Main instructions are read from whichever source the export actually carries —
`configuration.json`'s embedded `agentSettings.instructions`, a `GptComponentMetadata`
component (some exports point at one via `gPTSettings.defaultSchemaName` instead of
embedding instructions directly), or a modernization-layer `parent-agent/instructions.md`
— in that priority order, so hybrid/modernized exports are not misreported as having no
instructions just because the classic `configuration.json` field is empty.

A `.zip` is untrusted input: extraction refuses archives over 5,000 entries or whose
declared uncompressed size exceeds 200 MB, reporting the refusal rather than risking a
decompression-bomb upload.

See `references/EXPORT-FORMATS.md` for the full component-kind dispatch table, the
modernization-layer file conventions, and the format-variance tolerance details.

### 2. Lint

```bash
python scripts/lint_agent.py normalized.json --out lint-report.md
```

The report is written as **markdown** by default (`lint-report.md`) — a readable
document with the findings, their fixes, and a per-skill review table. Use
`--format json` for a machine-readable report (useful in CI) or `--format text`
for a plain console summary. Adjust collision/description-overlap sensitivity with
`--threshold` (default 0.75; lower catches more near-duplicates at the cost of more
noise). The same threshold governs topic-trigger collisions and skill-description
collisions.

The two scripts version independently (a team may run them from different checkouts),
so `lint_agent.py` checks the normalized model's `schema_version` and surfaces a warning,
rather than silently misreading fields, if it does not recognise it.

## The checks

Findings come in two tiers. Lead with correctness; hygiene is deferrable.

### Classic / topic-based

**Correctness — will cause user-visible failure or broken behaviour:**

- **L-COLLISION** — two topics whose trigger phrases overlap enough to misroute. Catches
  the high-risk *same-object / different-action* shape ("cancel my order" vs "change my
  order") that simple word-overlap misses, as well as ordinary lexical overlap.
- **L-UNREACHABLE** — a topic with no trigger phrases and no inbound route: dead or
  orphaned.
- **L-NOFALLBACK** — no system fallback, so unmatched input hits a dead end.
- **L-NOESCALATE** — no human handoff, so failed conversations have no exit.
- **L-NOCORRECT** — slot-filling topics with no interruption path, so a user cannot say
  "no, I meant..." and gets stuck.
- **L-VARUNSET** — a variable read but never set, which renders an empty value to the user.

**Hygiene:**

- **L-CYCLE** — two topics that call each other; check for an unintended loop.
- **L-NOWELCOME** — no conversation-start guidance.
- **L-VARDEAD** — a variable set but never read: a dead assignment.
- **L-MONOLITH** — an oversized topic worth decomposing.

Platform-managed **system topics** (Greeting, Fallback, Escalate, On Error,
Multiple Topics Matched, and so on) are recognised and excluded from the
noise-prone checks, because the maker did not write them and cannot meaningfully
change them.

### Agentic / skill-based (new experience)

**Correctness:**

- **A-DESC-COLLISION** — two skills whose descriptions overlap enough that the LLM router
  cannot reliably choose between them. This is the agentic analogue of a trigger collision.
- **A-NODESC** — a skill with no description. In the agentic experience the model selects a
  skill by its description, so a skill with none cannot be routed to.
- **A-WEAKDESC** — a description too thin for the router to distinguish from the others.
- **A-NOINSTRUCTION** — a skill with empty or near-empty instructions: it will be selected
  and then have no defined behaviour.
- **A-DUP-NAME** — two skills sharing the same name: routing and maintenance ambiguity.
- **A-NOTOOLS** — a skill whose instructions act on data (read/update/search/…) but which
  lists no tools, so it is told to act with nothing to act with.
- **A-TOOLREF** — a skill referencing a *custom* tool that is not wired into the agent.
  Built-in platform tools (`data_*`, `api_*`, and so on) are excluded — referencing them
  is not a defect.

**Hygiene:**

- **A-VAGUE-DESC** — a description long enough but stating no routing condition
  ("use when…", "when the user…"), so the router has no trigger signal to match on.

Agentic reports also include a **per-skill review**: for every skill, its description and
instruction size, whether it states a routing condition, its built-in vs custom tools, and
its closest sibling by description similarity — so the report shows the routing separation
margin even when there are no findings. Only lengths and structure are reported; the text
of descriptions and instructions is never reproduced.

### Token budget (estimated)

Every report includes a rough token estimate — main instructions, the sum of all skill
descriptions (always loaded for routing), a worst-case single turn (always-loaded plus the
largest skill's instructions, once selected), and connected agents' instructions shown
separately with a combined export-wide total (a connected agent runs in its own context,
not appended to the orchestrator's). This is a ~4-characters-per-token rule of thumb
computed from lengths already collected elsewhere, never from the underlying text — not an
exact tokenizer count, and actual usage depends on the specific model. It exists to make
prompt-size cost visible at a glance, not to price Credits or tokens (see "What this
skill is not").

Three length-based observations surface as **advisory notes** (judgement calls, not
defects) when a size crosses a rule-of-thumb threshold: main instructions over 12,000
characters, an always-loaded budget (instructions plus every skill description) over 8,000
tokens, or any single skill's instructions over 4,000 characters. None of these assert the
agent is broken — only that the prompt size is worth a deliberate look.

### Whole-agent component checks

Regardless of mode, the report also checks whichever of these components the export
has — wired tools (`C-TOOL-EMPTY`, `C-TOOL-NOCONN`), main instructions vs skills
(`C-INSTR-MISSING`, `C-INSTR-TOOLREF`), evaluation coverage (`C-EVAL-NONE`,
`C-EVAL-NOGRADER`), and connected-agent contracts (`C-CONTRACT-INVALID`,
`C-CONN-NOCONTRACT`). These are hard findings, not advisory. See `references/RULES.md`
for the complete catalog with tier, severity, and what each one detects.

### Pragmatic semantic rules

Seven further checks reason about Power Fx syntax, dialog branching, orchestration mode,
connector parameters, and connected-agent handoffs: `PFX-SAFETY`, `DIALOG-DEADEND`,
`TRG-QUALITY`, `ODATA-QUOTE`, `SEC-AI-LEAK`, `GUARDRAIL-GATE`, and `CONNECTED-AGENTS`.
Each is deliberately narrower than an obvious first draft of the same idea, to keep false
positives low — e.g. `DIALOG-DEADEND` only flags a `ConditionGroup` whose branches
*disagree* on how they exit, never a topic that simply ends on a plain message, which is
normal. Full detail, including the exact scope limit of each, is in `references/RULES.md`.

## Presenting results

Report the findings as they come from the script — the linter has already sorted them
(correctness first, then by severity) and attached evidence and a fix to each. Keep the
report faithful to the script output:

- **Always produce the actual `lint-report.md` file, and say where it is.** Running
  `lint_agent.py` with the default `--format md` already writes the full, detailed report
  (component inventory, guardrail table, connected agents, knowledge sources, skill
  review, token budget, advisory notes) to disk. A chat-only prose paraphrase is not a
  substitute for it — the tables and per-finding evidence do not survive being summarized.
  State the file's path (or attach it) so the user has the complete artifact, not just a
  recap. Only skip writing the file if the user has explicitly said they do not want one.
- **State the mode.** Say whether you linted a classic, agentic, or hybrid agent, and how
  many topics/skills/tools were analyzed. It tells the user which checks were relevant.
- **Lead with correctness findings.** Those are what break user experiences.
- **Keep the evidence.** Each finding cites the specific topics, phrases, skills, or
  variables involved. That is what makes it checkable rather than a vague warning.
- **Keep the fix line.** Each finding has a concrete, one-line remediation. Do not expand
  these into platform strategy — a linter suggests the local fix, not an architecture.
- **If the agent is clean, say so plainly.** "No structural issues found" is a valuable
  result, not a failure. Do not invent findings to fill a report.
- **Respect confidence.** If ingestion was incomplete (confidence `medium` or `low`), state
  that the lint is based on a partial parse and some checks may be understated. In
  particular, an export with neither topics nor skills yields low confidence — say so
  rather than implying the agent is clean.

## Working principles

**Report defects, not strategy.** The linter's job ends at "here is the structural problem
and its local fix." Whether to migrate, what it costs, or how to redesign is out of scope —
if the user asks, point them to the right tool rather than stretching the linter.

**Evidence over assertion.** Every finding names the specific artifact element. Never
report a problem the script did not measure.

**Do not fabricate.** A short report on a well-built agent is the correct output. Padding
it with soft findings trains the user to ignore the linter. If a mode's checks do not
apply (e.g. an agentic agent has no topics), that is not a gap to fill — it is simply not
where this agent's risks live.

**Tune, don't lower blindly.** The overlap threshold defaults to 0.75. Lowering it finds
more near-duplicates but adds noise; mention the trade-off if a user wants more or fewer
collision findings.
