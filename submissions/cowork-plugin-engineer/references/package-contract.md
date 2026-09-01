# Cowork plugin package contract

Check current Microsoft Learn documentation before changing version-specific
behavior. The baseline below follows the numbered Microsoft 365 app manifest
v1.28 guidance verified while this skill was created.

## Upload package

```text
plugin.zip
|-- manifest.json
|-- color.png
|-- outline.png
|-- tools/
|   `-- connector-tools.json
`-- skills/
    `-- skill-name/
        |-- SKILL.md
        |-- references/
        `-- scripts/
```

The ZIP must not contain a wrapper directory.

## Manifest invariants

- `$schema` and `manifestVersion` identify the same numbered schema.
- `id` is a stable GUID and does not change across releases.
- `version` is a three-part semantic version and increases for each update.
- Developer website, privacy, and terms URLs use HTTPS. Prefer the same domain.
- Short and full names and descriptions satisfy schema length limits.
- `color.png` is 192x192.
- `outline.png` is 32x32, white and transparent.
- At least one `agentSkills` or `agentConnectors` entry exists.

## Skill invariants

- At most 20 registered skills.
- Every `agentSkills[].folder` resolves inside the package.
- The registered folder has a root `SKILL.md`.
- Frontmatter contains exactly one `name` and one `description`.
- `name` is lowercase kebab-case and equals the folder leaf.
- Do not nest other files named `SKILL.md` under a registered skill. Cowork can
  interpret them as additional skills and reject the package.
- A skill has no more than 20 companion files, each no larger than 5 MB and no
  more than 10 MB combined.
- Use `references/` for deep guidance and `scripts/` for deterministic helpers.

## Connector invariants

- Connector IDs are unique.
- Remote MCP URLs use HTTPS and Streamable HTTP.
- Do not invent tool descriptions. Capture them from MCP `tools/list`.
- Every remote connector includes `mcpToolDescription.file`.
- The tool-description path is package-relative. Both `tools/file.json` and
  `./tools/file.json` resolve within the package root.
- The tool-description file exists in the ZIP and contains unique tool names,
  descriptions, and JSON input schemas.
- `None` has no `referenceId`.
- `OAuthPluginVault` has the generated OAuth client registration ID, never a
  human-readable placeholder.
- Dynamic Client Registration is represented by omitting `authorization`, not
  by declaring a `DynamicClientRegistration` authorization type.
- API key authentication is not treated as deployable unless current Cowork
  documentation explicitly supports it.

## Acceptance gate

The package is complete only when:

1. `Test-CoworkPlugin.ps1` passes.
2. `atk package` succeeds.
3. `atk validate --package-file` succeeds.
4. ZIP inspection confirms all manifest references are present at the root.
5. Authentication prerequisites are complete or the output is explicitly
   labeled a non-deployable draft.

For a ZIP supplied without its source project, run
`scripts/Test-CoworkPluginPackage.ps1`. It rejects unsafe archive paths and
wrapper directories before extraction, applies the same deep package checks,
and runs Agents Toolkit validation.
