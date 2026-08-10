# Authoring a skill

A **skill** is a reusable instruction set for an AI agent — targeting one or more
of **Cowork**, **Copilot Studio**, and **Scout** — published in this gallery
with optional helper `scripts/` (and `references/` / `assets/`).

You contribute every skill the same way: **add a submission to the
[`../submissions/`](../submissions/) folder and open a PR.** CI validates the
metadata and generates the published page (and any download bundle); you never
edit `src/content/skills/` by hand.

## 1. The submission shape

Every submission is a self-contained **unpacked** folder with the same layout:

```
submissions/<slug>/
├── SKILL.md          # the agent skill — frontmatter (name + agent description) + instructions
├── metadata.json     # OR metadata.yaml — catalog details for this gallery
└── scripts/          # optional helper files (bundled for download)
    └── summarize.py
```

Copy [`../submissions/_template/`](../submissions/_template) to start. The
`<slug>` is the folder name (lowercase, hyphenated), e.g.
`meeting-summarizer` → `/skills/meeting-summarizer`. Everything except the
`metadata.*` and optional `README.md` sidecars is packaged into the downloadable
bundle, and the detail page shows a **Download bundle** button.

## 2. Two descriptions (catalog vs. agent)

A skill carries two distinct descriptions:

| | Lives in | Read by | Write it as |
| --- | --- | --- | --- |
| **Agent description** | `SKILL.md` frontmatter `description` | the model, to decide *when to invoke* | a precise trigger |
| **Catalog description** | `metadata.json` `description` | people browsing the gallery | a friendly one-liner |

The gallery card, search, and the top of the detail page show the **catalog**
description. The detail page also surfaces the **agent** description in its own
labeled block, and the downloadable `SKILL.md` ships the agent description in its
frontmatter.

## 3. `SKILL.md`

The canonical Agent Skills file — `name`, the agent-facing `description`, and the
instructions body are all required:

```markdown
---
name: Meeting Summarizer
description: Use this skill whenever the user asks to summarize a meeting transcript, before drafting a reply.
---

You turn a raw meeting transcript into a concise, structured summary…
```

The instructions are agent-facing Markdown — headings, lists, and tables are
supported. A good structure:

- **When to use this skill** — what triggers it.
- **Instructions** — numbered, concrete steps.
- **Guardrails** — what the agent must not do.
- **Tone** — the voice the agent should adopt.

## 4. `metadata.json`

The catalog details, kept out of the agent file:

| Field         | Required | Type     | Description                                                             |
| ------------- | -------- | -------- | ----------------------------------------------------------------------- |
| `description` | yes      | string   | Catalog summary used on the card and as the page meta description.      |
| `platforms`   | yes      | string[] | One or more of `Cowork`, `Copilot Studio`, `Scout`.                     |
| `tags`        | yes      | string[] | Lowercase tags for filtering/search. Reuse existing tags where you can. |
| `author`      |          | string   | Person or team credited for the skill.                                  |
| `authorUrl`   |          | string   | URL to the author's website/profile; renders the author name as a link. |
| `version`     |          | string   | Semantic version, e.g. `1.0.0`.                                         |
| `createdAt`   |          | date     | `YYYY-MM-DD` when the skill was first published.                        |
| `updatedAt`   |          | date     | `YYYY-MM-DD` of the latest update.                                      |
| `coverColor`  |          | string   | CSS color to override the auto-generated cover gradient.                |
| `featured`    |          | boolean  | `true` to sort the skill to the top of the gallery.                     |

(`bundle` is set automatically when you include `scripts/` — don't add it
yourself.) The same fields work in a `metadata.yaml` if you prefer YAML. A
missing or invalid **required** field fails the PR with a message listing exactly
what's wrong.

If you bundle scripts, mention them in the instructions and include a `README.md`
in the submission explaining requirements and usage.

## 5. Preview locally

```bash
npm run check:submissions    # validate metadata only, write nothing
npm run import:submissions   # generate the skill page(s) + bundle(s)
npm run dev                  # open the site and confirm your skill looks right
```

## 6. Open a pull request

Submit a PR with your `submissions/<slug>/` folder. CI validates
the metadata, generates the skill page, and (for same-repo PRs) commits the
generated files back to your branch. Once merged to `main`, the site redeploys
automatically.

To **update** a skill later, edit the same `submissions/<slug>/` and open another
PR — the slug is the identity.
