# Cowork plugin evaluation design

Use evaluations to test behavior after package validation succeeds. Package
validation proves that files and schemas are valid; it does not prove that a
skill triggers correctly or that a connector returns the right result.

## Generate a draft suite

```powershell
pwsh -File .\scripts\New-CoworkPluginEvals.ps1 `
  -ProjectPath <project-path>
```

The script writes `evals/evals.json` using Microsoft 365 Copilot evaluation
schema v1.6.0. It creates:

- A discovery, positive workflow, and negative routing case for each skill.
- A tool-usage case for every statically described MCP tool.
- A connector-level case when dynamic tool discovery provides no static list.
- A confirmation-oriented safety case.
- Relevance and Coherence as default evaluators.

## Mandatory author review

Generated cases are drafts. Replace every `[REPLACE: ...]` value before using
the suite. Derive expected responses from approved business rules, deterministic
test data, and the behavior required by the skill. Never fabricate expected
records or connector results.

Cover these categories:

| Category | What to test |
|---|---|
| `skill-discovery` | The capability is described accurately. |
| `instruction-following` | The skill performs its primary workflow. |
| `skill-routing` | It triggers when appropriate and stays inactive otherwise. |
| `tool-usage` | The correct MCP tool is selected and errors are explained. |
| `safety` | Write or externally visible actions require confirmation. |
| `regression` | Previously fixed behavior remains fixed. |

Use stable `testId` values so results can be compared across plugin versions.
Add realistic edge cases, unavailable-record cases, permission failures, and
multi-turn workflows when the scenario requires conversation state.

This skill creates suites but does not run them.

## Current documentation

- [Dataset schema and test design](https://learn.microsoft.com/microsoft-365/copilot/extensibility/evaluations-cli-create-tests)
- [Agent Evaluations CLI quickstart](https://learn.microsoft.com/microsoft-365/copilot/extensibility/evaluations-cli-quickstart)
