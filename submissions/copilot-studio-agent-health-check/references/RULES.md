# Rule Reference

The complete catalog of structural findings `lint_agent.py` can emit, organised by
category. `SKILL.md` covers the classic (`L-*`) and agentic (`A-*`) rules; this file adds
the whole-agent component checks (`C-*`), the pragmatic semantic rules (Power Fx,
dialog branching, orchestration mode, OData, connected agents), and a compact index of
the advisory guardrail signals (`G-*` / `Q-*`) that `SKILL.md` already documents in full.

Every rule follows the same shape: a `rule` code, a `tier` (`correctness` breaks user
experience; `hygiene` is deferrable), a `severity` (`high` / `medium` / `low`), `evidence`
naming the specific artifact element, a one-line `fix`, and optional `file`/`line`
attributes populated when the parser located the violation's source. Nothing here is a
judgement call — each is decidable from the export alone.

## Classic / topic-based (`L-*`)

| Rule | Tier | Severity | Detects |
|---|---|---|---|
| `L-COLLISION` | correctness | high (score ≥ threshold) / medium (near, ≥ 0.70) | Two topics whose trigger phrases overlap enough to misroute, including same-object/different-action pairs ("cancel my order" vs "change my order"). |
| `L-UNREACHABLE` | correctness | high | A non-system topic with no trigger phrases and no inbound `BeginDialog` edge. |
| `L-CYCLE` | hygiene | medium | Two topics whose `calls_topics` reference each other. |
| `L-NOFALLBACK` | correctness | high | No topic name resolves to a system fallback topic. |
| `L-NOESCALATE` | correctness | high | No topic name resolves to a human-handoff topic. |
| `L-NOCORRECT` | correctness | high | A non-system topic has slot-filling (a `Question` node) with no interruption/correction branch. |
| `L-NOWELCOME` | hygiene | low | No greeting/conversation-start topic detected. |
| `L-VARUNSET` | correctness | high | A `Topic.` variable is read in some topic but never set in any topic. |
| `L-VARDEAD` | hygiene | low | A `Topic.` variable is set in some topic but never read in any topic. |
| `L-MONOLITH` | hygiene | low | A topic's node count exceeds 25. |

Variables used only inside platform system topics, and system topics themselves, are
excluded from these checks — the maker did not write them and cannot change them.

## Agentic / skill-based (`A-*`)

| Rule | Tier | Severity | Detects |
|---|---|---|---|
| `A-DESC-COLLISION` | correctness | high | Two skill descriptions similar enough (≥ threshold) that the router cannot reliably choose between them. |
| `A-NODESC` | correctness | high | A skill with no description at all. |
| `A-WEAKDESC` | correctness | medium | A description shorter than 30 characters. |
| `A-NOINSTRUCTION` | correctness | high | A skill with instructions shorter than 20 characters (including none). |
| `A-DUP-NAME` | correctness | high | Two or more skills sharing the same name. |
| `A-NOTOOLS` | correctness | medium | Instructions contain an action verb (read/write/update/create/delete/search/find/fetch/retrieve/query/call/invoke/post/send/modify/look up) but the skill lists no tools. |
| `A-TOOLREF` | correctness | low | A skill references a custom (non-built-in) tool name that matches no wired tool component. Confidence `medium`: the tool may be wired outside the export (an environment-level connection). |
| `A-VAGUE-DESC` | hygiene | low | A description ≥ 30 characters but with no routing-condition language ("use when…", "when the user…", "handles…", and similar). |

## Whole-agent component checks (`C-*`)

These apply regardless of classic/agentic/hybrid mode, to whichever components the export
actually has. Like `L-*`/`A-*`, they are hard findings, not advisory.

| Rule | Tier | Severity | Detects |
|---|---|---|---|
| `C-TOOL-EMPTY` | correctness | medium | An `McpTool` component whose `allowedTools` list is empty, so it exposes no operations. |
| `C-TOOL-NOCONN` | correctness | medium | An `McpTool` component with no `connectionReference`, so it cannot authenticate at runtime. Confidence `medium`. |
| `C-INSTR-TOOLREF` | hygiene | low | Main instructions mention what looks like a tool call, but the name matches no wired tool or MCP operation. Confidence `medium`. |
| `C-INSTR-MISSING` | correctness | medium | The agent has skills but no top-level main instructions were found anywhere. |
| `C-EVAL-NOGRADER` | hygiene | low | An `EvaluationSet` defines zero graders, so its cases cannot be scored. |
| `C-EVAL-NONE` | hygiene | low | The agent has skills but ships no evaluation sets and no test-case count at all. |
| `C-CONTRACT-INVALID` | correctness | medium | A `contracts/*.json` file does not parse as JSON, leaving the request/result shape between agents undefined. |
| `C-CONN-NOCONTRACT` | hygiene | low | Connected agent(s) exist but no request/result contract file was found. |

## Pragmatic semantic rules

Cross-cutting checks that reason about Power Fx syntax, dialog branching, orchestration
mode, connector parameters, and connected-agent handoffs. Each carries an explicit
scope limit noted below — they are deliberately narrower than a first-draft version of
the same idea, to keep false positives low on real, working agents.

| Rule | Tier | Severity | Detects |
|---|---|---|---|
| `PFX-SAFETY` | hygiene (unrecognised function) / correctness (syntax) | low / medium | A `=` Power Fx expression either (a) uses a function name outside the known-common set — advisory only, since the set is a heuristic, not an exhaustive reference — or (b) has unbalanced brackets/quotes, checked deterministically with string-literal contents treated as opaque. |
| `DIALOG-DEADEND` | correctness | medium | A `ConditionGroup` where at least one branch redirects/ends cleanly (`RedirectDialog`/`BeginDialog`/`ReplaceDialog`/`EndDialog`/`CancelAllDialogs`/`conversationOutcome`) and at least one does not. Deliberately does **not** flag a group where every branch exits the same way, including a plain `SendActivity` — almost every topic legitimately ends that way, so a broader "every leaf needs an explicit exit" version was tried and rejected as too noisy. |
| `TRG-QUALITY` | correctness (generative) / hygiene (classic) | medium / low | Bifurcates on `generative_actions_enabled`: if generative, a tool/action's `modelDescription` is missing or under 15 characters; if classic, a non-system topic has 1-4 distinct trigger phrases (0 phrases is a separate, already-covered `L-UNREACHABLE`-adjacent case). Silent if the orchestration mode itself is unknown — it does not guess. |
| `ODATA-QUOTE` | hygiene | low | A `$`-prefixed parameter (`$filter`, `$orderby`, `$top`, ...) appears with more than one quoting style within the same topic or tool — a common copy-paste break. Flags the inconsistency only; cannot assert a single correct convention without the specific connector's documentation. |
| `SEC-AI-LEAK` | correctness | high | A variable name tokenizes (camelCase/PascalCase/snake_case aware, so `Patient` never matches `pat`) to a security keyword (`token`, `key`, `secret`, `password`, `pat`, `api`, `auth`, `credential`). Flagged on the variable's existence alone, not a speculative `aIVisibility` property whose schema is unverified. |
| `GUARDRAIL-GATE` | hygiene | low | A topic uses the `OnOutgoingMessage` system trigger, which does not fire as a maker-facing trigger in the conversational runtime. |
| `CONNECTED-AGENTS` | correctness | medium | A connected agent's description is under 30 characters, or (for a native `AgentDialog` specifically) its `beginDialog.kind` is not `OnToolSelected` — the mechanism observed in a real export for a parent orchestrator to select it. |

`PFX-SAFETY`, `DIALOG-DEADEND`, `TRG-QUALITY`, `ODATA-QUOTE`, `SEC-AI-LEAK`, and
`GUARDRAIL-GATE` populate the finding's optional `file` (always) and `line` (only where
cheaply derivable from raw text — currently just `PFX-SAFETY`'s syntax half) attributes.
Older rules (`L-*`/`A-*`/`C-*`/`G-*`/`Q-*`) do not yet carry `file`/`line`; retrofitting
them is a larger, separate change.

## Guardrail & instruction-quality signals (`G-*` / `Q-*`)

Full detail lives in `SKILL.md`'s "Guardrail & instruction-quality signals" section — this
is a quick index. Advisory by default; promoted to hard findings with `--guardrails-strict`.

| Rule | Tier if strict | Severity | Detects |
|---|---|---|---|
| `G-NOCONFIRM` | correctness | high | The agent can mutate state (a wired tool, a skill's referenced tools, or a connected agent's description contains a create/update/delete/action-shaped marker) but instructions have no confirmation/approval language. |
| `G-NOGROUNDING` | correctness | high | Instructions contain no anti-fabrication / grounding marker. |
| `Q-NOOUTPUT` | correctness | medium | Instructions define no output/format constraint. |
| `Q-NOSCOPE` | correctness | medium | Instructions state no scope limit or prohibition. |
| `Q-SKILL-NOSTRUCTURE` | hygiene | low | One finding listing every skill whose instructions (≥ 20 chars) have neither an output-format nor a scope/prohibition marker. |
| `Q-SKILL-NOGROUNDING` | hygiene | low | One finding listing every skill whose instructions (≥ 20 chars) have no grounding/anti-fabrication marker of their own, independent of whatever the main instructions state. |

`G-NOCONFIRM`'s mutating-capability check looks at wired tools, skills' referenced tools,
and connected agents' `references_mutating_ops` signal (see `references/EXPORT-FORMATS.md`)
— not just wired `McpTool`/`WorkflowTool` components, since a hybrid agent's mutating
capability can live entirely in a connected execution agent.

## What this does NOT check: semantic quality or hallucination risk

None of the above — including `G-NOGROUNDING` and `Q-SKILL-NOGROUNDING` — judge whether an
instruction is *well-written* or whether the agent *will* hallucinate. They detect the
structural *absence* of a grounding marker, which is durable and decidable from the export;
whether the prose that's present is good enough to actually prevent fabrication is a model
behaviour question that shifts with model updates, prompt engineering technique, and the
specific request — not something a static export scan can determine. That judgement belongs
to evaluation sets (`EvaluationSet` components — see `C-EVAL-NONE`/`C-EVAL-NOGRADER`) and
red-teaming, run against the live agent, not to this linter.

