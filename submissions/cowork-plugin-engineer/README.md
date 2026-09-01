# Copilot Cowork Plugin Engineer

Build and maintain Microsoft Copilot Cowork plugins with a repeatable,
validation-first workflow. This Agent Skill combines practical guidance,
versioned templates, and PowerShell automation to reduce mistakes across
plugin structure, Model Context Protocol (MCP) connectors, OAuth, packaging,
evaluation design, and manifest upgrades.

This submission is an unpacked **Agent Skill**, not a Cowork plugin package.
Use it to create and validate plugin packages in your own workspace.

## Capabilities

- Scaffold a Cowork plugin project with the Microsoft 365 app-package layout.
- Import and normalize existing Claude Code or Cursor plugins.
- Support skills-only, connector-only, and combined package designs.
- Guide OAuth registration and reject unresolved authentication placeholders.
- Validate manifests, icons, skills, connectors, MCP tool descriptions, and
  package limits.
- Safely inspect an existing plugin ZIP without trusting or manually extracting
  its contents.
- Package and validate plugins with Microsoft 365 Agents Toolkit.
- Generate draft `evals.json` suites for skill routing, instruction following,
  MCP tool usage, safety, and regression coverage.
- Diagnose upload failures, connector retry loops, OAuth lookup failures, and
  MCP handshake or tool-execution problems.
- Apply a controlled upgrade process when Microsoft releases a new Cowork
  manifest version.

## Before you start

The guidance is useful in any Agent Skills host. To execute the included
automation, the host or development machine needs:

- PowerShell 7 or later.
- Node.js and `npx`.
- Network access when Microsoft 365 Agents Toolkit validation is requested.
- A local plugin project or plugin ZIP for validation.

Authenticated MCP connectors can also require a Microsoft Entra application,
Teams Developer Portal OAuth configuration, user or administrator consent, and
server-side allowed-client configuration.

## Example requests

- "Create a skills-plus-MCP Cowork plugin from this existing Claude plugin."
- "Validate this Cowork plugin ZIP and explain every failure."
- "Generate a behavioral evaluation suite for this plugin."
- "Fix the OAuth retry loop in this connector."
- "Upgrade this plugin engineering project to the newest Cowork-supported
  manifest by following the included upgrade instructions."

## Included automation

| Script | Purpose |
|---|---|
| `New-CoworkPluginProject.ps1` | Scaffold a new plugin project. |
| `Test-CoworkPlugin.ps1` | Apply deep project and package checks. |
| `Test-CoworkPluginPackage.ps1` | Safely validate a supplied ZIP. |
| `Set-CoworkOAuthReference.ps1` | Set an OAuth registration ID and increment the package version. |
| `Build-CoworkPlugin.ps1` | Package and validate with Agents Toolkit. |
| `New-CoworkPluginEvals.ps1` | Generate a draft Microsoft 365 Copilot evaluation dataset. |

## Good to know

- Generated evaluation cases are drafts. Replace every `[REPLACE: ...]` value
  with an approved prompt and expected response before running them.
- The skill creates evaluation suites but does not run evaluations.
- Package validation does not prove that OAuth consent, server policy, or MCP
  runtime behavior is working. Those remain separate deployment gates.
- Current templates are versioned. Follow
  `assets/manifest-upgrade-instructions.md` rather than blindly changing the
  manifest version when a new schema appears.
- Never put client secrets, access tokens, refresh tokens, cookies, or
  authorization codes in a plugin package or evaluation file.
