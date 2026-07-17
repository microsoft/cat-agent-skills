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

Every submission is a `submissions/<slug>/` folder with a `metadata.json` gallery
sidecar plus **exactly one** skill payload — either an unpacked skill or a
pre-packaged zip:

```
submissions/<slug>/
├── metadata.json     # OR metadata.yaml — catalog details (sidecar, not bundled)
└── EITHER an unpacked canonical Agent Skill…
    ├── SKILL.md      # frontmatter (name + agent description) + instructions
    ├── scripts/      # optional executable code
    ├── references/   # optional docs
    └── assets/       # optional templates / data files
    …OR a single pre-packaged bundle:
    └── <name>.zip    # a canonical Agent Skill (root SKILL.md + files)
```

Copy [`submissions/_template/`](submissions/_template) to get started. The
`<slug>` is the folder name (lowercase, hyphenated), e.g.
`meeting-summarizer` → `/skills/meeting-summarizer`. See
[`submissions/README.md`](submissions/README.md) for the full reference.

> **Everything except `metadata.*` is bundled into the agent-facing `.zip`,
> verbatim.** The download bundle *is* the skill the agent loads, so it must
> contain **only agent-facing files** (`SKILL.md`, `scripts/`, `references/`,
> `assets/`). **Do not include a `README.md` or any other human-facing file**
> (CONTRIBUTING, CHANGELOG, docs written for people, etc.) in your submission
> folder — it will be packaged into the bundle and waste the agent's context.
> Put contributor notes in your pull request description instead. Only
> `metadata.json`/`metadata.yaml` is stripped out as a sidecar.

### Cowork plugins

You can also submit a **Cowork plugin** — a Microsoft 365 app package that
bundles one or more skills (plus optional MCP connectors) and runs **only** in
Copilot Cowork. A plugin submission is a `submissions/<slug>/` folder with a
`metadata.json` sidecar plus a single pre-built `.zip` whose **root
`manifest.json`** (instead of a root `SKILL.md`) marks it as a plugin. Copy
[`submissions/_template-plugin/`](submissions/_template-plugin) to start and see
the [Cowork plugins section](submissions/README.md#cowork-plugins-advanced) of
the submissions reference for the required package contents and validation
rules.

### Scout automations

You can also submit a **Scout automation** — a scheduled/triggered `.json`
(a schedule plus an ordered list of prompt steps) that runs **only** in Scout.
An automation submission is a `submissions/<slug>/` folder with a `metadata.json`
sidecar plus a single `.json` automation export; the fact that the one
non-sidecar top-level file is a `.json` (instead of a `.zip` or a `SKILL.md`)
marks it as an automation. The `.json` is published verbatim as the download and
re-imports directly into Scout. Copy
[`submissions/_template-automation/`](submissions/_template-automation) to start
and see the
[Scout automations section](submissions/README.md#scout-automations-advanced) of
the submissions reference for the required shape and validation rules.

### Scout automation installers

Some automations aren't a directly-importable `.json` but an **installer**: a
`.zip` you download, unzip, and follow to set the automation up (for example, an
agent reads the instructions, gathers your settings, and calls
`m_create_automation`). Submit one as a `submissions/<slug>/` folder with a
`metadata.json` sidecar plus a single `.zip` containing an **`INSTALL.md`**
(the install procedure + the automation prompt) and one or more **JSON config
files** the automation consumes. It's auto-detected as an automation installer
because the `.zip` holds an `INSTALL.md` + JSON (and no root `SKILL.md` or
`manifest.json`). The `.zip` is published **verbatim** and offered as a `.zip`
download; the detail page renders your `INSTALL.md`. Validation is minimal —
just that the `INSTALL.md` and at least one JSON file are present (the config
JSON is **not** schema-checked). Copy
[`submissions/_template-automation-installer/`](submissions/_template-automation-installer)
to start and see the
[Scout automation installers section](submissions/README.md#scout-automation-installers-advanced)
of the submissions reference.

## Two descriptions

A skill carries **two** descriptions, on purpose:

- **Agent description** — `SKILL.md`'s frontmatter `description`. The model reads
  this to decide *when to invoke* the skill (write it as a precise trigger).
- **Catalog description** — `metadata.json`'s `description`. The friendly
  one-liner shown to people in the gallery.

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

Optional: `author`, `authorUrl`, `version`, `createdAt`, `updatedAt`,
`coverColor`, `featured`. (`bundle` is set automatically when your skill ships
files beyond `SKILL.md`. `authorGithub` — your GitHub login as the PR
submitter — is also filled in automatically by CI so the *skillbot* can
@-mention you on the first comment of your skill's discussion; don't set it
yourself.)

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
