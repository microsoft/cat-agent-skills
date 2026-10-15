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
Package entries must use ZIP Store or Deflate compression; other compression
methods are rejected before extraction.
Package paths reject Windows reserved device-name segments such as `NUL`,
`CON`, `CONIN$`, `CONOUT$`, `PRN`, `AUX`, `COM1`, and `LPT1`, including
superscript aliases, names with extensions, and spaces before extensions.
Manifest, tool-description JSON, and registered root `SKILL.md` files are read
with a 5 MB per-file safety limit during local validation.

## Manifest invariants

- `$schema` is the canonical Microsoft HTTPS schema URL for the supported
  `v1.28`/`1.28` or `vDevPreview`/`devPreview` manifest version.
- `id` is a stable GUID and does not change across releases.
- `version` is a three-part semantic version and increases for each update.
- Developer website, privacy, and terms URLs use HTTPS. Prefer the same domain.
- Short name is at most 30 characters, full name at most 100, short
  description at most 80, and full description at most 4000.
- `color.png` is 192x192.
- Both icons must decode successfully. The local decoder supports
  non-interlaced PNGs only; re-export interlaced icons without interlacing
  before validation. This is a local decoder limitation, not a host requirement.
- `outline.png` is 32x32 and its decoded pixels contain both transparent and
  visible regions. Every visible pixel is white; file format or alpha-channel
  presence alone is not sufficient.
- At least one `agentSkills` or `agentConnectors` entry exists.

## Skill invariants

- At most 20 registered skills.
- Every `agentSkills[].folder` resolves inside the package.
- Symbolic links are rejected throughout the package source tree so referenced
  or companion files cannot escape the package root.
- The registered folder has a root `SKILL.md`.
- Frontmatter contains exactly one `name` and one `description`.
- `name` is lowercase kebab-case and equals the folder leaf.
- Do not nest other files named `SKILL.md` under a registered skill. Cowork can
  interpret them as additional skills and reject the package.
- A skill has no more than 20 companion files, each no larger than 5 MB and no
  more than 10 MB combined.
- Use `references/` for deep guidance and `scripts/` for deterministic helpers.

## Connector invariants

- At most 10 connectors.
- Connector IDs are unique.
- Remote MCP URLs use HTTPS and Streamable HTTP.
- Do not invent tool descriptions. Capture them from MCP `tools/list`.
- Every v1.28 remote connector includes `mcpToolDescription.file`.
- A `devPreview` connector may omit `mcpToolDescription` for dynamic tool
  discovery. Draft evaluation generation still requires a static description.
- The tool-description path is package-relative. Both `tools/file.json` and
  `./tools/file.json` resolve within the package root.
- The tool-description file exists in the ZIP and contains unique tool names,
  descriptions, and JSON input schemas.
- Tool names, descriptions, titles, and schemas contain no template
  placeholders; capture real metadata from MCP `tools/list`.
- Each tool's `inputSchema` is an object with `type: "object"`. If present,
  `properties` is a mapping of schemas and `required` is an array of unique
  strings. These are local structural checks, not complete JSON Schema
  meta-validation or proof that inputs will work against the server.
- `None` has no `referenceId`.
- `OAuthPluginVault` has the generated OAuth client registration ID, never a
  human-readable placeholder or surrounding whitespace, and the ID does not
  exceed 128 characters.
- Cowork-managed Dynamic Client Registration can omit `authorization`.
  An explicit schema-valid `DynamicClientRegistration` object instead requires
  a non-placeholder `referenceId`.
- `ApiKeyPluginVault` is schema-valid but is not treated as deployable while
  current Cowork guidance says API key authentication is unavailable.

## Acceptance gate

The package is complete only when:

1. `test_cowork_plugin.py` passes.
2. `atk package` succeeds.
3. `atk validate --package-file` succeeds.
4. Safe ZIP extraction and deep validation of the packaged manifest, icons,
   skills, connectors, and tool descriptions succeeds.
5. Authentication prerequisites are complete or the output is explicitly
   labeled a non-deployable draft.

For a ZIP supplied without its source project, run
`scripts/test_cowork_plugin_package.py`. It rejects unsafe archive paths and
wrapper directories before extraction, rebuilds a sanitized archive from the
validated files, applies the same deep package checks, and runs Agents Toolkit
validation only against that sanitized archive.

`--skip-toolkit-validation` is for local diagnostics when Toolkit execution is
unavailable. It reports `LocalChecksOnly` and is never a deployable-package
acceptance result.
