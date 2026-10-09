# Export Formats and Parsing Notes

Technical reference for exactly what `ingest_agent.py` recognises, what it only counts,
and the format variance it tolerates. `SKILL.md` covers the user-facing behaviour; this
file is the detail behind it.

## Accepted inputs

- A Copilot Studio solution `.zip`
- An unzipped solution directory, including the `botcomponents/` layout used by current
  exports (detected by the presence of a `botcomponents` folder anywhere under the given
  path, at any depth — a hybrid export's `botcomponents/` does not need to be at the root)
- A directory of loose topic YAML files
- A single topic/agent YAML file

## `botcomponents/<component>/data` dispatch by `kind:`

| `kind:` value | Parsed as | Notes |
|---|---|---|
| `AdaptiveDialog` | Classic topic | Trigger phrases, node count, variable set/read, slot-filling and interruption handling, system-topic detection, Power Fx scan, `ConditionGroup` branch-termination scan, OData quoting scan, `OnOutgoingMessage` detection. |
| `InlineAgentSkill` | Agentic skill | Description, instructions, referenced tools. Tolerant of format variance (see below). |
| `McpTool` / `WorkflowTool` / `TaskDialog` | Tool binding | `allowedTools`, `connectionReference` (nested under `action.connectionReference` for `TaskDialog`), `connectorId`, `workflowId`, input count, `modelDescription` length (`TaskDialog`), OData quoting scan. |
| `EvaluationSet` | Evaluation set | Grader kinds and count. |
| `KnowledgeSourceConfiguration` | Knowledge source | Source kind and a short detail (site/url/dataset/etc). |
| `AgentDialog` | Connected/child agent | See "Connected agents: AgentDialog vs. markdown" below. |
| `MultiTurnEvaluationCase` | Counted only | Rolled up into `agent.evaluation_case_count`, not linted individually. |
| `GptComponentMetadata` | Main-instructions candidate | See "Main instructions" below. |
| Anything else (e.g. `TaskDialog`'s parent component types not yet seen) | Counted only | Recorded in `agent.other_components` and surfaced as a warning; not linted. |

Agent-level config (`bot.xml`, `configuration.json`) lives under `bots/<name>/`, not
`botcomponents/`, and is read separately.

## Connected agents: AgentDialog vs. markdown

A connected/child agent can appear two ways in an export: a native `AgentDialog`
component, or a modernization-layer `connected-agents/*.md` file. Both were observed
together in one real export, describing what is plausibly the same underlying agent
under different names ("Agent" vs "Dynamics 365 PO Execution Agent") — there is no
shared identifier to reliably match one to the other.

`AgentDialog` is treated as the primary source of truth: whenever at least one native
`AgentDialog` was parsed, `connected-agents/*.md` files are skipped entirely rather than
risking one real connected agent being double-counted as two. Each `connected_agents`
entry carries `source_kind` (`"AgentDialog"` or `"markdown"`) so this is inspectable.
An `AgentDialog`'s description is read from a top-level `modelDescription` field (matching
`TaskDialog`'s shape) or, if absent, `beginDialog.description` (what a real export has
actually shown); its `beginDialog.kind` is recorded as `has_on_tool_selected_trigger` for
`CONNECTED-AGENTS` to check against `OnToolSelected`.

## Main instructions: source priority

Read from whichever of these the export actually carries, in this order — a later source
only wins if an earlier one produced nothing:

1. `configuration.json`'s embedded `agentSettings.instructions.segments[].value`
2. A `GptComponentMetadata` component's own `instructions:` field — some exports point at
   one via `configuration.json`'s `gPTSettings.defaultSchemaName` instead of embedding
   instructions directly in step 1
3. A modernization-layer `parent-agent/instructions.md` or `*instructions.md` file

Only length, a `source_file` label, guardrail/quality signals (booleans), and referenced
tool names are ever kept — the instruction text itself is never stored, matching the
privacy guarantee in `SKILL.md`.

## System-topic recognition

A topic name is treated as platform-managed (and excluded from the noise-prone classic
checks) if, once lowercased with spaces/underscores stripped, it contains any of:
`fallback`, `escalate`, `escalation`, `greeting`, `goodbye`, `startover`,
`endofconversation`, `signin`, `resetconversation`, `multipletopicsmatched`,
`conversationstart`, `onerror`, `conversationalboosting`, `thankyou`, `signout`.

Note: the platform's "Search" system topic (an `OnUnknownIntent` / low-priority
`SearchAndSummarizeContent` topic) surfaces in exports under the display name
"Conversational boosting" (from the component's `<name>` in `botcomponent.xml`), not
literally "Search" — that's why the keyword list has `conversationalboosting` and not
`search`. The display name is what gets matched, not the component's schemaname suffix.

## Modernization layer (hybrid/modernized exports)

Read from anywhere under the given path (not restricted to a fixed depth):

- `parent-agent/*.md` or any `*instructions.md` — main-instructions fallback (see above)
- `connected-agents/*.md` — one entry per file; `# Title` heading (or filename) becomes the
  name, backticked tokens become `referenced_tools`, and the text is scanned for mutating-
  operation language (`create`, `update`, `delete`, `write`, `post`, `invoke_action`,
  `cancel`, `confirm`, `modify`, `remove`, `set_`) to set `references_mutating_ops` — this
  is what lets `G-NOCONFIRM` see mutating capability that lives entirely in a connected
  agent, with no `McpTool`/`WorkflowTool`/skill in the export to otherwise carry the signal.
- `contracts/*.json` — one entry per file; `valid_json` records whether it parses.

An export with a `botcomponents/` folder still gets its modernization layer read (both are
walked from the same extraction root), which is how a hybrid export — all-system-topics
plus a generative core — is detected as `hybrid` rather than `classic`.

## Format-variance tolerance (agentic skills)

`InlineAgentSkill` parsing is deliberately defensive, because export authors vary these
independently of the underlying defect:

- Description may live in YAML frontmatter (`---\nname: …\ndescription: …\n---`) or as a
  top-level `description`/`summary` field on the component.
- A YAML double-quoted description (required whenever the value contains `": "`) has its
  quote delimiters stripped, the same as the `name` field.
- Section headers are matched case-insensitively and tolerate `Tool`/`Tools`/
  `Available Tools` and `Instruction`/`Instructions`.
- Tool names may be backticked or plain list items (`- toolName (read)`).
- Text may carry HTML entities (`&amp;`) and CRLF line endings; both are normalised before
  any matching happens.

## Zip safety caps

A `.zip` is untrusted input. Before any bytes are extracted:

- Entries beyond `MAX_ZIP_ENTRIES` (5,000) refuse the whole archive.
- A declared total uncompressed size beyond `MAX_ZIP_UNCOMPRESSED_BYTES` (200 MB) refuses
  the whole archive.
- Any entry that would resolve outside the extraction root (zip-slip: absolute paths,
  `../` traversal) is skipped individually.

All three are reported in `parse_report` (`unreadable` for the first two, since nothing was
extracted; `warnings` for zip-slip, since the rest of the archive still was) rather than
raising, so a hostile or malformed upload degrades gracefully instead of crashing the
ingest step or exhausting memory/disk.
