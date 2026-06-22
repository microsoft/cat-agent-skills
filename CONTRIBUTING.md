# Contributing a skill

Thanks for helping grow the **CAT Agent Skills** gallery! A *skill* is a reusable
instruction set for an AI agent — targeting one or more of **Cowork**,
**Copilot Studio**, and **Scout** — published here as a Markdown page plus an
optional `.zip` of helper scripts.

There are **two ways** to contribute. Both open a pull request; both are
validated automatically.

## Option A — Submit a zip (recommended)

Best when your skill ships scripts, or you'd rather not hand-edit the site.

1. Assemble a folder containing:
   - **`SKILL.md`** — the front page: YAML frontmatter (metadata) + your
     instructions. Start from
     [`submissions/SKILL.template.md`](submissions/SKILL.template.md).
   - Any optional helper files (`scripts/`, schemas, a `README.md`).
2. Zip it so `SKILL.md` is at the **root** of the archive.
3. Name the zip after your slug, e.g. `meeting-summarizer.zip`, and place it in
   [`submissions/`](submissions/).
4. (Optional) Validate locally before pushing:
   ```bash
   npm run check:submissions   # metadata-only, writes nothing
   ```
5. Open a PR. CI extracts `SKILL.md` → `src/content/skills/<slug>.md`, bundles
   the rest → `public/bundles/<slug>.zip`, and **commits the result back to your
   PR**. If required metadata is missing, the check **fails** and tells you
   exactly which fields to fix.

See [`submissions/README.md`](submissions/README.md) for the exact zip layout.

## Option B — Add a Markdown file directly

Best for instruction-only skills with no scripts.

1. Create `src/content/skills/<slug>.md` (the filename becomes the URL slug).
2. Fill in the frontmatter and instructions — see
   [`docs/authoring-skills.md`](docs/authoring-skills.md).
3. (Optional) ship scripts by placing `public/bundles/<slug>.zip` and adding
   `bundle: bundles/<slug>.zip` to the frontmatter.
4. Open a PR.

## Required metadata

Every skill **must** include these frontmatter fields, or the build fails:

| Field         | Type     | Notes                                               |
| ------------- | -------- | --------------------------------------------------- |
| `name`        | string   | Display name.                                       |
| `description` | string   | One-line summary.                                   |
| `platforms`   | string[] | One or more of `Cowork`, `Copilot Studio`, `Scout`. |
| `tags`        | string[] | Lowercase tags for search/filtering.                |

Optional: `author`, `version`, `createdAt`, `updatedAt`, `coverColor`,
`featured`. (`bundle` is set automatically by the zip pipeline.)

## Preview locally

```bash
npm install
npm run dev      # http://localhost:4321/cat-agent-skills
npm run build    # runs the same content validation as CI
```

## What CI checks

- **PRs** run [`.github/workflows/ci.yml`](.github/workflows/ci.yml): it imports
  any submission zips, validates all skill metadata (hard fail with an itemized
  message), and builds the site.
- Merges to `main` deploy the site to GitHub Pages.

By contributing you agree your skill is shared under the repository's
[MIT license](LICENSE).
