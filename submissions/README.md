# Submit a skill

**Every** skill is contributed by adding it to this `submissions/` folder and
opening a pull request — you never edit `src/content/skills/` by hand. On each
PR, CI validates your metadata and generates the published skill page (and any
download bundle) for you.

Every submission is a **`submissions/<slug>/` folder** containing a
`metadata.json` gallery sidecar plus **exactly one** payload — an **unpacked**
canonical Agent Skill (or, for Scout, a single automation `.json`; see below):

```
submissions/<slug>/
├── metadata.json     # OR metadata.yaml — catalog details for this gallery
│                     # (a SIDECAR — never packaged into the download bundle)
├── README.md         # OPTIONAL — human-facing overview shown on the detail page
│                     # (never bundled, never seen by the agent)
└── an unpacked canonical Agent Skill:
    ├── SKILL.md      # frontmatter (name + agent description) + instructions
    ├── scripts/      # optional executable code
    ├── references/   # optional docs the agent reads on demand
    └── assets/       # optional templates / data files
```

`.zip` payloads are **no longer accepted** — submit your skill unpacked. (Scout
submissions can instead be a single automation `.json`; see below.)

The `<slug>` is the folder name — use lowercase, hyphenated names, e.g.
`submissions/meeting-summarizer/` -> `/skills/meeting-summarizer`. Start by
copying [`_template/`](./_template).

Bundling is **verbatim** — whatever you put in `scripts/`/`references/`/`assets/`
ships exactly as authored. Only `metadata.*` and the optional `README.md` are
stripped; they are sidecars and never land inside the bundle.

> ℹ️ **Talking to a human? Use `README.md`.** A root-level `README.md` is the one
> file meant for people, not the agent. It is **never bundled** and **never part
> of `SKILL.md`** — and when present it **becomes the main content** on the detail
> page (your own overview, setup steps, tips, and examples), with the exact
> `SKILL.md` still offered as the download. Without one, the page falls back to
> the skill's own instructions. It's optional and works for every entry type
> (skill or automation). Everything *else* in the folder is
> agent-facing and ships verbatim, so don't add stray docs like `CHANGELOG` or
> `CONTRIBUTING` next to your payload — they'd just waste the agent's context. Put
> those in your PR description.

## Two descriptions — they are different on purpose

| | Lives in | Who reads it |
| --- | --- | --- |
| **Agent description** | `SKILL.md` frontmatter `description` | the **agent/model**, to decide *when to invoke* the skill |
| **Catalog description** | `metadata.json` `description` | **people** browsing this gallery (card + top of the detail page) |

Write the agent description as a precise trigger ("Use this skill whenever the
user… BEFORE calling…"). Write the catalog description as a friendly one-liner.

## `SKILL.md` — name + description + instructions

The canonical Agent Skills file: frontmatter with a slug `name` (lowercase,
hyphenated, **matching the folder name**) and the **agent-facing** `description`,
then the instructions body. All three are required.

```markdown
---
name: meeting-summarizer
description: Use this skill whenever the user asks to summarize a meeting transcript, before drafting any reply.
---

Turn the transcript into concise notes and action items…
```

The human-friendly **display name** lives in `metadata.json` (`name`), not here.

## `README.md` — an optional human-facing overview

Want to tell the person adding your skill how to set it up, what to expect, or a
few tips? Drop a `README.md` in the submission folder. It's **optional**, plain
Markdown, and written for **people** — so it never ships in the download bundle
and the agent never reads it. When present, it **becomes the main content** on
the detail page (in your own words), while the exact `SKILL.md` stays available as
the download. Leave it out and the page falls back to showing the skill's
instructions. It works the same way for a skill or a Scout automation.

## `metadata.json` — catalog details

All the catalog details for the gallery (kept out of the agent file):

```json
{
  "name": "Meeting Summarizer",
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
| `name`        | `SKILL.md`      | yes      | Slug (lowercase-hyphenated), must match the folder name.     |
| `description` | `SKILL.md`      | yes      | **Agent-facing** trigger description.                        |
| `name`        | `metadata.json` | yes      | **Display** name shown in the gallery.                       |
| `description` | `metadata.json` | yes      | **Catalog** summary shown in the gallery.                    |
| `platforms`   | `metadata.json` | yes      | One or more of `Cowork`, `Copilot Studio`, `Scout`.          |
| `tags`        | `metadata.json` | yes      | Lowercase tags for search/filtering.                         |
| `author`      | `metadata.json` |          | Person or team.                                              |
| `authorUrl`   | `metadata.json` |          | Link to the author's website/profile.                        |
| `authorGithub`| `metadata.json` |          | Author's GitHub login. Normally derived from a `github.com/<login>` `authorUrl`; set it explicitly only when the author's link isn't a GitHub profile (see below).|
| `version`     | `metadata.json` |          | Semantic version, e.g. `1.0.0`.                              |
| `createdAt`   | `metadata.json` |          | `YYYY-MM-DD`.                                                |
| `updatedAt`   | `metadata.json` |          | `YYYY-MM-DD`.                                                |
| `coverColor`  | `metadata.json` |          | CSS color to override the auto-generated cover.              |
| `featured`    | `metadata.json` |          | `true` to sort the skill to the top.                         |
| `bundle`      | —               |          | Set automatically when your skill ships files beyond `SKILL.md` — don't add it.|

A missing or invalid **required** field fails the PR with a message listing
exactly what's wrong.

### `authorGithub` (attribution)

`authorGithub` is the author's GitHub login, stored WITHOUT a leading `@`. The
importer resolves it purely from your submission — never from whoever merges the
PR — so attribution is stable no matter who lands the skill:

1. an explicit `authorGithub` in `metadata.json` wins; otherwise
2. it is derived from `authorUrl` when that points to a GitHub profile
   (`https://github.com/<login>`); otherwise
3. it is left unset.

It exists so the repo's *skillbot* can @-mention the author on the first comment
of the skill's discussion, so they hear about early feedback. **Most contributors
don't need to set it** — just make `authorUrl` your GitHub profile. Set it
explicitly only when your only link isn't a GitHub profile (e.g. LinkedIn), or
leave it blank to opt out of the mention.

## Cowork plugins (no longer accepted)

Earlier, the gallery also accepted **Cowork plugins** — Microsoft 365 app
packages (a `.zip` with a root `manifest.json`) that bundle one or more skills
(plus optional MCP connectors) and run **only** in Copilot Cowork. Because the
gallery no longer accepts `.zip` payloads, **new plugin submissions are no longer
accepted**. Existing plugin submissions (e.g. [`legal-toolkit/`](./legal-toolkit))
stay published.

## Scout automations (advanced)

The gallery also hosts **Scout automations** — a scheduled/triggered `.json`
(a schedule plus an ordered list of prompt steps) that runs **only** in Scout.

An automation submission is a `submissions/<slug>/` folder with a `metadata.json`
sidecar plus a **single `.json` automation export**. It's auto-detected as an
automation because the one non-sidecar top-level file is a `.json` (not a
`SKILL.md`):

```
submissions/<slug>/
├── metadata.json          # catalog sidecar (name/description/tags optional —
│                          #  they fall back to the automation's own fields)
└── <name>.json            # the Scout automation export
    ├── name               # non-empty string
    ├── schedule           # required: single | interval | multi | monthly | cron
    ├── steps[]            # { label, prompt } — the ordered prompt steps
    └── …                  # optional: description, triggerType, model, etc.
```

The importer forces `platforms: ["Scout"]` and `type: "automation"`, publishes
the `.json` **verbatim** as the download, and synthesizes the detail page
(overview, the trigger/schedule, each step's prompt, and import steps).
Automations show an **Automation** badge on their card and are filterable on the
homepage. The exact `.json` you submit is what's offered for download and
re-imported into Scout — so strip any personal paths or secrets first.

This matches Scout's own GitHub-directory import convention: when Scout imports a
bundle from a GitHub directory, **every root-level `.json` is an automation** and
a `skills/` subdirectory holds skills. The file you submit here is the exact file
Scout imports.

Validation is a faithful port of Scout's import schema
(`scripts/validate-automation.ts`) and will fail the PR with an itemized list if
anything is off: `name` must be non-empty, every step needs a `label` and
`prompt`, and `schedule` must be a valid discriminated union — including that an
`interval`'s `intervalMinutes` divides 1440 evenly, a `monthly` selector can
actually fire, and a `cron` expression is valid and fireable. Copy
[`_template-automation/`](./_template-automation) to start, and see
[`spend-more-time-with-friends-and-family/`](./spend-more-time-with-friends-and-family)
for a complete example.

## Scout automation installers (no longer accepted)

Some automations aren't a directly-importable `.json` but an **installer**: a
`.zip` you download, unzip, and follow to set the automation up (an agent reads
the instructions, collects your settings into a personal config, and calls
`m_create_automation`). Because the gallery no longer accepts `.zip` payloads,
**new installer submissions are no longer accepted** — submit a Scout automation
as a single importable `.json` (above) instead. Existing installer submissions
(e.g. [`vacation-urgent-forwarder/`](./vacation-urgent-forwarder)) stay
published.

## Updating an existing skill

Same path: edit the files in your `submissions/<slug>/` folder and open a PR. The
slug is the identity — same slug updates the existing skill, a new slug creates a
new one.

## Try it locally before opening a PR

```bash
npm run check:submissions    # validate metadata only, write nothing
npm run import:submissions   # generate the skill page(s) + bundle(s)
npm run build                # confirm the site builds
```
