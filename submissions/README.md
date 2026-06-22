# Submit a skill

**Every** skill is contributed by dropping a file in this `submissions/` folder
and opening a pull request — you never edit `src/content/skills/` by hand. On
each PR, CI validates your metadata and generates the published skill page (and
any download bundle) for you.

Choose whichever fits your skill:

## Option 1 — a single Markdown file

Best for instruction-only skills (no scripts).

Add `submissions/<slug>.md` with the metadata in its frontmatter:

```markdown
---
name: Meeting Summarizer
description: Turn a meeting transcript into concise notes and action items.
platforms: [Cowork, Copilot Studio]
tags: [meetings, productivity]
author: Your Name
authorUrl: https://example.com
---

You are the **Meeting Summarizer** skill. Write the agent instructions here…
```

See [`skill.template.md`](./skill.template.md).

## Option 2 — a zip (metadata kept in its own file)

Best when your skill ships scripts, or you'd rather keep metadata out of the
instructions file. Add `submissions/<slug>.zip` containing:

```
meeting-summarizer.zip
├── skill.md          # instructions only — no frontmatter needed
├── metadata.json     # OR metadata.yaml — all the metadata fields
└── scripts/          # optional helper files (bundled for download)
    └── summarize.py
```

`metadata.json` example:

```json
{
  "name": "Meeting Summarizer",
  "description": "Turn a meeting transcript into concise notes and action items.",
  "platforms": ["Cowork", "Copilot Studio"],
  "tags": ["meetings", "productivity"],
  "author": "Your Name",
  "authorUrl": "https://example.com"
}
```

See [`metadata.template.json`](./metadata.template.json). The same fields work in
a `metadata.yaml` if you prefer YAML.

> The `<slug>` is the file name without its extension (e.g.
> `meeting-summarizer.zip` → `/skills/meeting-summarizer`). Use lowercase,
> hyphenated names.

## Metadata fields

| Field         | Required | Notes                                                       |
| ------------- | -------- | ----------------------------------------------------------- |
| `name`        | ✅       | Display name.                                               |
| `description` | ✅       | One-line summary.                                           |
| `platforms`   | ✅       | One or more of `Cowork`, `Copilot Studio`, `Scout`.         |
| `tags`        | ✅       | Lowercase tags for search/filtering.                        |
| `author`      |          | Person or team.                                             |
| `authorUrl`   |          | Link to the author's website/profile.                       |
| `version`     |          | Semantic version, e.g. `1.0.0`.                             |
| `createdAt`   |          | `YYYY-MM-DD`.                                               |
| `updatedAt`   |          | `YYYY-MM-DD`.                                               |
| `bundle`      |          | Set automatically by the pipeline — do not add it yourself. |

A missing or invalid **required** field fails the PR with a message listing
exactly what's wrong.

## Try it locally before opening a PR

```bash
npm run check:submissions    # validate metadata only, write nothing
npm run import:submissions   # generate the skill page(s) + bundle(s)
npm run build                # confirm the site builds
```
