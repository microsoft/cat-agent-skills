# Authoring a skill

A **skill** is a reusable instruction set for an AI agent — targeting one or more
of **Cowork**, **Copilot Studio**, and **Scout** — published in this gallery as a
single Markdown file (optionally accompanied by a `.zip` of helper scripts).

## 1. Create the Markdown file

Add a file at `src/content/skills/<slug>.md`. The file name (without `.md`)
becomes the skill's URL slug, e.g. `meeting-summarizer.md` →
`/skills/meeting-summarizer`.

### Frontmatter fields

| Field         | Required | Type       | Description                                                            |
| ------------- | -------- | ---------- | ---------------------------------------------------------------------- |
| `name`        | ✅       | string     | Display name shown on the card and detail page.                        |
| `description` | ✅       | string     | One-line summary used on the card and as the page meta description.    |
| `platforms`   | ✅       | string[]   | One or more of `Cowork`, `Copilot Studio`, `Scout` — the agent platforms the skill targets. |
| `tags`        | ✅       | string[]   | Lowercase tags for filtering/search. Reuse existing tags where you can.|
| `author`      |          | string     | Person or team credited for the skill.                                 |
| `version`     |          | string     | Semantic version, e.g. `1.0.0`.                                        |
| `createdAt`   |          | date       | `YYYY-MM-DD` when the skill was first published.                       |
| `updatedAt`   |          | date       | `YYYY-MM-DD` of the latest update.                                     |
| `bundle`      |          | string     | Path under `public/` to a `.zip` of scripts (see below).               |
| `coverColor`  |          | string     | CSS color to override the auto-generated cover gradient.               |
| `featured`    |          | boolean    | `true` to sort the skill to the top of the gallery.                    |

### Body = instructions

Everything after the frontmatter is the skill's **instructions**, rendered as
the "Instructions" section on the detail page. Write clear, agent-facing
guidance in Markdown — headings, lists, and tables are supported.

A good structure:

- **When to use this skill** — what triggers it.
- **Instructions** — numbered, concrete steps.
- **Guardrails** — what the agent must not do.
- **Tone** — the voice the agent should adopt.

## 2. (Optional) Bundle scripts in a `.zip`

If your skill ships executable helpers (scripts, schemas, config), bundle them:

1. Put your files in a `.zip` and place it at `public/bundles/<slug>.zip`.
2. Reference it in frontmatter: `bundle: bundles/<slug>.zip`.
3. Include a `README.md` **inside** the zip explaining requirements and usage.
4. Mention the bundled scripts in your instructions so the agent knows how to
   use them.

The detail page will automatically show a **Download scripts (.zip)** button,
and the card/cover will display a `.zip` badge.

## 3. Preview locally

```bash
npm run dev
```

Open the site, confirm your skill appears in the gallery, the cover looks good,
search/tags find it, and both downloads work.

## 4. Open a pull request

Submit a PR with your new `.md` (and any `.zip`). The GitHub Pages deploy runs
automatically when the PR is merged to `main`.
