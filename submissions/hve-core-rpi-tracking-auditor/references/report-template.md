# Report template

Choose the shape by channel first. In Copilot Studio in Teams, or when you cannot tell, use the chat shape: send the task state (or the lead) and the first actions as the first message, then offer sections by name and send each on request; never a table wider than three columns. Use the full structure in Cowork documents, long-form replies, or when the user asks for a report. Cite finding IDs (F1, F2, …) and rule IDs (PL1, RV4, …) wherever a statement rests on the audit, and artifact paths with section names or marker IDs wherever it rests on the tracking files. Finding numbers are assigned per run; rule IDs are stable.

## What the script's report looks like

```markdown
# HVE Core RPI tracking audit

| Item | Value |
| Workspace | /path/to/repo |
| Tracking folder | .copilot-tracking |
| RPI artifacts (current format) | 6 (1 research, 2 plan, 1 plan critique, 1 changes record, 1 review record) in 3 tasks |
| Legacy artifacts (retired Task Planner format) | 7 in 2 tasks |
| Reference date (--as-of) | 2026-10-17 |
| HVE Core conventions | microsoft/hve-core main at ee3df32 (2026-10-16), read 2026-10-17; ... The VS Code extension (PreRelease 3.3.101 ... and Stable 3.2.2 ...) ships the retired format. |
| Other tracking areas (not audited) | security-plans (1) |
| Session state files | 2 files |
| Symbolic links skipped | none |
| Rules not evaluated | TK6 (--stale-days 0); TK7, TK8, TK9 (no RPI Agent session state file ...) |
| Not visible to this audit | whether a person approved a plan or decided a finding, ... |
| Tool | hve_core_rpi_tracking_audit.py 1.0.0 |

## Summary
42 findings: 3 high, 17 medium, 17 low, 5 info. 4 artifacts need attention plus 2 workspace-level items. 3 tasks on the board, 2 legacy tasks.
## Task board
| Task | State | Phase reached | Plan | Readiness | Execution | Review exec / assessed outcome | Final outcome | Open decisions | Blockers | Undecided RV | Last change |
### Next action per task
- **good-task**: /rpi-implement plan=.copilot-tracking/plans/2026-10-02/good-task-plan.md task=P01-T02 (a blocker is recorded in ...)
### Legacy tasks (retired Task Planner format, not audited)
| Task | Files | Checklist | Last change | Next action |
## Artifacts needing attention
| Task | Artifact | High | Medium | Findings |
## Findings
### High (3) ... ### Medium ... ### Low ... ### Info
| # | Rule | Task | Artifact | Finding |
## Remediation plan
### Secrets / ### Plan markers and headings / ### Completion evidence / ### Cross-artifact links / ### Decisions and gates / ### Session state / ### Template completion / ### Folder layout
- **PL6 Task checked without a changes-record entry**, 1 medium on 1 artifact. Why: ... Verify: ... Fix: ... Refs: F14.
## Inventory
### <task slug>  (artifact table with summaries; plan marker table with Depends on; review finding table with destination and decision)
### <slug> (legacy) / ### Files in RPI areas not matching the naming convention / ### Session state files / ### Other tracking areas / ### Nested tracking folders
## Method and limits
```

How to read it:

- **State** is derived in a fixed order and uses these words: `researching`, `researched`, `planning`, `planned`, `implementing`, `blocked in implementation`, `implemented, not reviewed`, `reviewed, evidence missing` (a review whose plan or changes record is absent), `reviewed, findings open`, `reviewed, decision pending`, `review complete` (execution Complete and a final outcome recorded that is not Conformant), `review partial`, `review blocked`, `review incomplete` (execution not recorded), `accepted`, `unknown`.
- **`accepted`** requires all of: the plan and changes record exist, every plan task is checked, the latest review covers the full task (its `Review scope` names no `Pxx` or `Pxx-Txx`), its execution is Complete, and its Parent Decision Record records a final outcome of Conformant or Conformant with justified divergence. A bounded review, a pending final outcome, or any review written while plan tasks remain unchecked leaves the task in an earlier state.
- **Review exec / assessed outcome** is the Executive Summary, which HVE Core labels the reviewer's proposal. **Final outcome** is Current Disposition. Quote both and keep them apart.
- **Next action** is the command the artifacts' own fields imply, prefixed with a repair note when the task's artifacts carry high findings and suffixed when a blocker is recorded. Rejected and deferred review findings do not produce a route. It is a suggestion to confirm, not something the script ran.
- **Legacy tasks** are listed with checklist progress and a re-plan suggestion; no rule other than LY9 runs on them.
- **Superseded critiques and reviews** (an older file when a `-2` exists) keep their findings at info severity with a "superseded by" note, except HY1, which stays high.
- **Redaction**: any value matching a credential pattern is replaced with `[redacted ...]` before parsing, so every derived field, state value, and both report formats carry the placeholder. Do not look it up in the source file to quote it.
- **Task-filtered runs** (`--task`) drop the other tasks' session state files and their findings, so the report can be handed over without exposing another task's decisions or blockers.
- **Brief report** (`--brief`): six header rows (seven when legacy artifacts exist) plus the rules-not-evaluated row when any rule was skipped; the summary; a four-column board; the attention table; high and medium findings in three columns; one line per low or info rule without finding IDs; a one-line remediation plan per rule with finding IDs only for high and medium. When a user pastes a brief report and a question hangs on a low or info finding, ask for the full report or the JSON.
- **Single-file report** (`--file`): paths are made relative to the parent of the nearest `.copilot-tracking` ancestor, every cross-artifact rule is listed as not evaluated, `--task` is refused, and files in the retired format are refused with a pointer to the workspace run.
- **`--task SLUG`** keeps that task (current or legacy) plus workspace-level findings. A table ending "... and N more" is truncated; ask for `--max-rows` or the JSON before detailing that rule.

## Task status

1. **State in one sentence**: the task, its state from the board, the phase reached, and the plan progress (checked over total tasks), citing the artifact paths.
2. **What the artifacts say**: research readiness and disposition; plan readiness, critique verdict, open decisions; changes execution status, declared scope, blockers, remaining markers; review execution, assessed outcome, final outcome, review scope, undecided findings, their proposed destinations, and any final destination recorded in Decision History.
3. **Integrity**: high and medium findings on this task's artifacts with consequence and fix, each with its finding ID. If none, say the audit found no high or medium findings on N artifacts and name the rules not evaluated.
4. **Next action**: the command from the board, with the arguments spelled out and the file each phase will write, plus what to open or reference first (the first unchecked dependency-ready task's blocks, the latest critique disposition, the Parent Decision Record).
5. **To confirm**: anything only the user or the session knows (whether a decision was really theirs, whether validation ran, which host and HVE Core source).

## Resume brief

For a user about to type the next RPI command:

1. The command with `plan=`, `task=`, `research=`, or `changes=` arguments as workspace-relative paths.
2. The artifact that phase reads first and the IDs to look at, with the advice to open it in the editor or reference its path in the prompt.
3. The artifact it will write.
4. Whether to start a fresh chat or `/clear` (a new task, a changed lifecycle concept, or visible degradation), and that HVE Core prefers resuming from the artifacts over `/compact`.
5. The blockers, open decisions, or undecided findings that the phase will stop on.
6. One line on anything the audit found that should be repaired first (high findings on the plan, a stale marker, a missing critique result).

## Handover

For a teammate taking over one or several tasks:

1. A board of tasks with state, plan progress, blockers, and next action.
2. Per task: the decisions already confirmed (Confirmed User Direction); the decisions still open (Planning Decisions and Feedback rows, undecided RV findings, a pending final outcome); the blockers with owner; the follow-up items; the artifact paths in phase order.
3. Legacy tasks with their checklist progress and the note that they need the retired agents or a re-plan.
4. The integrity findings to repair before continuing.
5. What the handover cannot carry: chat context; the RPI Agent's mode and participation preferences unless a state file records them; who approved what; anything outside the tracking folder.
6. The fresh-chat advice and the first command for each task.

## Integrity audit

1. **Lead**: two or three sentences. How many tasks and artifacts the folder holds (current and legacy), the leading theme (markers, completion evidence, cross-artifact links, decisions, layout), and whether any artifact cannot be navigated or exposes a secret. Then the **first five actions**, ordered high to medium to low, each with finding IDs, the file, and who performs it.
2. **Scope and evidence**: workspace, reference date, HVE Core source and the host's version, artifacts by kind, tasks, legacy tasks, other areas not audited, state files found, symbolic links skipped, nested folders, rules not evaluated with the reason, what is not visible.
3. **Task board** from the script, with next actions, and the legacy table.
4. **Findings by theme**, in the eight controls of the rule catalog and in its heading order (Secrets first, Folder layout last). Build each block around tasks and artifacts, then roll up per rule.
5. **Remediation plan** by control, from the script's grouping. Name the HVE Core step that repairs each where one exists: `/rpi-plan task=<slug>` to revise a plan, `/rpi-plan-critique` for a missing result, `/rpi-review` to decide findings, and for stale markers `/rpi-implement plan=<path> task=<Pxx-Txx>` on the affected scope, whose flow begins by bringing the plan checklist and changes record current. HVE Core has no dedicated repair command; marker and metadata edits are otherwise plain-text edits the user makes, delivered as text.
6. **Open questions**: which tasks are still active, whether older dated files are superseded, whether two slugs are one renamed task, whether a nested folder was intentional, whether a state file belongs to a finished session, which HVE Core source wrote the legacy files.
7. **Unverifiable items**: human approval, chat history, host and model, validation execution, git tracking state.

End with one line saying the rules approximate HVE Core's documented conventions and are not HVE Core's own validation.

## Review routing

For a review record:

1. Execution, assessed outcome, and final outcome as recorded, kept apart, and the review scope (full task or bounded).
2. A table of `RV-xxx` findings with severity, proposed destination, final destination from Decision History (or `-`), and decision (or undecided).
3. What each destination means in commands: `/rpi-implement plan=...` for defects, `/rpi-plan task=...` for decision gaps, `/rpi-research topic=...` for evidence gaps, a separate task for follow-ups. This matches HVE Core's own iteration table (Conformant: commit; Defects found: Implement; research gap: Research; decision gap: Plan; residual work: a follow-up owner). Rejected and deferred findings do not route.
4. The findings that must be decided before the final outcome can be recorded, and whether the assessed outcome is consistent with the decisions so far (RV6).
5. The validation evidence and its limitations.
6. The next action.

## Artifact review

For one file passed with `--file`:

1. What kind of artifact it is and the task it belongs to.
2. Whether a downstream phase can navigate it (markers, IDs, required sections).
3. The findings with rule IDs, consequence, and fix in severity order.
4. The cross-artifact rules that could not run and the workspace command that evaluates them.
5. The corrected fragment as a fenced Markdown block when the fix is a marker, heading, or metadata line, changing only what the findings require.

## Compliance or readiness questions

When asked whether a task is "done", "ready", or "clean": say what the artifacts record (execution status, assessed and final outcome, readiness, checked markers over total); what the audit evaluated (N of 67 rules on M artifacts, rules not evaluated and why); what it found (X high and Y medium findings on Z artifacts); and that the rules approximate HVE Core's conventions. Never call a task done, ready, or clean on the audit's authority. The review record's Parent Decision Record is the record of acceptance, and only a person can say whether the human gates were theirs.
