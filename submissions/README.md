# Submit a skill

**Every** skill is contributed by adding it to this `submissions/` folder and
opening a pull request — you never edit `src/content/skills/` by hand. On each
PR, CI validates your metadata and generates the published skill page (and any
download bundle) for you.

Every submission has the **same shape**, whether you add it as a folder or as a
zip of that same folder:

```
submissions/<slug>/            (or submissions/<slug>.zip containing the same)
├── skill.md          # the agent skill: frontmatter (name + agent description) + instructions
├── metadata.json     # OR metadata.yaml — catalog details for this gallery
└── scripts/          # optional helper files (packaged into a download bundle)
    └── do-thing.py
```

The `<slug>` is the folder (or zip) name — use lowercase, hyphenated names, e.g.
`submissions/meeting-summarizer/` -> `/skills/meeting-summarizer`. Start by
copying [`_template/`](./_template).

## Two descriptions — they are different on purpose

| | Lives in | Who reads it |
| --- | --- | --- |
| **Agent description** | `skill.md` frontmatter `description` | the **agent/model**, to decide *when to invoke* the skill |
| **Catalog description** | `metadata.json` `description` | **people** browsing this gallery (card + top of the detail page) |

Write the agent description as a precise trigger ("Use this skill whenever the
user… BEFORE calling…"). Write the catalog description as a friendly one-liner.

## `skill.md` — name + description + instructions

The canonical Agent Skills file: frontmatter with the display `name` and the
**agent-facing** `description`, then the instructions body. All three are
required.

```markdown
---
name: Meeting Summarizer
description: Use this skill whenever the user asks to summarize a meeting transcript, before drafting any reply.
---

Turn the transcript into concise notes and action items…
```

## `metadata.json` — catalog details

All the catalog details for the gallery (kept out of the agent file):

```json
{
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
| `name`        | `skill.md`      | yes      | Display name.                                                |
| `description` | `skill.md`      | yes      | **Agent-facing** trigger description.                        |
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
| `bundle`      | —               |          | Set automatically when you include `scripts/` — don't add it.|

A missing or invalid **required** field fails the PR with a message listing
exactly what's wrong.

## Updating an existing skill

Same path: edit the files in your `submissions/<slug>/` folder (or replace the
`<slug>.zip`) and open a PR. The slug is the identity — same slug updates the
existing skill, a new slug creates a new one.

## Try it locally before opening a PR

```bash
npm run check:submissions    # validate metadata only, write nothing
npm run import:submissions   # generate the skill page(s) + bundle(s)
npm run build                # confirm the site builds
```
