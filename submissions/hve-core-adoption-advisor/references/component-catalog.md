# Component catalog

What HVE Core ships, as of **HVE Core 3.2.2 (plugin.json version), read from the main branch of microsoft/hve-core on 2026-10-17**. HVE Core changes weekly and the project says its interfaces may change without backward compatibility. When a name, count, or command matters for an action, confirm it against the live repository (`.github/CUSTOM-AGENTS.md`, `plugin.json`, `docs/plugins/hve-core.md`, and `docs/reference/`) if the host can browse; otherwise tell the user which page to check.

## Identities and install surfaces

| Surface | Identity | Notes |
| --- | --- | --- |
| VS Code extension | `ise-hve-essentials.hve-core` on the Visual Studio Marketplace | Stable and PreRelease channels carry the same component set and differ in source branch, cadence, and version. Stable tags are `v<version>` with even minor versions; PreRelease tags are `prerelease-v<version>` with odd minor versions. Managed updates, no configuration, no repository files. |
| Copilot CLI plugin | `hve-core@hve-core`, marketplace `microsoft/hve-core` | Tracks `main`; no Stable or PreRelease plugin channels and no release attestation. Older registrations of `release/prerelease`, `release/stable`, or tag refs no longer update and must be re-registered. |
| Marketplace locator | `.github/plugin/marketplace.json` | One entry pointing at the repository root. Membership lives only in the root `plugin.json`. |
| Selective clone | `hve-core-installer` skill | Copies chosen agents, instructions, and whole skill folders into a repository and records them in `.hve-tracking.json` (schema version 2). Hooks are never copied. |
| Clone-based methods | peer directory clone, submodule, git-ignored folder, Codespaces, multi-root workspace, mounted directory | Documented under `docs/getting-started/methods/`. Discovery relies on `chat.agentFilesLocations`, `chat.instructionsFilesLocations`, `chat.agentSkillsLocations` settings. |

Membership counts in the published package: 60 agents, 53 instructions, 85 skills, 0 prompts. The repository holds 64 agent files, 59 instruction files, and 87 skills; the difference is root-level repository-only artifacts (excluded from packaging) and one skill excluded for a noncommercial license (`owasp-docker`, CC BY-NC-SA 4.0). HVE Core ships no hooks and no prompt files today, although prompts remain a supported artifact type.

## The four artifact types

| Type | File | Location in HVE Core | Role |
| --- | --- | --- | --- |
| Prompt | `*.prompt.md` | `.github/prompts/<package-id>/` | Parameterised user entry point for a single-session workflow; routed with `agent:` (`ask`, `agent`, `plan`, or a custom agent). HVE Core ships none today. |
| Agent | `*.agent.md` | `.github/agents/<package-id>/`, subagents in `subagents/` | User-selected multi-turn role or bounded orchestrator with `tools`, `agents`, `handoffs`. |
| Instruction | `*.instructions.md` | `.github/instructions/<package-id>/` | Standards attached automatically to files matching `applyTo`, or loaded on demand from `description`. |
| Skill | `<skill>/SKILL.md` with `scripts/`, `references/`, `assets/`, `templates/`, `examples/`, `tests/` | `.github/skills/<package-id>/<skill>/` | On-demand workflow, knowledge set, or scripts; slash command when `user-invocable` is true (the default). |

Files placed directly under `.github/<type>/` with no package folder are repository-specific and excluded from packaging. `.github/copilot-instructions.md` holds cross-cutting rules; HVE Core's team policy says it overrides other instructions in a conflict and that the more specific `applyTo` wins among instruction files, while VS Code's own documentation says sources are additive and merge behavior varies by harness, so contradictions should be resolved in the files. `.github/deprecated/<type>/` holds retired artifacts, excluded from the build.

Per VS Code's agent customization documentation (October 2026, not HVE Core's), current VS Code also discovers customizations HVE Core does not use: `AGENTS.md` at the repository root (`chat.useAgentsMdFile`), Claude-format agents under `.claude/agents`, skills under `.claude/skills` and `.agents/skills`, user-level files under `~/.copilot` and `~/.claude`, and organization-level agents and instructions. The `chat.agentFilesLocations`, `chat.modeFilesLocations`, `chat.instructionsFilesLocations`, `chat.agentSkillsLocations`, `chat.promptFilesLocations`, and `chat.hookFilesLocations` settings that HVE Core's clone-based methods and its own `.vscode/settings.json` rely on are marked deprecated there and read only in Local harness sessions; `chat.useCustomizationsInParentRepositories` covers monorepos.

## Agents you select in the picker

Package in parentheses. "Experimental" is HVE Core's own label. Planner agents write session state and artifacts under `.copilot-tracking/` and hand off to backlog execution only after a human ticks the review checkboxes.

| Agent (`name:`) | What it does | Needs | Writes to |
| --- | --- | --- | --- |
| RPI Agent (hve-core) | Wraps Research, Plan, Implement, Review, and Follow-up under one task identity; manual mode by default, Full Auto on explicit authorisation. | A task statement with requirements, acceptance criteria, decisions, dependencies, evidence. MCP servers vary by activated skill. | `.copilot-tracking/research`, `plans`, `reviews/plans`, `changes`, `reviews/logs` |
| Documentation (hve-core) | Audits, detects drift in, authors, and validates documentation through the `documentation` skill; escalates formal accessibility, RAI, and security assessments to the planners. | A mode: audit, drift, author, validate. | `.copilot-tracking/documentation/` |
| Code Review (coding-standards) | Human-gated, review-only orchestrator; the operator confirms scope, perspectives, and depth, then it dispatches Functional, Standards, Accessibility, Security, Orientation, Readiness, Explainer, and Walkback perspective subagents and merges one report. | A branch or diff. | `.copilot-tracking/reviews/code-reviews/` |
| ADR Creator (project-planning) | Phase-gated creation of Architecture Decision Records (MADR, Y-Statement) with state recovery and bring-your-own template. | Decision context; optional `.adr-config.yml`. | `.copilot-tracking/adr-plans/`, `docs/planning/adrs/` |
| BRD Builder, PRD Builder (project-planning) | Guided Q&A producing solution-agnostic business or product requirements, with quality-reviewer subagents. | Interview answers; meeting-analyst output for PRDs. | `.copilot-tracking/brd-sessions/`, `prd-sessions/` |
| Meeting Analyst (project-planning), experimental | Extracts product requirements from meeting transcripts through the work-iq MCP server and hands off to PRD Builder. Files are unencrypted and must be deleted after handoff. | `workiq` server in `.vscode/mcp.json`. | `.copilot-tracking/` |
| Functional Planner (project-planning) | Read-only PRD to Azure DevOps, GitHub, or Jira work-item hierarchy; hands off to Backlog Manager. | A PRD; `ado` and `microsoft-docs` MCP servers. | `.copilot-tracking/workitems/` |
| Backlog Manager (project-planning) | Read-only backlog orchestrator for Azure DevOps, GitHub, Jira; every mutation goes to an executor subagent after confirmation. | `ado` or `github` MCP server; Jira and GitLab use skill credentials. | `.copilot-tracking/workitems/`, `github-issues/`, `jira-issues/` |
| System Architecture Reviewer (project-planning) | Reviews designs for trade-offs and well-architected alignment; routes security concerns to Security Planner and ADR coaching to ADR Creator. | Design material. | Architecture Review Record via `architecture-review` skill |
| UX UI Designer (project-planning) | Routes UX practitioners between coaching, evidence-labeled assets (JTBD, journey maps, inclusion decisions), design intent, and external surfaces; research only. | Delegates to PRD Builder, `backlog-plan`, `rpi-research`. | `.copilot-tracking/` |
| Network ISA-95 Planner (project-planning) | ISA-95-aligned network planning for edge Kubernetes to Azure connectivity. | Network context. | `.copilot-tracking/` |
| Security Planner (security), experimental | STRIDE-based security model, OWASP and NIST standards mapping, TM7 threat-model generation, backlog handoff; recommends RAI Planner when AI components exist. | Codebase or design; human-in-the-loop for TM7. | `.copilot-tracking/security-plans/` |
| Security Reviewer (security) | OWASP-based vulnerability assessment: Codebase Profiler, Skill Assessor, Finding Deep Verifier, Report Generator subagents. | Codebase. | `.copilot-tracking/security/` |
| SSSC Planner (security), experimental; SSSC Reviewer (security) | Secure Software Supply Chain (SSSC) assessment and review against OpenSSF Scorecard, SLSA, Sigstore, SBOM; CVE Analyzer produces VEX statements. | Repository; `gh` for code scanning. | `.copilot-tracking/sssc-plans/`, `sssc-reviews/`, `security/vex/` |
| Privacy Planner, Privacy Reviewer (privacy) | Data maps, DPIA assessments, controls, backlog handoff; evidence review and report. | Processing activities. | `.copilot-tracking/privacy-plans/`, `privacy-reviews/` |
| Accessibility Planner, Accessibility Reviewer (accessibility) | WCAG 2.2, ARIA APG, cognitive accessibility, Section 508, EN 301 549 planning with evidence register and backlog handoff; reviewer profiles the codebase and reports findings. | Codebase or design. | `.copilot-tracking/accessibility/` |
| RAI Planner (rai-planning), experimental; RAI Reviewer (rai-planning) | Responsible AI assessment against NIST AI RMF 1.0, AI STRIDE overlay, EU AI Act tiers; reviewer profiles the codebase. | AI components; can continue from a Security Planner session. | `.copilot-tracking/rai-plans/`, `rai-reviews/` |
| DT Coach, DT Learning Tutor (design-thinking) | Design Thinking coaching across nine methods in Problem, Solution, and Validation spaces; tutor runs the curriculum. | Session state resumes from `coaching-state.md`. | `.copilot-tracking/dt/<project-slug>/` |
| Data Science and Engineering Coach (data-science-engineering) | Coaches a persistent data science workstream through explicit jobs and durable state; routes to the data-science skills. | Workstream context. | `.copilot-tracking/ds/` |
| Engagement Report Generator (engagement-reporting) | Source-grounded engagement status reports with reviewer, Council critique, and optional Outlook draft subagents. | `engagement.yaml`; sources. | `.copilot-tracking/` |
| Experiment Designer, PowerPoint Builder, HVE Demo Material Builder (experimental) | Minimum Viable Experiment coaching; YAML-driven python-pptx decks; levelled training decks and narrated demos. | Python for pptx; FFmpeg and TTS for media. | `.copilot-tracking/mve/`, `ppt/` |
| Repository-only (root of `.github/agents/`, not packaged) | Backlog Grooming, Dependency Reviewer, Issue Triage Agent, agentic-workflows (gh-aw). | Used by HVE Core's own automation. | n/a |

Subagents (`user-invocable: false`, not in the picker): accessibility-framework-assessor, accessibility-surface-inventory; code-review-accessibility, -explainer, -functional, -orientation, -readiness, -security, -standards, -walkback; council-arbiter, council-critic, engagement-report-reviewer, outlook-drafter; pptx-subagent; hve-builder-review (HVE Builder Reviewer), rpi-researcher, rpi-reviewer, vally-test-author; ado-, github-, jira-backlog-executor, brd-quality-reviewer, prd-quality-reviewer; rai-skill-assessor; codebase-profiler, cve-analyzer, finding-deep-verifier, report-generator, skill-assessor, supply-chain-skill-assessor.

## Skills

Slash-visible skills are invoked as `/name` in VS Code and the CLI; `user-invocable` defaults to true, so a skill without the field is visible. Skills marked "loaded by agents" set `user-invocable: false` and are knowledge or contract packs their orchestrator reads. Skills marked "VS Code only" set `disable-model-invocation: true`, which the Copilot CLI cannot run today. Licenses other than MIT are noted because the content comes from third parties.

**RPI (rpi):** `/rpi-research` (evidence only; `[topic=...] [posture=balanced|focused|expansive] [chat]`), `/rpi-plan` (`[task=...] [research=...] [critique=standard|deep|skip]`, standard critique by default), `/rpi-plan-critique`, `/rpi-implement` (`[plan=...] [phase=Pxx] [task=Pxx-Txx]`), `/rpi-review` (`[task=...] [plan=...] [changes=...] [depth=standard|deep]`), `/rpi-challenger` (expose assumptions), `/rpi-walkthrough` (explain code or artifacts).

**HVE Core authoring and Git (hve-core):** `/hve-builder` (create, improve, refactor, replace, review, validate any artifact; `[targets=...] [mode=...] [requirements=...]`; outcome Pass, Revise, Deferred, or Blocked), `/hve-artifact-authoring` (coding-standards; frontmatter, membership, validation conventions), `/vally-tests` (conformance test stimuli), `/git-commit` (VS Code only), `/git-merge` (VS Code only), `/git-setup` (VS Code only), `/pull-request`, `/pr-reference` (shared), `/architecture-diagrams`, `/c4-architecture` (CC BY 4.0 and MIT), `/documentation` (the Documentation agent's capability; also visible as a slash command).

**Installer:** `/hve-core-installer` (environment detection, extension or six clone methods, validation, `.gitignore` and MCP setup, selective component copy; Bash scripts need `jq`).

**Code quality (coding-standards):** `/code-review` (multi-perspective review), `python-foundational` (loaded by agents).

**Project planning (project-planning):** `/backlog-plan` (read-only: discover, my-work, task-plan, triage, sprint, resume), `/backlog-execute` (mutating; `--dry-run` available), `backlog-management` (loaded), `/functional-planner` (CC BY 4.0 and CC BY-SA 4.0), `/jira`, `/gitlab`, `/adr-author`, `architecture-review` (CC BY 4.0, loaded), `/outcome-hypothesis` (CC BY 4.0), `/performance-slo-planner`, `/proposal-response` (RFP and questionnaire responses), `/security-planning` (STRIDE, TM7), `rai-planner` (loaded), `requirements-author` (CC BY 4.0, loaded), `privacy-standards` (CC BY 4.0 and CC BY-SA 3.0, loaded), `experiment-design` (CC BY 4.0, loaded), `/backlog-templates` (shared).

**Security (security):** `/incident-response` (Azure incident workflow; VS Code only), `/risk-register` (VS Code only), `/supply-chain-security`, `/gh-code-scanning`, and the packs loaded by the reviewers: `mcsb` (Microsoft Cloud Security Benchmark crosswalk), `secure-by-design` (OGL-UK-3.0 and CC BY 4.0), `vex` (Apache 2.0 and CC BY 4.0), `security-reviewer-formats`, `owasp-top-10`, `owasp-llm`, `owasp-mcp`, `owasp-agentic`, `owasp-cicd`, `owasp-infrastructure` (all CC BY-SA 4.0), `owasp-docker` (CC BY-NC-SA 4.0, excluded from the plugin).

**Accessibility, privacy, RAI:** `/accessibility-coverage-matrix` (VS Code only), `accessibility` (loaded), `rai-standards` (CC BY 4.0, loaded).

**Design Thinking and UX (design-thinking):** `/ux-artifacts`, `/ux-coaching`, `/dt-figma-export` (Figma MCP, paid seat for sustained use), `/demo-setup`, and the loaded packs `dt-coaching-foundation`, `dt-curriculum`, `dt-methods`, `dt-rpi-integration`.

**Data science (data-science-engineering, CC BY 4.0 unless noted):** `/synth-data-generate` (MIT; VS Code only), and the loaded packs `analysis-authoring`, `data-catalog`, `data-science-engineering-foundation`, `dataops`, `evaluation-design`, `feasibility`, `ml-experimentation`.

**Engagement reporting:** `/engagement-reporting`, `/engagement-report-council-critique` (VS Code only), `/telemetry-foundations` (shared).

**Experimental:** `/caveman` (compressed response style; VS Code only), `/copilot-otel-metrics` (VS Code only), `/cspell-config` (VS Code only), `/customer-card-render`, `/demo-video`, `/hve-demo-material`, `/mural`, `/powerpoint`, `/tts-voiceover`, `/video-to-gif`, `/vscode-playwright`. `/hve-slides` (VS Code only) sits at the root of `.github/skills/` and is repository-only.

## Instruction files

Grouped by package; `applyTo` as shipped. Root-level files (`ci-owned-validation`, `dependency-feeds`, `docusaurus-edits`, `pull-request`, `skill-security-model`, `workflows`) are repository-only.

| Package / file | applyTo |
| --- | --- |
| coding-standards: bash, bicep, csharp, csharp-tests, powershell, pester, python-script, python-tests, rust, rust-tests, terraform, typescript-doc-comments, uv-projects | `**/*.sh`; `**/*.bicep, **/*.bicepparam, **/bicep/**`; `**/*.cs` (both); `**/*.ps1, **/*.psm1, **/*.psd1`; `**/*.Tests.ps1`; `**/*.py` (both); `**/*.rs` (both); `**/*.tf, **/*.tfvars, **/terraform/**`; `**/*.ts, **/*.tsx, **/*.mts, **/*.cts`; `**/*.py, **/*.ipynb` |
| coding-standards/code-review: diff-computation, review-artifacts | none (referenced by agents); `**/.copilot-tracking/reviews/code-reviews/**` |
| hve-core: markdown, writing-style | `**/*.md` (both) |
| hve-core: hve-builder | `**/*.prompt.md, **/*.agent.md, **/*.instructions.md, **/SKILL.md` |
| hve-core: commit-message, git-merge | none (loaded by the Git skills) |
| hve-core: copilot-tracking, copilot-tracking-location, licensing-posture | tracking folders; `**/.copilot-tracking/**`; `**/skills/**, **/.copilot-tracking/**` |
| shared: content-policy-citation, coaching-patterns, planner-identity-base, disclaimer-language, telemetry-overlay, untrusted-content-boundary | all artifact files and workflow docs; planner tracking folders and planning agents |
| accessibility, privacy, rai-planning, security, project-planning (ADR, backlog, community) | the matching `.copilot-tracking/<area>/` folders, `docs/planning/adrs/**`, and specific agent files |
| design-thinking: dt-coach-telemetry; engagement-reporting: data-handling, style-guide, terminology; experimental: experiment-designer, pptx | `**/.copilot-tracking/dt/**`; engagement agent and skill folders; `**/.copilot-tracking/mve/**`, `**/.copilot-tracking/ppt/**` |

The Copilot CLI loads path-specific instructions only from the project's own `.github/instructions/`; plugin instruction files are available only through `#file:` references. Copy the ones you need into the repository to get automatic behavior in the CLI.

Handoff targets: HVE Core's own agents name the target by its `name:` value (`agent: RPI Agent`), while the contributing guide describes the field as the file name without `.agent.md`. The audit accepts both forms.

## Need to component

| Need | Start with | Then |
| --- | --- | --- |
| Any non-trivial coding task | RPI Agent, or `/rpi-research` when evidence is missing | `/rpi-plan`, `/rpi-implement plan=<path> task=P01-T01`, `/rpi-review task=<slug>` |
| Understand unfamiliar code or an artifact | `/rpi-walkthrough target=<path>` | |
| Pressure-test a plan or decision | `/rpi-challenger subject=<...>` | `/rpi-plan-critique plan=<path>` |
| Review a change before merge | Code Review agent or `/code-review` | Security Reviewer for a security-only pass |
| Write or improve a Copilot customization | `/hve-builder targets=<file> mode=review` (read-only) then `mode=improve` | `/vally-tests` for conformance stimuli |
| Install or change the install method | `hve-core-installer` skill | adoption playbook decision matrix |
| Architecture decision record | ADR Creator agent | `adr-author` skill for capture or template adoption |
| Requirements | BRD Builder, PRD Builder; Meeting Analyst from transcripts (experimental, needs work-iq MCP) | Functional Planner to work items, Backlog Manager to execute |
| Backlog work | `/backlog-plan` (read-only) | `/backlog-execute` (mutating, confirm first) |
| Security model, threat model, standards mapping | Security Planner (experimental) | RAI Planner when AI components exist; `/risk-register` |
| Vulnerability assessment | Security Reviewer | `vex` for VEX statements, `/supply-chain-security` and SSSC agents for supply chain |
| Privacy, accessibility, Responsible AI | Privacy Planner, Accessibility Planner, RAI Planner (experimental); the matching Reviewer for evidence review | `/backlog-templates` for the handoff |
| Documentation audit or drift | Documentation agent | |
| Architecture diagrams | `/c4-architecture`, `/architecture-diagrams` | System Architecture Reviewer |
| Unclear problem, stakeholders not aligned | DT Coach | `/ux-coaching`, `/ux-artifacts`, then hand off to RPI through `dt-rpi-integration` |
| Commit, merge, PR hygiene | `/git-commit` and `/git-merge` (VS Code only), `/pull-request` | `/pr-reference` for a diff bundle |

## MCP servers

Optional; an agent says when a required server is unavailable. Configure `.vscode/mcp.json` at the workspace root (not inside a cloned `hve-core` folder).

| Component | Servers |
| --- | --- |
| `rpi-research`, RPI Agent | `context7`, `microsoft-docs` (RPI Agent varies by activated skill) |
| Functional Planner | `ado`, `microsoft-docs` |
| `/backlog-plan`, `/backlog-execute`, Backlog Manager | `ado` or `github` depending on the tracker; Jira and GitLab use their skills' credentials |
| Meeting Analyst | `workiq` |
| `/dt-figma-export` | `figma` (browser OAuth on first call) |

Sample servers: `context7` (stdio, `npx -y @upstash/context7-mcp`), `microsoft-docs` (http, `https://learn.microsoft.com/api/mcp`), `ado` (stdio, `npx -y @azure-devops/mcp <org>`), `github` (http, `https://api.githubcopilot.com/mcp/`), `figma` (http, `https://mcp.figma.com/mcp`). Node.js and `npx` are needed for the stdio servers.

## Where artifacts go

`.copilot-tracking/` at the repository root, git-ignored, dated folders `YYYY-MM-DD`, kebab-case task slugs, exempt from HVE Core's linting:

| Area | Path |
| --- | --- |
| Research | `.copilot-tracking/research/{date}/{slug}-research.md` |
| Plan and critique | `.copilot-tracking/plans/{date}/{slug}-plan.md`, `.copilot-tracking/reviews/plans/{date}/{slug}-plan-critique.md` |
| Changes | `.copilot-tracking/changes/{date}/{slug}-changes.md` |
| Review | `.copilot-tracking/reviews/logs/{date}/{slug}-review.md` |
| HVE Builder evidence | `.copilot-tracking/hve-builder/{date}/` |
| Planners | `security-plans/`, `sssc-plans/`, `rai-plans/`, `privacy-plans/`, `accessibility/`, `adr-plans/`, `prd-sessions/`, `brd-sessions/`, `workitems/`, `github-issues/`, `jira-issues/`, `dt/<project-slug>/`, `ds/`, `mve/`, `ppt/`, `pr/` |
| Code reviews | `.copilot-tracking/reviews/code-reviews/` |

Plans use stable `Pxx` phase and `Pxx-Txx` task IDs with matching `<!-- rpi:... -->` markers; reviews use `RV-xxx` finding IDs. Session agents keep `state.json` for resume.

## Licensing

Most content is MIT. Skills that embed third-party standards carry their own SPDX `license:` and a Third-Party Attribution section: OWASP knowledge bases are CC BY-SA 4.0 (Docker, CC BY-NC-SA 4.0, is excluded from the plugin); several planning and data-science packs are CC BY 4.0; `secure-by-design` includes OGL-UK-3.0; `vex` includes Apache 2.0. `THIRD-PARTY-NOTICES` in the repository lists them. A team redistributing a fork should route those skills through its own licensing review.
