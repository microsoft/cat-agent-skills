# Rule catalog

The 67 rules `scripts/hve_core_rpi_tracking_audit.py` evaluates on the RPI artifacts under `.copilot-tracking/`, what each means, and where the fix lives. Titles are the script's titles, so a report line can be matched here by rule ID or title. They approximate the conventions on `microsoft/hve-core` `main` at ee3df32 (2026-10-16), read 2026-10-17: `copilot-tracking.instructions.md`, `copilot-tracking-location.instructions.md`, the templates and references of `rpi-research`, `rpi-plan`, `rpi-plan-critique`, `rpi-implement`, and `rpi-review`, and the RPI Agent's state contract. HVE Core has no validation of its own for tracking artifacts (the folder is exempt from its Markdown lint), so these rules are this skill's reading, not Microsoft's.

Severity is a review heuristic for ordering work, not a rating and not a verdict on the task: **high** means a downstream RPI phase cannot navigate the artifact, or a secret is exposed; **medium** means artifacts disagree in a way that misleads a resume or a review, or a gate is bypassed; **low** means convention or template completeness; **info** means a fact for the task board, not a defect. Count artifacts and tasks, not findings, when stating scale.

The newest dated file of each kind is the task's current artifact; earlier ones are listed under TK5. A rule is "not evaluated" when the run lacks what it needs (no tracking folder, no state file, `--stale-days 0`, a single-file run); that says nothing about conformance. Symbolic links are never followed and are listed in the header. A nested `.copilot-tracking` folder is listed and not read. Files in an RPI area whose names do not match the convention are listed under LY4 and not modeled. Files in the retired Task Planner format are listed under LY9 with checklist progress and not audited. Secrets detection uses a handful of exact token shapes and two assignment patterns (Markdown and JSON); it is conservative and will miss most real credentials, so a clean HY1 is not an assurance. Matched values are replaced before parsing, so no derived field, state value, or report carries them.

Each rule below names its **control**, the heading the report's remediation plan groups it under.

## Folder layout (LY1 to LY5, LY9, TK6, HY2)

**LY1 Tracking folder not git-ignored.** No `.copilot-tracking/` line (also accepted: `/.copilot-tracking`, `.copilot-tracking/**`, `**/.copilot-tracking`) in the root `.gitignore`. Medium. *Why:* HVE Core's install guide tells every install method to add the line; without it tracking files (which carry paths, decisions, sometimes transcript-derived text) can be committed. *Verify:* the root `.gitignore`; the script does not run `git` and cannot tell whether files are already tracked. *Fix:* add the line; if files were committed, remove them from the index.

**LY2 Tracking folder below the workspace root.** A `.copilot-tracking` folder exists in a subfolder (searched six levels deep). Medium. *Why:* HVE Core's location instruction keeps the folder at the codebase root, never in a subdirectory and never in an added HVE Core clone folder; the skills resolve only the root folder, so nested artifacts are invisible to a resume. The script lists a nested folder and does not read its contents; if both folders hold artifacts for the same slug, the user must say which is current before merging them (keep the newer dated files, then rerun). *Fix:* move the artifacts to the root folder and keep one.

**LY3 Artifact not directly under a YYYY-MM-DD folder of its area.** A file directly in the area, under a non-date folder, or one level too deep. Low. *Why:* artifacts are addressed by `{area}/{date}/{slug}-{kind}.md`; a different shape is not where a command looks. *Fix:* move the file.

**LY4 File name does not match the area's convention.** A file in `plans/` not ending in `-plan.md`, in `changes/` not `-changes.md`, in `reviews/plans/` not `-plan-critique.md` or `-plan-critique-N.md`, in `reviews/logs/` not `-review.md` or `-review-N.md`, in `research/` not `-research.md`, in `challenges/` not `-challenge.md`, in `walkthroughs/` not `-decisions.md`. Low. The file is listed in the inventory and not modeled, so it never appears as a task. *Fix:* rename.

**LY5 Task slug is not lower-kebab-case.** Low. *Why:* the slug joins every artifact and appears in every command; `Bad_Task` and `bad-task` are two tasks to the skills. *Fix:* rename the task's artifacts to one slug.

**LY9 Artifact in the retired Task Planner format.** A `{slug}-plan.instructions.md`, anything under `details/`, `plans/logs/`, `research/subagents/`, `reviews/{date}/` or `reviews/rpi/`, or a research or changes file at a current path that lacks the current sections and either carries legacy markers (`## Implementation Checklist`, `<!-- parallelizable`, references to `details/`, all taken from the 3.3.101 agent templates) or belongs to a slug with legacy siblings and does not start with the current template's title. Info, one finding per task. *Why:* written by the Task Researcher, Task Planner, Task Implementor, and Task Reviewer agents that the VS Code extension releases through 3.3.101 ship; the current `rpi-*` skills on `main` do not read this layout, and HVE Core publishes no converter. *Verify:* which HVE Core source the host runs (extension, CLI plugin, clone). *Fix:* finish the task with the agents that wrote it, or re-plan with `/rpi-plan task=<slug> draft=<old plan path>`.

**TK6 Open task without a change for longer than the stale threshold.** The newest modification time across the task's artifacts is more than `--stale-days` (default 30) before the reference date and the task is not accepted. Info. *Why:* an abandoned task keeps appearing as resumable. *Verify:* modification times reset when a folder is copied; confirm with the user. *Fix:* finish, hand over, or delete the task's artifacts. `--stale-days 0` disables the rule and records it as not evaluated.

**HY2 Non-Markdown file in an RPI area.** Info. JSON in these folders is usually session state (which the script detects by shape); anything else is unexpected.

## Plan markers and headings (PL1 to PL4, PC1, RV1)

**PL1 Phase or task marker has no matching heading.** A `<!-- rpi:phase -->` or `<!-- rpi:task -->` marker whose next line is not a heading, or a heading preceded by a marker with a different ID (reported once, from the heading). High. *Why:* `rpi-implement` navigates by marker; a mismatched marker makes the item unreachable by `task=` or attributes work to the wrong ID. *Fix:* one marker immediately before its heading, same ID. The marker form is `<!-- rpi:task id=P01-T01 -->`; extra spaces around `=` are read.

**PL2 Phase or task heading has no marker.** A `Pxx` or `Pxx-Txx` heading with no marker on the line before it. Medium. *Why:* readable, but not addressable; a resume by `task=Pxx-Txx` does not find it. *Fix:* add the marker.

**PL3 Duplicate phase or task ID.** High. *Why:* the changes record, review, and commands cannot tell the items apart. *Fix:* renumber and reconcile the artifacts that cite the ID.

**PL4 Task ID does not belong to its enclosing phase.** `P02-T01` under the `P01` heading. Medium. *Why:* phase completion is computed from the tasks under the phase heading; a misplaced task is counted for one phase and numbered for another. *Fix:* renumber or move.

**PC1 Critique finding marker and heading disagree or repeat. RV1 Review finding marker and heading disagree or repeat.** A `PC-xxx` or `RV-xxx` heading without its marker, a marker without a heading, or a repeated ID. Medium. *Why:* the plan's Critique Disposition and the review's Decision History key on these IDs. *Fix:* one marker and heading per finding.

## Completion evidence (PL5, PL6, CH2, CH4, CH5, CH9, CH10)

**PL5 Phase checked while one of its tasks is unchecked.** Medium. *Why:* the implementation reference checks a phase only after every task in it; a resume treats a checked phase as done and skips the task. *Fix:* uncheck the phase or finish the task.

**PL6 Task checked without a changes-record entry.** No changes record exists for the task, or none of its Completed Work entries or Completed scope markers names the task. Medium. *Why:* completion is the checked marker plus the changes record; without the entry there is no record of what changed or whether validation ran, and review has nothing to assess. An entry that names only the phase does not count. *Fix:* add the entry or uncheck.

**CH2 Changes record completes a task whose plan marker is unchecked.** Medium. *Why:* the plan is stale; the next `rpi-implement` resumes from the first unchecked item and may redo or conflict with finished work. *Fix:* check the marker in the plan after confirming the entry.

**CH4 Status Complete for the full plan while plan markers remain unchecked.** Medium. *Why:* full-plan completion needs completion evidence for every marker; a bounded scope must say `Partial` and list remaining markers. *Fix:* correct the status and scope.

**CH5 Completed-work entry without a validation line.** Low. *Why:* each entry records passed, failed, skipped, or unavailable; review needs the result. *Fix:* add `* Validation:`.

**CH9 Review readiness ready while blockers or remaining work are listed.** Low. *Why:* the pre-review reconciliation contradicts itself. *Fix:* set not ready with the reason, or clear the lists.

**CH10 Validation failed or unavailable.** Info. *Why:* carried into review as a limitation; not a defect of the record. *Fix:* rerun or keep the reason.

## Cross-artifact links (PL14, PL17, PC3, CH1, CH6, RV5, TK1 to TK5)

**PL14 Critique recorded in the plan but no critique file found.** The plan's Latest critique or Critique Disposition names a `-plan-critique.md` path with a verdict and `reviews/plans/` holds no critique for the slug. Medium. *Why:* readiness may rest on a result that cannot be read. *Fix:* restore the file, fix the path, or record `skipped` with provenance.

**PL17 Task slug in the plan differs from the file name.** Low. *Fix:* align.

**PC3 Critique points at a plan file that does not exist. CH6 Changes record points at a plan file that does not exist. RV5 Review points at a plan or changes file that does not exist.** The critique's `Plan:`, the changes record's `Related plan:`, or the review's `Plan:` and `Changes:` resolve to nothing. Medium. *Why:* the artifact cannot be matched to its evidence on resume; the review's comparison has no base. *Verify:* link destinations are relative to the artifact file (`../../plans/...` from `changes/{date}/` and from `reviews/logs/{date}/`); plain paths are workspace-relative. The finding quotes the destination, and the link text in parentheses when it differs. *Fix:* correct the path.

**CH1 Changes record names a task the plan does not define.** Medium. *Why:* the entry cannot be matched to plan work; review treats it as unassessed or as scope creep. *Fix:* correct the ID, or add the task to the plan as an implementation-time update with its changes entry.

**TK1 Changes record without a plan. TK2 Review without a changes record. TK3 Critique without a plan.** Medium. *Why:* each downstream artifact is read against the one before it; alone it cannot be resumed or assessed. *Fix:* restore the missing artifact or record where it lives.

**TK4 Task ID differs across the task's artifacts.** Medium. *Why:* one stable task ID joins the set. TK4 compares within one slug; a renamed slug shows up as two tasks whose inventory summaries carry the same Task ID. *Fix:* align the Metadata of each file.

**TK5 Several artifacts of one kind for one slug.** Info. *Why:* the newest is treated as current; the others may be superseded versions or a renamed task. Findings on an older critique or review that a `-2` file supersedes are downgraded to info with a "superseded by" note, except HY1, which keeps its severity. *Fix:* confirm which is current.

## Decisions and gates (PL12, PL13, PL15, PL16, PL18, PL19, PC2, CH7, CH8, RV2, RV4, RV6, RV7, RS1, RS4, TK10)

**PL15 Planning Readiness is Ready without a critique result or an explicit skip.** The Critique Disposition records `started`, `not run`, `not produced`, or nothing, no `Pass`, `Revise`, or `Blocked` verdict appears (a verdict is read as a word, never out of a file name), and no skip is recorded. Medium. *Why:* the `rpi-plan` skill says a critique that returned no result is never treated as a Pass; this rule reads that as readiness staying Not ready until a result exists or the user or parent records a skip. *Fix:* run `/rpi-plan-critique`, or record the skip with its provenance.

**PL18 Critique finding without a disposition in the plan.** A `PC-xxx` in the latest critique has no row in the plan's Critique Disposition table. Medium. *Why:* every finding is disposed of (resolved, superseded, accepted with risk, open) before readiness is claimed. *Fix:* add the row.

**PL12 Requirement not cited by any task. PL13 Task cites a requirement the plan does not define.** Low. *Why:* the plan self-check requires every FR and NFR to be cited by a task's Requirements block, and the critique compares tasks against the catalog. *Fix:* cite, define, or remove.

**PL16 Open planning decision.** A Planning Decisions and Feedback row with status proposed, unresolved, deferred, or input requested. Info. *Why:* implementation pauses affected tasks until the decision is recorded. *Fix:* decide, naming the affected `Pxx-Txx`.

**PL19 Plan marked Not ready or Blocked.** Info, with the blocker text. *Why:* implementation confirms with the user before acting on affected tasks.

**PC2 Critique verdict missing or outside Pass, Revise, Blocked, unavailable.** Medium. *Fix:* record one value; `unavailable` when no assessment was produced, never Pass.

**CH7 Business Alignment entry pending a decision.** Medium. *Why:* a `pending-decision` alignment blocks review readiness until the user decides. *Fix:* record the decision and the alignment value.

**CH8 Changes record reports a blocker.** Info, with the blocker text.

**RV2 Review finding without a proposed destination.** Not one of `rpi-implement`, `rpi-plan`, `rpi-research`, `follow-up`. Medium. *Why:* the parent disposes of findings by route; an unrouted finding goes nowhere. *Fix:* add the destination.

**RV4 Review finding with no decision event.** No `RD-xxx` row names the `RV-xxx`. Medium. *Why:* the finding is undecided; the final outcome stays pending and nothing is routed. *Fix:* append the event with accepted, rejected, deferred, or changed.

**RV6 Conformant outcome while a Critical or High finding is undecided or not accepted.** Medium. *Why:* the review reference says material skipped or deferred findings prevent Conformant outcomes. *Fix:* decide the finding or change the outcome.

**RV7 Final outcome pending in the Parent Decision Record.** Review execution is Complete and Current Disposition records no final outcome, or `pending`. Info. *Why:* the Executive Summary's assessed outcome is the reviewer's proposal; acceptance is only what Current Disposition records. The board's `accepted` state requires a recorded final outcome of Conformant or Conformant with justified divergence for the full scope, with the plan and changes record present and every plan task checked. *Fix:* decide the findings and refresh Current Disposition.

**RS1 Planning Readiness missing or outside Ready, Not ready, Not applicable, Blocked.** Low. **RS4 Research not ready for planning.** Info. *Why:* `/rpi-plan` reads the row; Not ready or Blocked means re-enter research on the named gap.

**TK10 Research exists but planning has not started.** Info for the board.

## Session state (TK7 to TK9)

**TK7 Session state points at an artifact that does not exist.** Medium. *Why:* RPI Agent reconciles `artifact_paths` on recovery; a missing file is a recovery blocker. *Fix:* correct or restore.

**TK8 Session state phase disagrees with the artifacts.** `next_action.phase` (or `active_phase`) is Implement, Review, or Follow-up and the task has no plan (or no changes record for Review and Follow-up), or the state names a slug with no artifacts. Medium. *Why:* the agent resumes the recorded phase; without the artifacts it needs, recovery fails or restarts research. *Fix:* reconcile before resuming; the artifacts are canonical.

**TK9 Session state marks the task completed while plan markers remain unchecked.** Low. *Fix:* reconcile.

## Template completion (PL7 to PL11, PC4, PC5, CH3, RV3, RS2, RS3, LY6 to LY8, LY10)

**LY10 Empty or unrecognized artifact.** The file is empty, or carries none of the sections its kind requires. Medium, reported once instead of one PL10 per section. *Why:* no phase can resume from it. The file is excluded from the task board. *Fix:* recreate it from the phase skill, or remove it if it is scratch.

**PL9 Unfilled template placeholder.** `{{...}}` left in the artifact. Medium in plans, critiques, changes records, and reviews; low in research. *Why:* the next phase reads it as content; in a plan it reaches the implementer. *Fix:* fill or delete.

**PL7 Task block missing a labeled block.** Goals, Requirements, Details, References, or Dependencies. **PL8 Phase block missing Goals or Dependencies.** Low. *Why:* the implementer, critique, and dependency ordering read these blocks. A phase's blocks are read up to its first task heading. *Fix:* add, even as `* none`.

**PL10 Required section missing.** Plan: Task Metadata, Executive Summary, Phase Checklist, User Decisions and Requirements, Planning Readiness and Next Step, Critique Disposition, Artifact Self-Check, Follow-Up Items, Handoff. Changes record: Metadata, Execution Status, Completed Work, Validation Record, Return-to-Caller State. Review record: Executive Summary, Findings and Proposed Routes, Parent Decision Record, Review Record. Research: Executive Summary, Findings, Planning Readiness and Next Step, Research Record. Critique: Metadata, Verdict, Findings, Recommended Next Action. Low. *Fix:* add from the template.

**PL11 Follow-Up Items not immediately before Handoff.** Low.

**PC4 Follow-up critique without Earlier Finding Reconciliation.** Low. **PC5 Critique execution missing or outside Complete, Partial, Blocked, not produced.** Low. **CH3 Execution status missing or outside Complete, Partial, Blocked.** Low. **RV3 Review execution or assessed outcome missing or outside the vocabulary.** Low. **RS3 Research disposition missing or outside executed, reused, satisfied-and-skipped.** Low.

**RS2 Evidence ID cited but not defined in the Evidence Log.** Low. *Why:* findings cite `C#` and `W#`; a citation without a row cannot be checked.

**LY6 Generated artifact does not start with the markdownlint disable comment.** Info. **LY7 Line-number reference in a tracking artifact.** `path.py:42`, `#L12`, or "line 12" outside code spans. Low. **LY8 #file: directive in a tracking artifact.** Low. *Why:* HVE Core's tracking convention; LY7 and LY8 matter because the convention navigates by ID, marker, heading, or symbol. Artifacts written from the Copilot CLI may not have had the instruction applied (the CLI does not apply `applyTo` automatically, though skills still link to the instruction); confirm the host before treating these three as drift.

## Secrets (HY1)

**HY1 Possible credential in a tracking artifact.** An AWS access key, GitHub token, private key block, Slack token, a quoted token or password assignment (Markdown `token: "..."` or JSON `"token": "..."`), or a connection string password, in an RPI artifact or a session state file. High. *Why:* tracking files are pasted into chats and reports, and the research self-check requires that no secrets are recorded. *Verify:* the line named in the finding; the pattern is a heuristic. The script replaces the matched value with `[redacted ...]` before parsing any field, and a state value under a credential-like key is replaced whole, so neither report carries it; the artifact itself is unchanged. *Fix:* remove the value and rotate it if it is real.

## Not covered

Things the script does not check, so say so when asked: whether the plan's Mermaid diagrams are current, whether a `Guidance:` block should exist, whether validation actually ran, whether a decision recorded as user-owned was in fact the user's, whether the RPI Agent honored a `before-implementation` boundary, the contents of nested tracking folders, and anything in the planner, reviewer, coach, and builder areas outside RPI.
