# Cowork manifest baseline upgrade instructions

Use this procedure when Microsoft releases a new numbered Microsoft 365 app
manifest version that is supported by Copilot Cowork.

## Required inputs

Before editing, identify:

- The current manifest version.
- The target manifest version.
- The official target JSON schema URL.
- The target version's release, migration, and Cowork host-support guidance.
- The minimum Microsoft 365 Agents Toolkit version that supports the target.

Do not infer General Availability (GA), preview status, host support, or
licensing. Verify these claims against current official Microsoft sources.

## Upgrade workflow

### 1. Verify Cowork support

Confirm that the target is supported by Cowork, not merely published as a
preview schema. Review:

- Required, added, renamed, and removed properties.
- Changes to `agentSkills` and `agentConnectors`.
- Model Context Protocol (MCP) tool-description and discovery requirements.
- Authentication changes.
- Package validation and Microsoft 365 App Store requirements.
- Minimum Agents Toolkit version.

Stop if Cowork support cannot be verified.

### 2. Preserve the existing template

Add a versioned template instead of overwriting the current one:

```powershell
Copy-Item `
  .\assets\manifest.v<CURRENT>.template.json `
  .\assets\manifest.v<TARGET>.template.json
```

In the new template, update both:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v<TARGET>/MicrosoftTeams.schema.json",
  "manifestVersion": "<TARGET>"
}
```

Apply all verified schema changes. Do not assume that changing these two values
alone constitutes an upgrade.

### 3. Update project scaffolding

Update `scripts\New-CoworkPluginProject.ps1` to select the target template.
Prefer adding or maintaining a `-ManifestVersion` parameter that maps supported
versions to their corresponding templates. Retain older templates while their
manifest versions remain supported.

### 4. Update version-specific validation

Review every manifest-version condition in:

```text
scripts\Test-CoworkPlugin.ps1
scripts\Test-CoworkPluginPackage.ps1
```

Add rules required by the target schema. Preserve rules for older supported
versions. Replace isolated equality checks with an explicit version-policy map
when multiple versions are supported.

Pay particular attention to:

- Schema and `manifestVersion` agreement.
- Allowed root properties.
- Skill registration and limits.
- Connector definitions.
- `mcpToolDescription` requirements.
- Authentication types and `referenceId` behavior.
- Referenced files and ZIP-root structure.

### 5. Update the Agents Toolkit baseline only when required

Review the default `AtkVersion` in:

```text
scripts\Build-CoworkPlugin.ps1
scripts\Test-CoworkPluginPackage.ps1
```

Update the pinned version only after confirming that it supports the target
manifest. Keep the version pinned for deterministic builds.

### 6. Update documentation

Review and update:

```text
SKILL.md
README.md
references\package-contract.md
references\import-and-normalization.md
references\troubleshooting.md
assets\manifest-upgrade-instructions.md
```

Document version-specific behavior instead of presenting it as universal.

### 7. Validate representative fixtures

Exercise all relevant package shapes:

- Skills only.
- Connector only.
- Skills plus connectors.
- Anonymous connector.
- OAuth connector.
- Static MCP tool descriptions.
- Dynamic tool discovery, when supported.
- Existing ZIP validation.
- Evaluation-suite generation.

Run:

```powershell
pwsh -File .\scripts\Test-CoworkPlugin.ps1 `
  -ProjectPath <fixture>

pwsh -File .\scripts\Build-CoworkPlugin.ps1 `
  -ProjectPath <fixture> `
  -AtkVersion <VERIFIED-TOOLKIT-VERSION>

pwsh -File .\scripts\Test-CoworkPluginPackage.ps1 `
  -PackagePath <fixture.zip> `
  -AtkVersion <VERIFIED-TOOLKIT-VERSION>

pwsh -File .\scripts\New-CoworkPluginEvals.ps1 `
  -ProjectPath <fixture> `
  -Force
```

The upgrade is complete only when the custom validators pass, Agents Toolkit
packaging succeeds, all Toolkit validation rules pass, and generated ZIPs have
the expected root structure.

### 8. Release the updated skill

When this skill is embedded in a Cowork plugin:

1. Copy the updated skill directory into the plugin repository.
2. Preserve the skill folder name and `agentSkills` registration.
3. Increment the parent plugin manifest version.
4. Rebuild and validate the parent plugin ZIP.

## Suggested Copilot CLI request

Open this project and use:

> Upgrade the Cowork plugin engineering skill from manifest version
> `<CURRENT>` to `<TARGET>`. Follow
> `assets\manifest-upgrade-instructions.md`. Verify current Microsoft
> documentation for Cowork support, rollout status, schema changes, and the
> minimum Agents Toolkit version before editing. Preserve support for older
> manifest versions where practical, update the scripts and documentation,
> and validate representative skills-only and connector fixtures.

## Completion report

Report:

- Verified target manifest and Cowork support status.
- Authoritative sources used.
- Schema and behavior changes found.
- Files changed.
- Agents Toolkit version used.
- Fixture and package-validation results.
- Compatibility retained or intentionally dropped.
- Assumptions and confidence level.
