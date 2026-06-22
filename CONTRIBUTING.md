# Contributing a skill

Thanks for helping grow the **CAT Agent Skills** gallery! A *skill* is a reusable
instruction set for an AI agent — targeting one or more of **Cowork**,
**Copilot Studio**, and **Scout** — published here with an optional `.zip` of
helper scripts.

You contribute by adding **one submission to the [`submissions/`](submissions/)
folder** and opening a pull request. You never edit `src/content/skills/`
directly — CI validates your metadata and generates the published page (and any
download bundle) for you.

## The submission shape

Every submission is the same, whether you add it as a folder or a zip of that
folder:

```
submissions/<slug>/            (or submissions/<slug>.zip containing the same)
├── skill.md          # the agent skill: frontmatter (name + agent description) + instructions
├── metadata.json     # OR metadata.yaml — catalog details for this gallery
└── scripts/          # optional helper files (packaged into a download bundle)
```

Copy [`submissions/_template/`](submissions/_template) to get started. The
`<slug>` is the folder/zip name (lowercase, hyphenated), e.g.
`meeting-summarizer` → `/skills/meeting-summarizer`. See
[`submissions/README.md`](submissions/README.md) for the full reference.

## Two descriptions

A skill carries **two** descriptions, on purpose:

- **Agent description** — `skill.md`'s frontmatter `description`. The model reads
  this to decide *when to invoke* the skill (write it as a precise trigger).
- **Catalog description** — `metadata.json`'s `description`. The friendly
  one-liner shown to people in the gallery.

## `skill.md`

The canonical Agent Skills file — frontmatter `name` + agent `description`, then
the instructions body. All three are required:

```markdown
---
name: Meeting Summarizer
description: Use this skill whenever the user asks to summarize a meeting transcript, before drafting a reply.
---

Turn the transcript into concise notes and action items…
```

## `metadata.json`

The catalog details, kept out of the agent file:

| Field         | Required | Notes                                               |
| ------------- | -------- | --------------------------------------------------- |
| `description` | yes      | Catalog summary shown in the gallery.               |
| `platforms`   | yes      | One or more of `Cowork`, `Copilot Studio`, `Scout`. |
| `tags`        | yes      | Lowercase tags for search/filtering.                |

Optional: `author`, `authorUrl`, `version`, `createdAt`, `updatedAt`,
`coverColor`, `featured`. (`bundle` is set automatically when you include
`scripts/`.)

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
2. Generates `src/content/skills/<slug>.md` (and `public/bundles/<slug>.zip` when
   you include scripts) and commits them back to your PR branch (same-repo PRs).
3. Builds the site.

Merges to `main` deploy to GitHub Pages.

By contributing you agree your skill is shared under the repository's
[MIT license](LICENSE).
