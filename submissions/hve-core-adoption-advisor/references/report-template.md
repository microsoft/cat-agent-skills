# Report template

Choose the shape by channel first. If the host is Copilot Studio in Teams, or you cannot tell, use the chat shape: send the verdict or recommendation and the first five actions as the first message, then offer sections by name and send each on request; never a table wider than three columns. Use the full structure in Cowork documents, long-form replies, or when the user asks for a report. Cite finding IDs (F1, F2, …) and rule IDs (AG2, WS1, …) wherever a statement rests on the audit, and catalog entries (an agent's `name:`, a skill's slash command, a docs page) wherever it rests on HVE Core. Finding numbers are assigned per run; rule IDs are stable, so cross-reference by rule ID and cite the run you attach.

## What the script's report looks like

The script's Markdown report is the raw audit; the shapes below are what you build from it. A pasted full report has these parts, in this order:

```markdown
# HVE Core workspace audit

| Item | Value |
| Workspace | /path/to/repo |
| Artifacts scanned | 14 (1 global, 6 agent, 4 instruction, 3 skill) |
| Reference date (--as-of) | 2026-10-17 |
| HVE Core catalog | 3.2.2 (2026-10-17); verify against the live repository when it matters |
| HVE Core copies | 5, exempt from convention rules (pass --include-hve-copies to audit them) |
| Rules not evaluated | LY3: no plugin.json at the root (...); WS3: no .hve-tracking.json (...) |
| Not visible to this audit | whether the extension or CLI plugin is installed on a machine, ... |
| Tool | hve_core_workspace_audit.py 1.0.0 |

## Posture summary
| Measure | Value |
| Agents the Copilot CLI would drop | 1 |
| Instructions without applyTo | 1 |
| .copilot-tracking ignored | no (folder present) |
| HVE Core sources detected | extension, copied-artifacts |
## Artifacts needing attention
| Artifact | Kind | High | Medium | Findings |
| .github/agents/team/reviewer.agent.md | agent | 1 | 2 | F3 F4 F5 · F6 |
Workspace-level high and medium findings: F1 (WS1), F2 (WS2).
## Findings
### High (2)
| # | Rule | Artifact | Finding |
| F3 | FM1 | .github/agents/team/reviewer.agent.md | frontmatter could not be parsed (unterminated inline list) Fix: ... |
... and 4 more findings (F9, F10, ...). Use --max-rows to show more or --json for the full list.
### Medium ... ### Low ... ### Info ...
## Remediation plan
### Install source choice
- **WS2 More than one HVE Core source in one workspace**, Medium, 1 finding on the workspace. Keep one HVE Core source. Refs: F2.
### Frontmatter of the artifact ... (one group per control, in the catalog's order)
## Inventory
### Packages / ### Agents / ### Instructions / ### Prompts / ### Skills / ### Deprecated artifacts
### HVE Core sources / ### Workspace files / ### RPI tracking activity
## Method and limits
```

A table that ends with "... and N more" is truncated: those findings exist but are not in the paste. In the attention table, finding IDs before the dot are high or medium and after it low or info. The brief report (`--brief`) keeps a five-row header, one summary line, the attention table, high and medium findings as three-column tables (#, Artifact, Finding with the rule ID in front), one line per low or info rule, a one-line-per-rule remediation plan, and a one-paragraph method note. It is raw input sized for pasting into a chat, not the chat shape you send: its attention table has five columns, so rebuild it into the shapes below. The single-file report (`--file`) has the same shape with workspace rules listed as not evaluated and an inventory table of the parsed frontmatter; for a `copilot-instructions.md` it evaluates WS7 only.

## Orientation

1. **What it is.** Five sentences from the adoption playbook, adapted to the user's words.
2. **How it works.** The four artifact types in one line each; RPI in one line per phase with where artifacts go.
3. **Fit.** Who it suits (teams on VS Code or the Copilot CLI with GitHub Copilot, wanting standards carried through the work; teams with security, privacy, accessibility, or RAI review obligations) and who should wait (teams that cannot accept breaking changes, cannot run MCP servers or Node.js, or need a stable vendor-supported product).
4. **Caveats.** Rapidly evolving; a source of patterns, not a dependency; CLI limitations; non-MIT skill content; experimental labels.
5. **Next step** for this user: install (which method), a first `/rpi-research` on their codebase, or a workspace audit.
6. **To confirm**: anything the catalog dates.

## Install choice

1. **Recommendation** in one sentence naming the method and why (environment, team shape, customization need).
2. **Steps** as a numbered list with the exact commands or Marketplace action, the post-install `.gitignore` line, and MCP setup if a chosen component needs it.
3. **What you give up** with this method (pinning, customization, automatic updates) and the method to move to later.
4. **Troubleshooting entries** that apply to this environment.
5. **Open questions**: VS Code version, Copilot CLI version, Codespaces or dev container, proxy or GitHub Enterprise Server.

## Component match

1. **Component**: `name:` or `/slash-command`, package, maturity label.
2. **How to invoke**, including the agent to select in the CLI, arguments from the argument hint, and the inputs to prepare.
3. **What it needs**: MCP servers, credentials, files, human review gates, confirmation before mutation.
4. **What it produces and where** under `.copilot-tracking/` or in the repository.
5. **Alternatives and companions** from the need-to-component table.
6. **Caveats**: experimental, license, CLI-only or VS Code-only, data handling (Meeting Analyst files, planner state).

## RPI walkthrough

1. **Task statement** in the shape RPI expects: requirements, acceptance criteria, decisions, dependencies, evidence, slug.
2. **Entry point**: RPI Agent (manual or Full Auto) or a phase skill, with the reason.
3. **Phase by phase**: the command with arguments, what to provide, the file it writes, what to check before moving on.
4. **Resume plan**: the paths and IDs to reference, when to `/clear` or `/compact`.
5. **Routing of review findings** and what becomes a new task.
6. **Unverifiable items**: whether MCP servers are configured, which model the session uses.

## Workspace audit

1. **Verdict**: two or three sentences. What the workspace is (artifact counts by kind, packages, HVE Core sources detected), the leading theme, and whether any artifact will not load or will be dropped. Then the **first five actions**, ordered high to medium to low, each with finding IDs, who performs it, and the file to change.
2. **Scope and evidence**: workspace or branch audited, reference date, catalog version, HVE Core copies and whether they were audited, rules not evaluated with the file each needs, what is not visible.
3. **Posture** from the summary table, with n/a where the workspace cannot support a measure.
4. **Findings by theme**: Install source and discovery (WS2, WS8, AG7, LY5, SK1, WS4); Frontmatter that blocks loading (FM1, FM2); Frontmatter that misbehaves or is host-specific (AG1 to AG6, AG8, FM3, FM4, FM6, IN1 to IN3, PR1, SK2); Workspace setup (WS1, WS3, WS5 to WS7); Skills (SK3 to SK6); Body content (CT1 to CT4, LY4); Packaging (LY1 to LY3); Facts to carry forward (FM5, PR2, IN4, IN5, SK5, CT5), as one short list. Build each block around artifacts: the artifact, its findings with consequence, verification, and action, then the roll-up per rule.
5. **Remediation plan** by control, from the script's grouping, with the HVE Core command or skill that applies when the workspace is HVE Core-enabled (`/hve-builder mode=improve`, `hve-core-installer`, `npm run plugin:sync`).
6. **Open questions** for the user (intended install source, whether copied files were edited, whether root-level artifacts are meant for distribution).
7. **Unverifiable items**: user-level extension install, CLI plugin, discovery settings outside the repository, git tracking state, MCP authentication, behavior of the rules.

End with one line saying the audit approximates HVE Core's conventions and is not HVE Core's own validation.

## Artifact review

1. **Verdict** for the one file: loads or not, routes or not, and the single most important fix.
2. **Findings** with rule IDs, consequence, and fix, in the catalog's severity order.
3. **Corrected frontmatter** as a fenced YAML block the user can paste, changing only what the findings require and keeping every capability-bearing field.
4. **What HVE Builder would still check** that this review cannot: instruction quality, model catalog membership, host validation, review rubric verdict.
5. **Open questions**: the intended host (VS Code or CLI), whether the file is distributable, the target agents' names.

## Team rollout

1. **Recommendation**: install method for the team and the first phase's artifacts.
2. **Phased plan** with what each phase adds, who owns it, and the exit criterion.
3. **Governance**: ownership, review, naming and layout, precedence, deprecation path, validation commands when a fork exists.
4. **Onboarding** by role.
5. **Measures** with the baseline to capture first.
6. **Pitfalls** that apply to this team.
7. **Open questions**: repository count, monorepo or many repos, Codespaces or local, GitHub or Azure DevOps or Jira, licensing review needs.

## Compliance or readiness questions

Answer in this shape: the audit evaluated N of 45 convention rules on M artifacts (list the rules not evaluated and the file each needs); it approximates HVE Core's documented conventions and is not HVE Core's own lint; it found X high and Y medium findings on Z artifacts; then the five actions. Never say compliant, ready, or clean.
