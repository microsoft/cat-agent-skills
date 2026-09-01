# Import and normalization

## Existing OpenPlugin source

Microsoft 365 Agents Toolkit imports Claude and Cursor plugins:

```powershell
atk import openplugin `
  --path <staged-source> `
  --output <destination> `
  --website-url <https-url> `
  --privacy-url <https-url> `
  --terms-url <https-url>
```

Always copy the source to a temporary staging directory first.

## Pre-import checks

- A supported manifest exists in `.claude-plugin/plugin.json`,
  `.cursor-plugin/plugin.json`, or `.plugin/plugin.json`.
- `.mcp.json` is adjacent to the plugin manifest directory.
- Skills are under `skills/`.
- No secrets are present.

Some plugin manifests duplicate MCP servers in both `.mcp.json` and an inline
`mcpServers` object. Current `atk import openplugin` accepts only the string
override form in the plugin manifest. When `.mcp.json` is authoritative, remove
the duplicate inline object from the staging copy only.

## Post-import normalization

1. Inspect the generated `appPackage/manifest.json`.
2. Replace `devPreview` only when current Microsoft guidance and the intended
   deployment channel require a numbered schema.
3. Do not assume imported OAuth reference IDs are real. Imports can generate
   human-readable placeholders.
4. Capture authenticated MCP tools only after completing an authenticated
   `tools/list` handshake.
5. Add the required tool-description file for schema versions that require it.
6. Detect nested `SKILL.md` files. Convert non-registered design documents to
   `REFERENCE.md` or `CAPABILITY.md`, updating internal links.
7. Enforce companion-file limits. Consolidate thin references when necessary.
8. Preserve source content and compare hashes where filenames did not change.
9. Run the deterministic validator before packaging.

## Source preservation

Never:

- Edit or delete the supplied source package.
- Copy a secret into the destination.
- Report conversion complete while placeholder metadata remains.
- Fall back to fabricated MCP schemas when authentication blocks discovery.

If tool discovery cannot run, stop with a named authentication blocker and
produce only a non-deployable draft.
