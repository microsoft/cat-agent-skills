# Skill submissions (zip)

Drop a single self-contained **`<slug>.zip`** in this folder to contribute a
skill without hand-editing the site. On every pull request, CI runs the import
pipeline (`npm run import:submissions`), which:

1. Finds each new/changed `submissions/*.zip`.
2. Reads the front-page **`SKILL.md`** inside it (your instructions + metadata).
3. **Validates the metadata** — a missing or invalid required field fails the PR
   with a message listing exactly what's wrong.
4. Writes `src/content/skills/<slug>.md`.
5. Bundles any remaining files (scripts, schemas, README) into
   `public/bundles/<slug>.zip` and links it from the skill page.

The `<slug>` is the zip filename without `.zip` (e.g. `meeting-summarizer.zip`
→ `/skills/meeting-summarizer`). Use lowercase, hyphenated names.

## Required zip layout

```
meeting-summarizer.zip
├── SKILL.md            # required: front page (frontmatter metadata + instructions)
├── README.md           # optional: goes into the downloadable bundle
└── scripts/            # optional: helper scripts, schemas, etc. (bundled)
    └── summarize.py
```

- `SKILL.md` **must** sit at the root of the zip.
- Everything other than `SKILL.md` is packaged into the downloadable bundle.
- If the zip contains only `SKILL.md`, no bundle is produced.

## Required metadata (frontmatter in `SKILL.md`)

| Field         | Required | Notes                                                        |
| ------------- | -------- | ------------------------------------------------------------ |
| `name`        | ✅       | Display name.                                                |
| `description` | ✅       | One-line summary.                                            |
| `platforms`   | ✅       | One or more of `Cowork`, `Copilot Studio`, `Scout`.          |
| `tags`        | ✅       | Lowercase tags for search/filtering.                         |
| `author`      |          | Person or team.                                              |
| `version`     |          | Semantic version, e.g. `1.0.0`.                              |
| `createdAt`   |          | `YYYY-MM-DD`.                                                |
| `updatedAt`   |          | `YYYY-MM-DD`.                                                |
| `bundle`      |          | Set automatically by the pipeline — do not add it yourself.  |

See [`SKILL.template.md`](./SKILL.template.md) for a starting point and
[`../docs/authoring-skills.md`](../docs/authoring-skills.md) for full guidance.

## Try it locally before opening a PR

```bash
npm run check:submissions   # validate metadata only, write nothing
npm run import:submissions   # actually extract into the site
npm run build                # confirm the site builds with your skill
```
