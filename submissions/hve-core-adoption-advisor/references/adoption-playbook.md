# Adoption playbook

How to install HVE Core, run work through RPI, customize alongside it, and roll it out to a team, from `docs/getting-started/`, `docs/rpi/`, and `docs/customization/` in microsoft/hve-core as of 3.2.2 (2026-10-17). Commands are for the user to run; the skill never runs them.

## What HVE Core is, in five sentences

HVE Core is Microsoft's opinionated agentic software development lifecycle framework for GitHub Copilot: agents, instruction files, and skills that carry standards, context, and process through the work so that, in its own words, "AI carries the rules, humans keep the judgment." Its spine is RPI: Research, Plan, Implement, Review, with Follow-up, each phase writing a dated artifact under `.copilot-tracking/` so work resumes from files rather than chat history. Around RPI sit planners and reviewers for security, supply chain, privacy, accessibility, Responsible AI, requirements, architecture decisions, backlog work, documentation, and Design Thinking. It ships as one VS Code extension and one Copilot CLI plugin, with clone-based methods for teams that need to customize or pin. Microsoft labels it rapidly evolving and a source of patterns rather than a stable production dependency, and some skill content carries non-MIT licenses.

Prerequisites: VS Code 1.99 or later with the GitHub Copilot and Copilot Chat extensions active (handoffs need 1.106 or later), Git on PATH for clone methods, network access to github.com, Node.js and `npx` for stdio MCP servers. Current VS Code distinguishes Copilot harness sessions from Local harness sessions; the deprecated `chat.*Locations` settings that clone-based methods depend on apply only to the latter.

## Install decision matrix

| Method | Best fit | Updates | Customize | Pin | Environments |
| --- | --- | --- | --- | --- | --- |
| VS Code extension (recommended default) | Anyone, any team size | Automatic | No (add your own `.instructions.md` files in the repo) | No | Local, dev container, Codespaces |
| Copilot CLI plugin | Terminal-first workflows | Manual, two steps | No | No (tracks `main`) | Any with the CLI |
| Selective clone (`hve-core-installer`) | Teams wanting a repository-owned subset | Automatic source updates or a pinned version, chosen at install | Yes | Yes | Any |
| Submodule | Teams needing version control | Controlled | Yes | Yes | Local, dev container, Codespaces |
| Peer directory clone | Solo, local VS Code only | Manual | Yes | Manual | Local |
| Git-ignored folder | Solo, local dev container | Automatic | Yes | No | Local dev container |
| GitHub Codespaces method | Codespaces-only projects | Automatic | Yes | No | Codespaces |
| Multi-root workspace | Local and Codespaces, portable | Any | Yes | Manual | Both |
| Mounted directory | Advanced shared install | Automatic | Limited | No | Dev container |

Decision path: simplest setup, use the extension; need to customize, pick by environment (local only: peer clone; local dev container only: git-ignored folder; Codespaces only: Codespaces method; both: multi-root workspace); team with version control: submodule or the selective installer; terminal-first: CLI plugin. Start with the extension; any clone-based method can be adopted later. Use a direct clone only when the installer's options are exhausted.

**Extension.** Install `ise-hve-essentials.hve-core` from the Marketplace, open a folder or workspace (a single open file activates nothing), open Copilot Chat (Ctrl+Alt+I or Cmd+Alt+I), select RPI Agent in the agent picker. Stable and PreRelease carry the same components.

**Copilot CLI.**

```bash
copilot plugin marketplace add microsoft/hve-core
copilot plugin install hve-core@hve-core
copilot plugin marketplace browse hve-core          # list
copilot plugin marketplace update hve-core          # refresh the catalog, then:
copilot plugin update hve-core@hve-core
copilot plugin marketplace remove hve-core --force  # replace an old release-channel or tag registration, then add and install again
copilot --agent hve-core:rpi-agent                  # or /agent hve-core:rpi-agent in a session
```

CLI limits: instruction files are not auto-applied (copy the ones you need into your repo's `.github/instructions/`); prompt files do not run; the CLI does not switch agents for a skill (select one or invoke a phase skill); agents with a list-valued `model` are dropped; skills with `disable-model-invocation: true` do not run (github/copilot-cli#4438): in 3.2.2 these are `git-commit`, `git-merge`, `git-setup`, `accessibility-coverage-matrix`, `synth-data-generate`, `engagement-report-council-critique`, `caveman`, `copilot-otel-metrics`, `cspell-config`, `hve-slides`, `incident-response`, and `risk-register`; removing the marketplace with `--force` may also uninstall its plugins depending on the CLI version.

**Selective installer.** Ask Copilot to use the `hve-core-installer` skill: it asks for consent, offers quick (extension) or clone, detects the environment (shell, container, Codespaces), recommends a method, runs it, validates (paths, settings, agent visibility), configures `.gitignore` and MCP, and optionally copies selected components with collision detection, recording the selection in `.hve-tracking.json`. Bash scripts require `jq`. Re-running validates or offers an upgrade; `eject` scripts reverse a selection.

**Developer setup (contributing or forking).** `git clone`, `npm ci`, open the included dev container. Behind a restricted network set the registry override as an environment variable or CLI flag, never in a tracked file; a user-level `~/.npmrc` is overridden by the project's `.npmrc`.

**Post-install, every method:** add `.copilot-tracking/` to `.gitignore`.

**Updating.** Extension: automatic. CLI: refresh the marketplace, then update the plugin. Clone methods: pull or bump the pinned ref, then re-run the installer's validation. Update VS Code, Copilot, Copilot Chat, and HVE Core together; read `CHANGELOG.md` for breaking changes.

## MCP configuration

Optional. Create `.vscode/mcp.json` at the workspace root (not inside a cloned `hve-core` folder; in multi-root setups, in the `.code-workspace` settings or the primary folder). Keep only the servers you use: `github` for GitHub repositories or `ado` for Azure DevOps (both only when working across platforms); `context7` and `microsoft-docs` for research; `figma` for `dt-figma-export`; `workiq` for Meeting Analyst. Trust the servers when prompted; GitHub uses VS Code's sign-in; Figma completes OAuth in the browser on first call. If a tool reports unavailable, check the file location, the MCP SERVERS section of the Extensions view, and the MCP Servers output channel.

## Troubleshooting

| Symptom | Check | Fix |
| --- | --- | --- |
| Extension installed, no agents or skills in chat | Copilot Chat active, VS Code 1.99 or later, HVE Core output channel | Developer: Reload Window; update the three extensions together |
| An agent or skill is missing | `.github/agents/` and `.github/skills/` exist with `.agent.md` and `SKILL.md`; a folder or workspace is open; `.gitignore` does not exclude them; `.hve-tracking.json` lists the component | Fix the file name or folder, open a folder, remove the ignore rule, re-run the installer |
| Duplicate agents or odd behavior | Extension plus copied or cloned files | One source per workspace; compare copied files with `.hve-tracking.json` before deleting; uninstalling the extension leaves repository files in place |
| Copilot ignores customizations in a multi-root setup or a clone-based install | The `.code-workspace` file is open, not just a folder; `chat.agentFilesLocations` and its siblings point at the right paths (these settings are deprecated in current VS Code and honored only in Local harness sessions); the window title shows the workspace name | Open the workspace file; fix the settings; for monorepos use `chat.useCustomizationsInParentRepositories`; if the settings are ignored, move to the extension or the selective installer |
| Errors after an update | Versions of VS Code, Copilot, Copilot Chat, HVE Core, copied artifacts | Update together; if artifacts drifted, remove the HVE Core files under `.github/` and reinstall |
| `npm ci` cannot reach the registry (contributors) | Network blocks public registries | Registry override as env var or flag; restore commands only, so lockfiles keep public URLs |
| MCP tool unavailable | `.vscode/mcp.json` at the root, server listed and trusted, Node.js for stdio servers, ADO org and tenant correct | Create or fix the file; sign in |

## Running work through RPI

Each phase is optional and research runs only when existing evidence has a demonstrated gap. Continuity comes from the artifacts, not the conversation.

1. **Define the task**: requirements, acceptance criteria, decisions already made, dependencies, evidence available. Give it a kebab-case slug; the phases reuse it.
2. **Research**, `/rpi-research topic=<...>` or let RPI Agent decide. Read-only; separates evidence from assumptions; writes `.copilot-tracking/research/{date}/{slug}-research.md` and says whether planning can proceed. Adequate existing evidence is reused and the reason recorded.
3. **Plan**, `/rpi-plan task=<slug> research=<path>`. No source changes; produces phases `Pxx`, tasks `Pxx-Txx`, `<!-- rpi:... -->` markers, Goals, Requirements, Details, References, Dependencies per task, and a critique (Pass, Revise, Blocked) unless `critique=skip`. Writes `plans/{date}/{slug}-plan.md` and `reviews/plans/{date}/{slug}-plan-critique.md`.
4. **Implement**, `/rpi-implement plan=<path> phase=P01` or `task=P01-T02`. Executes approved work, ticks checkboxes only with evidence, records departures and updates the plan after the decision, writes `changes/{date}/{slug}-changes.md` with validation.
5. **Review**, `/rpi-review task=<slug>` (optional). Reconciles requirements, plan status, critique dispositions, changes, and validation into `reviews/logs/{date}/{slug}-review.md`; findings `RV-xxx` with destinations; status (Complete, Partial, Blocked) kept apart from outcome (Conformant, Defects found, Not accepted).
6. **Follow-up**: defects go back to implement, decision gaps to plan, evidence gaps to research, residual work becomes a separate item.

**RPI Agent versus phase skills.** RPI Agent wraps the phases under one task identity and starts in manual mode; Full Auto, once explicitly authorised, runs through Review and offers ranked follow-ups while still stopping for blockers, safety confirmations, and human review. Use a phase skill when the next responsible action is already clear. In the CLI, select the agent or invoke a phase skill yourself.

**Resuming.** Open or reference the dated artifacts by path and the stable IDs, headings, and markers. `/clear` between tasks; `/compact` only mid-phase and knowing it can drop details. Do not reuse a long conversation for a new task (recency bias skips readiness checks) and do not mix tasks in one context. Signs of degradation: skipped readiness assessments, dropped instructions, shallow output, patterns echoed from earlier tasks.

**Large tasks.** Split into task identities that can be reviewed independently, reuse adequate research, keep each artifact set dated and task-specific. **Small tasks.** Skip research when evidence exists, skip the critique, skip review when no acceptance record is needed.

**Companions.** `/rpi-challenger` to expose assumptions before acting; `/rpi-walkthrough` to explain code or tracking artifacts; DT Coach before RPI when the problem itself is unclear, handing off through `dt-rpi-integration` with findings tagged validated, assumed, unknown, or conflicting.

## Customizing alongside HVE Core

**Instructions first.** `.github/copilot-instructions.md` for repository-wide rules and project structure (loads every interaction; start with a few targeted rules). `.github/instructions/<org>/*.instructions.md` with `description` and `applyTo` for path-specific rules; narrow patterns (`**/*.test.ts` rather than `**/*.ts`), comma-separated for several. Stacking is additive. HVE Core's team policy resolves conflicts as `copilot-instructions.md` first, then the more specific `applyTo`, then the artifact owner by pull request; VS Code's documentation says merge behavior varies by harness and advises against relying on precedence, so remove contradictions at the source. Works with the extension-only install. A repository that already has `AGENTS.md` keeps it; VS Code reads both. Use `/hve-builder mode=create` with reference files, `mode=review` for a read-only report, `mode=refactor` to consolidate overlap.

**Agents.** `.github/agents/<package-id>/<workflow>.agent.md`; subagents in `subagents/` with `user-invocable: false` and only the tools they need; orchestrators with `disable-model-invocation: true` and `agents:`; hybrids omit `disable-model-invocation`. Refer to subagents by name in `agents:` and, in the body, by glob such as `.github/agents/**/<name>.agent.md`. HVE Core's design rule is that only the parent orchestrates; current VS Code does support nested subagents, so keep the rule as policy rather than a platform limit. Omitting `tools` grants everything. Keep `model` a single string: VS Code accepts an ordered list, the Copilot CLI drops the agent. Invoke a granted tool from the body with `#tool:`. New research, indexing, planning, or general implementation agents are rejected upstream because equivalents exist; locally, prefer extending an existing workflow with a skill or research subagent (`extending-hve-builder` reference). Agents and skills cannot be modified under the extension-only install; that needs a clone-based method.

**Skills.** `.github/skills/<package-id>/<skill>/SKILL.md`, `name` equal to the folder, description in the words users type, body under about 5,000 tokens, references under about 2,000 tokens each and linked relatively, scripts with a shebang and usage, `SECURITY.md` when scripts egress, run subprocesses, handle credentials, or parse untrusted content. Referenced as `copilot-skill:/<skill>/SKILL.md`.

**Prompts.** `.github/prompts/<package-id>/<action>.prompt.md` with `description`, `agent` (`ask`, `agent`, `plan`, or a custom agent name; current VS Code routes on this and no longer documents the older `mode` that HVE Core's checklist still lists), optional `tools` and `model`, and `${input:var}` or `${input:var:default}` variables declared in an Inputs section. Invoke with `/name` in VS Code; the Copilot CLI does not run prompt files.

**Validation inside an HVE Core clone or fork:** `npm run lint:frontmatter`, `lint:md`, `lint:md-links`, `spell-check`, `lint:models`, `validate:skills`, `docs:generate` and `lint:asset-docs` for documented artifacts, `plugin:sync` and `plugin:validate` after membership changes, `docs:generate:check`. Local-safe commands only; `ci:*` lanes are CI-owned.

**Forking** only when in-place customization cannot meet the goal: replacing core workflow agents, changing membership, packaging, or the build, enforcing structural governance, or integrating internal systems through core scripts. Steps: fork, add `upstream`, `npm ci`, update `package.json` name and repository, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `extension/templates/`, root `plugin.json`; run `validate:local`, `plugin:sync`, `plugin:validate`. Sync at least once per release cycle (weekly or biweekly is smoother); expect conflicts in `package.json`, `.markdownlint.json`, `plugin.json`, workflows; accept upstream core scripts, schemas, templates, shared instructions, and docs; keep your branding and workflows; track the upstream version last synced.

**Restricted networks.** The enterprise artifact hub guide uses `HVE_GITHUB_RELEASES_URL`, `HVE_PSGALLERY_REPOSITORY`, `HVE_PSGALLERY_SOURCE_URL`, `HVE_GITHUB_API_URL` (GitHub Enterprise Server), plus `NPM_CONFIG_REGISTRY`, `PIP_INDEX_URL`, `UV_DEFAULT_INDEX`, set on the host or as repository variables for the coding agent, never in tracked files or with embedded credentials. Index URLs must match the tracked `uv.lock` exactly, trailing slash included.

## Team rollout and governance

**Phases.** 1: two or three instruction files (coding standards, commit format, PR conventions) and a short `copilot-instructions.md`. 2: agents for repeatable workflows (review, research) and prompts for one-off tasks. 3: skills for multi-step domain knowledge, placed under package-scoped paths with `plugin.json` kept in sync, or a repository-owned subset through the installer. Onboarding runs alongside: a first-customization exercise paired with an experienced teammate, and role-based starting points (engineer: RPI and coding instructions; tech lead: Code Review, ADR Creator; TPM or PM: PRD and BRD Builders, Functional Planner, Backlog Manager; security architect: Security Planner and Reviewer, the Secure Software Supply Chain (SSSC) Planner and Reviewer; SRE: `/performance-slo-planner`, `/incident-response`; data scientist: the data-science coach; new contributor: DT Coach and `/rpi-walkthrough`).

**Install for the team.** Extension by default for everyone; the installer when the team needs a repository-owned, version-controlled subset; direct clone only when artifact changes exceed what the installer offers.

**Naming and layout.** kebab-case; `{topic}.instructions.md`, `{workflow}.agent.md`, `{action}.prompt.md`, `{skill-name}/SKILL.md`; `.github/{type}/{package-id}/`; root-level files are repository-specific and never distributed; package ids unique, lowercase, kebab-case.

**Precedence.** `copilot-instructions.md` first, then more specific `applyTo` over broader, then the artifact owner by pull request.

**Ownership and review.** A maintainer or team per namespace, CODEOWNERS, separate owners per instruction file if useful, broader review for `copilot-instructions.md`. Treat customization files as production code: feature branch, `/hve-builder` create or improve with its gates resolved, local validation, `plugin:sync` when membership changes, docs updated when the user-visible surface changes, pull request.

**Communication and deprecation.** Announce new agents with purpose and an invocation example; explain modified instructions; give migration steps and a timeline. Deprecate by adding a notice with `/hve-builder mode=improve`, announcing, moving to `.github/deprecated/`, syncing and validating, then removing after the transition.

**Measures.** Artifact counts over time, invocation frequency, before-and-after error rates for targeted mistakes, time to productivity for new members; confidence surveys, consistency with conventions, fewer manual corrections. Review effectiveness in retrospectives, keep a channel for gaps, review artifacts quarterly, treat rarely used ones as deprecation candidates. Baseline before you start or the error-rate measures mean nothing.

**Pitfalls.** Skipping validation or sync after membership changes; artifacts at the root of a type folder when distribution was intended; unresolved same-specificity conflicts; deprecating without notice; starting with complex skills before instructions have built confidence; measuring without a baseline; moving to a direct clone before the installer's options are exhausted; two HVE Core sources in one workspace.
