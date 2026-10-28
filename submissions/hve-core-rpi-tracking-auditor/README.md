# HVE Core RPI Tracking Auditor

Microsoft's [HVE Core](https://github.com/microsoft/hve-core) (Hyper Velocity Engineering) runs engineering work through a Research, Plan, Implement, Review (RPI) lifecycle. It keeps the state of every task in dated Markdown files under a git-ignored `.copilot-tracking/` folder: a research artifact, a plan with `Pxx` and `Pxx-Txx` markers and checkboxes, a plan critique with `PC-xxx` findings, a changes record, and a review record with `RV-xxx` findings and decision events. Continuity lives in those files, not in chat. This skill reads them and tells you where each task stands, which `/rpi-*` command continues it, what a teammate needs to take it over, and whether the files still agree with each other well enough for HVE Core's skills to resume from them.

## What it produces

- **Task status**: the state of a task derived from its artifacts (for example `planned`, `implementing`, `blocked in implementation`, `implemented, not reviewed`, `reviewed, findings open`, `reviewed, decision pending`, `accepted`). With it: plan progress as checked tasks over total, the critique verdict, open decisions, blockers, undecided review findings, the review's assessed and final outcome kept apart, and the next command with its `plan=`, `task=`, `research=`, or `changes=` arguments filled in.
- **A resume brief** for the next session: the command, what that phase reads first and writes, whether to start a fresh chat, and the repairs to make before running it.
- **A handover** for a teammate: a board of tasks, the confirmed and open decisions, blockers, follow-ups, artifact paths, and what the files cannot carry (chat context, the RPI Agent's mode unless a state file records it).
- **An integrity audit** against 67 rules across folder layout, plan markers and headings, completion evidence, cross-artifact links, decisions and gates, RPI Agent session state, template completion, and secrets, with findings ranked by severity and a remediation plan grouped by the control that fixes each rule. Examples of what it catches: a marker that does not match its heading; a phase checked over an unchecked task; a checked task with no changes entry; a plan marked ready without a critique result; a review assessed conformant with an undecided high finding or a pending final outcome; a state file pointing at a missing artifact; a token pasted into a research artifact.
- **Review routing**: each `RV-xxx` finding with its severity, proposed destination (`rpi-implement`, `rpi-plan`, `rpi-research`, follow-up), the final destination once Decision History records one, and decision, and what must be decided before the final outcome can be recorded.
- **A single-artifact review** of one plan, critique, changes record, review record, or research file.
- **A legacy inventory**: tasks written by the retired Task Planner agents (see below) listed with their checklist progress and a re-plan suggestion.

Other `.copilot-tracking/` areas written by HVE Core's planner, reviewer, coach, and builder agents (security plans, ADRs, PRDs, Design Thinking, and so on) are listed so you know they exist, not audited. A rule that cannot run is listed as not evaluated, never as passed.

## Before you start

Point the bundled script at your repository root. It needs Python 3.8 or later and no packages, runs offline, follows no symbolic links (it lists the ones it skipped), and changes nothing. If your host cannot run Python, run it locally and paste the Markdown report (`--brief` for a chat-sized one).

```bash
python3 scripts/hve_core_rpi_tracking_audit.py . --md report.md --json report.json
python3 scripts/hve_core_rpi_tracking_audit.py . --brief                       # chat-sized
python3 scripts/hve_core_rpi_tracking_audit.py . --task split-exporter         # one task
python3 scripts/hve_core_rpi_tracking_audit.py --file .copilot-tracking/plans/2026-10-02/split-exporter-plan.md
```

`--stale-days N` sets the threshold for reporting an open task as stale (default 30; 0 disables it), `--as-of YYYY-MM-DD` fixes the reference date, `--max-rows N` lengthens tables (default 25). `--task` limits the whole report, session state files included, to one task, so it is safe to hand over. `--file` refuses a path that passes through a symbolic link.

## Example prompts

> Where does the split-exporter task stand, and what do I type to continue it?

> I'm handing my three RPI tasks to a colleague tomorrow. Give them everything the tracking folder knows and what it doesn't.

> rpi-implement keeps redoing P01-T02. Here is the audit report. What's inconsistent?

> Here is the review record. Which findings go back to implementation, which need a planning decision, and is the outcome actually final?

> Review this plan file against HVE Core's conventions before I run /rpi-plan-critique on it.

> Is anything in .copilot-tracking stale or orphaned? We have been using RPI for two months.

## Good to know

- **Which HVE Core you run matters.** The conventions here come from `microsoft/hve-core` `main` (commit ee3df32, 2026-10-16, read 2026-10-17), which the Copilot CLI plugin and clone installs track. The VS Code extension (PreRelease 3.3.101, published 2026-04-25; Stable 3.2.2, 2026-03-23) still ships the earlier RPI agents (Task Researcher, Task Planner, Task Implementor, Task Reviewer), which write `{slug}-plan.instructions.md`, a `details/` folder, planning logs, and line-number references. The script lists those tasks as legacy with their checklist progress and does not audit them; the current skills cannot resume them and HVE Core publishes no converter. HVE Core evolves quickly; when a section name or vocabulary word matters, the skill tells you to confirm it against the live repository.
- The tracking folder sits at the codebase root and is normally git-ignored, so most search tools skip it. The script reads it directly; the audit checks the `.gitignore` line but does not run `git` and cannot tell whether files were already committed.
- The newest dated file of each kind is treated as the task's current artifact. Older ones are listed so you can confirm whether they are superseded.
- State and next action are derived from the artifacts' own status fields and markers. They are suggestions to confirm, not commands the script ran, and the skill never runs `/rpi-*` commands or edits your files.
- HVE Core keeps execution status (Complete, Partial, Blocked) apart from outcome (Conformant, Defects found, and so on) and readiness (Ready, Not ready), and a review's assessed outcome is the reviewer's proposal until the Parent Decision Record records a final outcome. The skill quotes those words as written.
- The RPI Agent's session state is a JSON file whose path HVE Core does not fix; the script recognizes it by its fields. If none is found, the agent's mode and participation preferences live only in the conversation that set them.
- In the Copilot CLI the RPI Agent is selected with `/agent hve-core:rpi-agent`, and instruction files are not applied automatically, so formatting-convention findings on artifacts written there may come from the host rather than from drift.
- Severity orders the work. It is this skill's heuristic, not a Microsoft rating and not a verdict on the task or the team. Each finding says what to confirm before acting.
- Secrets detection covers a few exact token shapes and one assignment pattern. Matched values are replaced with `[redacted ...]` before any field is parsed, in Markdown artifacts and in session state JSON (where a value under a key named like `token`, `password`, `secret`, or `api_key` is also replaced), so a report can be pasted into a chat; the finding gives the file and line. A clean result is not an assurance that no secret was recorded.
- Finding IDs (F1, F2, …) are numbered per run; a brief, task-filtered, or single-file run renumbers them, so quote the run you attach and cross-reference by rule ID.
- For installing HVE Core, choosing components, writing agents and skills, or auditing `.github` customizations, use the HVE Core Adoption Advisor skill instead.

## Compatibility and attribution

This skill is published for Cowork and Copilot Studio. It consists of Markdown instructions plus one standard-library Python script. It relies on the public microsoft/hve-core repository and documentation and on no Microsoft tooling at runtime. It is a community contribution, not a Microsoft product, and does not replace HVE Core's own documentation, its RPI skills and RPI Agent, or your team's review.
