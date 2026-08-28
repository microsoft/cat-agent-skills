---
name: hol-guard
description: Use this skill when a user wants to install or configure HOL Guard, protect a supported local AI harness before tools execute, review HOL Guard approvals or receipts, or verify an agent plugin, skill, MCP server, or package with plugin-scanner.
---

# HOL Guard

Use the real HOL Guard commands for runtime protection and evidence. Do not replace Guard decisions with prompt-only checks.

## Guardrails

- Never read `.env` files.
- Never bypass a HOL Guard approval or turn a deny, review, or error result into an allowed tool call.
- Do not claim a harness is protected until a Guard command proves status.
- Prefer Guard-owned install and repair commands over manual harness config edits.
- Treat scanner findings as real until inspected.
- Preserve user changes and inspect `git status --short` before repository edits.

## Install and verify

First try Guard directly:

```bash
hol-guard status
hol-guard detect --json
```

If the executable is missing, prefer an isolated install and then rerun the checks:

```bash
pipx install hol-guard
hol-guard status
hol-guard detect --json
```

If `pipx` is unavailable, explain that an isolated CLI install is recommended instead of silently changing the user's Python environment.

## Protect a local harness

```bash
hol-guard bootstrap
hol-guard install <harness>
hol-guard run <harness> --dry-run
hol-guard run <harness>
hol-guard status
```

Supported harness targets include `codex`, `claude-code`, `copilot`, `cursor`, `gemini`, `hermes`, `openclaw`, `opencode`, and `antigravity`.

Useful aliases include `claude` for `claude-code`, `gemini-cli` for `gemini`, `open-code` for `opencode`, `open-claw` for `openclaw`, and `copilot-cli` for `copilot`.

For Hermes, use the harness-specific bootstrap when needed:

```bash
hol-guard hermes bootstrap
```

Verify a specific harness with:

```bash
hol-guard doctor <harness> --json
hol-guard diff <harness>
```

## Review blocked work

```bash
hol-guard approvals
hol-guard approvals open <request-id>
hol-guard receipts
hol-guard diff <harness>
```

For terminal-only decisions:

```bash
hol-guard approvals approve <request-id>
hol-guard approvals deny <request-id>
```

Only approve after reading the risk reason and understanding the requested scope.

## Capture evidence

```bash
hol-guard receipts
hol-guard inventory
hol-guard abom --format json
hol-guard events
hol-guard explain <artifact-id>
```

Cloud sync is optional and user-directed. Do not run `hol-guard connect` or any `hol-guard sync` command unless the user has explicitly asked for or confirmed Cloud pairing/sync. Before running either, explain that local protection works without Cloud and summarize the planned upload scope: Cloud receipt/decision-memory sync and redacted summaries where optional receipt sync applies. Then ask for confirmation.

```bash
hol-guard connect
hol-guard connect status
hol-guard sync
```

## Verify an agent package

`plugin-scanner` is a separate distribution. Try the tool directly first:

```bash
plugin-scanner --version
```

If the executable is missing, install it in isolation:

```bash
pipx install plugin-scanner
```

Then run both checks from the relevant package root:

```bash
plugin-scanner lint .
plugin-scanner verify .
```

Scan the relevant package root: the folder containing a Codex plugin or marketplace manifest, `.claude/` project surface, MCP server package, `SKILL.md`, or mixed agent configuration.

Useful diagnostics:

```bash
hol-guard doctor
hol-guard detect --json
hol-guard settings show
plugin-scanner verify . --json
```

## Report the result

Report the command that ran, what Guard found or changed, what remains blocked or risky, what receipt/diff/scanner evidence exists, and the exact next command when user action remains. Never claim protection, approval, or release readiness without command output proving it.
