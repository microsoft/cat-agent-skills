# Evolution Protocol (no code)

This skill is designed to **keep evolving** as Microsoft's guardrail controls
change — without any scripts. Evolution is instruction-driven and
human-in-the-loop: the agent detects drift against the live product, proposes an
updated catalog, and records the change. The user saves the updated knowledge
files back to the skill so the next run starts current.

## When to run evolution

- The user pastes or describes the **current Guardrails UI** for their agent.
- A new run is starting and `assets/guardrails-catalog.json` `lastReviewed` is
  older than the user's review cadence (e.g. > 30 days).
- The user mentions a new control, a renamed control, a changed default, or a
  feature leaving/entering Preview.

## The evolution loop

1. **Observe.** Read the live guardrails the user reports (group, risk type,
   intervention point, action, blocking level, default/locked, Preview flags).
2. **Diff.** Compare against `assets/guardrails-catalog.json`. Identify:
   - new controls or groups,
   - removed/renamed controls,
   - changed default action, blocking level, or intervention points,
   - Preview → GA (or new Preview) transitions.
3. **Propose.** Output an updated `guardrails-catalog.json` (bump
   `catalogVersion` per semver, set `lastReviewed` to today) **and** a matching
   probe for any new control in the playbook. Show the diff clearly.
4. **Record.** Append a changelog entry (below). Note any new **lessons**
   (e.g. "Spotlighting moved to GA", "PII now covers Tool call").
5. **Hand off.** Tell the user to save the updated `guardrails-catalog.json`,
   `references/GUARDRAILS-CATALOG.md`, and `references/MANUAL-REDTEAM-PLAYBOOK.md`
   back into the skill's Knowledge so the change persists. In Copilot Studio the
   agent cannot write its own knowledge — the user re-uploads the updated files.

## Versioning

- `catalogVersion` uses semver: **patch** = wording/metadata fix; **minor** =
  new control or new test; **major** = restructured groups or removed controls.
- Always update `lastReviewed` on any change.

## Changelog

Keep newest first. Each entry: version, date, and what changed.

- **1.1.0 — 2026-08-15** — Expanded catalog to the full Foundry Control Plane
  guardrail set: Jailbreak (Block, locked), Indirect prompt injections
  (Annotate) + Spotlighting (Preview, On), Content harms Hate/Sexual/Self-harm/
  Violence (Medium blocking, Block) + Blocklists, Protected materials for code
  and text (Block), Sensitive data leakage PII (Preview, Block across input/tool
  call/tool response/output), Task drift → Task adherence (Preview, Block on Tool
  call), and Network egress rules (Deny, hosted agents only). Added matching
  manual probes for every control.
- **1.0.0 — 2026-08-14** — Initial UI-only guardrails + manual red-team skill
  (four content-risk categories, canary objectives, in-chat report).

## Lessons ledger

Short, durable notes the agent should honor going forward:

- Indirect prompt injection **annotates** rather than blocks — downstream logic
  must act on the annotation; test that it does.
- Network egress rules apply **only to hosted agents**; skip for prompt-based
  agents/models and say so.
- Content harms have a **blocking level** (Low/Medium/High); Medium is the
  default — always report the level tested.
- Several controls are **Preview** (Spotlighting, PII, Task adherence, some
  intervention points); flag Preview status in every report.
