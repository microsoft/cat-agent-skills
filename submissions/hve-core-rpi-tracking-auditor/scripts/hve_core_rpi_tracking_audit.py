#!/usr/bin/env python3
"""Audit the RPI tracking artifacts a repository keeps under .copilot-tracking/.

Usage:
    python3 hve_core_rpi_tracking_audit.py [ROOT]
        [--md report.md] [--json report.json] [--brief]
        [--task SLUG]                report one task slug only
        [--file ARTIFACT]            audit one research, plan, critique, changes, or review file alone
        [--stale-days 30]            days without a change after which an open task is reported as stale (0 disables)
        [--as-of YYYY-MM-DD]         reference date printed in the header and used for staleness
        [--max-rows 25]              rows shown per table before "... and N more"

ROOT is a repository or workspace folder (default: the current directory). The
script reads .copilot-tracking/research, plans, reviews/plans, changes,
reviews/logs, challenges, and walkthroughs, groups the files by task slug, reads
each artifact's markers, headings, status fields, and links, and evaluates the
rules in references/rule-catalog.md. It writes a task board (where every task
stands and the command that continues it), findings ranked by severity, a
remediation plan grouped by the control that fixes each rule, an inventory, and
a method note. It also reads any RPI Agent session state file it finds under
.copilot-tracking/ (recognized by its fields, since HVE Core documents no fixed
path) and checks it against the artifacts.

Artifacts written by the retired Task Researcher, Task Planner, Task Implementor,
and Task Reviewer agents (shipped by the VS Code extension releases through
3.3.101) use a different layout: {slug}-plan.instructions.md, a details/ folder,
plans/logs/, research/subagents/, reviews/{date}/. They are recognized, listed
as legacy with their checklist progress, and not audited against the current
rules.

Other .copilot-tracking/ areas (security-plans, adr-plans, prd-sessions, dt, and
so on) belong to other HVE Core workflows and are listed, not audited.

Standard library only. No network access. Nothing is changed anywhere: the
script reads the folder and writes a report.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from datetime import date, datetime
from urllib.parse import unquote

TOOL_VERSION = "1.0.0"
HVE_CORE_SOURCE = "microsoft/hve-core main at ee3df32 (2026-10-16)"
HVE_CORE_READ_DATE = "2026-10-17"
HVE_EXTENSION_VERSION = "PreRelease 3.3.101 (published 2026-04-25) and Stable 3.2.2 (2026-03-23)"
TRACKING_DIR = ".copilot-tracking"

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}
SEV_LABEL = {"high": "High", "medium": "Medium", "low": "Low", "info": "Info"}
LIST_CAP = 5
MAX_SCAN_DEPTH = 6
LONG_LINE = 2000

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".tox", ".mypy_cache", "out", "target"}
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MARKER = re.compile(r"<!--\s*rpi:(phase|task|critique|review)\s+id\s*=\s*([A-Za-z0-9-]+)\s*-->")
PHASE_ID = re.compile(r"^P\d{2}$")
TASK_ID = re.compile(r"^P\d{2}-T\d{2}$")
ANY_PLAN_ID = re.compile(r"\bP\d{2}(?:-T\d{2})?\b")
TASK_ID_IN_TEXT = re.compile(r"\bP\d{2}-T\d{2}\b")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
ID_HEADING = re.compile(r"^(#{2,6})\s+(?:\[( |x|X)\]\s+)?((?:PC|RV)-\d{3}|P\d{2}(?:-T\d{2})?)\b(?:\s*\[([A-Za-z]+)\])?")
PLACEHOLDER = re.compile(r"\{\{[^{}\n]*\}\}")
LINE_REF_TOKEN = re.compile(r"^[\w./-]{1,200}\.(?:py|ts|tsx|js|md|cs|rs|go|java|yml|yaml|json|ps1|sh|bicep|tf):\d+[,.;:)]*$", re.I)
LINE_REF_ANCHOR = re.compile(r"#L\d+\b")
LINE_REF_PHRASE = re.compile(r"\blines?\s+\d+(?:\s*(?:-|to)\s*\d+)?\b", re.I)
FILE_DIRECTIVE = re.compile(r"#file:")
LABEL_BLOCK = re.compile(r"^(Goals|Requirements|Details|Guidance|References|Dependencies)\s*:\s*$")
BULLET_FIELD = re.compile(r"^\s*[*-]\s+([^:]+?)\s*:\s*(.*)$")
BOLD_WRAP = re.compile(r"(\*\*|__)")
MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
REQ_DEF = re.compile(r"^\s*[*-]\s+((?:N)?FR)-(\d{3})\s*:", re.M)
REQ_CITE = re.compile(r"\b((?:N)?FR-\d{3})\b")
EVIDENCE_DEF = re.compile(r"^\|?\s*([CW]\d+)\s*\|", re.M)
EVIDENCE_CITE = re.compile(r"\b([CW]\d+)\b")
RV_ID = re.compile(r"\bRV-\d{3}\b")
PC_ID = re.compile(r"\bPC-\d{3}\b")
RD_ID = re.compile(r"\bRD-\d{3}\b")
CHECKBOX = re.compile(r"^\s*(?:[*-]|#{2,6})\s+\[( |x|X)\]\s", re.M)
TABLE_SEP = re.compile(r"^:?-+:?$")
SECRET_PATTERNS = (
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("quoted token or password assignment", re.compile(r"(?i)\b(?:pat|token|password|secret|api[_-]?key)\s*[=:]\s*['\"][A-Za-z0-9+/_\-]{20,}['\"]")),
    ("connection string with password", re.compile(r"(?i)\bpassword=[^;\s]{8,};")),
    ("quoted key token or password (JSON)", re.compile(r"(?i)\"[\w-]*(?:pat|token|password|passwd|secret|api[_-]?key)\"\s*:\s*\"[A-Za-z0-9+/_\-]{20,}\"")),
)
SECRET_KEY = re.compile(r"(?i)(?:^|[_-])(?:pat|token|password|passwd|secret|api[_-]?key)$")

AREAS = OrderedDict([
    ("research", ("research", re.compile(r"^(?P<slug>.+?)-research\.md$"))),
    ("plans", ("plan", re.compile(r"^(?P<slug>.+?)-plan\.md$"))),
    ("reviews/plans", ("critique", re.compile(r"^(?P<slug>.+?)-plan-critique(?:-(?P<n>\d+))?\.md$"))),
    ("changes", ("changes", re.compile(r"^(?P<slug>.+?)-changes\.md$"))),
    ("reviews/logs", ("review", re.compile(r"^(?P<slug>.+?)-review(?:-(?P<n>\d+))?\.md$"))),
    ("challenges", ("challenge", re.compile(r"^(?P<slug>.+?)-challenge\.md$"))),
    ("walkthroughs", ("walkthrough", re.compile(r"^(?P<slug>.+?)-decisions\.md$"))),
])
# Retired Task Planner layout (extension releases through 3.3.101): area -> (subkind, name pattern)
LEGACY_AREAS = OrderedDict([
    ("research/subagents", ("subagent research", re.compile(r"^(?P<slug>.+?)-research\.md$"))),
    ("plans/logs", ("planning log", re.compile(r"^(?P<slug>.+?)-log\.md$"))),
    ("details", ("implementation details", re.compile(r"^(?P<slug>.+?)-details\.md$"))),
    ("reviews/rpi", ("validation output", re.compile(r"^(?P<slug>.+?)-\d{3}-validation\.md$"))),
    ("reviews", ("review log", re.compile(r"^(?P<slug>.+?)(?:-plan)?-review\.md$"))),
])
LEGACY_PLAN = re.compile(r"^(?P<slug>.+?)-plan\.instructions\.md$")
LEGACY_HINTS = ("## Implementation Checklist", "Implementation Phase ", "<!-- parallelizable", "## Context Summary", "## Objectives", "-plan.instructions.md", ".copilot-tracking/details/")
KIND_ORDER = ["research", "plan", "critique", "changes", "review", "challenge", "walkthrough"]
KIND_LABEL = {"research": "research", "plan": "plan", "critique": "plan critique", "changes": "changes record",
              "review": "review record", "challenge": "challenge session", "walkthrough": "decisions-and-changes ledger"}
SUFFIX_BY_KIND = {"research": "-research.md", "plan": "-plan.md", "critique": "-plan-critique.md",
                  "changes": "-changes.md", "review": "-review.md", "challenge": "-challenge.md", "walkthrough": "-decisions.md"}
KNOWN_OTHER_AREAS = {
    "hve-builder": "HVE Builder stage evidence", "proposal-responses": "proposal-response evidence",
    "prompts": "prompt tracking", "reviews/code-reviews": "Code Review agent reports", "reviews/architecture": "architecture-review skill",
    "security-plans": "Security Planner", "security": "Security Reviewer", "sssc-plans": "SSSC Planner",
    "sssc-reviews": "SSSC Reviewer", "privacy-plans": "Privacy Planner", "privacy-reviews": "Privacy Reviewer",
    "accessibility": "Accessibility Planner and Reviewer", "rai-plans": "RAI Planner", "rai-reviews": "RAI Reviewer",
    "adr-plans": "ADR Creator", "prd-sessions": "PRD Builder", "brd-sessions": "BRD Builder",
    "workitems": "Functional Planner and Backlog Manager", "github-issues": "Backlog Manager", "jira-issues": "Backlog Manager",
    "dt": "DT Coach", "ux-artifacts": "ux-artifacts skill", "ux-coaching": "ux-coaching skill",
    "ds": "Data Science and Engineering Coach", "mve": "Experiment Designer", "ppt": "PowerPoint Builder",
    "demo-material": "HVE Demo Material Builder", "pr": "pull-request skill", "documentation": "Documentation agent",
}

PLAN_READINESS = ("Not ready", "Not applicable", "Ready", "Blocked")
EXECUTION = ("Complete", "Partial", "Blocked")
OUTCOMES = ("Conformant with justified divergence", "Conformant", "Defects found", "Residual work", "Not accepted")
VERDICTS = ("Pass", "Revise", "Blocked", "unavailable")
DESTINATIONS = ("rpi-implement", "rpi-plan", "rpi-research", "follow-up")
RESEARCH_DISPOSITIONS = ("executed", "reused", "satisfied-and-skipped")
ALIGNMENT_VALUES = ("clarification", "divergence-confirmed", "source-gap", "pending-decision")
PLAN_REQUIRED_SECTIONS = ("Task Metadata", "Executive Summary", "Phase Checklist", "User Decisions and Requirements",
                          "Planning Readiness and Next Step", "Critique Disposition", "Artifact Self-Check",
                          "Follow-Up Items", "Handoff")
CHANGES_REQUIRED_SECTIONS = ("Metadata", "Execution Status", "Completed Work", "Validation Record", "Return-to-Caller State")
REVIEW_REQUIRED_SECTIONS = ("Executive Summary", "Findings and Proposed Routes", "Parent Decision Record", "Review Record")
RESEARCH_REQUIRED_SECTIONS = ("Executive Summary", "Findings", "Planning Readiness and Next Step", "Research Record")
CRITIQUE_REQUIRED_SECTIONS = ("Metadata", "Verdict", "Findings", "Recommended Next Action")
REQUIRED_BY_KIND = {"plan": PLAN_REQUIRED_SECTIONS, "changes": CHANGES_REQUIRED_SECTIONS, "review": REVIEW_REQUIRED_SECTIONS,
                    "research": RESEARCH_REQUIRED_SECTIONS, "critique": CRITIQUE_REQUIRED_SECTIONS}
STATE_FIELDS = {"task_slug", "active_phase", "artifact_paths"}

# Rule table: id -> (title, severity, control, consequence, verification, fix)
RULES = OrderedDict([
    # Layout
    ("LY1", ("Tracking folder not git-ignored", "medium", "Folder layout",
             "tracking artifacts can be committed, and HVE Core's install guide tells every install method to add the ignore line",
             "the root .gitignore", "add a `.copilot-tracking/` line to the root .gitignore")),
    ("LY2", ("Tracking folder below the workspace root", "medium", "Folder layout",
             "the RPI skills look for .copilot-tracking/ at the codebase root and will not find or resume from a nested one; the script lists a nested folder and does not read it",
             "the nested folder's path", "move the artifacts to the root .copilot-tracking/ and keep one folder")),
    ("LY3", ("Artifact not directly under a YYYY-MM-DD folder of its area", "low", "Folder layout",
             "artifacts are addressed by date folder; a different shape is not found by the documented paths",
             "the folder path", "move the file to {area}/{YYYY-MM-DD}/")),
    ("LY4", ("File name does not match the area's convention", "low", "Folder layout",
             "the skills resolve `{slug}-plan.md`, `{slug}-changes.md`, and the other documented names; anything else is invisible to them and is not modeled by this audit",
             "the file name against the area", "rename to the documented suffix for the area")),
    ("LY5", ("Task slug is not lower-kebab-case", "low", "Folder layout",
             "the slug is reused across every artifact and command; a slug with other characters breaks the match",
             "the slug", "rename the artifacts of the task to one lower-kebab-case slug")),
    ("LY6", ("Generated artifact does not start with the markdownlint disable comment", "info", "Template completion",
             "HVE Core's tracking convention exempts generated tracking Markdown from lint through this first line",
             "line 1 of the file", "no action unless the repository lints tracking files")),
    ("LY7", ("Line-number reference in a tracking artifact", "low", "Template completion",
             "HVE Core navigates tracking artifacts by IDs, markers, and headings; line numbers go stale on the first edit",
             "the quoted text", "replace with a path plus heading or symbol")),
    ("LY8", ("#file: directive in a tracking artifact", "low", "Template completion",
             "the tracking convention forbids #file: directives in generated tracking Markdown",
             "the quoted text", "use a plain path or a Markdown link")),
    ("LY9", ("Artifact in the retired Task Planner format", "info", "Folder layout",
             "written by the Task Researcher, Task Planner, Task Implementor, or Task Reviewer agents that the VS Code extension releases through 3.3.101 ship; the current RPI skills on main do not read this layout, and HVE Core publishes no converter",
             "the file and the HVE Core source the host runs", "finish the task with the agents that wrote it, or re-plan with `/rpi-plan task=<slug> draft=<old plan path>`")),
    ("LY10", ("Empty or unrecognized artifact", "medium", "Template completion",
              "the file carries none of the sections the current RPI skills write and read, so no phase can resume from it",
              "the file", "recreate it from the phase skill, or remove it if it is scratch")),
    # Plan
    ("PL1", ("Phase or task marker has no matching heading", "high", "Plan markers and headings",
             "rpi-implement navigates the plan by marker; a marker that does not precede its heading leaves the item unreachable or mis-attributed",
             "the marker line and the next heading", "place `<!-- rpi:task id=Pxx-Txx -->` immediately before `#### [ ] Pxx-Txx: ...`")),
    ("PL2", ("Phase or task heading has no marker", "medium", "Plan markers and headings",
             "the item is visible to a reader but not addressable by `/rpi-implement task=Pxx-Txx`",
             "the heading", "add the marker on the line before the heading")),
    ("PL3", ("Duplicate phase or task ID", "high", "Plan markers and headings",
             "implementation and review cannot tell which item a marker, changes entry, or command refers to",
             "both headings", "renumber one item and reconcile the changes record and review")),
    ("PL4", ("Task ID does not belong to its enclosing phase", "medium", "Plan markers and headings",
             "the task is counted under one phase and numbered for another; phase completion rules misfire",
             "the task heading and the phase above it", "renumber the task to its phase prefix or move it")),
    ("PL5", ("Phase checked while one of its tasks is unchecked", "medium", "Completion evidence",
             "rpi-implement checks a phase only when every task in it is checked; a resume reads the phase as done and skips the task",
             "the phase heading and its task headings", "uncheck the phase or finish and check the task")),
    ("PL6", ("Task checked without a changes-record entry", "medium", "Completion evidence",
             "completion is the checked marker plus the changes record; a checked task with no entry has no evidence of what changed or whether validation ran",
             "the changes record for the task", "add the completed-work entry naming the task, or uncheck it")),
    ("PL7", ("Task block missing a labeled block", "low", "Template completion",
             "every task carries Goals, Requirements, Details, References, and Dependencies; the implementer and critique read those blocks",
             "the task body", "add the missing block, even as `* none`")),
    ("PL8", ("Phase block missing Goals or Dependencies", "low", "Template completion",
             "phase order and dependency readiness are read from these blocks", "the phase body", "add the block")),
    ("PL9", ("Unfilled template placeholder", "medium", "Template completion",
             "a `{{placeholder}}` left in a handoff artifact is read by the next phase as content; in a plan it reaches the implementer",
             "the quoted placeholder", "fill or delete the placeholder")),
    ("PL10", ("Required section missing", "low", "Template completion",
              "the phase skills read fixed sections (readiness, critique disposition, follow-up items, handoff, decision record)",
              "the heading list", "add the section from the phase skill's template")),
    ("PL11", ("Follow-Up Items not immediately before Handoff", "low", "Template completion",
              "the planning reference fixes this position so implementation-time discoveries are found",
              "the last two H2 headings", "move `## Follow-Up Items` directly before `## Handoff`")),
    ("PL12", ("Requirement not cited by any task", "low", "Decisions and gates",
              "the plan self-check requires every FR-nnn and NFR-nnn to be cited by a task's Requirements block, otherwise nothing implements it",
              "the task Requirements blocks", "cite it in the task that satisfies it, or remove it")),
    ("PL13", ("Task cites a requirement the plan does not define", "low", "Decisions and gates",
              "the critique and review compare tasks against the requirement catalog; an undefined ID cannot be checked",
              "the Functional and Non-Functional Requirements sections", "define the requirement or fix the citation")),
    ("PL14", ("Critique recorded in the plan but no critique file found", "medium", "Cross-artifact links",
              "the plan claims a critique result that cannot be read; readiness may rest on it",
              "the reviews/plans folder for the task", "restore the critique, correct the path, or record `skipped` with provenance")),
    ("PL15", ("Planning Readiness is Ready without a critique result or an explicit skip", "medium", "Decisions and gates",
              "the planning reference says a missing critique result is never a Pass and readiness stays Not ready until a result exists or the critique is skipped",
              "Critique Disposition and the critique file", "run `/rpi-plan-critique`, or record the skip and its provenance")),
    ("PL16", ("Open planning decision", "info", "Decisions and gates",
              "a decision with status proposed, unresolved, deferred, or input requested blocks the tasks it names",
              "the Planning Decisions and Feedback table", "resolve it before implementing the affected tasks")),
    ("PL17", ("Task slug in the plan differs from the file name", "low", "Cross-artifact links",
              "the slug is the join key across research, critique, changes, and review", "Task Metadata", "align the metadata and the file name")),
    ("PL18", ("Critique finding without a disposition in the plan", "medium", "Decisions and gates",
              "the plan must dispose of every PC-xxx (resolved, superseded, accepted with risk, or open); an undisposed finding is unresolved critique input",
              "the Critique Disposition table", "add the row with the disposition and the resolving evidence")),
    ("PL19", ("Plan marked Not ready or Blocked", "info", "Decisions and gates",
              "implementation should confirm with the user before acting on affected tasks",
              "Planning Readiness and Next Step", "clear the blocker named there")),
    # Critique
    ("PC1", ("Critique finding marker and heading disagree or repeat", "medium", "Plan markers and headings",
             "the plan's Critique Disposition keys on PC-xxx; a repeated or unmarked ID cannot be disposed",
             "the Findings section", "give every finding one `<!-- rpi:critique id=PC-xxx -->` marker and heading")),
    ("PC2", ("Critique verdict missing or outside Pass, Revise, Blocked, unavailable", "medium", "Decisions and gates",
             "the planner reads the verdict to set readiness", "the Verdict section", "record one of the four values")),
    ("PC3", ("Critique points at a plan file that does not exist", "medium", "Cross-artifact links",
             "the critique cannot be matched to its plan on resume", "the Metadata Plan line", "correct the path")),
    ("PC4", ("Follow-up critique without Earlier Finding Reconciliation", "low", "Template completion",
             "a numbered follow-up must mark each earlier finding resolved, still open, or superseded",
             "the section list", "add the reconciliation table")),
    ("PC5", ("Critique execution missing or outside Complete, Partial, Blocked, not produced", "low", "Template completion",
             "execution is recorded apart from the verdict; a missing value hides an interrupted run",
             "the Metadata Critique execution line", "record the execution status")),
    # Changes
    ("CH1", ("Changes record names a task the plan does not define", "medium", "Cross-artifact links",
             "the entry cannot be matched to plan work; review will treat it as unassessed",
             "the plan's task IDs", "correct the ID or add the task to the plan as an implementation-time update")),
    ("CH2", ("Changes record completes a task whose plan marker is unchecked", "medium", "Completion evidence",
             "the plan is stale; rpi-implement resumes from the first unchecked item and may redo the work",
             "the plan heading for the task", "check the marker in the plan, or correct the changes record")),
    ("CH3", ("Execution status missing or outside Complete, Partial, Blocked", "low", "Template completion",
             "the caller and review read this field first", "Execution Status", "record one of the three values")),
    ("CH4", ("Status Complete for the full plan while plan markers remain unchecked", "medium", "Completion evidence",
             "full-plan completion requires every marker to have completion evidence",
             "the plan checklist", "set Partial and list the remaining markers, or finish the work")),
    ("CH5", ("Completed-work entry without a validation line", "low", "Completion evidence",
             "each entry records passed, failed, skipped, or unavailable; review needs it",
             "the entry", "add `* Validation:` with the result or reason")),
    ("CH6", ("Changes record points at a plan file that does not exist", "medium", "Cross-artifact links",
             "the changes record cannot be matched to its plan on resume", "the Metadata Related plan line", "correct the link")),
    ("CH7", ("Business Alignment entry pending a decision", "medium", "Decisions and gates",
             "a `pending-decision` alignment blocks review readiness until the user decides",
             "the Business Alignment section", "record the user decision and the resulting alignment value")),
    ("CH8", ("Changes record reports a blocker", "info", "Decisions and gates",
             "implementation is paused on the named item", "the Blockers section", "clear the blocker named there")),
    ("CH9", ("Review readiness ready while blockers or remaining work are listed", "low", "Completion evidence",
             "the pre-review reconciliation contradicts itself; review may start on an incomplete scope",
             "Pre-Review Reconciliation, Blockers, Remaining Work", "set not ready with the reason, or clear the lists")),
    ("CH10", ("Validation failed or unavailable", "info", "Completion evidence",
              "a failed or unavailable check is carried into review as a limitation", "the Validation Record", "rerun or record the reason")),
    # Review
    ("RV1", ("Review finding marker and heading disagree or repeat", "medium", "Plan markers and headings",
             "decisions in the Parent Decision Record key on RV-xxx", "the Findings section",
             "give every finding one `<!-- rpi:review id=RV-xxx -->` marker and heading")),
    ("RV2", ("Review finding without a proposed destination", "medium", "Decisions and gates",
             "every finding routes to rpi-implement, rpi-plan, rpi-research, or follow-up; without it the parent cannot dispose of it",
             "the finding's Proposed destination line", "add one of the four destinations")),
    ("RV3", ("Review execution or assessed outcome missing or outside the vocabulary", "low", "Template completion",
             "execution (Complete, Partial, Blocked) and outcome (Conformant, Conformant with justified divergence, Defects found, Residual work, Not accepted) are separate fields",
             "the Executive Summary", "record both values")),
    ("RV4", ("Review finding with no decision event", "medium", "Decisions and gates",
             "a finding without an RD event is undecided; the final outcome stays pending and nothing is routed",
             "the Decision History table", "append the RD event with the disposition and destination")),
    ("RV5", ("Review points at a plan or changes file that does not exist", "medium", "Cross-artifact links",
             "the review cannot be matched to its evidence on resume", "Scope and Evidence", "correct the paths")),
    ("RV6", ("Conformant outcome while a Critical or High finding is undecided or not accepted", "medium", "Decisions and gates",
             "material skipped or deferred findings prevent a Conformant outcome under the review reference",
             "the finding and its RD events", "record the decision or change the outcome")),
    ("RV7", ("Final outcome pending in the Parent Decision Record", "info", "Decisions and gates",
             "the Executive Summary's assessed outcome is the reviewer's proposal; acceptance is recorded only in Current Disposition",
             "Current Disposition under Parent Decision Record", "decide the findings and refresh Current Disposition")),
    # Research
    ("RS1", ("Planning Readiness missing or outside Ready, Not ready, Not applicable, Blocked", "low", "Decisions and gates",
             "the planner reads this row to decide whether planning can start", "Planning Readiness and Next Step", "record one of the four values")),
    ("RS2", ("Evidence ID cited but not defined in the Evidence Log", "low", "Template completion",
             "findings cite C# and W# IDs; a citation without a row cannot be checked", "the Evidence Log", "add the row or fix the citation")),
    ("RS3", ("Research disposition missing or outside executed, reused, satisfied-and-skipped", "low", "Template completion",
             "the value tells the parent whether research ran", "Planning Readiness and Next Step", "record the value")),
    ("RS4", ("Research not ready for planning", "info", "Decisions and gates",
             "planning should not start until readiness is Ready or an explicit parent records adequacy", "Planning Readiness", "re-enter research on the named gap")),
    # Task-level
    ("TK1", ("Changes record without a plan", "medium", "Cross-artifact links",
             "implementation evidence exists for a plan the folder does not hold; nothing can be resumed or reviewed against it",
             "the plans folder", "restore the plan or record where it lives")),
    ("TK2", ("Review without a changes record", "medium", "Cross-artifact links",
             "a review compares the changes record with the plan; without one its findings have no implementation evidence",
             "the changes folder", "restore the changes record")),
    ("TK3", ("Critique without a plan", "medium", "Cross-artifact links",
             "a critique of a plan the folder does not hold cannot be disposed", "the plans folder", "restore the plan")),
    ("TK4", ("Task ID differs across the task's artifacts", "medium", "Cross-artifact links",
             "one stable task ID joins plan, critique, changes, and review; a mismatch breaks resume and review",
             "the Metadata of each artifact", "align the Task ID in every artifact")),
    ("TK5", ("Several artifacts of one kind for one slug", "info", "Cross-artifact links",
             "the newest dated file is treated as current; older ones may be superseded or a renamed task",
             "the dates and contents", "confirm which is current and consider removing the rest")),
    ("TK6", ("Open task without a change for longer than the stale threshold", "info", "Folder layout",
             "an abandoned task keeps appearing as resumable; modification times reset when a folder is copied",
             "the latest modification date", "finish, hand over, or delete the task's artifacts")),
    ("TK7", ("Session state points at an artifact that does not exist", "medium", "Session state",
             "RPI Agent reconciles state against artifact paths on recovery; a missing file is a recovery blocker",
             "artifact_paths in the state file", "correct the path or restore the file")),
    ("TK8", ("Session state phase disagrees with the artifacts", "medium", "Session state",
             "the agent resumes the recorded phase; if the artifacts the phase needs are missing, recovery fails or restarts",
             "active_phase, next_action, and the task's artifacts", "reconcile the state with the artifacts before resuming")),
    ("TK9", ("Session state marks the task completed while plan markers remain unchecked", "low", "Session state",
             "task status completed should follow a complete review or full-plan implementation", "status and the plan checklist", "reconcile")),
    ("TK10", ("Research exists but planning has not started", "info", "Decisions and gates",
              "a fact for the task board", "the task's artifacts", "run `/rpi-plan` when readiness is Ready")),
    # Hygiene
    ("HY1", ("Possible credential in a tracking artifact", "high", "Secrets",
             "tracking files are git-ignored but are pasted into chats and reports; the research self-check requires that no secrets are recorded",
             "the quoted line", "remove the value and rotate it if it is real")),
    ("HY2", ("Non-Markdown file in an RPI area", "info", "Folder layout",
             "RPI artifacts are Markdown; JSON here is usually session state, anything else is unexpected", "the file", "none unless the file is not expected")),
])

CONTROL_ORDER = ["Secrets", "Plan markers and headings", "Completion evidence", "Cross-artifact links",
                 "Decisions and gates", "Session state", "Template completion", "Folder layout"]
CROSS_ARTIFACT_RULES = ("PL6", "PL14", "PL18", "PC3", "CH1", "CH2", "CH4", "CH6", "RV5") + tuple("TK%d" % i for i in range(1, 11))


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def posix(path):
    return path.replace(os.sep, "/")


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            return fh.read().replace("\r\n", "\n").replace("\r", "\n")
    except OSError:
        return ""


def md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def plural(count, noun, plural_noun=None):
    return "%d %s" % (count, noun if count == 1 else (plural_noun or noun + "s"))


def capped(items, cap=LIST_CAP, sep=", "):
    items = list(items)
    if len(items) <= cap:
        return sep.join(items)
    return sep.join(items[:cap]) + " and %d more" % (len(items) - cap)


PRIVATE_KEY_BODY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")


def redact(text):
    """Replace credential-shaped values with a labeled placeholder; line count is preserved so line numbers stay valid."""
    text = PRIVATE_KEY_BODY.sub(lambda mm: "[redacted private key block]" + "\n" * mm.group(0).count("\n"), text)
    for label, pat in SECRET_PATTERNS:
        text = pat.sub("[redacted %s]" % label, text)
    return text


def redact_obj(obj):
    """Apply redact() to every string inside nested dicts, lists, and tuples; a string under a key named like a credential is replaced whole."""
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return obj.__class__((k, "[redacted value of %s]" % k if isinstance(k, str) and isinstance(v, str) and len(v) >= 8 and SECRET_KEY.search(k) else redact_obj(v))
                             for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return [redact_obj(v) for v in obj]
    return obj


def short(text, cap=90):
    text = redact(" ".join(str(text).split()))
    return text if len(text) <= cap else text[:cap - 1] + "…"


def file_mtime(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).date()
    except OSError:
        return None


def dash(value):
    return "-" if value in (None, "", "None") else str(value)


# --------------------------------------------------------------------------
# Markdown parsing
# --------------------------------------------------------------------------

class Doc:
    """A parsed tracking Markdown file: lines, headings, markers, H2 sections."""

    def __init__(self, text):
        self.text = text
        self.lines = text.split("\n")
        self.headings = []       # (level, text, line_index)
        self.markers = []        # (kind, id, line_index)
        in_fence = False
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = HEADING.match(line)
            if m:
                self.headings.append((len(m.group(1)), m.group(2), i))
            for mm in MARKER.finditer(line):
                self.markers.append((mm.group(1), mm.group(2), i))
        self.sections = OrderedDict()   # H2 title -> (start, end)
        h2 = [(t, i) for lvl, t, i in self.headings if lvl == 2]
        for idx, (title, start) in enumerate(h2):
            end = h2[idx + 1][1] if idx + 1 < len(h2) else len(self.lines)
            self.sections.setdefault(title, (start, end))

    def section(self, name):
        """Text of the H2 section whose title starts with name (case-insensitive), or ''."""
        for title, (start, end) in self.sections.items():
            if title.lower().startswith(name.lower()):
                return "\n".join(self.lines[start + 1:end])
        return ""

    def has_section(self, name):
        return any(t.lower().startswith(name.lower()) for t in self.sections)

    def h2_titles(self):
        return list(self.sections.keys())

    def heading_range(self, line_index):
        """(start, end) of the body under the heading at line_index: until the next heading of equal or higher level."""
        level = None
        for lvl, _, i in self.headings:
            if i == line_index:
                level = lvl
                break
        if level is None:
            return (line_index, line_index + 1)
        for lvl, _, i in self.headings:
            if i > line_index and lvl <= level:
                return (line_index, i)
        return (line_index, len(self.lines))

    def body_lines(self, line_index):
        start, end = self.heading_range(line_index)
        return self.lines[start + 1:end]

    def own_body_lines(self, line_index):
        """Body lines under a heading up to the next heading of any level (excludes nested items)."""
        out = []
        for line in self.body_lines(line_index):
            if HEADING.match(line):
                break
            out.append(line)
        return out

    def subsection_bodies(self, section_name, level=3):
        """[(title, body_text, line)] for each heading of `level` inside the named H2 section."""
        out = []
        for title, (start, end) in self.sections.items():
            if not title.lower().startswith(section_name.lower()):
                continue
            for lvl, t, i in self.headings:
                if lvl == level and start < i < end:
                    out.append((t, "\n".join(self.body_lines(i)), i))
            break
        return out


def bullet_fields(text):
    """`* Label: value` bullets (bold labels allowed) -> OrderedDict(label -> value); first occurrence wins."""
    out = OrderedDict()
    for line in text.split("\n"):
        m = BULLET_FIELD.match(line)
        if not m:
            continue
        label = BOLD_WRAP.sub("", m.group(1)).strip()
        value = m.group(2).strip()
        if value.startswith(("**", "__")):      # `* **Status:** Partial` puts the closing bold after the colon
            value = value[2:].strip()
        if label and label not in out:
            out[label] = value
    return out


def table_blocks(text):
    """Pipe tables in text as (header_cells, rows) pairs, separator rows dropped.

    Accepts tables with or without outer pipes; a block counts as a table when its second line is a separator row.
    """
    blocks = []
    block = []

    def split_cells(line):
        s = line.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    def flush():
        if len(block) >= 2 and all(TABLE_SEP.match(c or "-") for c in split_cells(block[1])):
            blocks.append((split_cells(block[0]), [split_cells(line) for line in block[2:]]))
        del block[:]

    for line in text.split("\n"):
        if "|" in line and not line.strip().startswith(("```", "~~~")):
            block.append(line)
        else:
            flush()
    flush()
    return blocks


def table_rows(text):
    """Rows of pipe tables in text (header and separator rows dropped), each a list of cells."""
    return [row for _, rows in table_blocks(text) for row in rows]


def field_table(text):
    """Two-column `| Field | Record |` table -> dict."""
    out = OrderedDict()
    for cells in table_rows(text):
        if len(cells) >= 2 and cells[0] and cells[0] not in out:
            out[BOLD_WRAP.sub("", cells[0]).strip()] = cells[1]
    return out


def labeled_blocks(body_lines):
    """Labeled blocks (Goals:, Requirements:, ...) inside a task or phase body -> dict label -> text.

    Stops at the first heading so a phase does not absorb its tasks' blocks; marker comments end a block.
    """
    blocks = OrderedDict()
    current = None
    for line in body_lines:
        if HEADING.match(line):
            break
        if MARKER.search(line):
            current = None
            continue
        m = LABEL_BLOCK.match(line.strip())
        if m:
            current = m.group(1)
            blocks.setdefault(current, [])
            continue
        if line.strip().startswith("```"):
            current = None
        if current is not None:
            blocks[current].append(re.sub(r"<!--.*?-->", " ", line))
    return OrderedDict((k, "\n".join(v)) for k, v in blocks.items())


def strip_fences_and_comments(text):
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    out, in_fence = [], False
    for line in text.split("\n"):
        if line.strip().startswith("```") or line.strip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def strip_inline_code(text):
    return re.sub(r"`[^`\n]*`", " ", text)


def is_placeholder_value(value):
    v = (value or "").strip()
    return not v or PLACEHOLDER.search(v) is not None


def vocab_match(value, vocabulary, strip_paths=False):
    """The vocabulary entry that occurs earliest in value as a whole word (longest at a tie), or None.

    Placeholders count as absent. With strip_paths, Markdown links and path-like tokens are removed first so a
    verdict is not read out of a file name such as `revise-login-plan-critique.md`.
    """
    v = value or ""
    if is_placeholder_value(v):
        return None
    if strip_paths:
        v = MD_LINK.sub(" ", v)
        v = re.sub(r"\S*/\S*|\S+\.md\b", " ", v)
    pattern = r"(?<![\w-])(" + "|".join(re.escape(e) for e in sorted(vocabulary, key=len, reverse=True)) + r")(?![\w-])"
    for m in re.finditer(pattern, v, re.I):
        before = v[:m.start()]
        after = v[m.end():]
        if re.search(r"\bno\s*$", before, re.I):            # "No defects found; Conformant" -> skip the negated entry
            continue
        if re.match(r"\s*:\s*none\b", after, re.I):          # "Blocked: none. Ready" -> skip the labeled-none entry
            continue
        low = m.group(1).lower()
        for entry in vocabulary:
            if entry.lower() == low:
                return entry
    return None


def real_bullets(text):
    """Top-level bullets of a section that are neither `None` nor unfilled placeholders."""
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith(("* ", "- ")):
            continue
        item = s[2:].strip()
        if not item or re.match(r"^none\b", item, re.I) or is_placeholder_value(item):
            continue
        out.append(item)
    return out


def line_number_reference(text):
    """The first line-number reference outside code, or None. Token-based so long lines stay linear."""
    for line in strip_inline_code(text).split("\n"):
        if len(line) > LONG_LINE:
            continue
        m = LINE_REF_ANCHOR.search(line) or LINE_REF_PHRASE.search(line)
        if m:
            return m.group(0)
        for tok in line.split():
            if LINE_REF_TOKEN.match(tok):
                return tok
    return None


# --------------------------------------------------------------------------
# Artifacts and discovery
# --------------------------------------------------------------------------

class Artifact:
    def __init__(self, root, path, area, kind, slug, date_dir, suffix_n):
        self.root = root
        self.path = path
        self.rel = posix(os.path.relpath(path, root)) if root else posix(path)
        self.area = area
        self.kind = kind
        self.slug = slug
        self.date_dir = date_dir
        self.suffix_n = suffix_n
        self.raw_text = read_text(path)
        self.text = redact(self.raw_text)   # every parsed field derives from the redacted text; HY1 scans raw_text
        self.doc = Doc(self.text)
        self.mtime = file_mtime(path)
        self.model = {}
        self.legacy = None      # subkind when the file is in the retired format
        self.unrecognized = False

    def sort_key(self):
        return (self.date_dir or "", self.suffix_n or 0, os.path.basename(self.path))


def find_tracking_roots(root):
    """The root tracking folder (or None), nested tracking folders below the root, whether the scan hit the depth limit,
    and whether the root tracking folder is a symbolic link (never followed)."""
    top = os.path.join(root, TRACKING_DIR)
    top_is_link = os.path.islink(top)
    top = top if os.path.isdir(top) and not top_is_link else None
    nested, depth_limited = [], False
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not os.path.islink(os.path.join(dirpath, d))]
        depth = 0 if dirpath == root else posix(os.path.relpath(dirpath, root)).count("/") + 1
        if depth >= MAX_SCAN_DEPTH:
            if dirnames:
                depth_limited = True
            dirnames[:] = []
            continue
        for d in list(dirnames):
            if d == TRACKING_DIR:
                full = os.path.join(dirpath, d)
                if os.path.abspath(full) != os.path.abspath(os.path.join(root, TRACKING_DIR)):
                    nested.append(posix(os.path.relpath(full, root)))
                dirnames.remove(d)
    return top, sorted(nested), depth_limited, top_is_link


def classify_file(rel_in_tracking):
    """Classify a path relative to .copilot-tracking/.

    Returns ('current', area, kind, slug, date_dir, n, date_ok, name_ok), ('legacy', area, subkind, slug, date_dir),
    or None when the file lies outside the RPI areas.
    """
    parts = rel_in_tracking.split("/")
    fn = parts[-1]
    # legacy areas first: they are nested inside current areas (plans/logs, research/subagents, reviews/*)
    for area_name, (subkind, pattern) in LEGACY_AREAS.items():
        area_parts = area_name.split("/")
        if parts[:len(area_parts)] == area_parts and len(parts) >= len(area_parts) + 1:
            remainder = parts[len(area_parts):]
            if area_name == "reviews" and remainder[0] in ("plans", "logs", "code-reviews", "architecture", "rpi"):
                break
            if area_name == "reviews" and not (len(remainder) == 2 and DATE_DIR.match(remainder[0])):
                break
            m = pattern.match(fn)
            slug = m.group("slug") if m else re.sub(r"\.md$", "", fn)
            return ("legacy", area_name, subkind, slug, remainder[0] if len(remainder) >= 2 else None)
    if parts[0] == "plans" and LEGACY_PLAN.match(fn):
        return ("legacy", "plans", "implementation plan", LEGACY_PLAN.match(fn).group("slug"), parts[1] if len(parts) >= 3 else None)
    for area_name, (kind, pattern) in AREAS.items():
        area_parts = area_name.split("/")
        if parts[:len(area_parts)] == area_parts and len(parts) >= len(area_parts) + 1:
            remainder = parts[len(area_parts):]
            date_dir = next((p for p in remainder[:-1] if DATE_DIR.match(p)), None)
            m = pattern.match(fn)
            slug = m.group("slug") if m else re.sub(r"\.md$", "", fn)
            n = int(m.group("n")) if (m and m.groupdict().get("n")) else None
            date_ok = len(remainder) == 2 and DATE_DIR.match(remainder[0]) is not None
            return ("current", area_name, kind, slug, date_dir, n, date_ok, m is not None)
    return None


def discover(root, tracking_root):
    """Walk the tracking folder: RPI artifacts, legacy artifacts, misnamed files, other files, other areas, state files, symlinks."""
    artifacts, legacy, misnamed, extras, state_files, symlinks = [], [], [], [], [], []
    other_areas = Counter()
    for dirpath, dirnames, filenames in os.walk(tracking_root):
        keep = []
        for d in sorted(dirnames):
            full = os.path.join(dirpath, d)
            if os.path.islink(full):
                symlinks.append(posix(os.path.relpath(full, root)))
            else:
                keep.append(d)
        dirnames[:] = keep
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            if os.path.islink(full):
                symlinks.append(posix(os.path.relpath(full, root)))
                continue
            rel_t = posix(os.path.relpath(full, tracking_root))
            if fn.lower().endswith(".json"):
                st = load_state(full)
                if st is not None:
                    state_files.append((full, st))
                    continue
            info = classify_file(rel_t)
            if info is None:
                segs = rel_t.split("/")
                if len(segs) == 1:
                    other_areas["(files at the tracking root)"] += 1
                else:
                    two = "/".join(segs[:2])
                    other_areas[two if two in KNOWN_OTHER_AREAS else segs[0]] += 1
                continue
            if info[0] == "legacy":
                _, area, subkind, slug, date_dir = info
                art = Artifact(root, full, area, "legacy", slug, date_dir, None)
                art.legacy = subkind
                legacy.append(art)
                continue
            _, area, kind, slug, date_dir, n, date_ok, name_ok = info
            if not fn.lower().endswith(".md"):
                extras.append((posix(os.path.relpath(full, root)), area))
                continue
            if not name_ok:
                misnamed.append((posix(os.path.relpath(full, root)), area, kind))
                continue
            art = Artifact(root, full, area, kind, slug, date_dir, n)
            art.model["date_ok"] = date_ok
            artifacts.append(art)
    # second pass: research and changes files in the retired format, recognized by content or by legacy siblings
    legacy_slugs = {a.slug for a in legacy}
    current = []
    for art in artifacts:
        if looks_legacy(art, legacy_slugs):
            art.legacy = {"research": "research document", "changes": "changes log"}[art.kind]
            art.kind = "legacy"
            legacy.append(art)
        else:
            current.append(art)
    return current, legacy, misnamed, extras, state_files, other_areas, sorted(set(symlinks))


LEGACY_DISTINCTIVE = {"research": ("Planning Readiness and Next Step", "Research Record"),
                      "changes": ("Execution Status", "Return-to-Caller State", "Completed Work")}


def looks_legacy(art, legacy_slugs=()):
    """A research or changes file at a current path but written in the retired format.

    True when the file has none of the sections only the current skills write and either carries a legacy hint
    or belongs to a slug that has legacy siblings (a details file, a plan.instructions.md, a planning log).
    """
    if art.kind not in ("research", "changes") or not art.text.strip():
        return False
    if any(art.doc.has_section(s) for s in LEGACY_DISTINCTIVE[art.kind]):
        return False
    if any(h in art.text for h in LEGACY_HINTS):
        return True
    first = art.doc.headings[0][1] if art.doc.headings else ""
    current_header = first.startswith(("Task Research:", "RPI Changes:"))
    return art.slug in legacy_slugs and not current_header


def load_state(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    if isinstance(data, dict) and STATE_FIELDS.issubset(set(data.keys())):
        return redact_obj(data)
    return None


def resolve_ref(raw, art_dir, root):
    """Resolve a path mention (Markdown link, plain, or backticked) to a file; returns (display, exists, resolved_rel) or None."""
    raw = (raw or "").strip()
    if not raw or is_placeholder_value(raw):
        return None
    m = MD_LINK.search(raw)
    candidates = []
    if m:
        text = m.group(1).strip()
        dest = unquote(m.group(2).split("#")[0])
        display = dest
        if text and text != dest and text.lower() not in ("link", "plan", "changes", "research", "critique", "review"):
            display = "%s (link text %s)" % (dest, text)
        candidates.append(os.path.normpath(os.path.join(art_dir, dest)))
        if dest.startswith(TRACKING_DIR):
            candidates.append(os.path.normpath(os.path.join(root, dest)))
    else:
        display = raw.strip("`").strip()
        if not display or display.lower() in ("none", "not applicable", "n/a", "skipped"):
            return None
        display = display.split(" ")[0].strip("`,;")
        if not re.search(r"\.(md|ya?ml|json)$", display):
            return None
        candidates.append(os.path.normpath(os.path.join(root, display)))
        candidates.append(os.path.normpath(os.path.join(art_dir, display)))
    for cand in candidates:
        if os.path.isfile(cand):
            return (display, True, posix(os.path.relpath(cand, root)))
    return (display, False, None)


# --------------------------------------------------------------------------
# Models per artifact kind
# --------------------------------------------------------------------------

def model_plan(art):
    doc = art.doc
    m = art.model
    meta = bullet_fields(doc.section("Task Metadata"))
    m["task_id"] = meta.get("Task ID", "")
    m["task_slug"] = meta.get("Task slug", "")
    m["plan_date"] = meta.get("Plan date", "")
    phases, tasks = [], []
    marker_lines = {i: (k, mid) for k, mid, i in doc.markers if k in ("phase", "task")}
    for lvl, text, i in doc.headings:
        hm = ID_HEADING.match(doc.lines[i])
        if not hm:
            continue
        hid = hm.group(3)
        if not (PHASE_ID.match(hid) or TASK_ID.match(hid)):
            continue
        checked = (hm.group(2) or " ").lower() == "x"
        marker = None
        j = i - 1
        while j >= 0 and doc.lines[j].strip() == "" and i - j <= 2:
            j -= 1
        if j >= 0 and j in marker_lines:
            marker = marker_lines[j]
        blocks = labeled_blocks(doc.own_body_lines(i))
        entry = {"id": hid, "line": i, "checked": checked, "has_box": hm.group(2) is not None, "marker": marker, "blocks": blocks,
                 "title": hm.string[hm.end():].strip(" :-")}
        if PHASE_ID.match(hid):
            entry["tasks"] = []
            phases.append(entry)
        else:
            entry["phase"] = hid.split("-")[0]
            deps = TASK_ID_IN_TEXT.findall(blocks.get("Dependencies", ""))
            entry["deps"] = [d for d in deps if d != hid]
            encl = None
            for ph in phases:
                if ph["line"] < i:
                    encl = ph
            entry["enclosing"] = encl["id"] if encl else None
            if encl is not None:
                encl["tasks"].append(hid)
            tasks.append(entry)
    m["phases"] = phases
    m["tasks"] = tasks
    # markers without headings (a marker followed by a heading with a different plan ID is reported from the heading side)
    orphan_markers = []
    for k, mid, i in doc.markers:
        if k not in ("phase", "task"):
            continue
        j = i + 1
        while j < len(doc.lines) and doc.lines[j].strip() == "" and j - i <= 2:
            j += 1
        hm = ID_HEADING.match(doc.lines[j]) if j < len(doc.lines) else None
        if not hm:
            orphan_markers.append((mid, i))
    m["orphan_markers"] = orphan_markers
    reqs_text = doc.section("Functional Requirements") + "\n" + doc.section("Non-Functional Requirements")
    m["req_defined"] = ["%s-%s" % (a, b) for a, b in REQ_DEF.findall(reqs_text)]
    cited = set()
    for t in tasks:
        cited.update(REQ_CITE.findall(t["blocks"].get("Requirements", "")))
    m["req_cited"] = sorted(cited)
    ready_tbl = field_table(doc.section("Planning Readiness and Next Step"))
    m["readiness_raw"] = ready_tbl.get("Planning execution and readiness", "")
    m["readiness"] = vocab_match(m["readiness_raw"], PLAN_READINESS)
    m["latest_critique_raw"] = ready_tbl.get("Latest critique", "")
    m["blockers_raw"] = ready_tbl.get("Blockers", "")
    m["next_action_raw"] = ready_tbl.get("Next action", "")
    m["continuation_owner"] = ready_tbl.get("Continuation owner", "")
    m["relevant_research_raw"] = ready_tbl.get("Relevant research", "")
    cd = doc.section("Critique Disposition")
    cdf = bullet_fields(cd)
    m["critique_setting"] = cdf.get("Critique setting and provenance", "")
    m["critique_status"] = cdf.get("Critique status", "")
    m["critique_latest"] = cdf.get("Latest critique and verdict", "")
    disposed = set()
    for cells in table_rows(cd):
        if cells and PC_ID.search(cells[0]):
            disposed.update(PC_ID.findall(cells[0]))
    m["pc_disposed"] = sorted(disposed)
    claims = " ".join([m["critique_setting"], m["critique_status"], m["critique_latest"], m["latest_critique_raw"]])
    m["critique_skipped"] = re.search(r"\bskip", claims, re.I) is not None
    m["critique_verdict"] = vocab_match(m["critique_latest"] + " " + m["latest_critique_raw"], ("Pass", "Revise", "Blocked"), strip_paths=True)
    m["critique_path_claimed"] = re.search(r"plan-critique(?:-\d+)?\.md", m["critique_latest"] + " " + m["latest_critique_raw"]) is not None
    open_decisions = []
    for cells in table_rows(doc.section("User Decisions and Requirements")):
        if len(cells) >= 3 and re.search(r"\b(proposed|unresolved|deferred|input requested)\b", cells[2], re.I) and not is_placeholder_value(cells[1]):
            open_decisions.append((cells[0], short(cells[1], 60), cells[2]))
    m["open_decisions"] = open_decisions
    m["follow_ups"] = real_bullets(doc.section("Follow-Up Items"))
    m["h2"] = doc.h2_titles()
    return m


def model_critique(art):
    doc = art.doc
    m = art.model
    meta = bullet_fields(doc.section("Metadata"))
    m["task_id"] = meta.get("Task ID", "")
    m["plan_ref"] = meta.get("Plan", "")
    m["execution_raw"] = meta.get("Critique execution", "")
    m["execution"] = vocab_match(m["execution_raw"], EXECUTION + ("not produced",))
    m["type"] = meta.get("Critique type", "")
    m["depth"] = meta.get("Critique depth", "")
    m["verdict_raw"] = bullet_fields(doc.section("Verdict")).get("Verdict", "")
    m["verdict"] = vocab_match(m["verdict_raw"], VERDICTS, strip_paths=True)
    ids_h, sev = [], {}
    for _, _, i in doc.headings:
        hm = ID_HEADING.match(doc.lines[i])
        if hm and hm.group(3).startswith("PC-"):
            ids_h.append(hm.group(3))
            sev[hm.group(3)] = (hm.group(4) or "").capitalize()
    m["finding_ids"] = ids_h
    m["marker_ids"] = [mid for k, mid, _ in doc.markers if k == "critique"]
    m["severities"] = sev
    m["has_reconciliation"] = doc.has_section("Earlier Finding Reconciliation")
    m["next_action"] = bullet_fields(doc.section("Recommended Next Action"))
    m["h2"] = doc.h2_titles()
    return m


def model_changes(art):
    doc = art.doc
    m = art.model
    meta = bullet_fields(doc.section("Metadata"))
    m["task_id"] = meta.get("Task ID", "")
    m["plan_ref"] = meta.get("Related plan", "")
    es = bullet_fields(doc.section("Execution Status"))
    m["status_raw"] = es.get("Status", "")
    m["status"] = vocab_match(m["status_raw"], EXECUTION)
    m["scope_raw"] = es.get("Declared invocation scope", "")
    m["full_plan_scope"] = re.search(r"full[\s-]*plan", m["scope_raw"], re.I) is not None
    m["completed_markers"] = sorted(set(ANY_PLAN_ID.findall(es.get("Completed scope markers", ""))))
    m["remaining_markers"] = sorted(set(ANY_PLAN_ID.findall(es.get("All remaining active-plan markers", ""))))
    entries = []
    for title, body, i in doc.subsection_bodies("Completed Work", 3):
        f = bullet_fields(body)
        entries.append({"title": title, "related": sorted(set(ANY_PLAN_ID.findall(f.get("Related phase or task", "")))),
                        "validation": f.get("Validation", ""), "line": i})
    m["entries"] = entries
    m["entry_markers"] = sorted({r for e in entries for r in e["related"]})
    m["all_mentioned"] = sorted(set(m["completed_markers"]) | set(m["entry_markers"]) | set(m["remaining_markers"]))
    m["validation_rows"] = [c for c in table_rows(doc.section("Validation Record")) if len(c) >= 3]
    m["alignment_values"] = [vocab_match(bullet_fields(body).get("Alignment", ""), ALIGNMENT_VALUES) for _, body, _ in doc.subsection_bodies("Business Alignment", 3)]
    pr = bullet_fields(doc.section("Pre-Review Reconciliation"))
    m["review_readiness_raw"] = pr.get("Review readiness", "")
    m["review_ready"] = re.match(r"^\s*ready\b", m["review_readiness_raw"], re.I) is not None
    m["blockers"] = real_bullets(doc.section("Blockers"))
    m["remaining_work"] = [b for b in real_bullets(doc.section("Remaining Work")) if not b.startswith("Canonical")]
    m["h2"] = doc.h2_titles()
    return m


def model_review(art):
    doc = art.doc
    m = art.model
    summ = bullet_fields(doc.section("Executive Summary"))
    m["execution_raw"] = summ.get("Review execution", "")
    m["execution"] = vocab_match(m["execution_raw"], EXECUTION)
    m["outcome_raw"] = summ.get("Assessed outcome", "")
    m["outcome"] = vocab_match(m["outcome_raw"], OUTCOMES)
    findings = []
    for title, body, i in doc.subsection_bodies("Findings and Proposed Routes", 3):
        hm = ID_HEADING.match(doc.lines[i])
        if not hm or not hm.group(3).startswith("RV-"):
            continue
        f = bullet_fields(body)
        dest_raw = f.get("Proposed destination", "")
        findings.append({"id": hm.group(3), "severity": (hm.group(4) or "").capitalize(), "destination": vocab_match(dest_raw, DESTINATIONS),
                         "destination_raw": dest_raw, "title": short(title.split(":", 1)[-1], 60), "line": i})
    m["findings"] = findings
    m["marker_ids"] = [mid for k, mid, _ in doc.markers if k == "review"]
    decided, decisions, final_dests = set(), {}, {}
    pdr = doc.section("Parent Decision Record")
    for header, rows in table_blocks(pdr):
        fin_col = next((i for i, h in enumerate(header) if h.strip().lower() == "final destination"), None)
        for cells in rows:
            if len(cells) >= 4 and RD_ID.search(cells[0]):
                for rv in RV_ID.findall(cells[1]):
                    decided.add(rv)
                    decisions[rv] = cells[3]
                    # the latest event for a subject governs; a recorded route replaces the reviewer's proposal, `none` removes it
                    if fin_col is not None and fin_col < len(cells) and not is_placeholder_value(cells[fin_col]):
                        route = vocab_match(cells[fin_col], DESTINATIONS)
                        final_dests[rv] = route or ("none" if re.search(r"\bnone\b", cells[fin_col], re.I) else None)
    m["decided"] = sorted(decided)
    m["decisions"] = decisions
    for f in findings:
        fd = final_dests.get(f["id"])
        f["final_destination"] = fd
        f["route"] = f["destination"] if fd is None else (None if fd == "none" else fd)
    cur = bullet_fields(pdr)
    m["final_outcome_raw"] = cur.get("Final outcome", "")
    m["final_outcome"] = vocab_match(m["final_outcome_raw"], OUTCOMES)
    m["final_pending"] = m["final_outcome"] is None or re.search(r"\bpending\b", m["final_outcome_raw"], re.I) is not None
    rrf = bullet_fields(doc.section("Review Record"))
    m["task_id"] = rrf.get("Task ID", "")
    m["plan_ref"] = rrf.get("Plan", "")
    m["changes_ref"] = rrf.get("Changes", "")
    scope_raw = rrf.get("Review scope", "")
    m["scope_raw"] = scope_raw
    m["bounded_scope"] = ANY_PLAN_ID.search(scope_raw) is not None and not re.search(r"\bfull\b", scope_raw, re.I)
    m["h2"] = doc.h2_titles()
    return m


def model_research(art):
    doc = art.doc
    m = art.model
    tbl = field_table(doc.section("Planning Readiness and Next Step"))
    m["readiness_raw"] = tbl.get("Planning Readiness", "")
    m["readiness"] = vocab_match(m["readiness_raw"], PLAN_READINESS)
    m["disposition_raw"] = tbl.get("Research disposition", "")
    m["disposition"] = vocab_match(m["disposition_raw"], RESEARCH_DISPOSITIONS)
    m["next_action_raw"] = tbl.get("Next action", "")
    m["blockers_raw"] = tbl.get("Blockers", "")
    m["status_raw"] = bullet_fields(doc.section("Executive Summary")).get("Research status", "")
    m["evidence_defined"] = sorted(set(EVIDENCE_DEF.findall(doc.section("Research Record"))))
    user_facing = "\n".join([doc.section("Findings"), doc.section("Recommendation and Alternatives"), doc.section("Decisions and Feedback"), doc.section("What You May Not Know")])
    m["evidence_cited"] = sorted(set(EVIDENCE_CITE.findall(strip_fences_and_comments(user_facing))))
    m["h2"] = doc.h2_titles()
    return m


def model_legacy(art):
    m = art.model
    boxes = CHECKBOX.findall(art.text)
    m["steps_total"] = len(boxes)
    m["steps_checked"] = sum(1 for b in boxes if b.lower() == "x")
    m["title"] = art.doc.headings[0][1] if art.doc.headings else ""
    return m


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------

class Finding:
    def __init__(self, rule, artifact_rel, detail, slug=None, severity=None):
        self.rule = rule
        self.severity = severity or RULES[rule][1]
        self.artifact = artifact_rel
        self.detail = detail
        self.slug = slug
        self.num = None

    def fid(self):
        return "F%d" % self.num if self.num else "F?"


class Audit:
    def __init__(self, root, as_of, stale_days, single=False):
        self.root = root
        self.as_of = as_of
        self.stale_days = stale_days
        self.single = single
        self.findings = []
        self.not_evaluated = OrderedDict()
        self.artifacts = []
        self.legacy = []
        self.misnamed = []
        self.extras = []
        self.state_files = []
        self.other_areas = Counter()
        self.symlinks = []
        self.nested = []
        self.depth_limited = False
        self.tracking_root_is_link = False
        self.tracking_root = None
        self.gitignore_has_tracking = None
        self.tasks = OrderedDict()
        self.legacy_tasks = OrderedDict()
        self.board = []
        self.legacy_board = []

    # ---- bookkeeping
    def add(self, rule, artifact_rel, detail, slug=None, severity=None):
        for existing in self.findings:
            if existing.rule == rule and existing.artifact == artifact_rel and existing.detail == detail:
                return existing
        f = Finding(rule, artifact_rel, detail, slug, severity)
        self.findings.append(f)
        return f

    def scan_secrets(self, raw, rel, slug):
        for label, pat in SECRET_PATTERNS:
            mm = pat.search(raw)
            if mm:
                self.add("HY1", rel, "%s pattern at line %d" % (label, raw.count("\n", 0, mm.start()) + 1), slug)
                break

    def skip(self, rule, reason):
        self.not_evaluated.setdefault(rule, reason)

    # ---- entry points
    def run_workspace(self):
        top, nested, depth_limited, top_is_link = find_tracking_roots(self.root)
        self.tracking_root = top
        self.nested = nested
        self.depth_limited = depth_limited
        self.tracking_root_is_link = top_is_link
        if top_is_link:
            self.symlinks.append(TRACKING_DIR)
        gi = os.path.join(self.root, ".gitignore")
        if os.path.isfile(gi):
            text = read_text(gi)
            self.gitignore_has_tracking = any(re.match(r"^\s*(?:\*\*/)?/?\.copilot-tracking(?:/(?:\*\*?)?)?\s*(#.*)?$", l) for l in text.split("\n"))
        else:
            self.gitignore_has_tracking = False
        if self.gitignore_has_tracking is False:
            self.add("LY1", ".gitignore", "no `.copilot-tracking/` line in the root .gitignore%s" % ("" if os.path.isfile(gi) else " (no .gitignore at the root)"))
        for n in nested:
            self.add("LY2", n, "a .copilot-tracking folder exists below the workspace root; the RPI skills resolve only the root folder, and this audit did not read it")
        if not self.stale_days:
            self.skip("TK6", "--stale-days 0")
        if top is None:
            reason = ".copilot-tracking at the workspace root is a symbolic link, which is not followed" if top_is_link else "no .copilot-tracking/ folder at the workspace root"
            for rule in RULES:
                if rule not in ("LY1", "LY2", "TK6"):
                    self.skip(rule, reason)
            return
        self.artifacts, self.legacy, self.misnamed, self.extras, self.state_files, self.other_areas, found_links = discover(self.root, top)
        self.symlinks = sorted(set(self.symlinks) | set(found_links))
        for rel, area in self.extras:
            self.add("HY2", rel, "non-Markdown file in the %s area" % area)
        for rel, area, kind in self.misnamed:
            self.add("LY4", rel, "expected `{slug}%s` in %s; the file is listed but not modeled" % (SUFFIX_BY_KIND[kind], area))
        for art in self.artifacts:
            self.audit_artifact(art)
        for art in self.legacy:
            model_legacy(art)
        self.group_tasks()
        for slug, task in self.tasks.items():
            self.audit_task(slug, task)
        for slug, arts in self.legacy_tasks.items():
            lead = next((a for a in arts if a.legacy == "implementation plan"), arts[0])
            self.add("LY9", lead.rel, "%s for `%s`: %s" % (plural(len(arts), "legacy file"), slug, capped(sorted({a.legacy for a in arts}), 4)), slug)
        self.audit_state()
        self.build_board()
        if not self.state_files:
            for rule in ("TK7", "TK8", "TK9"):
                self.skip(rule, "no RPI Agent session state file (JSON with task_slug, active_phase, artifact_paths) found under .copilot-tracking/")

    def run_single(self, path):
        if os.path.islink(path):
            raise SystemExit("--file refuses a symbolic link: %s" % path)
        abs_path = os.path.abspath(path)
        fn = os.path.basename(abs_path)
        kind = None
        for area_name, (k, pattern) in AREAS.items():
            m = pattern.match(fn)
            if m:
                kind, slug, area = k, m.group("slug"), area_name
                n = int(m.group("n")) if m.groupdict().get("n") else None
                break
        if kind is None:
            if LEGACY_PLAN.match(fn) or fn.endswith(("-details.md", "-log.md", "-validation.md")):
                raise SystemExit("--file does not audit files in the retired Task Planner format (%s); run the script on the workspace to list them as legacy" % fn)
            raise SystemExit("--file expects a file named {slug}-research.md, -plan.md, -plan-critique.md, -changes.md, -review.md, -challenge.md, or -decisions.md; got %s" % fn)
        # workspace root: the parent of the nearest .copilot-tracking ancestor, else the file's folder
        probe, root = os.path.dirname(abs_path), None
        while True:
            if os.path.basename(probe) == TRACKING_DIR:
                root = os.path.dirname(probe)
                break
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent
        root = root or os.path.dirname(abs_path)
        self.root = root
        # the no-follow boundary applies to every component below the workspace root, not only the file itself
        probe = abs_path
        while probe != root and os.path.dirname(probe) != probe:
            if os.path.islink(probe):
                raise SystemExit("--file refuses a path through a symbolic link: %s (the audit follows no links)" % posix(os.path.relpath(probe, root)))
            probe = os.path.dirname(probe)
        date_dir = os.path.basename(os.path.dirname(abs_path))
        art = Artifact(root, abs_path, area, kind, slug, date_dir, n)
        art.model["date_ok"] = DATE_DIR.match(date_dir) is not None
        if looks_legacy(art):
            art.kind = "legacy"
            art.legacy = {"research": "research document", "changes": "changes log"}.get(kind, kind)
            model_legacy(art)
            self.legacy = [art]
            self.add("LY9", art.rel, "written in the retired format (%s)" % art.legacy, slug)
        else:
            self.artifacts = [art]
            self.audit_artifact(art)
        for rule in RULES:
            if rule in CROSS_ARTIFACT_RULES:
                self.skip(rule, "single-file run; needs the other artifacts of the task")
            elif rule in ("LY1", "LY2", "HY2"):
                self.skip(rule, "single-file run; needs the workspace")
        self.group_tasks()
        self.build_board()

    # ---- per-artifact rules
    def audit_artifact(self, art):
        rel, slug = art.rel, art.slug
        if not art.model.get("date_ok"):
            self.add("LY3", rel, "expected %s/YYYY-MM-DD/%s" % (art.area, os.path.basename(art.path)), slug)
        if slug and not KEBAB.match(slug):
            self.add("LY5", rel, "slug `%s` is not lower-kebab-case" % slug, slug)
        if not art.text.strip():
            art.unrecognized = True
            self.add("LY10", rel, "the file is empty", slug)
            return
        required = REQUIRED_BY_KIND.get(art.kind)
        if required and not any(art.doc.has_section(s) for s in required):
            art.unrecognized = True
            self.add("LY10", rel, "none of the sections a %s carries (%s) is present" % (KIND_LABEL[art.kind], capped(["`## %s`" % s for s in required], 3)), slug)
        first = art.doc.lines[0].strip() if art.doc.lines else ""
        if "markdownlint-disable-file" not in first:
            self.add("LY6", rel, "first line is `%s`" % short(first, 50), slug)
        body = strip_fences_and_comments(art.text)
        ref = line_number_reference(body)
        if ref:
            self.add("LY7", rel, "`%s`" % short(ref, 50), slug)
        if FILE_DIRECTIVE.search(body):
            self.add("LY8", rel, "`#file:` used in a tracking artifact", slug)
        self.scan_secrets(art.raw_text, rel, slug)
        placeholders = sorted(set(PLACEHOLDER.findall(body)))
        if placeholders:
            sev = "medium" if art.kind in ("plan", "changes", "review", "critique") else "low"
            self.add("PL9", rel, "%s: %s" % (plural(len(placeholders), "placeholder"), capped(["`%s`" % short(p, 40) for p in placeholders], 3)), slug, severity=sev)
        if art.unrecognized:
            return
        if art.kind == "plan":
            self.audit_plan(art)
        elif art.kind == "critique":
            self.audit_critique(art)
        elif art.kind == "changes":
            self.audit_changes(art)
        elif art.kind == "review":
            self.audit_review(art)
        elif art.kind == "research":
            self.audit_research(art)

    def check_sections(self, art):
        for sec in REQUIRED_BY_KIND[art.kind]:
            if not art.doc.has_section(sec):
                self.add("PL10", art.rel, "no `## %s` section (%s)" % (sec, KIND_LABEL[art.kind]), art.slug)

    def audit_plan(self, art):
        m = model_plan(art)
        rel, slug = art.rel, art.slug
        self.check_sections(art)
        titles = [t.strip() for t in m["h2"]]
        if "Follow-Up Items" in titles and "Handoff" in titles and titles.index("Handoff") != titles.index("Follow-Up Items") + 1:
            self.add("PL11", rel, "`## Follow-Up Items` is not directly before `## Handoff`", slug)
        for mid, i in m["orphan_markers"]:
            self.add("PL1", rel, "marker `%s` at line %d is not followed by a heading with that ID" % (mid, i + 1), slug)
        ids = Counter([p["id"] for p in m["phases"]] + [t["id"] for t in m["tasks"]])
        for dup, c in ids.items():
            if c > 1:
                self.add("PL3", rel, "`%s` appears %d times" % (dup, c), slug)
        for p in m["phases"]:
            if p["marker"] is None:
                self.add("PL2", rel, "phase `%s` heading has no `<!-- rpi:phase id=%s -->` marker before it" % (p["id"], p["id"]), slug)
            elif p["marker"] != ("phase", p["id"]):
                self.add("PL1", rel, "phase `%s` is preceded by marker `%s`" % (p["id"], p["marker"][1]), slug)
            for blk in ("Goals", "Dependencies"):
                if blk not in p["blocks"]:
                    self.add("PL8", rel, "phase `%s` has no `%s:` block" % (p["id"], blk), slug)
            if p["checked"]:
                unchecked = sorted({t["id"] for t in m["tasks"] if t["enclosing"] == p["id"] and not t["checked"]})
                if unchecked:
                    self.add("PL5", rel, "phase `%s` is checked but %s unchecked" % (p["id"], capped(unchecked)), slug)
        for t in m["tasks"]:
            if t["marker"] is None:
                self.add("PL2", rel, "task `%s` heading has no `<!-- rpi:task id=%s -->` marker before it" % (t["id"], t["id"]), slug)
            elif t["marker"] != ("task", t["id"]):
                self.add("PL1", rel, "task `%s` is preceded by marker `%s`" % (t["id"], t["marker"][1]), slug)
            if t["enclosing"] and t["enclosing"] != t["phase"]:
                self.add("PL4", rel, "task `%s` sits under phase `%s`" % (t["id"], t["enclosing"]), slug)
            missing = [b for b in ("Goals", "Requirements", "Details", "References", "Dependencies") if b not in t["blocks"]]
            if missing:
                self.add("PL7", rel, "task `%s` lacks %s" % (t["id"], capped(["`%s:`" % b for b in missing])), slug)
        defined, cited = set(m["req_defined"]), set(m["req_cited"])
        for r in sorted(defined - cited):
            self.add("PL12", rel, "`%s` is defined but no task cites it" % r, slug)
        if defined:
            for r in sorted(cited - defined):
                self.add("PL13", rel, "`%s` is cited but not defined" % r, slug)
        if m["task_slug"] and not is_placeholder_value(m["task_slug"]) and m["task_slug"].strip("`") != slug:
            self.add("PL17", rel, "Task slug `%s` in metadata, `%s` in the file name" % (m["task_slug"], slug), slug)
        if m["readiness"] in ("Not ready", "Blocked"):
            self.add("PL19", rel, "readiness `%s`; blockers: %s" % (m["readiness"], short(m["blockers_raw"] or "(not recorded)", 70)), slug)
        for grp, item, status in m["open_decisions"]:
            self.add("PL16", rel, "%s `%s` is %s" % (grp, item, short(status, 30)), slug)
        if m["readiness"] == "Ready" and not m["critique_skipped"] and m["critique_verdict"] is None:
            self.add("PL15", rel, "readiness is Ready, Critique Disposition records `%s`, no Pass, Revise, or Blocked verdict and no skip" % short(m["critique_status"] or "(nothing)", 40), slug)

    def audit_critique(self, art):
        m = model_critique(art)
        rel, slug = art.rel, art.slug
        self.check_sections(art)
        if m["verdict"] is None:
            self.add("PC2", rel, "verdict is `%s`" % short(m["verdict_raw"] or "(missing)", 40), slug)
        if m["execution"] is None:
            self.add("PC5", rel, "critique execution is `%s`" % short(m["execution_raw"] or "(missing)", 40), slug)
        for d, c in Counter(m["finding_ids"]).items():
            if c > 1:
                self.add("PC1", rel, "`%s` heading repeats" % d, slug)
        for fid in m["finding_ids"]:
            if fid not in m["marker_ids"]:
                self.add("PC1", rel, "`%s` has no `<!-- rpi:critique id=%s -->` marker" % (fid, fid), slug)
        for mid in m["marker_ids"]:
            if mid not in m["finding_ids"]:
                self.add("PC1", rel, "marker `%s` has no finding heading" % mid, slug)
        if (art.suffix_n or re.search(r"follow", m["type"], re.I)) and not m["has_reconciliation"]:
            self.add("PC4", rel, "follow-up critique without `## Earlier Finding Reconciliation`", slug)
        ref = resolve_ref(m["plan_ref"], os.path.dirname(art.path), art.root)
        if ref and not ref[1] and not self.single:
            self.add("PC3", rel, "Plan `%s` not found" % ref[0], slug)

    def audit_changes(self, art):
        m = model_changes(art)
        rel, slug = art.rel, art.slug
        self.check_sections(art)
        if m["status"] is None:
            self.add("CH3", rel, "status is `%s`" % short(m["status_raw"] or "(missing)", 40), slug)
        for e in m["entries"]:
            if is_placeholder_value(e["validation"]):
                self.add("CH5", rel, "entry `%s` (%s) has no validation result" % (short(e["title"], 40), ", ".join(e["related"]) or "no marker"), slug)
        for cells in m["validation_rows"]:
            if re.match(r"^(failed|unavailable)", cells[2], re.I):
                check = short(cells[0], 40)
                self.add("CH10", rel, "check %s is %s" % (check if check.startswith("`") else "`%s`" % check, cells[2].split()[0]), slug)
        if "pending-decision" in m["alignment_values"]:
            self.add("CH7", rel, "a Business Alignment entry is `pending-decision`", slug)
        for b in m["blockers"]:
            self.add("CH8", rel, short(b, 80), slug)
        if m["review_ready"] and (m["blockers"] or m["remaining_work"]):
            self.add("CH9", rel, "review readiness `%s` with %s and %s listed" % (short(m["review_readiness_raw"], 30), plural(len(m["blockers"]), "blocker"), plural(len(m["remaining_work"]), "remaining item")), slug)
        ref = resolve_ref(m["plan_ref"], os.path.dirname(art.path), art.root)
        if ref and not ref[1] and not self.single:
            self.add("CH6", rel, "Related plan `%s` not found" % ref[0], slug)

    def audit_review(self, art):
        m = model_review(art)
        rel, slug = art.rel, art.slug
        self.check_sections(art)
        if m["execution"] is None or m["outcome"] is None:
            self.add("RV3", rel, "execution `%s`, assessed outcome `%s`" % (short(m["execution_raw"] or "(missing)", 30), short(m["outcome_raw"] or "(missing)", 40)), slug)
        ids = [f["id"] for f in m["findings"]]
        for d, c in Counter(ids).items():
            if c > 1:
                self.add("RV1", rel, "`%s` heading repeats" % d, slug)
        for fid in ids:
            if fid not in m["marker_ids"]:
                self.add("RV1", rel, "`%s` has no `<!-- rpi:review id=%s -->` marker" % (fid, fid), slug)
        for mid in m["marker_ids"]:
            if mid not in ids:
                self.add("RV1", rel, "marker `%s` has no finding heading" % mid, slug)
        conformant = m["outcome"] in ("Conformant", "Conformant with justified divergence")
        for f in m["findings"]:
            if f["destination"] is None:
                self.add("RV2", rel, "`%s` destination is `%s`" % (f["id"], short(f["destination_raw"] or "(missing)", 40)), slug)
            if f["id"] not in m["decided"]:
                self.add("RV4", rel, "`%s` [%s] has no RD event in Decision History" % (f["id"], f["severity"] or "?"), slug)
                if conformant and f["severity"] in ("Critical", "High"):
                    self.add("RV6", rel, "`%s` [%s] undecided with assessed outcome %s" % (f["id"], f["severity"], m["outcome"]), slug)
            elif conformant and f["severity"] in ("Critical", "High") and not re.search(r"\baccepted\b", m["decisions"].get(f["id"], ""), re.I):
                self.add("RV6", rel, "`%s` [%s] decision `%s` with assessed outcome %s" % (f["id"], f["severity"], short(m["decisions"].get(f["id"], ""), 30), m["outcome"]), slug)
        if m["final_pending"] and m["execution"] == "Complete":
            self.add("RV7", rel, "Final outcome `%s`; assessed outcome `%s`" % (short(m["final_outcome_raw"] or "(not recorded)", 30), m["outcome"] or "?"), slug)
        for label, raw in (("Plan", m["plan_ref"]), ("Changes", m["changes_ref"])):
            ref = resolve_ref(raw, os.path.dirname(art.path), art.root)
            if ref and not ref[1] and not self.single:
                self.add("RV5", rel, "%s `%s` not found" % (label, ref[0]), slug)

    def audit_research(self, art):
        m = model_research(art)
        rel, slug = art.rel, art.slug
        self.check_sections(art)
        if m["readiness"] is None:
            self.add("RS1", rel, "Planning Readiness is `%s`" % short(m["readiness_raw"] or "(missing)", 40), slug)
        elif m["readiness"] in ("Not ready", "Blocked"):
            self.add("RS4", rel, "Planning Readiness `%s`; blockers: %s" % (m["readiness"], short(m["blockers_raw"] or "(not recorded)", 60)), slug)
        if m["disposition"] is None:
            self.add("RS3", rel, "Research disposition is `%s`" % short(m["disposition_raw"] or "(missing)", 40), slug)
        undefined = sorted(set(m["evidence_cited"]) - set(m["evidence_defined"]))
        if undefined and m["evidence_defined"]:
            self.add("RS2", rel, "cited but not in the Evidence Log: %s" % capped(["`%s`" % u for u in undefined]), slug)

    # ---- task grouping and cross-artifact rules
    def group_tasks(self):
        tasks = OrderedDict()
        for art in sorted(self.artifacts, key=lambda a: (a.slug, a.sort_key())):
            if art.unrecognized:
                continue
            tasks.setdefault(art.slug, {k: [] for k in KIND_ORDER})[art.kind].append(art)
        self.tasks = OrderedDict(sorted(tasks.items()))
        legacy = OrderedDict()
        for art in sorted(self.legacy, key=lambda a: (a.slug, a.sort_key())):
            legacy.setdefault(art.slug, []).append(art)
        self.legacy_tasks = OrderedDict(sorted(legacy.items()))

    @staticmethod
    def latest(task, kind):
        return task[kind][-1] if task[kind] else None

    @staticmethod
    def plan_fully_checked(plan):
        return plan is not None and bool(plan.model["tasks"]) and all(t["checked"] for t in plan.model["tasks"])

    def audit_task(self, slug, task):
        plan, changes, review, critique, research = (self.latest(task, k) for k in ("plan", "changes", "review", "critique", "research"))
        for kind in ("plan", "changes", "research"):
            if len(task[kind]) > 1:
                self.add("TK5", task[kind][-1].rel, "%s for `%s`: %s" % (plural(len(task[kind]), KIND_LABEL[kind] + " file"), slug, capped([a.rel for a in task[kind]], 3)), slug)
        # findings on a superseded critique or review are facts about history, not work to do
        for kind in ("critique", "review"):
            for older in task[kind][:-1]:
                for f in self.findings:
                    if f.artifact == older.rel and f.severity != "info" and f.rule != "HY1":
                        f.severity = "info"
                        f.detail += " (superseded by %s)" % task[kind][-1].rel
        if changes and not plan:
            self.add("TK1", changes.rel, "no `%s-plan.md` under .copilot-tracking/plans/" % slug, slug)
        if review and not changes:
            self.add("TK2", review.rel, "no `%s-changes.md` under .copilot-tracking/changes/" % slug, slug)
        if critique and not plan:
            self.add("TK3", critique.rel, "no `%s-plan.md` under .copilot-tracking/plans/" % slug, slug)
        if research and not plan and not changes and not review:
            self.add("TK10", research.rel, "research only; readiness `%s`" % (research.model.get("readiness") or "(not recorded)"), slug)
        ids = OrderedDict()
        for a in (plan, critique, changes, review):
            if a is not None:
                tid = a.model.get("task_id", "")
                if tid and not is_placeholder_value(tid):
                    ids[a.kind] = tid.strip("`")
        if len(set(ids.values())) > 1:
            self.add("TK4", (plan or changes or review or critique).rel, "; ".join("%s `%s`" % (k, v) for k, v in ids.items()), slug)
        if plan is not None:
            pm = plan.model
            task_ids = {t["id"] for t in pm["tasks"]}
            plan_ids = task_ids | {p["id"] for p in pm["phases"]}
            checked_tasks = {t["id"] for t in pm["tasks"] if t["checked"]}
            if changes is not None:
                cm = changes.model
                evidenced = set(cm["entry_markers"]) | set(cm["completed_markers"])
                for mid in sorted(set(cm["all_mentioned"]) - plan_ids):
                    self.add("CH1", changes.rel, "`%s` is not a phase or task in %s" % (mid, plan.rel), slug)
                for tid in sorted(checked_tasks - evidenced):
                    self.add("PL6", plan.rel, "`%s` is checked; %s has no entry for it" % (tid, changes.rel), slug)
                for tid in sorted((evidenced & task_ids) - checked_tasks):
                    self.add("CH2", changes.rel, "`%s` is recorded as completed; its plan marker is unchecked" % tid, slug)
                unchecked = sorted(task_ids - checked_tasks)
                if cm["status"] == "Complete" and cm["full_plan_scope"] and unchecked:
                    self.add("CH4", changes.rel, "status Complete for the full plan; unchecked: %s" % capped(unchecked), slug)
            elif checked_tasks:
                self.add("PL6", plan.rel, "%s checked and no changes record exists for `%s`" % (capped(sorted(checked_tasks)), slug), slug)
            if critique is None and pm["critique_verdict"] and pm["critique_path_claimed"] and not pm["critique_skipped"]:
                self.add("PL14", plan.rel, "plan records `%s`; no critique file under .copilot-tracking/reviews/plans/ for `%s`" % (short(pm["critique_latest"] or pm["latest_critique_raw"], 60), slug), slug)
            if critique is not None:
                for pc in critique.model["finding_ids"]:
                    if pc not in pm["pc_disposed"]:
                        self.add("PL18", plan.rel, "`%s` [%s] from %s has no disposition row" % (pc, critique.model["severities"].get(pc) or "?", critique.rel), slug)
        latest_change = max([a.mtime for k in KIND_ORDER for a in task[k] if a.mtime], default=None)
        if latest_change and self.stale_days and not self.task_accepted(task) and (self.as_of - latest_change).days > self.stale_days:
            anchor = plan or research or changes or review or next(task[k][-1] for k in KIND_ORDER if task[k])
            self.add("TK6", anchor.rel, "last change %s, %d days before the reference date" % (latest_change.isoformat(), (self.as_of - latest_change).days), slug)

    def task_accepted(self, task):
        """True when the latest review's Parent Decision Record records a Conformant final outcome for the whole task."""
        review, plan, changes = (self.latest(task, k) for k in ("review", "plan", "changes"))
        if review is None:
            return False
        rm = review.model
        if rm["execution"] != "Complete" or rm["final_pending"] or rm["final_outcome"] not in ("Conformant", "Conformant with justified divergence"):
            return False
        if rm["bounded_scope"] or plan is None or changes is None:
            return False
        return self.plan_fully_checked(plan)

    def audit_state(self):
        for path, st in self.state_files:
            rel = posix(os.path.relpath(path, self.root))
            slug = st.get("task_slug")
            slug = slug if isinstance(slug, str) and slug else None
            self.scan_secrets(read_text(path), rel, slug)
            paths = st.get("artifact_paths") or {}
            if isinstance(paths, dict):
                for key, p in paths.items():
                    if isinstance(p, str) and p and not os.path.isfile(os.path.join(self.root, p)):
                        self.add("TK7", rel, "artifact_paths.%s = `%s` does not exist" % (key, p), slug)
            task = self.tasks.get(slug) if slug else None
            phase = st.get("active_phase")
            nxt = st.get("next_action") if isinstance(st.get("next_action"), dict) else {}
            target = nxt.get("phase") or phase
            if task is not None and target in ("Implement", "Review", "Follow-up") and not task["plan"]:
                self.add("TK8", rel, "phase `%s` recorded, no plan for `%s`" % (target, slug), slug)
            elif task is not None and target in ("Review", "Follow-up") and not task["changes"]:
                self.add("TK8", rel, "phase `%s` recorded, no changes record for `%s`" % (target, slug), slug)
            elif task is None and slug and slug not in self.legacy_tasks:
                self.add("TK8", rel, "state names task `%s`, which has no recognized artifacts under .copilot-tracking/" % slug, slug)
            if st.get("status") == "completed" and task is not None and task["plan"]:
                unchecked = [t["id"] for t in task["plan"][-1].model["tasks"] if not t["checked"]]
                if unchecked:
                    self.add("TK9", rel, "status completed; unchecked: %s" % capped(unchecked), slug)

    # ---- task board
    def build_board(self):
        for slug, task in self.tasks.items():
            self.board.append(self.task_row(slug, task))
        for slug, arts in self.legacy_tasks.items():
            plan = next((a for a in arts if a.legacy == "implementation plan"), None)
            steps = (plan.model["steps_checked"], plan.model["steps_total"]) if plan else (0, 0)
            self.legacy_board.append({
                "slug": slug, "files": [a.rel for a in arts], "kinds": sorted({a.legacy for a in arts}),
                "progress": "%d/%d steps" % steps if plan else "no plan file",
                "last_change": max([a.mtime for a in arts if a.mtime], default=None),
                "next": ("finish with the Task Implementor agent that wrote it, or re-plan with `/rpi-plan task=%s draft=%s`" % (slug, plan.rel)) if plan else "re-plan with `/rpi-plan task=%s`, citing the legacy files as context" % slug,
            })

    def task_row(self, slug, task):
        plan, changes, review, research = (self.latest(task, k) for k in ("plan", "changes", "review", "research"))
        row = {"slug": slug, "artifacts": OrderedDict((k, [a.rel for a in task[k]]) for k in KIND_ORDER if task[k])}
        row["phase_reached"] = "Review" if review else "Implement" if changes else "Plan" if plan else "Research" if research else "none"
        if plan:
            pm = plan.model
            total = len(pm["tasks"])
            row["plan_progress"] = "%d/%d tasks" % (sum(1 for t in pm["tasks"] if t["checked"]), total) if total else "no tasks"
            row["readiness"] = pm["readiness"] or "(not recorded)"
            row["open_decisions"] = len(pm["open_decisions"])
            row["follow_ups"] = len(pm["follow_ups"])
            row["next_task"] = self.next_task(pm)
        else:
            row["plan_progress"] = "-"
            row["readiness"] = (research.model["readiness"] or "(not recorded)") if research else "-"
            row["open_decisions"] = 0
            row["follow_ups"] = 0
            row["next_task"] = None
        row["execution"] = (changes.model["status"] or "(not recorded)") if changes else "-"
        row["blockers"] = len(changes.model["blockers"]) if changes else 0
        if review:
            rm = review.model
            row["review"] = "%s / %s" % (rm["execution"] or "?", rm["outcome"] or "?")
            row["final_outcome"] = "pending" if rm["final_pending"] else rm["final_outcome"]
            row["undecided"] = [f["id"] for f in rm["findings"] if f["id"] not in rm["decided"]]
            row["routes"] = dict(Counter(f["route"] or ("none" if f["final_destination"] == "none" else "unrouted") for f in rm["findings"]))
            row["review_scope"] = "bounded" if rm["bounded_scope"] else "full"
        else:
            row["review"] = "-"
            row["final_outcome"] = "-"
            row["undecided"] = []
            row["routes"] = {}
            row["review_scope"] = "-"
        row["last_change"] = max([a.mtime for k in KIND_ORDER for a in task[k] if a.mtime], default=None)
        row["state"] = self.task_state(task, row)
        row["next"] = self.next_command(slug, task, row)
        high_arts = sorted({f.artifact for f in self.findings if f.severity == "high" and f.slug == slug})
        if high_arts:
            row["next"] = "repair the high findings on %s first, then: %s" % (capped(high_arts, 2), row["next"])
        if changes and changes.model["blockers"] and changes.model["status"] != "Blocked":
            row["next"] += " (a blocker is recorded in %s)" % changes.rel
        return row

    @staticmethod
    def next_task(pm):
        checked = {t["id"] for t in pm["tasks"] if t["checked"]}
        for t in pm["tasks"]:
            if not t["checked"] and all(d in checked for d in t["deps"]):
                return t["id"]
        for t in pm["tasks"]:
            if not t["checked"]:
                return t["id"] + " (dependencies unchecked)"
        return None

    def task_state(self, task, row):
        plan, changes, review, research = (self.latest(task, k) for k in ("plan", "changes", "review", "research"))
        if self.task_accepted(task):
            return "accepted"
        if review and not review.model["bounded_scope"] and (self.plan_fully_checked(plan) or plan is None):
            rm = review.model
            if plan is None or changes is None:
                return "reviewed, evidence missing"
            if row["undecided"] or rm["outcome"] in ("Defects found", "Residual work", "Not accepted"):
                return "reviewed, findings open"
            if rm["execution"] == "Complete" and rm["final_pending"]:
                return "reviewed, decision pending"
            return "review %s" % (rm["execution"] or "incomplete").lower()
        if changes and changes.model["status"] == "Blocked":
            return "blocked in implementation"
        if self.plan_fully_checked(plan):
            return "implemented, not reviewed"
        if changes:
            return "implementing"
        if plan:
            return "planned" if plan.model["readiness"] == "Ready" else "planning"
        if research:
            return "researched" if research.model["readiness"] == "Ready" else "researching"
        return "unknown"

    def next_command(self, slug, task, row):
        plan, changes, review, research = (self.latest(task, k) for k in ("plan", "changes", "review", "research"))
        state = row["state"]
        if state == "accepted":
            return "none; task accepted in the Parent Decision Record"
        if state.startswith("review") and review:
            rm = review.model
            if state == "reviewed, evidence missing":
                return "restore the %s the review compares against (%s), then rerun the audit" % ("plan and changes record" if plan is None and changes is None else "plan" if plan is None else "changes record", review.rel)
            if row["undecided"]:
                return "decide %s in the Parent Decision Record of %s, then route" % (capped(row["undecided"], 3), review.rel)
            if rm["execution"] != "Complete":
                return "/rpi-review task=%s plan=%s%s (review %s)" % (slug, plan.rel if plan else "<plan>", " changes=%s" % changes.rel if changes else "", rm["execution"] or "incomplete")
            live = [f for f in rm["findings"] if not re.search(r"\b(rejected|deferred)\b", rm["decisions"].get(f["id"], ""), re.I)]
            dests = [d for d in DESTINATIONS if any(f["route"] == d for f in live)]
            cmds = []
            if "rpi-implement" in dests and plan:
                cmds.append("/rpi-implement plan=%s" % plan.rel)
            if "rpi-plan" in dests:
                cmds.append("/rpi-plan task=%s" % slug)
            if "rpi-research" in dests:
                cmds.append("/rpi-research topic=%s" % slug)
            if "follow-up" in dests:
                cmds.append("plan the follow-up items as a separate task")
            if rm["final_pending"]:
                cmds.insert(0, "record the final outcome in Current Disposition of %s" % review.rel)
            return "; ".join(cmds) or "none recorded"
        if changes and changes.model["status"] == "Blocked":
            nt = row.get("next_task")
            return "clear the blocker (%s), then /rpi-implement plan=%s%s" % (short(changes.model["blockers"][0], 50) if changes.model["blockers"] else "see Blockers", plan.rel if plan else "<plan>", " task=%s" % nt if nt and "(" not in nt else "")
        if plan:
            pm = plan.model
            if not pm["tasks"]:
                return "/rpi-plan task=%s (the plan has no tasks)" % slug
            if self.plan_fully_checked(plan):
                return "/rpi-review task=%s plan=%s%s" % (slug, plan.rel, " changes=%s" % changes.rel if changes else "")
            if pm["readiness"] in ("Not ready", "Blocked"):
                return "/rpi-plan task=%s (readiness %s)" % (slug, pm["readiness"])
            if pm["open_decisions"]:
                return "resolve %s in %s, then /rpi-implement plan=%s" % (plural(len(pm["open_decisions"]), "open decision"), plan.rel, plan.rel)
            nt = row.get("next_task")
            if nt and "(" in nt:
                return "/rpi-implement plan=%s (first unchecked task %s)" % (plan.rel, nt)
            return "/rpi-implement plan=%s%s" % (plan.rel, " task=%s" % nt if nt else "")
        if research:
            rm = research.model
            if rm["readiness"] == "Ready":
                return "/rpi-plan task=%s research=%s" % (slug, research.rel)
            return "/rpi-research topic=%s (readiness %s)" % (slug, rm["readiness"] or "not recorded")
        return "none derivable"

    # ---- finalize
    def finalize(self):
        self.findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], str(f.slug or ""), f.artifact, f.rule))
        for n, f in enumerate(self.findings, 1):
            f.num = n


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def table(headers, rows, max_rows, more_label="rows"):
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows[:max_rows]:
        out.append("| " + " | ".join(md_escape(c) for c in r) + " |")
    if len(rows) > max_rows:
        out.append("")
        out.append("... and %d more %s. Use --max-rows to show more or --json for the full list." % (len(rows) - max_rows, more_label))
    return "\n".join(out)


def render_header(audit, brief=False, single_path=None):
    kinds = Counter(a.kind for a in audit.artifacts)
    kinds_txt = ", ".join("%d %s" % (kinds[k], KIND_LABEL[k]) for k in KIND_ORDER if kinds[k]) or "none"
    rows = []
    if single_path:
        rows.append(("File", single_path))
        rows.append(("Workspace root used for paths", audit.root))
    else:
        rows.append(("Workspace", audit.root))
        rows.append(("Tracking folder", (audit.tracking_root and posix(os.path.relpath(audit.tracking_root, audit.root))) or "not found at the root"))
    rows.append(("RPI artifacts (current format)", "%d (%s) in %s" % (len(audit.artifacts), kinds_txt, plural(len(audit.tasks), "task"))))
    if audit.legacy or not brief:
        rows.append(("Legacy artifacts (retired Task Planner format)", "%d in %s" % (len(audit.legacy), plural(len(audit.legacy_tasks), "task")) if audit.legacy else "none"))
    rows.append(("Reference date (--as-of)", audit.as_of.isoformat()))
    rows.append(("HVE Core conventions", "%s, read %s; the Copilot CLI plugin and clone installs track main. The VS Code extension (%s) ships the retired format." % (HVE_CORE_SOURCE, HVE_CORE_READ_DATE, HVE_EXTENSION_VERSION)))
    by_reason = OrderedDict()
    for rule, reason in audit.not_evaluated.items():
        by_reason.setdefault(reason, []).append(rule)
    not_eval = "; ".join("%s (%s)" % (", ".join(rules) if len(rules) <= 8 else "%d rules: %s" % (len(rules), capped(rules, 4)), reason) for reason, rules in by_reason.items())
    if brief:
        if not_eval:
            rows.append(("Rules not evaluated", not_eval))
    else:
        if audit.other_areas:
            rows.append(("Other tracking areas (not audited)", ", ".join("%s (%d)" % (k, v) for k, v in sorted(audit.other_areas.items()))))
        rows.append(("Session state files", plural(len(audit.state_files), "file") if audit.state_files else "none found"))
        rows.append(("Symbolic links skipped", ", ".join(audit.symlinks) if audit.symlinks else "none"))
        if audit.depth_limited:
            rows.append(("Scan depth", "folders deeper than %d levels were not searched for nested tracking folders" % MAX_SCAN_DEPTH))
        rows.append(("Rules not evaluated", not_eval or "none"))
        rows.append(("Not visible to this audit", "whether a person approved a plan or decided a finding, what the agent did outside the artifacts, "
                     "which host or model ran each phase, whether validation commands actually ran, git history of the ignored folder"))
    rows.append(("Tool", "hve_core_rpi_tracking_audit.py %s" % TOOL_VERSION))
    return "| Item | Value |\n| --- | --- |\n" + "\n".join("| %s | %s |" % (md_escape(k), md_escape(v)) for k, v in rows)


def render_board(audit, max_rows, brief=False):
    out = []
    if not audit.board and not audit.legacy_board:
        return "No RPI tasks found."
    if audit.board:
        if brief:
            rows = [(r["slug"], r["state"], r["plan_progress"], r["next"]) for r in audit.board]
            out.append(table(["Task", "State", "Plan", "Next action"], rows, max_rows, "tasks"))
        else:
            rows = [(r["slug"], r["state"], r["phase_reached"], r["plan_progress"], r["readiness"], r["execution"], r["review"], dash(r["final_outcome"]),
                     str(r["open_decisions"]), str(r["blockers"]), str(len(r["undecided"])), r["last_change"].isoformat() if r["last_change"] else "-") for r in audit.board]
            out.append(table(["Task", "State", "Phase reached", "Plan", "Readiness", "Execution", "Review exec / assessed outcome", "Final outcome", "Open decisions", "Blockers", "Undecided RV", "Last change"], rows, max_rows, "tasks"))
            out.append("")
            out.append("### Next action per task")
            out.append("")
            for r in audit.board[:max_rows]:
                out.append("- **%s**: %s" % (r["slug"], r["next"]))
            if len(audit.board) > max_rows:
                out.append("- ... and %d more tasks" % (len(audit.board) - max_rows))
    if audit.legacy_board:
        out.append("")
        out.append("### Legacy tasks (retired Task Planner format, not audited)")
        out.append("")
        rows = [(r["slug"], ", ".join(r["kinds"]), r["progress"], r["last_change"].isoformat() if r["last_change"] else "-", r["next"]) for r in audit.legacy_board]
        out.append(table(["Task", "Files", "Checklist", "Last change", "Next action"], rows, max_rows, "legacy tasks"))
    return "\n".join(out)


def render_attention(audit, max_rows):
    per = OrderedDict()
    for f in audit.findings:
        if f.severity in ("high", "medium"):
            per.setdefault((f.slug or "(workspace)", f.artifact), []).append(f)
    rows = []
    for (slug, art), fs in sorted(per.items(), key=lambda kv: (-sum(1 for f in kv[1] if f.severity == "high"), -len(kv[1]), kv[0])):
        hi = sum(1 for f in fs if f.severity == "high")
        rows.append((slug, art, str(hi), str(len(fs) - hi), " ".join(f.fid() for f in fs)))
    if not rows:
        return "No high or medium findings."
    return table(["Task", "Artifact", "High", "Medium", "Findings"], rows, max_rows, "artifacts")


def render_findings(audit, max_rows, brief=False):
    out = []
    by_sev = defaultdict(list)
    for f in audit.findings:
        by_sev[f.severity].append(f)
    for sev in ("high", "medium", "low", "info"):
        fs = by_sev.get(sev, [])
        if not fs:
            continue
        out.append("### %s (%d)" % (SEV_LABEL[sev], len(fs)))
        out.append("")
        if brief and sev in ("low", "info"):
            for rule, c in Counter(f.rule for f in fs).most_common():
                out.append("- **%s %s**: %s on %s. Fix: %s." % (rule, RULES[rule][0], plural(c, "finding"), plural(len({f.artifact for f in fs if f.rule == rule}), "artifact"), RULES[rule][5]))
        elif brief:
            rows = [(f.fid(), f.artifact, "%s %s. Fix: %s" % (f.rule, f.detail, RULES[f.rule][5])) for f in fs]
            out.append(table(["#", "Artifact", "Finding"], rows, max_rows, "findings"))
        else:
            rows = [(f.fid(), f.rule, f.slug or "-", f.artifact, "%s. Fix: %s." % (f.detail, RULES[f.rule][5])) for f in fs]
            out.append(table(["#", "Rule", "Task", "Artifact", "Finding"], rows, max_rows, "findings"))
        out.append("")
    return "\n".join(out).rstrip() or "No findings."


def render_remediation(audit, brief=False):
    by_control = OrderedDict((c, OrderedDict()) for c in CONTROL_ORDER)
    for f in audit.findings:
        by_control.setdefault(RULES[f.rule][2], OrderedDict()).setdefault(f.rule, []).append(f)
    out = []
    for control, rules in by_control.items():
        if not rules:
            continue
        out.append("### %s" % control)
        out.append("")
        for rule, fs in sorted(rules.items(), key=lambda kv: min(SEVERITY_ORDER[f.severity] for f in kv[1])):
            title, _, _, consequence, verify, fix = RULES[rule]
            sev_counts = Counter(f.severity for f in fs)
            sev_txt = ", ".join("%d %s" % (sev_counts[s], SEV_LABEL[s].lower()) for s in ("high", "medium", "low", "info") if sev_counts[s])
            arts = len({f.artifact for f in fs})
            refs = capped([f.fid() for f in fs])
            if brief:
                shown_refs = [f.fid() for f in fs if f.severity in ("high", "medium")]   # the brief findings section lists only these IDs
                out.append("- **%s %s**, %s on %s. %s.%s" % (rule, title, sev_txt, plural(arts, "artifact"), fix[0].upper() + fix[1:], " Refs: %s." % capped(shown_refs) if shown_refs else ""))
            else:
                out.append("- **%s %s**, %s on %s. Why: %s. Verify: %s. Fix: %s. Refs: %s." % (rule, title, sev_txt, plural(arts, "artifact"), consequence, verify, fix, refs))
        out.append("")
    return "\n".join(out).rstrip() or "Nothing to remediate."


def render_inventory(audit, max_rows):
    out = []
    for slug, task in audit.tasks.items():
        out.append("### %s" % slug)
        out.append("")
        rows = [(KIND_LABEL[kind], a.rel, a.date_dir or "-", a.mtime.isoformat() if a.mtime else "-", artifact_summary(a)) for kind in KIND_ORDER for a in task[kind]]
        out.append(table(["Kind", "Path", "Date folder", "Modified", "Summary"], rows, max_rows, "artifacts"))
        plan = Audit.latest(task, "plan")
        if plan is not None and plan.model["tasks"]:
            out.append("")
            prow = []
            for p in plan.model["phases"]:
                prow.append(("[%s] %s" % ("x" if p["checked"] else " ", p["id"]), short(p["title"], 50), "phase", "-"))
                for t in plan.model["tasks"]:
                    if t["enclosing"] == p["id"]:
                        prow.append(("[%s] %s" % ("x" if t["checked"] else " ", t["id"]), short(t["title"], 50), "task", ", ".join(t["deps"]) or "-"))
            out.append(table(["Marker", "Title", "Kind", "Depends on"], prow, max_rows, "items"))
        review = Audit.latest(task, "review")
        if review is not None and review.model["findings"]:
            out.append("")
            rrows = [(f["id"], f["severity"] or "-", f["title"], f["destination"] or "(unrouted)", f["final_destination"] or "-", short(review.model["decisions"].get(f["id"], "undecided"), 30)) for f in review.model["findings"]]
            out.append(table(["Finding", "Severity", "Title", "Proposed destination", "Final destination", "Decision"], rrows, max_rows, "findings"))
        out.append("")
    for slug, arts in audit.legacy_tasks.items():
        out.append("### %s (legacy)" % slug)
        out.append("")
        rows = [(a.legacy, a.rel, a.date_dir or "-", a.mtime.isoformat() if a.mtime else "-", "%d/%d checklist items" % (a.model.get("steps_checked", 0), a.model.get("steps_total", 0)) if a.model.get("steps_total") else "-") for a in arts]
        out.append(table(["Kind", "Path", "Date folder", "Modified", "Summary"], rows, max_rows, "files"))
        out.append("")
    if audit.misnamed:
        out.append("### Files in RPI areas not matching the naming convention (not modeled)")
        out.append("")
        out.append(table(["Path", "Area"], [(rel, area) for rel, area, _ in audit.misnamed], max_rows, "files"))
        out.append("")
    if audit.state_files:
        out.append("### Session state files")
        out.append("")
        rows = []

        def scalar(value):
            return dash(value) if isinstance(value, (str, int, float)) or value is None else short(json.dumps(value), 40)

        for path, st in audit.state_files:
            nxt = st.get("next_action") if isinstance(st.get("next_action"), dict) else None
            rows.append((posix(os.path.relpath(path, audit.root)), scalar(st.get("task_slug")), scalar(st.get("mode")), scalar(st.get("active_phase")), scalar(st.get("status")), scalar(st.get("session_status")),
                         "%s: %s" % (scalar(nxt.get("phase")), scalar(nxt.get("action"))) if nxt else scalar(st.get("next_action"))))
        out.append(table(["Path", "Task", "Mode", "Active phase", "Task status", "Session", "Next action"], rows, max_rows, "files"))
        out.append("")
    if audit.other_areas:
        out.append("### Other tracking areas (not audited)")
        out.append("")
        rows = [(k, KNOWN_OTHER_AREAS.get(k, "not an HVE Core area this tool knows"), str(v)) for k, v in sorted(audit.other_areas.items())]
        out.append(table(["Folder", "Owner workflow", "Files"], rows, max_rows, "areas"))
        out.append("")
    if audit.nested:
        out.append("### Nested tracking folders (listed, not read)")
        out.append("")
        out.extend("- %s" % n for n in audit.nested)
        out.append("")
    return "\n".join(out).rstrip() or "No RPI artifacts."


def artifact_summary(a):
    m = a.model
    if a.kind == "plan":
        total = len(m.get("tasks", []))
        return "%d/%d tasks checked; readiness %s; critique %s; task ID %s" % (sum(1 for t in m.get("tasks", []) if t["checked"]), total, m.get("readiness") or "?",
                                                                               m.get("critique_verdict") or ("skipped" if m.get("critique_skipped") else "none"), short(m.get("task_id") or "?", 30))
    if a.kind == "changes":
        return "status %s; scope %s; %s; task ID %s" % (m.get("status") or "?", short(m.get("scope_raw") or "?", 25), plural(len(m.get("entries", [])), "entry", "entries"), short(m.get("task_id") or "?", 30))
    if a.kind == "review":
        return "%s / assessed %s; final %s; %s, %d undecided; scope %s" % (m.get("execution") or "?", m.get("outcome") or "?", "pending" if m.get("final_pending") else m.get("final_outcome"),
                                                                            plural(len(m.get("findings", [])), "finding"), len([f for f in m.get("findings", []) if f["id"] not in m.get("decided", [])]),
                                                                            "bounded" if m.get("bounded_scope") else "full")
    if a.kind == "critique":
        return "verdict %s; execution %s; %s" % (m.get("verdict") or "?", m.get("execution") or "?", plural(len(m.get("finding_ids", [])), "finding"))
    if a.kind == "research":
        return "readiness %s; disposition %s" % (m.get("readiness") or "?", m.get("disposition") or "?")
    return "-"


def render_method(audit, brief=False):
    if brief:
        return ("The script read the Markdown and JSON files under .copilot-tracking/ and evaluated the rules in references/rule-catalog.md, which approximate the "
                "RPI tracking conventions on %s. Severity is an ordering heuristic, not a rating. States and next actions are derived from the artifacts' own fields and "
                "are suggestions to confirm. It did not read source code, git history, or chat transcripts, and cannot tell whether a person approved anything." % HVE_CORE_SOURCE)
    return "\n".join([
        "- The rules approximate the conventions in %s (read %s): the copilot-tracking instructions, the RPI skill templates and references, and the RPI Agent state contract. They are not HVE Core's own validation, which does not cover tracking files." % (HVE_CORE_SOURCE, HVE_CORE_READ_DATE),
        "- The VS Code extension (%s) ships the retired Task Researcher, Task Planner, Task Implementor, and Task Reviewer agents. Their artifacts are listed as legacy with checklist progress and are not audited." % HVE_EXTENSION_VERSION,
        "- Severity is a heuristic for ordering work: high means a downstream RPI phase cannot navigate the artifact or a secret is exposed; medium means artifacts disagree in a way that misleads a resume or bypasses a gate; low is convention; info is a fact for the board.",
        "- The newest dated file of each kind is treated as the task's current artifact. Earlier ones are listed under TK5, and findings on a superseded critique or review are downgraded to info, except HY1.",
        "- Values matching a credential pattern are replaced with `[redacted ...]` before any field is parsed, so neither this report nor the JSON carries them; HY1 gives the file and line.",
        "- A task is `accepted` only when its plan and changes record exist, every plan task is checked, and the latest full-scope review's Parent Decision Record records a final outcome of Conformant or Conformant with justified divergence; the Executive Summary's assessed outcome is the reviewer's proposal.",
        "- Next actions are derived from the artifacts' own status fields and markers. They are suggestions for the user to confirm, not commands the script ran.",
        "- Staleness uses file modification time against the reference date; copying a folder resets it.",
        "- Not visible: human approval, what happened in chat, which host or model ran a phase, whether validation commands ran, and anything outside the tracking folder.",
    ])


def render_markdown(audit, brief=False, max_rows=25, single_path=None):
    sev = Counter(f.severity for f in audit.findings)
    known = {a.rel for a in audit.artifacts} | {a.rel for a in audit.legacy} | {posix(os.path.relpath(p, audit.root)) for p, _ in audit.state_files}
    arts = len({f.artifact for f in audit.findings if f.severity in ("high", "medium") and f.artifact in known})
    ws = len({f.artifact for f in audit.findings if f.severity in ("high", "medium") and f.artifact not in known})
    summary = "%s: %d high, %d medium, %d low, %d info. %s%s. %s on the board%s." % (
        plural(len(audit.findings), "finding"), sev["high"], sev["medium"], sev["low"], sev["info"],
        plural(arts, "artifact needs attention", "artifacts need attention"), " plus %s" % plural(ws, "workspace-level item") if ws else "",
        plural(len(audit.tasks), "task"), ", %s" % plural(len(audit.legacy_tasks), "legacy task") if audit.legacy_tasks else "")
    parts = ["# HVE Core RPI tracking audit", "", render_header(audit, brief, single_path), "", "## Summary", "", summary, "",
             "## Task board", "", render_board(audit, max_rows, brief), "",
             "## Artifacts needing attention", "", render_attention(audit, max_rows), "",
             "## Findings", "", render_findings(audit, max_rows, brief), "",
             "## Remediation plan", "", render_remediation(audit, brief), ""]
    if not brief:
        parts += ["## Inventory", "", render_inventory(audit, max_rows), ""]
    parts += ["## Method and limits", "", render_method(audit, brief), ""]
    return "\n".join(parts)


def to_json(audit, single_path=None):
    def art_json(a):
        m = dict(a.model)
        for k in ("phases", "tasks"):
            if k in m:
                slim = []
                for item in m[k]:
                    entry = {kk: vv for kk, vv in item.items() if kk != "blocks"}
                    entry["blocks"] = sorted(item.get("blocks", {}).keys())
                    slim.append(entry)
                m[k] = slim
        if "h2" in m:
            m["sections"] = m.pop("h2")
        return {"path": a.rel, "kind": a.kind, "legacy_kind": a.legacy, "slug": a.slug, "date_dir": a.date_dir, "suffix_n": a.suffix_n,
                "modified": a.mtime.isoformat() if a.mtime else None, "unrecognized": a.unrecognized, "model": m}
    return redact_obj({
        "tool": {"name": "hve_core_rpi_tracking_audit.py", "version": TOOL_VERSION, "hve_core_source": HVE_CORE_SOURCE, "read_date": HVE_CORE_READ_DATE, "extension_versions": HVE_EXTENSION_VERSION},
        "workspace": audit.root,
        "file": single_path,
        "tracking_root": posix(os.path.relpath(audit.tracking_root, audit.root)) if audit.tracking_root else None,
        "reference_date": audit.as_of.isoformat(),
        "gitignore_has_tracking": audit.gitignore_has_tracking,
        "nested_tracking_folders": audit.nested,
        "symlinks_skipped": audit.symlinks,
        "scan_depth_limited": audit.depth_limited,
        "other_areas": dict(audit.other_areas),
        "misnamed_files": [{"path": p, "area": a} for p, a, _ in audit.misnamed],
        "rules_not_evaluated": dict(audit.not_evaluated),
        "summary": dict(Counter(f.severity for f in audit.findings)),
        "board": [dict(r, last_change=r["last_change"].isoformat() if r["last_change"] else None) for r in audit.board],
        "legacy_board": [dict(r, last_change=r["last_change"].isoformat() if r["last_change"] else None) for r in audit.legacy_board],
        "findings": [{"id": f.fid(), "rule": f.rule, "title": RULES[f.rule][0], "severity": f.severity, "control": RULES[f.rule][2], "task": f.slug, "artifact": f.artifact, "detail": f.detail, "fix": RULES[f.rule][5]} for f in audit.findings],
        "artifacts": [art_json(a) for a in audit.artifacts],
        "legacy_artifacts": [art_json(a) for a in audit.legacy],
        "state_files": [{"path": posix(os.path.relpath(p, audit.root)), "state": st} for p, st in audit.state_files],
        "rules": {k: {"title": v[0], "severity": v[1], "control": v[2]} for k, v in RULES.items()},
    })


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit RPI tracking artifacts under .copilot-tracking/ against HVE Core conventions.")
    ap.add_argument("root", nargs="?", default=".", help="repository or workspace root (default: current directory)")
    ap.add_argument("--md", help="write the Markdown report to this file")
    ap.add_argument("--json", help="write the JSON report to this file")
    ap.add_argument("--brief", action="store_true", help="chat-sized Markdown report")
    ap.add_argument("--task", help="report one task slug only")
    ap.add_argument("--file", help="audit one tracking artifact alone")
    ap.add_argument("--stale-days", type=int, default=30, help="days without change after which an open task is stale (0 disables)")
    ap.add_argument("--as-of", help="reference date YYYY-MM-DD (default: today)")
    ap.add_argument("--max-rows", type=int, default=25, help="rows per table before truncation")
    args = ap.parse_args(argv)

    try:
        as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date() if args.as_of else date.today()
    except ValueError:
        raise SystemExit("--as-of expects YYYY-MM-DD")
    if args.max_rows < 1:
        raise SystemExit("--max-rows must be at least 1")
    if args.stale_days < 0:
        raise SystemExit("--stale-days must be 0 or more")
    if args.file and args.task:
        raise SystemExit("--task cannot be combined with --file")

    single_path = None
    if args.file:
        if not os.path.isfile(args.file):
            raise SystemExit("not a file: %s" % args.file)
        audit = Audit(os.path.dirname(os.path.abspath(args.file)), as_of, 0, single=True)
        audit.run_single(args.file)
        single_path = args.file
    else:
        root = os.path.abspath(args.root)
        if not os.path.isdir(root):
            raise SystemExit("not a folder: %s" % root)
        audit = Audit(root, as_of, args.stale_days)
        audit.run_workspace()
        if args.task:
            if args.task not in audit.tasks and args.task not in audit.legacy_tasks:
                raise SystemExit("no task `%s`; tasks found: %s" % (args.task, ", ".join(list(audit.tasks) + list(audit.legacy_tasks)) or "none"))
            dropped = {posix(os.path.relpath(p, audit.root)) for p, st in audit.state_files if st.get("task_slug") != args.task}
            audit.state_files = [(p, st) for p, st in audit.state_files if st.get("task_slug") == args.task]
            audit.findings = [f for f in audit.findings if f.slug == args.task or (f.slug is None and f.artifact not in dropped)]
            audit.tasks = OrderedDict([(args.task, audit.tasks[args.task])]) if args.task in audit.tasks else OrderedDict()
            audit.legacy_tasks = OrderedDict([(args.task, audit.legacy_tasks[args.task])]) if args.task in audit.legacy_tasks else OrderedDict()
            audit.artifacts = [a for a in audit.artifacts if a.slug == args.task]
            audit.legacy = [a for a in audit.legacy if a.slug == args.task]
            audit.board = [r for r in audit.board if r["slug"] == args.task]
            audit.legacy_board = [r for r in audit.legacy_board if r["slug"] == args.task]
    audit.finalize()

    md = redact(render_markdown(audit, brief=args.brief, max_rows=args.max_rows, single_path=single_path))
    if args.md:
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write(md)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(to_json(audit, single_path), fh, indent=2, default=str)
    if not args.md and not args.json:
        sys.stdout.write(md)
    else:
        sev = Counter(f.severity for f in audit.findings)
        sys.stdout.write("%s, %d high, %d medium; %s%s. Wrote %s\n" % (plural(len(audit.findings), "finding"), sev["high"], sev["medium"], plural(len(audit.tasks), "task"),
                                                                     ", %s" % plural(len(audit.legacy_tasks), "legacy task") if audit.legacy_tasks else "",
                                                                     " and ".join(p for p in (args.md, args.json) if p)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
