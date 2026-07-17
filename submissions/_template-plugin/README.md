# Cowork plugin template

> **Heads up:** this README is contributor guidance for the template. If you keep
> a `README.md` in your own submission it **becomes the main content** on the
> gallery detail page — so replace this text with a human-facing overview of your
> plugin, or delete the file to fall back to the auto-generated page.

Copy this folder to `submissions/<your-slug>/` to submit a **Cowork plugin** — a
Microsoft 365 app package that bundles one or more skills (plus optional MCP
connectors) and runs **only** in Copilot Cowork.

See the
[Cowork plugin development guide](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development)
for how to build the package, and [`../legal-toolkit/`](../legal-toolkit) for a
complete working example.

## What to put here

```
submissions/<your-slug>/
├── metadata.json      # catalog sidecar (this file's sibling) — tweak or delete
│                      #  name/description; they fall back to the manifest
└── <your-plugin>.zip  # the pre-built M365 package (add this yourself)
```

The submission is auto-detected as a **plugin** (not a single skill) because the
`.zip` has a **root `manifest.json`** instead of a root `SKILL.md`. Do **not**
set `platforms` in `metadata.json` — the importer forces `["Cowork"]`.

## Required `.zip` contents

```
<your-plugin>.zip
├── manifest.json      # M365 app manifest, manifestVersion "devPreview" or "1.28"
├── color.png          # 192×192 color icon (must match icons.color in manifest)
├── outline.png        # 32×32 outline icon (must match icons.outline)
└── skills/
    └── <skill-name>/
        └── SKILL.md    # frontmatter `name` (kebab-case) must equal the folder
```

The manifest must be valid JSON with a GUID `id`, non-empty `name.short` and
`description.short`, `icons.color`/`icons.outline` pointing at the real PNGs of
the exact sizes above, and at least one `agentSkills` entry (or connector). Each
`agentSkills[].folder` must exist and contain a `SKILL.md` whose frontmatter
`name` is kebab-case and matches the folder name.

## Validate locally

```bash
npm run check:submissions    # thorough validation, writes nothing
npm run import:submissions    # generate the plugin page + published .zip
npm run build
```
