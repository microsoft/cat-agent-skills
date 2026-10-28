# Artifact catalog

What HVE Core writes under `.copilot-tracking/` for a task that runs through RPI (Research, Plan, Implement, Review), how the files are named, which sections and identifiers each one carries, and which status vocabularies the phases read.

**Source and versions.** Read from `microsoft/hve-core` `main` at commit ee3df32 (2026-10-16) on 2026-10-17: the `copilot-tracking` and `copilot-tracking-location` instruction files, the templates and references of the seven `rpi-*` skills, the RPI Agent's state contract, and the `docs/rpi` pages. `main` is what the Copilot CLI plugin (`hve-core@hve-core`) and clone-based installs track. `main` is not a release-please target, so its `package.json` still reads 3.2.2 and that number says nothing about how current its content is. The VS Code extension's PreRelease channel is at 3.3.101 (published 2026-04-25; odd minor versions are PreRelease) and its Stable channel at 3.2.2 (2026-03-23). Both ship the retired Task Researcher, Task Planner, Task Implementor, and Task Reviewer agents and the `/rpi` prompt, which write a different artifact set described in the last section. HVE Core evolves quickly (Microsoft calls it rapidly evolving); when a section name, field label, or vocabulary word matters, confirm it against the live repository.

## Where the folder lives

`.copilot-tracking/` sits directly under the codebase root, which is the root of the open workspace folder (the first folder of a multi-root workspace, never an added HVE Core clone). HVE Core's install guide tells every install method to add it to `.gitignore`, and the location instruction says it is usually git-ignored, so most search tools skip it; HVE Core tells its agents to search with ignored files included, and an empty search result is inconclusive until the folder is read directly. Durable working state lives in these files, not in chat: a resume reads the artifacts and their IDs.

Dates are ISO `YYYY-MM-DD` folders directly under the area. `{{task_slug}}` is lower-kebab-case and is reused across every artifact of the task. Generated tracking Markdown starts with `<!-- markdownlint-disable-file -->`, uses no `#file:` directives and no line numbers, and navigates by stable IDs, markers, and headings. Plans and changes records are read by people in an editor: code, commands, and symbols go in backticks, existing files are Markdown links whose text is the workspace-relative path and whose destination is relative to the artifact file (a repository file is three levels up, a sibling tracking artifact two levels up). Research, critique, and review artifacts use plain workspace-relative paths without links or backticks.

## Areas and file names

| Area | File | Written by | Consumed by |
| --- | --- | --- | --- |
| `research/{date}/` | `{slug}-research.md` (the primary research artifact) | `/rpi-research`, RPI Agent | `/rpi-plan`, planners that delegate research |
| `plans/{date}/` | `{slug}-plan.md` | `/rpi-plan` (kept current by `/rpi-implement`) | `/rpi-plan-critique`, `/rpi-implement`, `/rpi-review` |
| `reviews/plans/{date}/` | `{slug}-plan-critique.md`, follow-ups `-plan-critique-2.md`, `-3.md` | `/rpi-plan-critique` | `/rpi-plan` (disposition), `/rpi-review` |
| `changes/{date}/` | `{slug}-changes.md` (the changes record) | `/rpi-implement` | `/rpi-review`, the next `/rpi-implement` |
| `reviews/logs/{date}/` | `{slug}-review.md`, re-reviews `-review-2.md` (the review record, written from `templates/review-log.md`) | `/rpi-review` | RPI Agent follow-up, the user |
| `challenges/{date}/` | `{slug}-challenge.md` | `/rpi-challenger` | the user |
| `walkthroughs/{date}/` | `{slug}-decisions.md` (the decisions-and-changes ledger) | `/rpi-walkthrough` | the user, RPI follow-ons |
| `hve-builder/{date}/` | `{artifact_slug}-{stage}-{attempt}.md` | `/hve-builder` | HVE Builder resume |
| `proposal-responses/{slug}/` | `response-evidence.yml` | `/proposal-response` | that skill |

HVE Core's prose calls the files the research artifact, the plan, the plan critique (or critique artifact), the changes record, and the review record; the docs also say "review log" for the last one, after its template name. This skill uses the prose names.

Other folders (`security-plans`, `sssc-plans`, `privacy-plans`, `rai-plans`, `accessibility`, `adr-plans`, `prd-sessions`, `brd-sessions`, `workitems`, `github-issues`, `jira-issues`, `dt`, `ux-artifacts`, `ux-coaching`, `ds`, `mve`, `ppt`, `demo-material`, `pr`, `prompts`, `documentation`, `reviews/code-reviews`, `reviews/architecture`, `security`, `sssc-reviews`, `privacy-reviews`, `rai-reviews`) belong to the planner, reviewer, coach, and builder agents and skills. They keep their own `state.json` and phase files and are outside this skill's rules; the script lists them so the user knows they exist.

## Identity and markers

- One stable **task ID** across plan, critique, changes, and review (`* Task ID:` in each Metadata section). HVE Core keeps `task_id` and `task_slug` as two fields and does not say how the ID is formed; in practice it is often the slug, but compare them as two fields.
- **Phases** are `Pxx`, **tasks** `Pxx-Txx`. The marker `<!-- rpi:phase id=P01 -->` or `<!-- rpi:task id=P01-T01 -->` sits immediately before the matching heading, which carries the checkbox: `### [ ] P01: name`, `#### [x] P01-T01: name`. During planning the planner may renumber; once implementation starts, IDs are the join key for the changes record and review.
- **Critique findings** are `PC-xxx` with `<!-- rpi:critique id=PC-001 -->`. The ID is minted only in the critique; the plan's Critique Disposition table and the changes record's planning-and-critique-state lines cite it. A follow-up critique continues the numbering.
- **Review findings** are `RV-xxx` with `<!-- rpi:review id=RV-001 -->`; decisions about them are `RD-xxx` events in the review's Decision History.
- **Requirements** are `FR-nnn` and `NFR-nnn` in the plan; every one is cited by at least one task's `Requirements:` block.
- **Evidence** in research is `C#` (codebase, path plus heading or symbol) and `W#` (external, title, URL, retrieval date).
- The changes record has no identity scheme of its own: entries use descriptive headings and name the `Pxx` or `Pxx-Txx` they complete.

## Research artifact

Sections in order: a header table (Date, Researcher / agent, Output mode: convergence, analysis, audit, comparison, research-only, no-handoff), `## Executive Summary` (Bottom line, Why this matters, Research status, Confidence and uncertainty), `## What You May Not Know`, `## Findings` (one H3 per finding with Questions, Evidence state, Evidence, Confidence and limits), `## Recommendation and Alternatives`, `## Scope and Questions` (Q1… table with open, answered, blocked), `## Decisions and Feedback` (D1… groups with confirmed, proposed, deferred, unresolved, input requested), `## Risks and Open Questions`, `## Planning Readiness and Next Step`, and `## Research Record` (Method and Boundaries, Extensions and Participation, Research Cycle Log with Wider, Deeper, Contrarian waves per cycle, Evidence Log, Contradictions and Conflicts, Artifact Self-Check).

The **Planning Readiness and Next Step** table is the continuation record. Rows: Research disposition (`executed`, `reused`, `satisfied-and-skipped`; only `executed` applies to a standalone run), Decision participation, Planning Readiness (`Ready`, `Not ready`, `Not applicable`, `Blocked` with evidence IDs and reason), Research depth and helpers, Blockers, Output mode and planning support, Continuation owner (`user`, `manual RPI Agent`, `confirmed automatic RPI Agent`), Required gates or confirmations, Next action, Primary evidence file.

Research is read-only and writes only inside `research/` (or a caller's trusted alternate evidence root). Research is re-entered, not skipped, when a material gap remains; a user-directed skip of an optional step is not a gap.

## Plan

Section order (the planning reference fixes it): `## Task Metadata` (Task ID, Task slug, Plan date), `## Executive Summary` with `### What You May Not Know`, `## Phase Checklist` (Before and After Mermaid diagrams, then phases and tasks), `## User Decisions and Requirements` (`### Confirmed User Direction` list, `### Planning Decisions and Feedback` table with Group, item, Status, Owner, Rationale or input needed, Evidence, Planning impact), `## Planning Readiness and Next Step`, then `## Goals`, `## Scope and Non-Goals`, `## Functional Requirements`, `## Non-Functional Requirements`, `## Risks and Open Questions`, `## Dependencies`, `## Sources` when they hold content, then `## Critique Disposition`, `## Artifact Self-Check`, `## Follow-Up Items` (initialized `* None`, immediately before Handoff), `## Handoff`.

Each **phase** has `Goals:`, `Dependencies:`, a phase diagram, and `Highlighted work:`. Each **task** has `Goals:`, `Requirements:` (cites FR and NFR IDs and binding conditions), `Details:`, optional `Guidance:` (added by implementation when earlier work created something a later task needs), `References:`, `Dependencies:`. A task carries no status, acceptance, or validation block: completion is the `[x]` marker plus the changes record. Open decisions live in Planning Decisions and Feedback and risks in Risks and Open Questions, each naming the affected `Pxx-Txx`.

**Planning Readiness and Next Step** rows: Planning execution and readiness (`Complete`, `Partial`, `Blocked`, `Needs clarification` and `Ready`, `Not ready`, `Blocked` with reason), Decision participation, Blockers, Latest critique (link with verdict, or `skipped` with provenance), Relevant research, Plan path, Changes-record role, Continuation owner, Required gates or confirmations, Next action.

**Critique Disposition** records setting and provenance (`standard`, `deep`, `skip`), status (`not run`, `started`, `skipped`, `Complete`, `Partial`, `Blocked`, `not produced`), latest critique path with verdict (`Pass`, `Revise`, `Blocked`, `unavailable`, or not applicable when skipped), earlier critiques, limitations, and a table with one row per `PC-xxx` (disposition `resolved`, `superseded`, `accepted with risk`, `open`; action owner; exact resolving evidence; decision route; plan response or residual risk). The `rpi-plan` skill says a critique that returned no result is never treated as a Pass; this skill reads that as readiness staying Not ready until a result exists or the user or parent records a skip. An implementation-ready plan is not a human sign-off; human review applies only where an instruction, domain artifact, or explicit user requirement names it.

## Plan critique

`## Metadata` (Task ID, Critique date, Plan path, Critique execution `Complete`, `Partial`, `Blocked`, `not produced`, Critique depth `standard` or `deep`, Depth provenance, Critique type `initial` or `follow-up`, Earlier critique), `## Inputs and Criterion Boundary`, `## Coverage Assessment` (Covered, Partial, Missing per requirement, research, phase, or task ID), `## Verdict` (`Pass`, `Revise`, `Blocked`, or `unavailable` when no assessment was produced), `## Earlier Finding Reconciliation` (follow-up only: resolved, still open, superseded), `## Findings` (one `PC-xxx [Critical|High|Medium|Low]` per finding with Related IDs, Evidence, Concern, Impact, Smallest useful change, Action owner, Exact resolving evidence, Decision route), `## Strengths and Residual Risk`, `## Questions or Blocking Evidence Gaps`, `## Limitations`, `## Recommended Next Action`. The critique never edits the plan.

## Changes record

`## Metadata` (Task ID, Related plan link, Implementation date), `## Execution Status` (Status `Complete`, `Partial`, `Blocked`; Declared invocation scope `full plan`, `Pxx`, or `Pxx-Txx`; Completed scope markers; All remaining active-plan markers; Status basis), `## Execution Summary`, `## Completed Work` (one H3 per completed item with Related phase or task, Files, Behavior or functionality changed, Validation `passed`, `failed`, `skipped`, `unavailable` with reason), `## Implementation-Time Plan Updates` (one H3 per plan update with affected markers, what changed, why, triggering evidence, user decision, reconciliation performed, planning and critique state), `## Business Alignment` (`None` or one entry per affected BRD, PRD, or ADR requirement with Alignment `clarification`, `divergence-confirmed`, `source-gap`, `pending-decision`), `## Validation Record` (Check, Scope, Status `Passed`, `Failed`, `Skipped`, `Unavailable`, Evidence or reason), `## Pre-Review Reconciliation` (Review readiness `ready` or `not ready` with reason), `## Blockers`, `## Remaining Work`, `## Follow-Up Items` (mirrors the plan's list), `## Return-to-Caller State`.

Implementation rules the audit leans on: the first unchecked dependency-ready item in declared scope starts first; a `Pxx-Txx` is checked immediately after its changes entry exists; a `Pxx` is checked only when every task in it is checked and the phase is in scope; nothing outside declared scope is checked; a bounded scope confirms only its markers and lists all remaining markers; a `pending-decision` alignment blocks review readiness; before handoff to review, `rpi-implement` brings plan markers, entries, blockers, remaining work, follow-ups, and validation current. HVE Core has no dedicated repair command for a stale plan; that reconciliation step, run on the affected scope, is the closest thing, and anything else is a plain-text edit.

## Review record

`## Executive Summary` (Assessment, Why this matters, Review execution `Complete`, `Partial`, `Blocked`; Assessed outcome `Conformant`, `Conformant with justified divergence`, `Defects found`, `Residual work`, `Not accepted`; Validation coverage; Confidence and limitations), `## What You May Not Know`, `## Findings and Proposed Routes` (one `RV-xxx [severity]` per finding with Related scope, Expected behavior, Observed behavior and evidence, Impact, Resolution condition, Proposed destination `rpi-implement`, `rpi-plan`, `rpi-research`, or `follow-up`, Smallest useful next action), `## Parent Decision Record` (`### Current Disposition` with Final outcome, projected from `### Decision History`, an append-only table of `RD-xxx` events with Subject, Decision source, Status or value `accepted`, `rejected`, `deferred`, `changed`, Proposed and Final destination, Owner, More information needed, Smallest next action, Rationale), `## Validation Evidence`, `## Risks, Blockers, and Residual Work`, optional `## Stakeholder Note Draft`, `## Review Record` (Scope and Evidence with Task ID, Review date, Review scope `full task`, `Pxx`, or `Pxx-Txx`, depth, Plan, Plan critique, Changes paths; Opening Review State; Acceptance and Change Coverage with Met, Gap, Not assessed; Critique and Follow-Up Assessment; Reviewer Self-Check).

**The assessed outcome is the reviewer's proposal.** The template says so in its first lines: "Parent Decision Record contains the final decisions and next actions, or states that decisions are pending." Acceptance is the `Final outcome` under Current Disposition (Conformant or Conformant with justified divergence), and it is `pending` until the parent has decided every finding. Execution and outcome are separate vocabularies and never substitute for each other. Routing: implementation defects to `rpi-implement`; decision gaps and invalid assumptions to `rpi-plan`; material evidence gaps to `rpi-research`; non-blocking residual work to a distinct follow-up owner, never described as a defect. Material skipped or deferred findings prevent `Conformant` and `Conformant with justified divergence`. A bounded review (`Review scope` names a `Pxx` or `Pxx-Txx`) accepts only that scope. The review is read-only and writes only its own record; a later `/rpi-implement` may implement review findings as ordinary work without a second mandatory review.

## Challenge session and decisions-and-changes ledger

`{slug}-challenge.md`: Session Details (Date, Status `In progress`, `Complete`, `Partial`, `Blocked`, Record path, Scope source, Focus), Confirmed Scope, Related Artifacts, Challenge Coverage (explored, unresolved, skipped, out of scope), Q&A Log, Unresolved Items with a suggested next owner (`user`, `rpi-research`, `rpi-plan`, `rpi-implement`, `rpi-review`, `none`), Session Outcome. `{slug}-decisions.md`: Material decisions and Requested changes tables with Reconciliation `open`, `applied now`, `handed off`, `deferred`, `declined`. The script inventories both and applies only the layout rules to them.

## RPI Agent session state

The RPI Agent persists one JSON object per session. HVE Core documents the fields, not a fixed path, so the script recognizes a state file by shape: a JSON file under `.copilot-tracking/` with at least `task_slug`, `active_phase`, and `artifact_paths`. Stable fields: `task_id`, `task_slug`, `parent_task`, `mode` (`manual`, `automatic`), `active_phase` (`Research`, `Plan`, `Implement`, `Review`, `Follow-up`), `status` (`active`, `blocked`, `completed`; the task), `session_status` (`running`, `stopped`; distinct from the task status), `artifact_paths` (keys `research`, `plan`, `critique`, `changes`, `review`), `confirmed_decisions` (including `Automatic session scope`, `Automatic progression boundary` `through-review` or `before-implementation`, per-phase decision participation `agent-owned` or `user-retained`, `Planning critique` `standard`, `deep`, `skip`, `Review step` `run` or `skip`), `blockers`, `next_action` (`phase`, `action`), `prioritized_follow_ups`. State is written before and after every transition; on recovery the agent reconciles it against the canonical artifacts, and the artifacts win.

## Commands and arguments

Argument hints as declared in each skill's frontmatter on `main`:

| Command | Arguments | Reads | Writes |
| --- | --- | --- | --- |
| `/rpi-research` | `[topic=...] [posture={balanced\|focused\|expansive}] [chat]` | codebase, external sources, prior research | `research/{date}/{slug}-research.md` |
| `/rpi-plan` | `[task=...] [research=...] [context=...] [draft=...] [decisions=...] [critique={standard\|deep\|skip}]` | research, user direction | plan, and the critique through `/rpi-plan-critique` |
| `/rpi-plan-critique` | `[plan=...] [evidence=...] [output=...] [depth={standard\|deep}] [prior=...]` | plan, research | `reviews/plans/{date}/{slug}-plan-critique.md` |
| `/rpi-implement` | `[plan=...] [phase=...] [task=...]` | plan, critique disposition, prior changes | `changes/{date}/{slug}-changes.md`, plan markers and Guidance blocks |
| `/rpi-review` | `[task=...] [plan=...] [changes=...] [depth={standard\|deep}]` (the lifecycle docs also pass `critique=` and `research=`) | plan, critique, changes, validation | `reviews/logs/{date}/{slug}-review.md` |
| `/rpi-challenger` | `[subject=...] [artifacts=...] [focus=...]` | any artifact | `challenges/{date}/{slug}-challenge.md` |
| `/rpi-walkthrough` | `[target=...] [detail={brief\|normal\|deep}] [chat]` | code or artifacts | `walkthroughs/{date}/{slug}-decisions.md` |

RPI Agent wraps the phases under one task identity (manual by default, Full Auto on explicit authorization, with a `before-implementation` boundary available). In VS Code it is selected as **RPI Agent** in the agent picker; in the Copilot CLI with `/agent hve-core:rpi-agent` or `copilot --agent hve-core:rpi-agent`. The seven phase skills are `user-invocable: true` and run in both hosts. In the CLI, instruction files are not attached automatically, so artifacts written there may not have had the copilot-tracking conventions applied.

## Resuming

HVE Core's context-engineering guidance: continuity comes from the dated artifacts, not chat. Resume by opening the artifact in the editor before invoking the next skill, or by referencing its path in the prompt, and by naming the stable IDs: `/rpi-implement plan=.copilot-tracking/plans/2026-10-02/{slug}-plan.md task=P01-T02`. What to open at each transition: research into plan, the research artifact; plan into implement, the plan and its critique; implement into review, the changes record with the plan and critique; review into follow-up, the review record. Implementation resumes from the first unchecked dependency-ready item in declared scope after reading prior changes entries, current markers, and the latest critique disposition; it does not resume a task awaiting a user decision. Review reads the Parent Decision Record before rebuilding stale projections.

Use `/clear` or a new chat when switching tasks, when changing lifecycle concepts, or when behavior has visibly degraded (skipped readiness checks, dropped instructions, shallow output, patterns echoed from earlier tasks). `/compact` remains a typed command for a long mid-phase conversation, but HVE Core removed it from agent handoff buttons because Autopilot mode could trigger compaction loops that degraded context, and its guidance is to resume from the artifacts rather than rely on it. When several artifact sets exist, reference the intended path explicitly so the resumed work uses the right task identity.

**Team handoffs.** HVE Core's own summary of what the artifacts carry: the research artifact explains decisions; the plan shows remaining `Pxx` and `Pxx-Txx` work and the context needed to implement it; the changes record shows completed work, validation, and implementation-time plan updates with their rationale; the review record shows separate execution status, outcome, findings, and routing. Nothing carries the conversation or, unless a state file records them, the RPI Agent's mode and participation preferences.

## The retired Task Planner format

The VS Code extension releases through 3.3.101 (and the Stable 3.2.2 release) ship the earlier RPI: agents **Task Researcher**, **Task Planner**, **Task Implementor**, **Task Reviewer** (with Researcher Subagent, Plan Validator, Phase Implementor, RPI Validator, Implementation Validator) and the prompts `/rpi`, `/task-research`, `/task-plan`, `/task-implement`, `/task-review`. On `main` these are retired; the migration guide maps `/rpi` to the RPI Agent. Their artifacts:

| File | Shape |
| --- | --- |
| `research/{date}/{topic}-research.md` and `research/subagents/{date}/{topic}-research.md` | prose research with file references and line numbers |
| `plans/{date}/{task}-plan.instructions.md` | frontmatter `applyTo:` the changes file; `## Overview`, `## Objectives`, `## Context Summary`, `## Implementation Checklist` with `### [ ] Implementation Phase N:` headings, `<!-- parallelizable: true -->` comments, `* [ ] Step N.M:` items pointing at details line ranges; `## Planning Log`, `## Dependencies`, `## Success Criteria` |
| `details/{date}/{task}-details.md` | step details with line-number references |
| `plans/logs/{date}/{task}-log.md` | planning log with `DR-`/`DD-` discrepancy items and follow-on work |
| `changes/{date}/{task}-changes.md` | changes log by category (files added, modified, removed; additional or deviating changes) |
| `reviews/{date}/{plan-name}-review.md` or `-plan-review.md`, `reviews/rpi/{date}/{name}-NNN-validation.md` | review log and per-phase validation outputs |

The current `rpi-*` skills do not read this layout, and HVE Core publishes no converter. The script recognizes these files by path, and research or changes files by content (the markers above, taken from the 3.3.101 agent templates, which no longer exist on `main`) or by legacy siblings of the same slug; it lists them per task with checklist progress (`[x]` over all checkboxes) and does not apply the current rules to them. The options are to finish the task with the agents that wrote it, or to re-plan with `/rpi-plan task=<slug> draft=<old plan path>` and cite the old research and changes as context.
