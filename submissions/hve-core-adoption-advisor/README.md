# HVE Core Adoption Advisor

Microsoft's [HVE Core](https://github.com/microsoft/hve-core) (Hyper Velocity Engineering) is an opinionated set of GitHub Copilot customizations: agents, instruction files, and skills that carry engineering standards through a Research, Plan, Implement, Review lifecycle, plus planners for security, privacy, accessibility, Responsible AI, requirements, and architecture decisions. This skill helps you adopt it with the facts in hand: what it is, how to install it for your environment, which component answers a given need, how to run work through RPI, how to roll it out to a team, and whether your own repository's Copilot customizations follow HVE Core's conventions.

## What it produces

- **Orientation** in plain terms: the four artifact types, the RPI lifecycle, who HVE Core suits, and the caveats Microsoft itself states (rapidly evolving, a source of patterns rather than a stable dependency, some skill content under non-MIT licenses).
- **An install recommendation** matched to your environment (VS Code, Copilot CLI, GitHub Codespaces, a dev container, team or solo) with the exact steps, the post-install `.gitignore` line, Model Context Protocol (MCP) server needs, and the troubleshooting entries that apply.
- **A component match**: the agent or skill that covers a need (code review, architecture decision records, product requirements documents, security or privacy planning, backlog work, accessibility, documentation, Design Thinking), how to invoke it, what it needs, what it writes and where, and whether HVE Core labels it experimental.
- **An RPI walkthrough** for a concrete task: entry point, what to state up front, the dated artifacts each phase writes under `.copilot-tracking/`, and how to resume.
- **A team rollout plan**: phased adoption, ownership and review rules, naming and layout, deprecation, and measures.
- **A workspace audit** of your repository's Copilot customizations (`.github/agents`, `prompts`, `instructions`, `skills`, `copilot-instructions.md`, plus skills under `.claude/skills` and `.agents/skills`) against 45 convention rules across frontmatter, agents, prompts, instructions, skills, layout and packaging, workspace setup, and body content, with an inventory, findings ranked by severity, and a remediation plan grouped by the control that fixes each rule. Where current VS Code behavior differs from what HVE Core documents, the finding says so. A single-file mode reviews one `.agent.md`, `.prompt.md`, `.instructions.md`, `SKILL.md`, or `copilot-instructions.md`.

Copies of HVE Core's own artifacts in your repository are recognized by path and exempt from the convention rules unless you ask for them. A rule that cannot run because the workspace lacks the file it needs is listed as not evaluated, never as passed.

## Before you start

For orientation, component matching, RPI help, and rollout planning you need nothing: the skill carries a catalog of HVE Core's agents, skills, instructions, install identities, and commands as of HVE Core 3.2.2 (October 2026). HVE Core changes often, so when a detail matters the skill tells you what to confirm against the live repository.

For a workspace audit, point the bundled script at your repository root. It needs Python 3.8 or later and no packages, runs offline, and changes nothing. If your host cannot run Python, run it locally and paste the Markdown report.

```bash
python3 scripts/hve_core_workspace_audit.py . --md report.md --json report.json
python3 scripts/hve_core_workspace_audit.py . --brief                                   # chat-sized
python3 scripts/hve_core_workspace_audit.py . --include-hve-copies                      # audit copied HVE Core files too
python3 scripts/hve_core_workspace_audit.py --file .github/agents/team/reviewer.agent.md  # one artifact
```

## Example prompts

> We are a platform team of 40 engineers on VS Code and Codespaces. Should we adopt HVE Core, and which install method keeps us version-pinned?

> Which HVE Core agent writes an ADR, and what does it need from me before it starts?

> I have a research file from yesterday under .copilot-tracking. How do I continue into planning and implementation without losing it?

> Here is the audit report for our monorepo. What should we fix before we recommend the HVE Core extension to everyone?

> Review this reviewer.agent.md against HVE Core's conventions and give me the corrected frontmatter.

> Draft a three-phase rollout for our team with ownership rules and a deprecation path.

## Good to know

- HVE Core ships through one VS Code extension (`ise-hve-essentials.hve-core`, Stable and PreRelease channels with the same components) and one Copilot CLI plugin (`hve-core@hve-core`, tracking `main`). Clone-based methods and the selective `hve-core-installer` skill exist for teams that need to customize or pin.
- In the Copilot CLI, instruction files do not attach automatically, prompt files do not run, agents are selected with `/agent hve-core:<name>`, and skills that set `disable-model-invocation: true` (twelve in 3.2.2, including the three Git skills) are VS Code only.
- Every install method ends with the same step: add `.copilot-tracking/` to `.gitignore`. The audit checks it.
- The audit's rules approximate HVE Core's documented conventions. They are not HVE Core's own lint commands, which only run inside an HVE Core clone or fork.
- Severity orders the work. It is this skill's heuristic, not a Microsoft rating and not a compliance verdict. Each finding says what to confirm before acting.
- The script sees what is in the repository. A user-level extension install, a CLI plugin, or discovery settings kept outside the repository are invisible to it and are reported as such.
- Finding IDs (F1, F2, …) are numbered per run; a brief or single-file run renumbers them, so quote the run you attach and cross-reference by rule ID.
- Some HVE Core skills carry content under CC BY-SA, CC BY, OGL, or Apache licenses alongside MIT; the catalog marks them so you can route a licensing review.
- The skill reads and reports. It never installs, clones, edits, or runs commands against your repository.

## Compatibility and attribution

This skill is published for Cowork and Copilot Studio. It consists of Markdown instructions plus one standard-library Python script. It relies on the public microsoft/hve-core repository and documentation and on no Microsoft tooling at runtime. It is a community contribution, not a Microsoft product, and does not replace HVE Core's own documentation, its `hve-builder` and `hve-core-installer` skills, or your organization's review.
