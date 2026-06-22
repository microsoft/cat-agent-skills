# Authoring a skill

A **skill** is a reusable instruction set for an AI agent — targeting one or more
of **Cowork**, **Copilot Studio**, and **Scout** — published in this gallery
with an optional `.zip` of helper scripts.

You contribute every skill the same way: **drop a file in the
[`../submissions/`](../submissions/) folder and open a PR.** CI validates the
metadata and generates the published page (and any download bundle); you never
edit `src/content/skills/` by hand.

## 1. Pick a submission shape

### A single Markdown file — `submissions/<slug>.md`

Best for instruction-only skills. Metadata goes in the frontmatter, instructions
in the body:

```markdown
---
name: Meeting Summarizer
description: Turn a meeting transcript into concise notes and action items.
platforms: [Cowork, Copilot Studio]
tags: [meetings, productivity]
author: Your Name
authorUrl: https://example.com
---

You are the **Meeting Summarizer** skill. Write the instructions here…
```

Start from [`../submissions/skill.template.md`](../submissions/skill.template.md).

### A zip — `submissions/<slug>.zip`

Best when your skill ships scripts, or you'd rather keep metadata **out** of the
instructions file:

```
meeting-summarizer.zip
├── skill.md          # instructions only — no frontmatter needed
├── metadata.json     # OR metadata.yaml — all the metadata fields
└── scripts/          # optional helper files (bundled for download)
    └── summarize.py
```

Start from
[`../submissions/metadata.template.json`](../submissions/metadata.template.json).
Anything other than `skill.md`/`metadata.*` is packaged into the downloadable
bundle, and the detail page shows a **Download bundle** button.

The `<slug>` is the file name without its extension, e.g.
`meeting-summarizer.zip` → `/skills/meeting-summarizer`.

## 2. Metadata fields

| Field         | Required | Type       | Description                                                            |
| ------------- | -------- | ---------- | ---------------------------------------------------------------------- |
| `name`        | ✅       | string     | Display name shown on the card and detail page.                        |
| `description` | ✅       | string     | One-line summary used on the card and as the page meta description.    |
| `platforms`   | ✅       | string[]   | One or more of `Cowork`, `Copilot Studio`, `Scout`.                    |
| `tags`        | ✅       | string[]   | Lowercase tags for filtering/search. Reuse existing tags where you can.|
| `author`      |          | string     | Person or team credited for the skill.                                 |
| `authorUrl`   |          | string     | URL to the author's website/profile; renders the author name as a link.|
| `version`     |          | string     | Semantic version, e.g. `1.0.0`.                                        |
| `createdAt`   |          | date       | `YYYY-MM-DD` when the skill was first published.                       |
| `updatedAt`   |          | date       | `YYYY-MM-DD` of the latest update.                                     |
| `coverColor`  |          | string     | CSS color to override the auto-generated cover gradient.               |
| `featured`    |          | boolean    | `true` to sort the skill to the top of the gallery.                    |

(`bundle` is set automatically by the pipeline — don't add it yourself.)

A missing or invalid **required** field fails the PR with a message listing
exactly what's wrong.

## 3. Write the instructions

The instructions are agent-facing guidance in Markdown — headings, lists, and
tables are supported. A good structure:

- **When to use this skill** — what triggers it.
- **Instructions** — numbered, concrete steps.
- **Guardrails** — what the agent must not do.
- **Tone** — the voice the agent should adopt.

If you bundle scripts, mention them in the instructions and include a `README.md`
in the zip explaining requirements and usage.

## 4. Preview locally

```bash
npm run check:submissions    # validate metadata only, write nothing
npm run import:submissions   # generate the skill page(s) + bundle(s)
npm run dev                  # open the site and confirm your skill looks right
```

## 5. Open a pull request

Submit a PR with your file in `submissions/`. CI validates the metadata,
generates the skill page, and (for same-repo PRs) commits the generated files
back to your branch. Once merged to `main`, the site redeploys automatically.
