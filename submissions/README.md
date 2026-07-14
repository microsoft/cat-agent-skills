# Submit a skill

**Every** skill is contributed by adding it to this `submissions/` folder and
opening a pull request — you never edit `src/content/skills/` by hand. On each
PR, CI validates your metadata and generates the published skill page (and any
download bundle) for you.

Every submission is a **`submissions/<slug>/` folder** containing a
`metadata.json` gallery sidecar plus **exactly one** skill payload, in one of
two shapes:

```
submissions/<slug>/
├── metadata.json     # OR metadata.yaml — catalog details for this gallery
│                     # (a SIDECAR — never packaged into the download bundle)
└── EITHER an unpacked canonical Agent Skill…
    ├── SKILL.md      # frontmatter (name + agent description) + instructions
    ├── scripts/      # optional executable code
    ├── references/   # optional docs the agent reads on demand
    └── assets/       # optional templates / data files
    …OR a single pre-packaged bundle:
    └── <name>.zip    # a canonical Agent Skill (root SKILL.md + files)
```

The `<slug>` is the folder name — use lowercase, hyphenated names, e.g.
`submissions/meeting-summarizer/` -> `/skills/meeting-summarizer`. Start by
copying [`_template/`](./_template).

Bundling is **verbatim** — whatever you put in `scripts/`/`references/`/`assets/`
(or inside your `.zip`) ships exactly as authored. Only `metadata.*` is stripped;
it is a sidecar and never lands inside the bundle.

## Two descriptions — they are different on purpose

| | Lives in | Who reads it |
| --- | --- | --- |
| **Agent description** | `SKILL.md` frontmatter `description` | the **agent/model**, to decide *when to invoke* the skill |
| **Catalog description** | `metadata.json` `description` | **people** browsing this gallery (card + top of the detail page) |

Write the agent description as a precise trigger ("Use this skill whenever the
user… BEFORE calling…"). Write the catalog description as a friendly one-liner.

## `SKILL.md` — name + description + instructions

The canonical Agent Skills file: frontmatter with a slug `name` (lowercase,
hyphenated, **matching the folder name**) and the **agent-facing** `description`,
then the instructions body. All three are required.

```markdown
---
name: meeting-summarizer
description: Use this skill whenever the user asks to summarize a meeting transcript, before drafting any reply.
---

Turn the transcript into concise notes and action items…
```

The human-friendly **display name** lives in `metadata.json` (`name`), not here.

## `metadata.json` — catalog details

All the catalog details for the gallery (kept out of the agent file):

```json
{
  "name": "Meeting Summarizer",
  "description": "Turn a meeting transcript into concise notes and action items.",
  "platforms": ["Cowork", "Copilot Studio"],
  "tags": ["meetings", "productivity"],
  "author": "Your Name",
  "authorUrl": "https://example.com",
  "version": "1.0.0",
  "createdAt": "2026-01-01",
  "updatedAt": "2026-01-01"
}
```

The same fields work in a `metadata.yaml` if you prefer YAML.

## Metadata fields

| Field         | Where           | Required | Notes                                                        |
| ------------- | --------------- | -------- | ------------------------------------------------------------ |
| `name`        | `SKILL.md`      | yes      | Slug (lowercase-hyphenated), must match the folder name.     |
| `description` | `SKILL.md`      | yes      | **Agent-facing** trigger description.                        |
| `name`        | `metadata.json` | yes      | **Display** name shown in the gallery.                       |
| `description` | `metadata.json` | yes      | **Catalog** summary shown in the gallery.                    |
| `platforms`   | `metadata.json` | yes      | One or more of `Cowork`, `Copilot Studio`, `Scout`.          |
| `tags`        | `metadata.json` | yes      | Lowercase tags for search/filtering.                         |
| `author`      | `metadata.json` |          | Person or team.                                              |
| `authorUrl`   | `metadata.json` |          | Link to the author's website/profile.                        |
| `version`     | `metadata.json` |          | Semantic version, e.g. `1.0.0`.                              |
| `createdAt`   | `metadata.json` |          | `YYYY-MM-DD`.                                                |
| `updatedAt`   | `metadata.json` |          | `YYYY-MM-DD`.                                                |
| `coverColor`  | `metadata.json` |          | CSS color to override the auto-generated cover.              |
| `featured`    | `metadata.json` |          | `true` to sort the skill to the top.                         |
| `bundle`      | —               |          | Set automatically when your skill ships files beyond `SKILL.md` — don't add it.|

A missing or invalid **required** field fails the PR with a message listing
exactly what's wrong.

## Cowork plugins (advanced)

Besides single cross-platform skills, the gallery also hosts **Cowork plugins** —
Microsoft 365 app packages that bundle one or more skills (plus optional MCP
connectors) and run **only** in Copilot Cowork. See the
[Cowork plugin development guide](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development).

A plugin submission is a `submissions/<slug>/` folder with a `metadata.json`
sidecar plus a **single pre-built `.zip` M365 package**. It's auto-detected as a
plugin (rather than a single skill) because the `.zip` has a **root
`manifest.json`** instead of a root `SKILL.md`:

```
submissions/<slug>/
├── metadata.json         # catalog sidecar (name/description/tags optional —
│                         #  they fall back to the manifest)
└── <name>.zip
    ├── manifest.json     # M365 app manifest (manifestVersion "devPreview" or "1.28")
    ├── color.png         # 192×192 color icon (referenced by the manifest)
    ├── outline.png       # 32×32 outline icon (referenced by the manifest)
    └── skills/
        ├── <skill-a>/
        │   └── SKILL.md  # frontmatter name must match the folder name
        └── <skill-b>/
            └── SKILL.md
```

The importer forces `platforms: ["Cowork"]` and `type: "plugin"`, publishes the
`.zip` verbatim as the download package, and synthesizes the detail page
(overview, the skills it contains, any connectors, and install steps). Plugins
show a **Plugin** badge on their card and are filterable on the homepage.

Validation is thorough and will fail the PR with an itemized list if anything is
off: the manifest must be valid JSON with a `manifestVersion` of `"devPreview"`
or `"1.28"` (real-world plugins and Microsoft's conversion script emit
`"devPreview"`; the docs reference `"1.28"`), a GUID `id`,
non-empty `name.short`/`description.short`, and `icons.color`/`icons.outline`
that reference real PNGs of the exact required dimensions; there must be at least
one `agentSkills` entry (or connector); and every `agentSkills[].folder` must
exist with a `SKILL.md` whose frontmatter `name` is kebab-case and matches the
folder. See [`legal-toolkit/`](./legal-toolkit) for a complete example, and copy
[`_template-plugin/`](./_template-plugin) to start.

## Updating an existing skill

Same path: edit the files in your `submissions/<slug>/` folder (or replace the
`<name>.zip` payload) and open a PR. The slug is the identity — same slug updates
the existing skill, a new slug creates a new one.

## Try it locally before opening a PR

```bash
npm run check:submissions    # validate metadata only, write nothing
npm run import:submissions   # generate the skill page(s) + bundle(s)
npm run build                # confirm the site builds
```
