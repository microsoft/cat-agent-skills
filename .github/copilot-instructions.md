# Copilot instructions for cat-agent-skills

This repo is a gallery of reusable **Agent Skills**. Contributors add one
submission under `submissions/<slug>/` (a `metadata.json` sidecar plus exactly
one payload — an unpacked `SKILL.md` skill, a `.zip`, or a Scout `.json`); CI
generates the published page and download bundle. See
[`CONTRIBUTING.md`](../CONTRIBUTING.md) and
[`submissions/README.md`](../submissions/README.md) for the full rules.

## Code review rules

When reviewing a pull request, check the following in addition to CI:

### The bar: block real problems, not style

These checks are a **merge gate, not a copy-edit.** Skills are human-authored
prose and code; treat the author's wording, formatting, and structure as theirs.
**Only post a comment you could defend as "must fix before merge."** If the worst
case is "could be tidier" or "slightly inconsistent," say nothing — prefer zero
comments over a nit.

**Block-worthy — do raise** (the rest of this section defines these):

- Executable steps, runtime dependencies, or paths that **won't run** on a
  targeted platform (see *Platform fit vs. executable code*).
- Human-facing prose leaking into the agent-facing `SKILL.md`, or setup/adoption
  guidance with nowhere to live (see *Human-facing vs. agent-facing content*).
- Submission-hygiene breaks: mixed-scope PR, hand-committed generated artifacts,
  wrong file layout, invalid or renamed **required** `metadata.json` fields,
  `name`/slug mismatch, or a payload that isn't a `SKILL.md` / `.zip` / Scout
  `.json`.
- Anything that **breaks CI**, or is a **security / privacy** problem (secrets,
  data exfiltration, harmful content).

**Not block-worthy — do NOT raise:**

- **Writing style in the skill's own text** — wording, tone, grammar,
  capitalization, heading style, and **punctuation, including em-dashes,
  hyphens, and Oxford commas.** A skill telling itself "no em-dashes in output"
  is a rule for the **generated text**, not for the instructions that describe
  it; do not flag em-dashes (or any other "banned" token) in the playbook's own
  prose. Raise it **only** if the token appears inside a **literal
  example/template the agent emits verbatim.**
- **Internal-consistency and "you could also…" nits** that don't change whether
  the skill runs or what it produces.
- **Cosmetic `metadata.json` preferences** — `updatedAt` / date freshness,
  optional-field bikeshedding — as long as the required fields are present and
  valid.
- **Generated artifacts CI commits back** (`src/content/**`, `public/bundles/**`):
  never flag their presence, content, or that a PR "also changes" them — they are
  CI-owned, not the contributor's edit.
- **The same point on many lines.** Make it once, in one thread; don't open a
  thread per occurrence.

When unsure whether something clears the bar, treat it as **non-blocking** and
leave it out.

### Platform fit vs. executable code

A skill's `platforms` (`Cowork`, `Copilot Studio`, `Scout`) must match the
runtime its executable steps actually assume. The runtimes are **not** the same,
so the same snippet can be fine on one platform and broken on another:

- **Cowork** and **Copilot Studio** execute code in a **Python/Linux
  container** — no Windows shell, no drive letters, no desktop apps. **Python**
  (with POSIX shell) is the safe choice for any executable step.
- **Scout** runs on the **user's own device**, so it is **cross-OS**: the same
  automation may run on Windows, macOS, or Linux. Executable steps must be
  **platform-agnostic** — ideally written in a runtime that behaves the same on
  every OS (**Python** or **Node** are fine as-is). Scout also uses **whatever
  shell the device has** (POSIX `sh`, `cmd.exe`, or PowerShell — you **cannot**
  assume which), so read environment info such as the working directory from the
  runtime (`os.getcwd()` / `process.cwd()`) or the agent's workspace tools rather
  than shelling out for it. A per-OS **branch** is acceptable only when each
  branch calls a command that OS's shell genuinely has; a branch like that is
  doing the *right* thing and must **not** be flagged as a "won't run" error.

Flag a submission when its runnable code, **runtime dependency**, or filesystem
assumptions don't match the platforms it targets, for example:

- **Windows dependencies in a Cowork / Copilot Studio skill** — Windows
  PowerShell or `.ps1` scripts, Windows-only cmdlets (`Expand-Archive`,
  `Get-ChildItem`), `.exe` / .NET-Framework calls, drive letters, or `C:\...`
  paths. None of these run in the Linux container as authored. Ask the author to
  rewrite the step(s) in **Python** with POSIX paths, or mark the code as
  illustrative-only. This does **not** apply to Scout.
- **A non-portable runtime dependency in a Scout skill / automation** — because
  Scout runs on whatever machine the user is on, an executable step that
  hard-depends on a **single-OS runtime or shell** is not portable: an
  unconditional **PowerShell** step (macOS/Linux may not have it installed), a
  `bash`-only assumption on Windows, or a Windows-only cmdlet / `.exe`. This
  includes a per-OS branch that **bets on a shell that isn't guaranteed** — e.g.
  `$PWD.Path` assumes PowerShell, but on Windows Scout often spawns `cmd.exe`
  where it fails. Ask the author to move the logic into a **cross-OS runtime
  (Python or Node)**, or read the value from the runtime / workspace tools (e.g.
  `os.getcwd()` / `process.cwd()` instead of `pwd` / `$PWD.Path`). **Python and
  Node are fine; a bare PowerShell/`.ps1` dependency is not.** Do **not** flag a
  genuinely agnostic payload — a cross-OS runtime, or a branch that calls only
  commands each OS's shell actually has.
- **Non-portable filesystem assumptions in a Scout skill / automation** — a
  step that assumes a **single** OS's paths (Linux-only paths with no Windows
  branch, or vice versa) or bakes in an absolute path, drive letter, or a
  specific username. Paths must resolve at runtime relative to the workspace.
  Again, do **not** flag one that already handles multiple OSes.
- Desktop/Office-host assumptions (`.docx` output, "if the file is locked by
  Word or OneDrive", GUI automation) on a **container** platform that has no
  such host.
- Any executable payload whose language/OS doesn't match the runtime it will
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

**Do not flag runtime steps that merely mention the user.** A step written *to
the agent* that has it interact with the end-user during a run — ask a question,
show or hand off output it just generated, "tell the user how to upload the file
it produced", guide them to a next action — is **agent-facing** and stays in
`SKILL.md`, even though it references "the user". The README carve-out is only
for guidance a human reads *outside* a run (preparing inputs, installing the
submission, adding it to their agent), not for the agent's own runtime turns. In
particular, a **fallback branch** ("if no skill-creation tool exists, output the
`SKILL.md` and tell the user how to upload it") is a runtime instruction, not
setup prose — do not ask for it to move to a `README.md`.

When such content exists, ask the author to **move it into a `README.md`
sidecar** and leave `SKILL.md` as the lean runtime SOP (activation, procedure,
decision rules, output format). A skill that has meaningful setup or adoption
guidance but **no `README.md`** should be flagged — that guidance has nowhere
to live except wrongly inside `SKILL.md`, and the gallery page has no
human-facing overview. (A `README.md` is optional only when there is genuinely
no human-facing content to host.)

The distinction to apply: *would the running agent ever need this sentence to
do the task?* If no — it's documentation, and belongs in the `README.md`. Apply
the test to the sentence's **reader**: an instruction the agent must read to act
— including one that tells it to communicate with the user at run time — is
needed by the agent, so it stays in `SKILL.md`.

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
