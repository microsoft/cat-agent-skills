---
name: cowork-plugin-engineer
description: Use this skill whenever a user asks to create, import, repair, authenticate, package, validate, sideload, evaluate, upgrade, or troubleshoot a Microsoft Copilot Cowork plugin containing Agent Skills or remote Model Context Protocol (MCP) connectors.
---

# Copilot Cowork Plugin Engineer

Build upload-ready Cowork plugins with deterministic validation. Treat the
Microsoft 365 app package, its authentication configuration, and its deployment
as separate gates.

## Mandatory workflow

1. Read [package-contract.md](references/package-contract.md).
2. Search current Microsoft Learn documentation before choosing a manifest
   version or making rollout, preview, authentication, or licensing claims.
   For a manifest baseline upgrade, follow
   [manifest-upgrade-instructions.md](assets/manifest-upgrade-instructions.md).
3. Inspect the source without modifying it. Detect:
   - Native Microsoft 365 app package
   - Claude, Cursor, or Agent Plugin package
   - Skills-only folder
   - Existing Agents Toolkit project
4. Choose the workflow:
   - New project: use `scripts/New-CoworkPluginProject.ps1`.
   - Open plugin import: follow
     [import-and-normalization.md](references/import-and-normalization.md).
   - Existing project: validate before editing.
   - Existing ZIP: use `scripts/Test-CoworkPluginPackage.ps1`; never extract
     an untrusted archive without its path and expansion safeguards.
5. If an MCP connector is present:
   - Discover tools through `initialize`, `notifications/initialized`, and
     `tools/list`; never invent tool names or schemas.
   - Read [authentication.md](references/authentication.md).
   - Reject unresolved OAuth placeholders before producing a deployable ZIP.
6. Run `scripts/Test-CoworkPlugin.ps1`.
7. Build through `scripts/Build-CoworkPlugin.ps1`. This uses Microsoft 365
   Agents Toolkit (`atk`) for both packaging and package validation.
8. Inspect the final ZIP and return its exact path.
9. When evaluations are requested, read
   [evaluations.md](references/evaluations.md) and use
   `scripts/New-CoworkPluginEvals.ps1`. Treat generated cases as drafts until
   every placeholder has an approved expected response.
10. Sideload or deploy only when the user explicitly asks. Keep tenant-wide
   deployment approval-gated.

## Non-negotiable gates

- Never modify an imported source tree; import from a temporary staging copy.
- Never call a package deployable while OAuth `referenceId` contains a
  placeholder.
- Never place secrets, tokens, client secrets, or API keys in a manifest,
  skill, script, or ZIP.
- A registered skill folder contains exactly one root `SKILL.md`. Nested
  companion documents must use another filename such as `REFERENCE.md` or
  `CAPABILITY.md`.
- Skill frontmatter `name` must be lowercase kebab-case and match its folder.
- `manifest.json` and all referenced assets must be at the ZIP root.
- Preserve the manifest application ID across upgrades and increment the
  package version.
- Do not use raw `Compress-Archive` as the final acceptance gate.
- Do not fabricate a successful MCP connection from package validation;
  authentication and allowed-client configuration must also succeed.

## Standard commands

```powershell
# Validate a project without building.
pwsh -File .\scripts\Test-CoworkPlugin.ps1 -ProjectPath <project>

# Validate an existing ZIP without trusting its contents.
pwsh -File .\scripts\Test-CoworkPluginPackage.ps1 -PackagePath <package.zip>

# Insert the Teams Developer Portal OAuth client registration ID.
pwsh -File .\scripts\Set-CoworkOAuthReference.ps1 `
  -ProjectPath <project> `
  -ConnectorId <connector-id> `
  -OAuthConfigurationId <generated-id>

# Build and validate the upload package.
pwsh -File .\scripts\Build-CoworkPlugin.ps1 -ProjectPath <project>

# Generate a draft behavioral evaluation suite.
pwsh -File .\scripts\New-CoworkPluginEvals.ps1 -ProjectPath <project>
```

## Troubleshooting

Read [troubleshooting.md](references/troubleshooting.md) and map the observed
HTTP status, endpoint, and response body to a specific layer:

1. Package/manifest
2. OAuth configuration lookup
3. User sign-in or consent
4. MCP allowed-client policy
5. MCP protocol handshake
6. Tool invocation

Do not repeatedly retry configuration errors.

## Dynamic Microsoft documentation

| Topic | Search |
|---|---|
| Current Cowork package schema | `microsoft_docs_search(query="Build plugins for Copilot Cowork manifest validation rules")` |
| Connector authentication | `microsoft_docs_search(query="Cowork MCP OAuthPluginVault authentication configuration")` |
| Agents Toolkit commands | `microsoft_docs_search(query="Microsoft 365 Agents Toolkit CLI import openplugin package validate")` |
| Dataverse MCP setup | `microsoft_docs_search(query="Dataverse MCP remote endpoint allowed clients Entra app")` |
| Evaluation dataset schema | `microsoft_docs_search(query="Microsoft 365 Copilot Agent Evaluations CLI dataset schema test design")` |

If Learn MCP tools are unavailable, use:

| MCP tool | CLI equivalent |
|---|---|
| `microsoft_docs_search` | `npx @microsoft/learn-cli search "<query>"` |
| `microsoft_docs_fetch` | `npx @microsoft/learn-cli fetch "<url>"` |
| `microsoft_code_sample_search` | `npx @microsoft/learn-cli code-search "<query>" --language <language>` |

## References

- [Package contract](references/package-contract.md)
- [Authentication](references/authentication.md)
- [Import and normalization](references/import-and-normalization.md)
- [Evaluation design](references/evaluations.md)
- [Troubleshooting](references/troubleshooting.md)
