# Contributing a skill

Thanks for helping grow the **CAT Agent Skills** gallery! A *skill* is a reusable
instruction set for an AI agent — targeting one or more of **Cowork**,
**Copilot Studio**, and **Scout** — published here with an optional `.zip` of
helper scripts.

You contribute by dropping **one file in the [`submissions/`](submissions/)
folder** and opening a pull request. You never edit `src/content/skills/`
directly — CI validates your metadata and generates the published page (and any
download bundle) for you.

## Two ways to submit

### 1. A single Markdown file — `submissions/<slug>.md`

Best for instruction-only skills. Put the metadata in the frontmatter and the
instructions in the body. Start from
[`submissions/skill.template.md`](submissions/skill.template.md).

### 2. A zip — `submissions/<slug>.zip`

Best when your skill ships scripts, or you'd rather keep metadata **out** of the
instructions file. The zip contains:

- `skill.md` — the instructions (no frontmatter needed),
- `metadata.json` **or** `metadata.yaml` — all the metadata fields
  (start from [`submissions/metadata.template.json`](submissions/metadata.template.json)),
- optional scripts / other files, which become a downloadable bundle.

The `<slug>` is the file name without its extension (e.g.
`meeting-summarizer.zip` → `/skills/meeting-summarizer`). Use lowercase,
hyphenated names. See [`submissions/README.md`](submissions/README.md) for the
exact layouts.

## Required metadata

Whether it lives in a `.md` frontmatter or a `metadata.json`/`metadata.yaml`,
every skill **must** include these fields or the PR fails:

| Field         | Type     | Notes                                               |
| ------------- | -------- | --------------------------------------------------- |
| `name`        | string   | Display name.                                       |
| `description` | string   | One-line summary.                                   |
| `platforms`   | string[] | One or more of `Cowork`, `Copilot Studio`, `Scout`. |
| `tags`        | string[] | Lowercase tags for search/filtering.                |

Optional: `author`, `authorUrl`, `version`, `createdAt`, `updatedAt`,
`coverColor`, `featured`. (`bundle` is set automatically by the pipeline.)

## Validate locally

```bash
npm install
npm run check:submissions   # validate metadata only, writes nothing
npm run import:submissions   # generate the skill page(s) + bundle(s)
npm run dev                  # preview at http://localhost:4321/cat-agent-skills
npm run build                # runs the same content validation as CI
```

## What CI does

On a pull request, [`.github/workflows/ci.yml`](.github/workflows/ci.yml):

1. Imports your submission, **hard-failing** with an itemized message if any
   required metadata is missing or invalid.
2. Generates `src/content/skills/<slug>.md` (and `public/bundles/<slug>.zip` for
   zips) and commits them back to your PR branch (same-repo PRs).
3. Builds the site.

Merges to `main` deploy to GitHub Pages.

By contributing you agree your skill is shared under the repository's
[MIT license](LICENSE).
