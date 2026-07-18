# Copilot instructions for cat-agent-skills

This repo is a gallery of reusable **Agent Skills**. Contributors add one
submission under `submissions/<slug>/` (a `metadata.json` sidecar plus exactly
one payload — an unpacked `SKILL.md` skill, a `.zip`, or a Scout `.json`); CI
generates the published page and download bundle. See
[`CONTRIBUTING.md`](../CONTRIBUTING.md) and
[`submissions/README.md`](../submissions/README.md) for the full rules.

## Code review rules

When reviewing a pull request, check the following in addition to CI:

### Platform fit vs. executable code

A skill's `platforms` (`Cowork`, `Copilot Studio`, `Scout`) must match the
runtime its executable steps actually assume. **All three platforms execute code
in a Python/Linux container — none of them run Windows PowerShell.**

Flag a submission when its runnable code or filesystem assumptions don't match
the platforms it targets, for example:

- **Windows PowerShell** snippets (`Expand-Archive`, `Get-ChildItem`,
  `C:\...` paths) in a skill tagged for Cowork / Copilot Studio / Scout — these
  won't run as authored. Ask the author to rewrite the step(s) in **Python**
  with Linux-style paths, or mark the code as illustrative-only.
- Desktop/Office-host assumptions (`.docx` output, "if the file is locked by
  Word or OneDrive", local drive letters, GUI automation) on a platform that has
  no such host.
- Any executable payload whose language/OS doesn't match the container it will
  run in.

Either the executable steps are made portable to the targeted runtime, or the
`platforms` list is narrowed to where the skill genuinely runs.

### Submission hygiene

- **One concern per PR: submission content OR site/repo changes, never both.**
  A pull request should either add/edit a `submissions/**` entry *or* change the
  site/infrastructure (`.github/**`, `scripts/**`, `src/**` app code, Astro/root
  config, etc.) — not both at once. This keeps a reviewer from accidentally
  approving an infra change while signing off on a skill. CI enforces this via
  the **Guard PR scope** check; the `allow-mixed-changes` label overrides it when
  a mix is genuinely intended. (Generated artifacts CI commits back —
  `src/content/skills/*`, `src/content/guides/*`, `public/bundles/*` — don't
  count as site changes.)
- Do **not** hand-commit generated artifacts: `src/content/skills/*` and
  `public/bundles/*` are produced by CI, never by the contributor.
- The bundle ships **only agent-facing files** (`SKILL.md`, `scripts/`,
  `references/`, `assets/`). A root-level `README.md` is the one allowed
  human-facing file: it is a sidecar (stripped alongside `metadata.*`), never
  bundled and never read by the agent, and when present it becomes the main
  content on the detail page. No other human-facing docs (`CONTRIBUTING`,
  `CHANGELOG`, stray notes) belong in the submission folder — everything except
  the `metadata.*` and `README.md` sidecars is packaged into the agent bundle
  and wastes context. Ad-hoc contributor notes still belong in the PR
  description.
- `SKILL.md` is agent-only: no "Human setup instructions" / Overview / Quick
  start prose. Open straight into the agent instructions.
- `references/`, `assets/`, and `scripts/` are **top-level siblings** inside the
  submission (or the `.zip`), not nested under one another (e.g. not
  `scripts/references/`).
- Canonical instruction filename is uppercase `SKILL.md` (legacy lowercase
  `skill.md` still imports, but prefer `SKILL.md`).
- `metadata.json` should carry the documented fields only
  (`name`, `description`, `platforms`, `tags`, and the optional `author`,
  `authorUrl`, `version`, `createdAt`, `updatedAt`, `coverColor`, `featured`).
  Unknown keys are silently stripped by the schema — flag them as noise.
- Never set `authorGithub` or `bundle` by hand; CI populates them.
- The `SKILL.md` frontmatter `name` must be a lowercase-hyphenated slug that
  matches the submission folder name.
