# Contributing a skill

Thanks for helping grow the **CAT Agent Skills** gallery! A *skill* is a reusable
instruction set for an AI agent — targeting one or more of **Cowork**,
**Copilot Studio**, and **Scout** — published here with optional helper
`scripts/`, `references/`, and `assets/`.

You contribute by adding **one submission to the [`submissions/`](submissions/)
folder** and opening a pull request. You never edit `src/content/skills/`
directly — CI validates your metadata and generates the published page (and any
download bundle) for you.

## The submission shape

Every submission is a `submissions/<slug>/` folder: a `metadata.json` sidecar, an
optional `README.md`, and **exactly one** payload. This section covers the common
payload — a **skill**, as an **unpacked** folder. Scout submissions can instead
ship a single automation `.json` (covered just below). `.zip` payloads are **no
longer accepted** — submit your skill unpacked.

```
submissions/<slug>/
├── metadata.json     # OR metadata.yaml — catalog details (sidecar, not bundled)
├── README.md         # optional — becomes the page's main content (not bundled)
└── an unpacked canonical Agent Skill:
    ├── SKILL.md      # frontmatter (name + agent description) + instructions
    ├── scripts/      # optional executable code
    ├── references/   # optional docs
    └── assets/       # optional templates / data files
```

Copy [`submissions/_template/`](submissions/_template) to get started. The
`<slug>` is the folder name (lowercase, hyphenated), e.g.
`meeting-summarizer` → `/skills/meeting-summarizer`. See
[`submissions/README.md`](submissions/README.md) for the full reference.

> **A submission holds two kinds of files: agent-facing and human-facing.**
> Everything **agent-facing** is bundled into the download **verbatim** — the
> bundle *is* the skill the agent loads — so keep it to `SKILL.md`, `scripts/`,
> `references/`, and `assets/`. The two **human-facing** files are **never
> bundled**: the `metadata.json` sidecar and an optional
> [`README.md`](#what-visitors-see). Don't leave other docs (CHANGELOG, personal
> notes) next to your payload — they'd ship to the agent and waste its context;
> put those in your pull request description instead.

### Cowork plugins (no longer accepted)

Cowork **plugin** packages — an M365 app `.zip` with a root `manifest.json`
bundling one or more skills (plus optional MCP connectors) — are **no longer
accepted** as new submissions, because the gallery no longer takes `.zip`
payloads. Existing plugin submissions stay published.

### Scout automations

You can also submit a **Scout automation** — a scheduled/triggered `.json`
(a schedule plus an ordered list of prompt steps) that runs **only** in Scout.
An automation submission is a `submissions/<slug>/` folder with a `metadata.json`
sidecar plus a single `.json` automation export; the fact that the one
non-sidecar top-level file is a `.json` (instead of a `SKILL.md`) marks it as an
automation. The `.json` is published verbatim as the download and re-imports
directly into Scout. Copy
[`submissions/_template-automation/`](submissions/_template-automation) to start
and see the
[Scout automations section](submissions/README.md#scout-automations-advanced) of
the submissions reference for the required shape and validation rules.

### Scout automation installers (no longer accepted)

Scout automation **installers** — a `.zip` you download, unzip, and follow to
set an automation up — are **no longer accepted** as new submissions, because
the gallery no longer takes `.zip` payloads. Submit a Scout automation as a
single importable `.json` (above) instead. Existing installer submissions stay
published.

## What visitors see

The `SKILL.md` frontmatter `description` is written for the **agent** — it's the
trigger the model reads to decide when to invoke your skill, and nobody browsing
the gallery ever sees it. People see two things you write for **them**:

- The **catalog description** (`metadata.json`'s `description`) — the one-liner on
  your gallery card.
- Your optional **`README.md`** — drop one in the submission folder (any entry
  type) and it becomes the main content on the detail page, in your own voice.
  Without it, the page shows the `SKILL.md` instructions instead.

## `SKILL.md`

The canonical Agent Skills file — frontmatter `name` (a slug matching the folder)
+ agent `description`, then the instructions body. All three are required:

```markdown
---
name: meeting-summarizer
description: Use this skill whenever the user asks to summarize a meeting transcript, before drafting a reply.
---

Turn the transcript into concise notes and action items…
```

## `metadata.json`

The catalog details, kept out of the agent file (a sidecar — never packaged into
the download bundle):

| Field         | Required | Notes                                               |
| ------------- | -------- | --------------------------------------------------- |
| `name`        | yes      | Display name shown in the gallery.                  |
| `description` | yes      | Catalog summary shown in the gallery.               |
| `platforms`   | yes      | One or more of `Cowork`, `Copilot Studio`, `Scout`. |
| `tags`        | yes      | Lowercase tags for search/filtering.                |
| `author`      | yes      | Person or team who wrote the skill.                 |

Optional: `authorUrl`, `authorGithub`, `version`, `createdAt`, `updatedAt`,
`coverColor`, `featured`. (`bundle` is set automatically when your skill ships
files beyond `SKILL.md`. `authorGithub` — the author's GitHub login — is
normally derived from an `authorUrl` that points to a GitHub profile
(`https://github.com/<login>`); the *skillbot* uses it to @-mention the author
on the first comment of the skill's discussion. Set it explicitly only when your
only link isn't a GitHub profile, e.g. LinkedIn.)

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
   your skill ships files beyond `SKILL.md`) and commits them back to your PR
   branch (same-repo PRs).
3. Builds the site.

Merges to `main` deploy to GitHub Pages.

By contributing you agree your skill is shared under the repository's
[MIT license](LICENSE).
