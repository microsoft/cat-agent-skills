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

### Human-facing vs. agent-facing content (README split)

`SKILL.md` is read by the **agent at runtime**; the optional root-level
`README.md` is read by a **human browsing the gallery**. They have different
audiences, so onboarding/setup prose does not belong in `SKILL.md`.

Actively flag a submission when human-facing content is embedded in `SKILL.md`
instead of a `README.md`, for example:

- **Setup / "before you start" guidance** — how to prepare inputs the skill
  needs (e.g. "fill in your personas file", "create a config with these
  fields", "8–12 personas is a good range"), installation/upload steps, or
  "how to add this to your agent" instructions.
- **Overview / marketing / "why use this" framing**, "at a glance" tables,
  quick-start example prompts, tested-model notes, and limitations written for
  a reader deciding whether to adopt the skill.
- Any second-person "you"-addressed prose that tells the *user* what to do
  before/around a run, rather than telling the *agent* how to execute one.

When such content exists, ask the author to **move it into a `README.md`
sidecar** and leave `SKILL.md` as the lean runtime SOP (activation, procedure,
decision rules, output format). A skill that has meaningful setup or adoption
guidance but **no `README.md`** should be flagged — that guidance has nowhere
to live except wrongly inside `SKILL.md`, and the gallery page has no
human-facing overview. (A `README.md` is optional only when there is genuinely
no human-facing content to host.)

The distinction to apply: *would the running agent ever need this sentence to
do the task?* If no — it's documentation, and belongs in the `README.md`.

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
  start / setup-prep prose (see **Human-facing vs. agent-facing content**
  above). Open straight into the agent instructions.
- `references/`, `assets/`, and `scripts/` are **top-level siblings** inside the
  submission (or the `.zip`), not nested under one another (e.g. not
  `scripts/references/`).
- Canonical instruction filename is uppercase `SKILL.md` (legacy lowercase
  `skill.md` still imports, but prefer `SKILL.md`).
- `metadata.json` should carry the documented fields only
  (`name`, `description`, `platforms`, `tags`, `author`, and the optional
  `authorUrl`, `authorGithub`, `version`, `createdAt`, `updatedAt`, `coverColor`,
  `featured`). Unknown keys are silently stripped by the schema — flag them as noise.
- `authorGithub` is normally derived from a `github.com/<login>` `authorUrl`; set
  it explicitly only to attribute an author whose link isn't a GitHub profile
  (e.g. LinkedIn), or leave it unset. It is never the PR/merger login. Never set
  `bundle` by hand; CI populates it.
- The `SKILL.md` frontmatter `name` must be a lowercase-hyphenated slug that
  matches the submission folder name.
