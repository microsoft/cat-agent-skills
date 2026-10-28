#!/usr/bin/env python3
"""Audit a repository's GitHub Copilot customization layout against HVE Core conventions.

Usage:
    python3 hve_core_workspace_audit.py [ROOT]
        [--md report.md] [--json report.json] [--brief]
        [--file ARTIFACT]            audit one agent, prompt, instruction, SKILL.md, or copilot-instructions.md file alone
        [--include-hve-copies]       also apply convention rules to copied HVE Core artifacts
        [--global-lines 200]         soft line threshold for .github/copilot-instructions.md
        [--as-of YYYY-MM-DD]         reference date printed in the header
        [--max-rows 25]              rows shown per table before "... and N more"

ROOT is a repository or workspace folder (default: the current directory). The
script inventories .github/copilot-instructions.md, .github/agents/**/*.agent.md,
.github/prompts/**/*.prompt.md, .github/instructions/**/*.instructions.md,
.github/skills/**/SKILL.md, .github/deprecated/**, .copilot-tracking/, the root
.gitignore, .vscode/settings.json, .vscode/extensions.json, .vscode/mcp.json,
.hve-tracking.json, plugin.json, and any HVE Core clone, submodule, or
git-ignored folder it can see. It then evaluates the rules in
references/convention-catalog.md and writes an inventory, findings, and a
remediation plan.

Artifacts whose path matches a file shipped by HVE Core (catalog version below)
are reported as copies and, by default, exempt from the convention rules, since
they are maintained upstream.

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

TOOL_VERSION = "1.0.0"
HVE_CORE_CATALOG_VERSION = "3.2.2"
HVE_CORE_CATALOG_DATE = "2026-10-17"
HVE_EXTENSION_ID = "ise-hve-essentials.hve-core"

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}
SEV_LABEL = {"high": "High", "medium": "Medium", "low": "Low", "info": "Info"}
LIST_CAP = 5

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".tox", ".mypy_cache", "out", "target"}
ALLOWED_SKILL_DIRS = ("scripts", "references", "assets", "templates", "examples", "tests")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Frontmatter fields recognized per artifact type (HVE Core schema reference, 3.2.2).
AGENT_FIELDS = {"name", "description", "argument-hint", "agents", "tools", "model", "handoffs", "user-invocable",
                "disable-model-invocation", "target", "mcp-servers", "hooks", "infer"}
PROMPT_FIELDS = {"name", "description", "agent", "argument-hint", "model", "tools", "mode", "disable-model-invocation",
                 "category", "version", "author", "lastUpdated"}
INSTRUCTION_FIELDS = {"name", "description", "applyTo", "version", "author", "lastUpdated"}
SKILL_FIELDS = {"name", "description", "argument-hint", "license", "user-invocable", "disable-model-invocation",
                "compatibility", "metadata", "allowed-tools", "context"}
BUILTIN_PROMPT_AGENTS = {"ask", "agent", "plan"}
SKILL_ROOTS = ((".github", "skills"), (".claude", "skills"), (".agents", "skills"))
AGENT_ONLY_FIELDS = ("tools", "model", "agent", "handoffs", "applyTo", "agents", "mcp-servers")
MCP_SERVER_HINTS = ("microsoft-docs", "context7", "ado", "github", "figma", "work-iq", "workiq", "mural")
EGRESS_PATTERNS = (
    ("network access", re.compile(r"\b(curl|wget|Invoke-WebRequest|Invoke-RestMethod|requests\.(get|post|put|delete|request)|urllib\.request|httpx\.|fetch\(|http\.client|socket\.)", re.I)),
    ("subprocess execution", re.compile(r"\b(subprocess\.|os\.system|Start-Process|child_process|execSync|spawn\()", re.I)),
    ("credential handling", re.compile(r"\b(api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|password|passwd|bearer\s|authorization:|get_credential|DefaultAzureCredential|keyring\.)", re.I)),
)
PLACEHOLDER_LINK = re.compile(r"[{}<>]|path/to/|\.ext(#|$)|^url$|^placeholder|workspace-relative", re.I)

# Agents shipped by HVE Core: (path under .github/, name, user-invocable value or '')
HVE_AGENTS = (
    ('agents/accessibility/accessibility-planner.agent.md', 'Accessibility Planner', ''),
    ('agents/accessibility/accessibility-reviewer.agent.md', 'Accessibility Reviewer', 'true'),
    ('agents/accessibility/subagents/accessibility-framework-assessor.agent.md', 'Accessibility Framework Assessor', 'false'),
    ('agents/accessibility/subagents/accessibility-surface-inventory.agent.md', 'Accessibility Surface Inventory', 'false'),
    ('agents/agentic-workflows.agent.md', '', ''),
    ('agents/backlog-grooming.agent.md', 'Backlog Grooming', 'false'),
    ('agents/coding-standards/code-review.agent.md', 'Code Review', 'true'),
    ('agents/coding-standards/subagents/code-review-accessibility.agent.md', 'Code Review Accessibility', 'false'),
    ('agents/coding-standards/subagents/code-review-explainer.agent.md', 'Code Review Explainer', 'false'),
    ('agents/coding-standards/subagents/code-review-functional.agent.md', 'Code Review Functional', 'false'),
    ('agents/coding-standards/subagents/code-review-orientation.agent.md', 'Code Review Orientation', 'false'),
    ('agents/coding-standards/subagents/code-review-readiness.agent.md', 'Code Review Readiness', 'false'),
    ('agents/coding-standards/subagents/code-review-security.agent.md', 'Code Review Security', 'false'),
    ('agents/coding-standards/subagents/code-review-standards.agent.md', 'Code Review Standards', 'false'),
    ('agents/coding-standards/subagents/code-review-walkback.agent.md', 'Code Review Walkback', 'false'),
    ('agents/data-science-engineering/data-science-engineering-coach.agent.md', 'Data Science and Engineering Coach', 'true'),
    ('agents/dependency-reviewer.agent.md', 'Dependency Reviewer', ''),
    ('agents/design-thinking/dt-coach.agent.md', 'DT Coach', ''),
    ('agents/design-thinking/dt-learning-tutor.agent.md', 'DT Learning Tutor', ''),
    ('agents/engagement-reporting/engagement-report-generator.agent.md', 'Engagement Report Generator', ''),
    ('agents/engagement-reporting/subagents/council-arbiter.agent.md', 'Engagement Report Council Arbiter', 'false'),
    ('agents/engagement-reporting/subagents/council-critic.agent.md', 'Engagement Report Council Critic', 'false'),
    ('agents/engagement-reporting/subagents/engagement-report-reviewer.agent.md', 'Engagement Report Reviewer', 'false'),
    ('agents/engagement-reporting/subagents/outlook-drafter.agent.md', 'Engagement Report Outlook Drafter', 'false'),
    ('agents/experimental/experiment-designer.agent.md', 'Experiment Designer', ''),
    ('agents/experimental/hve-demo-material.agent.md', 'HVE Demo Material Builder', ''),
    ('agents/experimental/pptx.agent.md', 'PowerPoint Builder', ''),
    ('agents/experimental/subagents/pptx-subagent.agent.md', 'PowerPoint Subagent', 'false'),
    ('agents/hve-core/documentation.agent.md', 'Documentation', ''),
    ('agents/hve-core/rpi-agent.agent.md', 'RPI Agent', ''),
    ('agents/hve-core/subagents/hve-builder-review.agent.md', 'HVE Builder Reviewer', 'false'),
    ('agents/hve-core/subagents/rpi-researcher.agent.md', 'RPI Researcher', 'false'),
    ('agents/hve-core/subagents/rpi-reviewer.agent.md', 'RPI Reviewer', 'false'),
    ('agents/hve-core/subagents/vally-test-author.agent.md', 'Vally Test Author', 'false'),
    ('agents/issue-triage.agent.md', 'Issue Triage Agent', ''),
    ('agents/privacy/privacy-planner.agent.md', 'Privacy Planner', ''),
    ('agents/privacy/privacy-reviewer.agent.md', 'Privacy Reviewer', 'true'),
    ('agents/project-planning/adr-creation.agent.md', 'ADR Creator', ''),
    ('agents/project-planning/backlog-manager.agent.md', 'Backlog Manager', ''),
    ('agents/project-planning/brd-builder.agent.md', 'BRD Builder', ''),
    ('agents/project-planning/functional-planner.agent.md', 'Functional Planner', ''),
    ('agents/project-planning/meeting-analyst.agent.md', 'Meeting Analyst', ''),
    ('agents/project-planning/network-isa95-planner.agent.md', 'Network ISA-95 Planner', ''),
    ('agents/project-planning/prd-builder.agent.md', 'PRD Builder', ''),
    ('agents/project-planning/subagents/ado-backlog-executor.agent.md', 'ADO Backlog Executor', 'false'),
    ('agents/project-planning/subagents/brd-quality-reviewer.agent.md', 'BRD Quality Reviewer', 'false'),
    ('agents/project-planning/subagents/github-backlog-executor.agent.md', 'GitHub Backlog Executor', 'false'),
    ('agents/project-planning/subagents/jira-backlog-executor.agent.md', 'Jira Backlog Executor', 'false'),
    ('agents/project-planning/subagents/prd-quality-reviewer.agent.md', 'PRD Quality Reviewer', 'false'),
    ('agents/project-planning/system-architecture-reviewer.agent.md', 'System Architecture Reviewer', ''),
    ('agents/project-planning/ux-ui-designer.agent.md', 'UX UI Designer', ''),
    ('agents/rai-planning/rai-planner.agent.md', 'RAI Planner', ''),
    ('agents/rai-planning/rai-reviewer.agent.md', 'RAI Reviewer', 'true'),
    ('agents/rai-planning/subagents/rai-skill-assessor.agent.md', 'RAI Skill Assessor', 'false'),
    ('agents/security/security-planner.agent.md', 'Security Planner', ''),
    ('agents/security/security-reviewer.agent.md', 'Security Reviewer', 'true'),
    ('agents/security/sssc-planner.agent.md', 'SSSC Planner', ''),
    ('agents/security/sssc-reviewer.agent.md', 'SSSC Reviewer', 'true'),
    ('agents/security/subagents/codebase-profiler.agent.md', 'Codebase Profiler', 'false'),
    ('agents/security/subagents/cve-analyzer.agent.md', 'CVE Analyzer', 'false'),
    ('agents/security/subagents/finding-deep-verifier.agent.md', 'Finding Deep Verifier', 'false'),
    ('agents/security/subagents/report-generator.agent.md', 'Report Generator', 'false'),
    ('agents/security/subagents/skill-assessor.agent.md', 'Skill Assessor', 'false'),
    ('agents/security/subagents/supply-chain-skill-assessor.agent.md', 'Supply Chain Skill Assessor', 'false'),
)

# Instruction files shipped by HVE Core: (path under .github/, applyTo)
HVE_INSTRUCTIONS = (
    ('instructions/accessibility/accessibility-identity.instructions.md', '**/.copilot-tracking/accessibility/**'),
    ('instructions/accessibility/accessibility-license-posture.instructions.md', '**/.github/skills/accessibility/**, **/.copilot-tracking/accessibility/**'),
    ('instructions/ci-owned-validation.instructions.md', 'package.json, docs/docusaurus/package.json, scripts/evals/**, .github/workflows/docusaurus-tests.yml, .github/workflows/eval-validation.yml, .github/workflows/agent-conformance.yml, .github/workflows/pr-validation.yml'),
    ('instructions/coding-standards/bash/bash.instructions.md', '**/*.sh'),
    ('instructions/coding-standards/bicep/bicep.instructions.md', '**/*.bicep, **/*.bicepparam, **/bicep/**'),
    ('instructions/coding-standards/code-review/diff-computation.instructions.md', ''),
    ('instructions/coding-standards/code-review/review-artifacts.instructions.md', '**/.copilot-tracking/reviews/code-reviews/**'),
    ('instructions/coding-standards/csharp/csharp-tests.instructions.md', '**/*.cs'),
    ('instructions/coding-standards/csharp/csharp.instructions.md', '**/*.cs'),
    ('instructions/coding-standards/powershell/pester.instructions.md', '**/*.Tests.ps1'),
    ('instructions/coding-standards/powershell/powershell.instructions.md', '**/*.ps1, **/*.psm1, **/*.psd1'),
    ('instructions/coding-standards/python-script.instructions.md', '**/*.py'),
    ('instructions/coding-standards/python-tests.instructions.md', '**/*.py'),
    ('instructions/coding-standards/rust/rust-tests.instructions.md', '**/*.rs'),
    ('instructions/coding-standards/rust/rust.instructions.md', '**/*.rs'),
    ('instructions/coding-standards/terraform/terraform.instructions.md', '**/*.tf, **/*.tfvars, **/terraform/**'),
    ('instructions/coding-standards/typescript/typescript-doc-comments.instructions.md', '**/*.ts, **/*.tsx, **/*.mts, **/*.cts'),
    ('instructions/coding-standards/uv-projects.instructions.md', '**/*.py, **/*.ipynb'),
    ('instructions/dependency-feeds.instructions.md', '**/package.json, **/package-lock.json, **/npm-shrinkwrap.json, **/.npmrc, **/pyproject.toml, **/uv.lock, **/requirements*.txt'),
    ('instructions/design-thinking/dt-coach-telemetry.instructions.md', '**/.copilot-tracking/dt/**'),
    ('instructions/docusaurus-edits.instructions.md', 'docs/**'),
    ('instructions/engagement-reporting/data-handling.instructions.md', '**/.github/agents/engagement-reporting/**, **/.github/skills/engagement-reporting/**, **/engagement.yaml'),
    ('instructions/engagement-reporting/style-guide.instructions.md', '**/.github/agents/engagement-reporting/**, **/.github/skills/engagement-reporting/**'),
    ('instructions/engagement-reporting/terminology.instructions.md', '**/.github/agents/engagement-reporting/**, **/.github/skills/engagement-reporting/**, **/engagement.yaml'),
    ('instructions/experimental/experiment-designer.instructions.md', '**/.copilot-tracking/mve/**'),
    ('instructions/experimental/pptx.instructions.md', '**/.copilot-tracking/ppt/**'),
    ('instructions/hve-core/commit-message.instructions.md', ''),
    ('instructions/hve-core/copilot-tracking-location.instructions.md', '**/.copilot-tracking/**'),
    ('instructions/hve-core/copilot-tracking.instructions.md', '.copilot-tracking/research/**, .copilot-tracking/plans/**, .copilot-tracking/changes/**, .copilot-tracking/reviews/**, .copilot-tracking/challenges/**, .copilot-tracking/prompts/**, .copilot-tracking/walkthroughs/**, .copilot-tracking/hve-builder/**, .copilot-tracking/proposal-responses/**'),
    ('instructions/hve-core/git-merge.instructions.md', ''),
    ('instructions/hve-core/hve-builder.instructions.md', '**/*.prompt.md, **/*.agent.md, **/*.instructions.md, **/SKILL.md'),
    ('instructions/hve-core/licensing-posture.instructions.md', '**/skills/**, **/.copilot-tracking/**'),
    ('instructions/hve-core/markdown.instructions.md', '**/*.md'),
    ('instructions/hve-core/writing-style.instructions.md', '**/*.md'),
    ('instructions/privacy/privacy-identity.instructions.md', '**/.copilot-tracking/privacy-plans/**'),
    ('instructions/project-planning/adr-byo-template.instructions.md', '**/.copilot-tracking/adr-plans/**, **/docs/planning/adrs/**/.adr-config.yml, **/docs/planning/adrs/**'),
    ('instructions/project-planning/adr-handoff.instructions.md', '**/.copilot-tracking/adr-plans/**, **/docs/planning/adrs/**'),
    ('instructions/project-planning/adr-identity.instructions.md', '**/.copilot-tracking/adr-plans/**, **/docs/planning/adrs/**, **/docs/planning/adrs/**/.adr-config.yml'),
    ('instructions/project-planning/adr-standards.instructions.md', '**/.copilot-tracking/adr-plans/**, **/docs/planning/adrs/**'),
    ('instructions/project-planning/backlog-guardrails.instructions.md', '**/.copilot-tracking/workitems/**, **/.copilot-tracking/github-issues/**, **/.copilot-tracking/jira-issues/**'),
    ('instructions/project-planning/community-interaction.instructions.md', '**/.github/agents/project-planning/backlog-manager.agent.md, **/.github/agents/project-planning/subagents/github-backlog-executor.agent.md, **/.github/skills/project-planning/backlog-management/references/github.md'),
    ('instructions/project-planning/github-backlog-grooming.instructions.md', '**/.copilot-tracking/github-issues/backlog/**'),
    ('instructions/pull-request.instructions.md', '**/.copilot-tracking/pr/**'),
    ('instructions/rai-planning/rai-identity.instructions.md', '**/.copilot-tracking/rai-plans/**'),
    ('instructions/rai-planning/rai-license-posture.instructions.md', '**/skills/rai**/**, **/.copilot-tracking/rai-plans/**'),
    ('instructions/security/identity.instructions.md', '**/.copilot-tracking/security-plans/**'),
    ('instructions/security/sssc-planner.instructions.md', '**/.copilot-tracking/sssc-plans/**'),
    ('instructions/security/standards-mapping.instructions.md', '**/.copilot-tracking/security-plans/**'),
    ('instructions/security/tm7-generation-workflow.instructions.md', '.github/agents/security/security-planner.agent.md, .github/agents/security/security-reviewer.agent.md'),
    ('instructions/security/vex-generation.instructions.md', '**/.github/agents/security/sssc-reviewer.agent.md, **/.github/agents/security/subagents/cve-*.agent.md'),
    ('instructions/security/vex-standards.instructions.md', '**/security/vex/**, **/.copilot-tracking/security/vex/**'),
    ('instructions/shared/coaching-patterns.instructions.md', '**/.copilot-tracking/rai-plans/**, **/.copilot-tracking/security-plans/**, **/.copilot-tracking/sssc-plans/**, **/.copilot-tracking/privacy-plans/**'),
    ('instructions/shared/content-policy-citation.instructions.md', '**/*.agent.md, **/*.prompt.md, **/*.instructions.md, **/SKILL.md, **/.github/workflows/*.md, **/.github/workflows/**/*.md, **/.github/hooks/**'),
    ('instructions/shared/disclaimer-language.instructions.md', '**/.copilot-tracking/rai-plans/**, **/.copilot-tracking/rai-reviews/**, **/.copilot-tracking/security-plans/**, **/.copilot-tracking/sssc-plans/**, **/.copilot-tracking/sssc-reviews/**, **/.copilot-tracking/performance-plans/**, **/.copilot-tracking/adr-plans/**, **/.copilot-tracking/dt/**, **/.copilot-tracking/ds/**, **/docs/planning/adrs/**, **/docs/planning/outcome-hypotheses/**, **/.copilot-tracking/reviews/code-reviews/**, **/.copilot-tracking/security/**, **/.copilot-tracking/accessibility/**, **/.copilot-tracking/privacy-plans/**, **/.copilot-tracking/privacy-reviews/**, **/.copilot-tracking/prd-sessions/**, **/.copilot-tracking/brd-sessions/**, **/.copilot-tracking/documentation/**'),
    ('instructions/shared/planner-identity-base.instructions.md', '**/.copilot-tracking/sssc-plans/**, **/.copilot-tracking/rai-plans/**, **/.copilot-tracking/security-plans/**, **/.copilot-tracking/accessibility/**, **/.copilot-tracking/privacy-plans/**'),
    ('instructions/shared/telemetry-overlay.instructions.md', '**/.copilot-tracking/sssc-plans/**, **/.copilot-tracking/sssc-reviews/**, **/.copilot-tracking/rai-plans/**, **/.copilot-tracking/security-plans/**, **/.copilot-tracking/adr-plans/**, **/docs/planning/adrs/**, **/.copilot-tracking/prd-sessions/**, **/.copilot-tracking/accessibility/**, **/.copilot-tracking/privacy-plans/**, **/.copilot-tracking/privacy-reviews/**, **/.copilot-tracking/reviews/code-reviews/**, **/.copilot-tracking/changes/**'),
    ('instructions/shared/untrusted-content-boundary.instructions.md', '**/.copilot-tracking/rai-plans/**, **/.copilot-tracking/rai-reviews/**, **/.copilot-tracking/accessibility/**, **/.copilot-tracking/security-plans/**, **/.copilot-tracking/sssc-plans/**, **/.copilot-tracking/sssc-reviews/**, **/.copilot-tracking/adr-plans/**, **/.copilot-tracking/privacy-plans/**, **/.copilot-tracking/privacy-reviews/**, **/docs/planning/adrs/**, **/.copilot-tracking/prd-sessions/**, **/.copilot-tracking/brd-sessions/**, **/.copilot-tracking/proposal-responses/**, **/.copilot-tracking/documentation/**, **/.copilot-tracking/ds/**, **/.copilot-tracking/workitems/**, **/.copilot-tracking/github-issues/**, **/.copilot-tracking/jira-issues/**, **/.github/agents/design-thinking/dt-coach.agent.md, **/.github/agents/project-planning/ux-ui-designer.agent.md, **/.github/agents/project-planning/backlog-manager.agent.md, **/.github/agents/project-planning/functional-planner.agent.md, **/.github/agents/project-planning/brd-builder.agent.md, **/.github/agents/project-planning/prd-builder.agent.md, **/.github/agents/project-planning/subagents/ado-backlog-executor.agent.md, **/.github/agents/project-planning/subagents/github-backlog-executor.agent.md, **/.github/agents/project-planning/subagents/jira-backlog-executor.agent.md, **/.github/skills/project-planning/backlog-plan/SKILL.md, **/.github/skills/project-planning/backlog-execute/SKILL.md, **/.github/skills/project-planning/proposal-response/SKILL.md, **/.github/agents/project-planning/meeting-analyst.agent.md, **/.github/agents/data-science-engineering/data-science-engineering-coach.agent.md'),
    ('instructions/skill-security-model.instructions.md', '**/.github/skills/**/SECURITY.md, **/.github/skills/**/*.ps1, **/.github/skills/**/*.psm1, **/.github/skills/**/*.sh, **/.github/skills/**/*.py, **/.github/skills/**/*.js, **/.github/skills/**/*.mjs, **/.github/skills/**/*.cjs, **/.github/skills/**/*.ts, **/scripts/linting/skill-security-classification.json'),
    ('instructions/workflows.instructions.md', '**/.github/workflows/*.yml'),
)

# Skills shipped by HVE Core: (path under .github/, name, user-invocable value or '')
HVE_SKILLS = (
    ('skills/accessibility/accessibility-coverage-matrix/SKILL.md', 'accessibility-coverage-matrix', 'true'),
    ('skills/accessibility/accessibility/SKILL.md', 'accessibility', 'false'),
    ('skills/coding-standards/code-review/SKILL.md', 'code-review', 'true'),
    ('skills/coding-standards/hve-artifact-authoring/SKILL.md', 'hve-artifact-authoring', 'true'),
    ('skills/coding-standards/python-foundational/SKILL.md', 'python-foundational', 'false'),
    ('skills/data-science-engineering/analysis-authoring/SKILL.md', 'analysis-authoring', 'false'),
    ('skills/data-science-engineering/data-catalog/SKILL.md', 'data-catalog', 'false'),
    ('skills/data-science-engineering/data-science-engineering-foundation/SKILL.md', 'data-science-engineering-foundation', 'false'),
    ('skills/data-science-engineering/dataops/SKILL.md', 'dataops', 'false'),
    ('skills/data-science-engineering/evaluation-design/SKILL.md', 'evaluation-design', 'false'),
    ('skills/data-science-engineering/feasibility/SKILL.md', 'feasibility', 'false'),
    ('skills/data-science-engineering/ml-experimentation/SKILL.md', 'ml-experimentation', 'false'),
    ('skills/data-science-engineering/synth-data-generate/SKILL.md', 'synth-data-generate', 'true'),
    ('skills/design-thinking/demo-setup/SKILL.md', 'demo-setup', 'true'),
    ('skills/design-thinking/dt-coaching-foundation/SKILL.md', 'dt-coaching-foundation', 'false'),
    ('skills/design-thinking/dt-curriculum/SKILL.md', 'dt-curriculum', 'false'),
    ('skills/design-thinking/dt-figma-export/SKILL.md', 'dt-figma-export', 'true'),
    ('skills/design-thinking/dt-methods/SKILL.md', 'dt-methods', 'false'),
    ('skills/design-thinking/dt-rpi-integration/SKILL.md', 'dt-rpi-integration', 'false'),
    ('skills/design-thinking/ux-artifacts/SKILL.md', 'ux-artifacts', 'true'),
    ('skills/design-thinking/ux-coaching/SKILL.md', 'ux-coaching', 'true'),
    ('skills/engagement-reporting/engagement-report-council-critique/SKILL.md', 'engagement-report-council-critique', 'true'),
    ('skills/engagement-reporting/engagement-reporting/SKILL.md', 'engagement-reporting', 'true'),
    ('skills/experimental/caveman/SKILL.md', 'caveman', ''),
    ('skills/experimental/copilot-otel-metrics/SKILL.md', 'copilot-otel-metrics', 'true'),
    ('skills/experimental/cspell-config/SKILL.md', 'cspell-config', 'true'),
    ('skills/experimental/customer-card-render/SKILL.md', 'customer-card-render', ''),
    ('skills/experimental/demo-video/SKILL.md', 'demo-video', ''),
    ('skills/experimental/hve-demo-material/SKILL.md', 'hve-demo-material', ''),
    ('skills/experimental/mural/SKILL.md', 'mural', ''),
    ('skills/experimental/powerpoint/SKILL.md', 'powerpoint', ''),
    ('skills/experimental/tts-voiceover/SKILL.md', 'tts-voiceover', ''),
    ('skills/experimental/video-to-gif/SKILL.md', 'video-to-gif', ''),
    ('skills/experimental/vscode-playwright/SKILL.md', 'vscode-playwright', ''),
    ('skills/hve-core/architecture-diagrams/SKILL.md', 'architecture-diagrams', 'true'),
    ('skills/hve-core/c4-architecture/SKILL.md', 'c4-architecture', 'true'),
    ('skills/hve-core/documentation/SKILL.md', 'documentation', ''),
    ('skills/hve-core/git-commit/SKILL.md', 'git-commit', 'true'),
    ('skills/hve-core/git-merge/SKILL.md', 'git-merge', 'true'),
    ('skills/hve-core/git-setup/SKILL.md', 'git-setup', 'true'),
    ('skills/hve-core/hve-builder/SKILL.md', 'hve-builder', 'true'),
    ('skills/hve-core/pull-request/SKILL.md', 'pull-request', 'true'),
    ('skills/hve-core/vally-tests/SKILL.md', 'vally-tests', 'true'),
    ('skills/hve-slides/SKILL.md', 'hve-slides', 'true'),
    ('skills/installer/hve-core-installer/SKILL.md', 'hve-core-installer', ''),
    ('skills/project-planning/adr-author/SKILL.md', 'adr-author', ''),
    ('skills/project-planning/architecture-review/SKILL.md', 'architecture-review', 'false'),
    ('skills/project-planning/backlog-execute/SKILL.md', 'backlog-execute', 'true'),
    ('skills/project-planning/backlog-management/SKILL.md', 'backlog-management', 'false'),
    ('skills/project-planning/backlog-plan/SKILL.md', 'backlog-plan', 'true'),
    ('skills/project-planning/experiment-design/SKILL.md', 'experiment-design', 'false'),
    ('skills/project-planning/functional-planner/SKILL.md', 'functional-planner', 'true'),
    ('skills/project-planning/gitlab/SKILL.md', 'gitlab', ''),
    ('skills/project-planning/jira/SKILL.md', 'jira', 'true'),
    ('skills/project-planning/outcome-hypothesis/SKILL.md', 'outcome-hypothesis', 'true'),
    ('skills/project-planning/performance-slo-planner/SKILL.md', 'performance-slo-planner', 'true'),
    ('skills/project-planning/privacy-standards/SKILL.md', 'privacy-standards', 'false'),
    ('skills/project-planning/proposal-response/SKILL.md', 'proposal-response', 'true'),
    ('skills/project-planning/rai-planner/SKILL.md', 'rai-planner', 'false'),
    ('skills/project-planning/requirements-author/SKILL.md', 'requirements-author', 'false'),
    ('skills/project-planning/security-planning/SKILL.md', 'security-planning', 'true'),
    ('skills/rai/rai-standards/SKILL.md', 'rai-standards', 'false'),
    ('skills/rpi/rpi-challenger/SKILL.md', 'rpi-challenger', 'true'),
    ('skills/rpi/rpi-implement/SKILL.md', 'rpi-implement', 'true'),
    ('skills/rpi/rpi-plan-critique/SKILL.md', 'rpi-plan-critique', 'true'),
    ('skills/rpi/rpi-plan/SKILL.md', 'rpi-plan', 'true'),
    ('skills/rpi/rpi-research/SKILL.md', 'rpi-research', 'true'),
    ('skills/rpi/rpi-review/SKILL.md', 'rpi-review', 'true'),
    ('skills/rpi/rpi-walkthrough/SKILL.md', 'rpi-walkthrough', 'true'),
    ('skills/security/gh-code-scanning/SKILL.md', 'gh-code-scanning', ''),
    ('skills/security/incident-response/SKILL.md', 'incident-response', 'true'),
    ('skills/security/mcsb/SKILL.md', 'mcsb', 'false'),
    ('skills/security/owasp-agentic/SKILL.md', 'owasp-agentic', 'false'),
    ('skills/security/owasp-cicd/SKILL.md', 'owasp-cicd', 'false'),
    ('skills/security/owasp-docker/SKILL.md', 'owasp-docker', 'false'),
    ('skills/security/owasp-infrastructure/SKILL.md', 'owasp-infrastructure', 'false'),
    ('skills/security/owasp-llm/SKILL.md', 'owasp-llm', 'false'),
    ('skills/security/owasp-mcp/SKILL.md', 'owasp-mcp', 'false'),
    ('skills/security/owasp-top-10/SKILL.md', 'owasp-top-10', 'false'),
    ('skills/security/risk-register/SKILL.md', 'risk-register', 'true'),
    ('skills/security/secure-by-design/SKILL.md', 'secure-by-design', 'false'),
    ('skills/security/security-reviewer-formats/SKILL.md', 'security-reviewer-formats', 'false'),
    ('skills/security/supply-chain-security/SKILL.md', 'supply-chain-security', 'true'),
    ('skills/security/vex/SKILL.md', 'vex', 'false'),
    ('skills/shared/backlog-templates/SKILL.md', 'backlog-templates', 'true'),
    ('skills/shared/pr-reference/SKILL.md', 'pr-reference', 'true'),
    ('skills/shared/telemetry-foundations/SKILL.md', 'telemetry-foundations', ''),
)


HVE_PATHS = set()
HVE_AGENT_BY_NAME = {}
HVE_AGENT_STEMS = {}
HVE_SKILL_BY_NAME = {}
HVE_PATTERNS = defaultdict(list)


def agent_stem(path):
    return os.path.basename(path)[:-len(".agent.md")].lower() if path.lower().endswith(".agent.md") else ""


def build_catalog_indexes():
    for rel, name, _ui in HVE_AGENTS:
        HVE_PATHS.add(rel)
        if name:
            HVE_AGENT_BY_NAME[name.lower()] = rel
        HVE_AGENT_STEMS[agent_stem(rel)] = rel
    for rel, apply_to in HVE_INSTRUCTIONS:
        HVE_PATHS.add(rel)
        for pat in split_patterns(apply_to):
            HVE_PATTERNS[pat].append(rel)
    for rel, name, _ui in HVE_SKILLS:
        HVE_PATHS.add(rel)
        if name:
            HVE_SKILL_BY_NAME[name.lower()] = rel


# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------


def posix(path):
    return path.replace(os.sep, "/")


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def plural(count, noun, plural_noun=None):
    return "%d %s" % (count, noun if count == 1 else (plural_noun or noun + "s"))


def capped(items, cap=LIST_CAP, sep=", "):
    items = list(items)
    if len(items) <= cap:
        return sep.join(items)
    return sep.join(items[:cap]) + " and %d more" % (len(items) - cap)


def split_patterns(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        parts = []
        for item in value:
            parts.extend(split_patterns(item))
        return parts
    text = str(value).strip().strip("'\"")
    return [p.strip().strip("'\"") for p in text.split(",") if p.strip()]


def strip_jsonc(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(^|[^:\\\"'])//[^\n]*", r"\1", text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return text


def load_json_lenient(path):
    text = read_text(path)
    if text is None:
        return None, "unreadable"
    try:
        return json.loads(text), None
    except ValueError:
        try:
            return json.loads(strip_jsonc(text)), None
        except ValueError as exc:
            return None, str(exc)


def walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            for item in walk_strings(value):
                yield item
    elif isinstance(node, list):
        for value in node:
            for item in walk_strings(value):
                yield item


# --------------------------------------------------------------------------
# Minimal YAML subset parser for frontmatter
# --------------------------------------------------------------------------


class YAMLError(Exception):
    pass


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _is_blank(line):
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _split_inline_list(text):
    items, cur, quote, depth = [], "", None, 0
    for ch in text:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch in "[{":
            depth += 1
            cur += ch
        elif ch in "]}":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            items.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        items.append(cur.strip())
    return [yaml_scalar(i) for i in items if i != ""]


def strip_trailing_comment(text):
    """Remove a trailing ' # comment' that sits outside quotes and brackets; keep '#' inside strings or words."""
    quote, depth = None, 0
    for idx, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "#" and depth <= 0 and (idx == 0 or text[idx - 1] in " \t"):
            return text[:idx].rstrip()
    return text


def yaml_scalar(text):
    s = strip_trailing_comment(text).strip()
    if s == "":
        return ""
    if s[0] in "\"'":
        q = s[0]
        end = s.rfind(q)
        inner = s[1:end] if end > 0 else s[1:]
        return inner.replace('\\"', '"') if q == '"' else inner.replace("''", "'")
    if s.startswith("["):
        if not s.endswith("]"):
            raise YAMLError("unterminated inline list")
        return _split_inline_list(s[1:-1])
    if s.startswith("{"):
        if not s.endswith("}"):
            raise YAMLError("unterminated inline mapping")
        return OrderedDict((("_inline", s),))
    s = re.sub(r"\s+#.*$", "", s)
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "~"):
        return None
    return s


def _collect_block_scalar(lines, i, parent_indent, style):
    chunk = []
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            chunk.append("")
            i += 1
            continue
        if _indent(line) <= parent_indent:
            break
        chunk.append(line)
        i += 1
    while chunk and chunk[-1] == "":
        chunk.pop()
    if not chunk:
        return "", i
    base = min(_indent(l) for l in chunk if l.strip())
    body = [l[base:] if l.strip() else "" for l in chunk]
    if style.startswith("|"):
        return "\n".join(body), i
    folded, para = [], []
    for l in body:
        if l == "":
            if para:
                folded.append(" ".join(para))
                para = []
            folded.append("")
        else:
            para.append(l.strip())
    if para:
        folded.append(" ".join(para))
    text = "\n".join(folded)
    return re.sub(r"\n{2,}", "\n", text).strip(), i


def _collect_quoted(lines, i, first):
    q = first[0]
    first = strip_trailing_comment(first)
    if len(first) > 1 and first.endswith(q) and not first.endswith("\\" + q):
        return yaml_scalar(first), i + 1
    parts = [first]
    i += 1
    while i < len(lines):
        piece = lines[i].strip()
        if q == '"':
            closed = re.search(r'(?<!\\)"(\s+#.*)?$', piece) is not None
        else:
            closed = re.search(r"'(\s+#.*)?$", piece) is not None and not piece.endswith("''")
        parts.append(strip_trailing_comment(piece) if closed else piece)
        if closed:
            return yaml_scalar(" ".join(parts)), i + 1
        i += 1
    raise YAMLError("unterminated quoted string")


def parse_node(lines, i, min_indent):
    while i < len(lines) and _is_blank(lines[i]):
        i += 1
    if i >= len(lines):
        return None, i
    ind = _indent(lines[i])
    if ind < min_indent:
        return None, i
    content = lines[i].strip()
    if content == "-" or content.startswith("- "):
        return parse_seq(lines, i, ind)
    return parse_map(lines, i, ind)


def parse_map(lines, i, indent):
    result = OrderedDict()
    while i < len(lines):
        line = lines[i]
        if _is_blank(line):
            i += 1
            continue
        ind = _indent(line)
        if ind < indent:
            break
        if ind > indent:
            raise YAMLError("unexpected indentation at line %d" % (i + 1))
        content = line.strip()
        if content == "-" or content.startswith("- "):
            raise YAMLError("list item where a key was expected at line %d" % (i + 1))
        m = re.match(r"^(\"[^\"]*\"|'[^']*'|[^:#]+?)\s*:(?:\s+(.*))?$", content)
        if not m:
            raise YAMLError("expected 'key: value' at line %d" % (i + 1))
        key = m.group(1).strip().strip("\"'")
        rest = (m.group(2) or "").strip()
        if rest.startswith("#"):
            rest = ""
        elif rest[:1] not in "\"'":
            rest = strip_trailing_comment(rest).strip()
        if rest == "":
            j = i + 1
            while j < len(lines) and _is_blank(lines[j]):
                j += 1
            if j < len(lines):
                nind = _indent(lines[j])
                ncontent = lines[j].strip()
                if nind > indent:
                    value, i = parse_node(lines, j, nind)
                    result[key] = value
                    continue
                if nind == indent and (ncontent == "-" or ncontent.startswith("- ")):
                    value, i = parse_seq(lines, j, indent)
                    result[key] = value
                    continue
            result[key] = None
            i += 1
            continue
        if rest in ("|", ">", "|-", ">-", "|+", ">+"):
            value, i = _collect_block_scalar(lines, i + 1, indent, rest)
            result[key] = value
            continue
        if rest[0] in "\"'":
            value, i = _collect_quoted(lines, i, rest)
            result[key] = value
            continue
        # Plain scalar; fold continuation lines that are more indented and are neither keys nor list items.
        parts = [rest]
        i += 1
        while i < len(lines) and not _is_blank(lines[i]) and _indent(lines[i]) > indent:
            cont = lines[i].strip()
            if cont == "-" or cont.startswith("- ") or re.match(r"^(\"[^\"]*\"|'[^']*'|[^:#]+?)\s*:(\s+|$)", cont):
                break
            parts.append(cont)
            i += 1
        result[key] = yaml_scalar(" ".join(parts))
    return result, i


def parse_seq(lines, i, indent):
    result = []
    while i < len(lines):
        line = lines[i]
        if _is_blank(line):
            i += 1
            continue
        ind = _indent(line)
        if ind < indent:
            break
        if ind > indent:
            raise YAMLError("unexpected indentation at line %d" % (i + 1))
        content = line.strip()
        if not (content == "-" or content.startswith("- ")):
            break
        item = content[1:].strip()
        if item.startswith("#"):
            item = ""
        elif item[:1] not in "\"'":
            item = strip_trailing_comment(item).strip()
        if item == "":
            value, i = parse_node(lines, i + 1, indent + 1)
            result.append(value)
            continue
        if re.match(r"^(\"[^\"]*\"|'[^']*'|[^:#]+?)\s*:(\s+.*)?$", item) and not item.startswith("[") and not item[0] in "\"'":
            col = ind + 2
            lines[i] = " " * col + item
            value, i = parse_map(lines, i, col)
            result.append(value)
            continue
        if item[0] in "\"'":
            value, i = _collect_quoted(lines, i, item)
            result.append(value)
            continue
        result.append(yaml_scalar(item))
        i += 1
    return result, i


def parse_frontmatter(text):
    """Return (mapping or None, error or None, body)."""
    if text is None:
        return None, "file could not be read", ""
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return None, "no frontmatter at the top of the file", text
    lines = text.splitlines()
    if lines[0].strip() != "---":
        return None, "no frontmatter at the top of the file", text
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() in ("---", "..."):
            end = idx
            break
    if end is None:
        return None, "frontmatter is not closed with a second '---' line", text
    block = lines[1:end]
    body = "\n".join(lines[end + 1:])
    if not any(l.strip() for l in block):
        return OrderedDict(), None, body
    for offset, line in enumerate(block):
        if line.startswith("\t") or re.match(r"^ *\t", line):
            return None, "frontmatter could not be parsed (tab used for indentation at line %d; YAML requires spaces)" % (offset + 2), body
    try:
        value, _ = parse_node(list(block), 0, 0)
    except YAMLError as exc:
        return None, "frontmatter could not be parsed (%s)" % exc, body
    if value is None:
        return OrderedDict(), None, body
    if not isinstance(value, dict):
        return None, "frontmatter is not a mapping of keys to values", body
    return value, None, body


# --------------------------------------------------------------------------
# Artifact model and discovery
# --------------------------------------------------------------------------


class Artifact:
    def __init__(self, abs_path, rel_path, kind):
        self.abs_path = abs_path
        self.rel = posix(rel_path)
        self.kind = kind            # agent | prompt | instruction | skill | global | misnamed | deprecated
        self.github_rel = ""        # path under the owning .github/ folder
        self.location = ".github"   # .github, .claude, or .agents
        self.gh_prefix = ""         # "" for the root .github, "packages/app/" for a nested one
        self.package = ""
        self.is_subagent = False
        self.hve_copy = False
        self.fm = None
        self.fm_error = None
        self.body = ""
        self.text = ""
        self.findings = []
        self.skill_dir = None

    @property
    def name(self):
        if isinstance(self.fm, dict):
            value = self.fm.get("name")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    @property
    def description(self):
        if isinstance(self.fm, dict):
            value = self.fm.get("description")
            if isinstance(value, str):
                return value.strip()
            if value is not None:
                return str(value)
        return ""

    def label(self):
        return self.rel


def kind_from_name(filename, in_type=None):
    low = filename.lower()
    if low.endswith(".agent.md"):
        return "agent"
    if low.endswith(".prompt.md"):
        return "prompt"
    if low.endswith(".instructions.md"):
        return "instruction"
    if filename == "SKILL.md":
        return "skill"
    return None


def discover(root, hve_clone_dirs):
    """Walk ROOT and return artifacts, misnamed files, deprecated files, and skipped symlinks.

    Symlinked folders and files are never followed: os.walk would traverse a symlink given as
    its starting directory even with followlinks=False, which could pull files from outside
    ROOT into the report. Every skipped link is recorded so the header can list it.
    """
    artifacts, misnamed, deprecated, symlinks = [], [], [], []
    root = os.path.abspath(root)
    skip_abs = set(os.path.abspath(p) for p in hve_clone_dirs)

    def rel(path):
        return posix(os.path.relpath(path, root))

    def linked(path):
        if os.path.islink(path):
            symlinks.append(rel(path))
            return True
        return False

    def prune(dirpath, dirnames):
        kept = []
        for d in dirnames:
            full = os.path.join(dirpath, d)
            if d in SKIP_DIRS or full in skip_abs:
                continue
            if linked(full):
                continue
            kept.append(d)
        dirnames[:] = kept

    for dirpath, dirnames, filenames in os.walk(root):
        prune(dirpath, dirnames)
        base_name = os.path.basename(dirpath)
        if base_name in (".claude", ".agents"):
            skills_dir = os.path.join(dirpath, "skills")
            if not linked(skills_dir) and os.path.isdir(skills_dir):
                for dp, dns, fns in os.walk(skills_dir):
                    prune(dp, dns)
                    if "SKILL.md" in fns and not linked(os.path.join(dp, "SKILL.md")):
                        full = os.path.join(dp, "SKILL.md")
                        art = Artifact(full, os.path.relpath(full, root), "skill")
                        art.location = base_name
                        art.skill_dir = dp
                        artifacts.append(art)
            continue
        if base_name != ".github":
            continue
        gh = dirpath
        gh_rel_prefix = posix(os.path.relpath(gh, root))
        gh_rel_prefix = "" if gh_rel_prefix == ".github" else gh_rel_prefix[:-len(".github")]
        global_path = os.path.join(gh, "copilot-instructions.md")
        if os.path.isfile(global_path) and not linked(global_path):
            art = Artifact(global_path, os.path.relpath(global_path, root), "global")
            art.github_rel = "copilot-instructions.md"
            art.gh_prefix = gh_rel_prefix
            artifacts.append(art)
        for type_dir, kind in (("agents", "agent"), ("prompts", "prompt"), ("instructions", "instruction"), ("skills", "skill")):
            base = os.path.join(gh, type_dir)
            if linked(base) or not os.path.isdir(base):
                continue
            for dp, dns, fns in os.walk(base):
                prune(dp, dns)
                for fn in fns:
                    full = os.path.join(dp, fn)
                    if fn.lower().endswith(".md") and linked(full):
                        continue
                    rel_in_type = posix(os.path.relpath(full, base))
                    parts = rel_in_type.split("/")
                    detected = kind_from_name(fn)
                    if kind == "skill":
                        if fn.lower() == "skill.md" and fn != "SKILL.md":
                            misnamed.append((posix(os.path.relpath(full, root)), kind, "named %s; Copilot looks for SKILL.md (exact case)" % fn))
                            continue
                        if fn != "SKILL.md":
                            continue
                        art = Artifact(full, os.path.relpath(full, root), "skill")
                        art.github_rel = "skills/" + rel_in_type
                        art.gh_prefix = gh_rel_prefix
                        art.skill_dir = dp
                        if len(parts) == 1:
                            misnamed.append((posix(os.path.relpath(full, root)), kind, "SKILL.md sits directly under .github/skills/ with no skill folder"))
                            continue
                        art.package = parts[0] if len(parts) >= 3 else ""
                        art.hve_copy = art.github_rel in HVE_PATHS
                        artifacts.append(art)
                        continue
                    if not fn.lower().endswith(".md"):
                        continue
                    if fn.lower() == "readme.md":
                        continue
                    if detected is None or detected != kind:
                        if "/references/" in "/" + rel_in_type or "/assets/" in "/" + rel_in_type or "/templates/" in "/" + rel_in_type:
                            continue
                        if kind == "agent":
                            reason = "a .md file under .github/agents/ without the .agent.md suffix; VS Code loads it as a Claude-format agent, but it is outside HVE Core's naming convention, excluded from packaging, and not an agent for hosts that key on the suffix"
                        else:
                            reason = "a .md file under .github/%s/ that does not end with .%s.md, so no host discovers it" % (type_dir, type_dir[:-1] if kind != "instruction" else "instructions")
                        misnamed.append((posix(os.path.relpath(full, root)), kind, reason))
                        continue
                    art = Artifact(full, os.path.relpath(full, root), kind)
                    art.github_rel = type_dir + "/" + rel_in_type
                    art.gh_prefix = gh_rel_prefix
                    art.package = parts[0] if len(parts) >= 2 else ""
                    art.is_subagent = kind == "agent" and "subagents" in parts[:-1]
                    art.hve_copy = art.github_rel in HVE_PATHS
                    artifacts.append(art)
        dep = os.path.join(gh, "deprecated")
        if os.path.isdir(dep) and not linked(dep):
            for dp, dns, fns in os.walk(dep):
                prune(dp, dns)
                for fn in fns:
                    if fn.lower().endswith(".md") and not linked(os.path.join(dp, fn)):
                        deprecated.append(os.path.join(dp, fn))
    for art in artifacts:
        art.text = read_text(art.abs_path) or ""
        if art.kind == "global":
            art.body = art.text
            fm, err, body = parse_frontmatter(art.text)
            art.fm = fm if fm is not None else OrderedDict()
            art.body = body if fm is not None else art.text
        else:
            art.fm, art.fm_error, art.body = parse_frontmatter(art.text)
    return artifacts, misnamed, deprecated, sorted(set(symlinks))


def linked_component(path):
    """Return the first symbolic link among the file and its ancestors inside the customization tree.

    Ancestors are checked from the nearest .github, .claude, or .agents folder in the given path
    down to the file; when the path has none, the parent folder and the file are checked. System
    links above the repository (such as /tmp on macOS) are left alone.
    """
    norm = os.path.normpath(path)
    parts = norm.split(os.sep)
    start = next((i for i, p in enumerate(parts) if p in (".github", ".claude", ".agents")), max(0, len(parts) - 2))
    for idx in range(start, len(parts)):
        prefix = os.sep.join(parts[:idx + 1]) or os.sep
        if os.path.islink(prefix):
            return prefix
    return None


def load_single(path):
    link = linked_component(path)
    if link:
        raise SystemExit("--file refuses a path through a symbolic link (%s); links can point outside the workspace" % link)
    abs_path = os.path.abspath(path)
    fn = os.path.basename(abs_path)
    kind = kind_from_name(fn)
    if kind is None:
        if fn.lower() == "copilot-instructions.md":
            kind = "global"
        else:
            raise SystemExit("--file expects a *.agent.md, *.prompt.md, *.instructions.md, SKILL.md, or copilot-instructions.md file")
    art = Artifact(abs_path, fn, kind)
    art.text = read_text(abs_path) or ""
    parent = posix(abs_path)
    if kind == "skill":
        art.skill_dir = os.path.dirname(abs_path)
    m = re.search(r"/\.github/(agents|prompts|instructions|skills)/(.*)$", parent)
    if m:
        art.github_rel = m.group(1) + "/" + m.group(2)
        parts = m.group(2).split("/")
        art.package = parts[0] if len(parts) >= (3 if kind == "skill" else 2) else ""
        art.is_subagent = kind == "agent" and "subagents" in parts[:-1]
        art.hve_copy = art.github_rel in HVE_PATHS
    if kind == "global":
        fm, err, body = parse_frontmatter(art.text)
        art.fm = fm if fm is not None else OrderedDict()
        art.body = body if fm is not None else art.text
    else:
        art.fm, art.fm_error, art.body = parse_frontmatter(art.text)
    return art


# --------------------------------------------------------------------------
# Workspace context (install sources, tracking, settings)
# --------------------------------------------------------------------------


def detect_workspace(root):
    ctx = OrderedDict()
    root = os.path.abspath(root)
    ctx["root"] = root
    gitignore = read_text(os.path.join(root, ".gitignore"))
    ctx["gitignore_present"] = gitignore is not None
    ignore_lines = [l.strip() for l in (gitignore or "").splitlines() if l.strip() and not l.strip().startswith("#")]
    ctx["tracking_ignored"] = any(re.match(r"^/?(\*\*/)?\.copilot-tracking(/|/\*|/\*\*)?$", l) for l in ignore_lines)
    ctx["tracking_present"] = os.path.isdir(os.path.join(root, ".copilot-tracking"))
    ctx["tracking_activity"] = tracking_activity(os.path.join(root, ".copilot-tracking")) if ctx["tracking_present"] else OrderedDict()
    sources = []
    ext_path = os.path.join(root, ".vscode", "extensions.json")
    ctx["extensions_json"] = os.path.isfile(ext_path)
    ctx["extension_recommended"] = False
    if ctx["extensions_json"]:
        data, _err = load_json_lenient(ext_path)
        recs = []
        if isinstance(data, dict):
            recs = [str(r).lower() for r in data.get("recommendations", []) if isinstance(r, str)]
        if HVE_EXTENSION_ID in recs:
            ctx["extension_recommended"] = True
            sources.append(("extension", ".vscode/extensions.json recommends %s" % HVE_EXTENSION_ID, ""))
    clones = []
    gitmodules = read_text(os.path.join(root, ".gitmodules")) or ""
    submodule_paths = []
    cur = None
    for line in gitmodules.splitlines():
        m = re.match(r'^\s*\[submodule\s+"([^"]+)"\]', line)
        if m:
            cur = {"name": m.group(1)}
            submodule_paths.append(cur)
            continue
        m = re.match(r"^\s*(path|url)\s*=\s*(.+)$", line)
        if m and cur is not None:
            cur[m.group(1)] = m.group(2).strip()
    for sm in submodule_paths:
        if "hve-core" in (sm.get("url", "") + sm.get("name", "") + sm.get("path", "")).lower():
            p = os.path.join(root, sm.get("path", sm.get("name", "")))
            clones.append(("submodule", p))
    candidates = [os.path.join(root, "hve-core"), os.path.join(os.path.dirname(root), "hve-core")]
    for cand in candidates:
        if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "plugin.json")) and not any(os.path.abspath(cand) == os.path.abspath(c[1]) for c in clones):
            method = "peer-clone" if os.path.dirname(os.path.abspath(cand)) == os.path.dirname(root) else "folder"
            if method == "folder" and any(re.match(r"^/?hve-core/?$", l) for l in ignore_lines):
                method = "git-ignored-folder"
            clones.append((method, cand))
    for fn in os.listdir(root) if os.path.isdir(root) else []:
        if fn.endswith(".code-workspace"):
            text = read_text(os.path.join(root, fn)) or ""
            if "hve-core" in text.lower():
                sources.append(("multi-root", "%s references hve-core" % fn, ""))
    ctx["clones"] = []
    for method, path in clones:
        version = ""
        data, _err = load_json_lenient(os.path.join(path, "plugin.json"))
        if isinstance(data, dict):
            version = str(data.get("version", ""))
        ctx["clones"].append(OrderedDict((("method", method), ("path", posix(path)), ("version", version))))
        sources.append((method, "%s at %s%s" % (method, posix(os.path.relpath(path, root)) if path.startswith(root) else posix(path), " (plugin.json version %s)" % version if version else ""), ""))
    track_path = os.path.join(root, ".hve-tracking.json")
    ctx["hve_tracking"] = None
    if os.path.isfile(track_path):
        data, err = load_json_lenient(track_path)
        entry = OrderedDict((("present", True), ("error", err), ("schemaVersion", None), ("paths", []), ("missing", [])))
        if data is not None and not isinstance(data, dict) and not err:
            entry["error"] = "file is a JSON %s, not an object" % type(data).__name__
        if isinstance(data, dict):
            entry["schemaVersion"] = data.get("schemaVersion", data.get("schema_version", data.get("version")))
            paths = sorted(set(s for s in walk_strings(data) if ".github/" in s and s.lower().endswith((".md", "/"))))
            entry["paths"] = paths
            entry["missing"] = [p for p in paths if not os.path.exists(os.path.join(root, p.lstrip("/")))]
        ctx["hve_tracking"] = entry
        sources.append(("selective-clone", ".hve-tracking.json present (%s)" % ("schema version %s" % entry["schemaVersion"] if entry["schemaVersion"] is not None else "schema version unknown"), ""))
        entry["schemaLabel"] = str(entry["schemaVersion"]) if entry["schemaVersion"] is not None else "unknown"
    ctx["sources"] = sources
    settings_path = os.path.join(root, ".vscode", "settings.json")
    ctx["settings_json"] = os.path.isfile(settings_path)
    ctx["settings_locations"] = OrderedDict()
    ctx["settings_error"] = None
    if ctx["settings_json"]:
        data, err = load_json_lenient(settings_path)
        ctx["settings_error"] = err
        if isinstance(data, dict):
            for key in ("chat.agentFilesLocations", "chat.modeFilesLocations", "chat.instructionsFilesLocations", "chat.agentSkillsLocations", "chat.promptFilesLocations", "chat.hookFilesLocations"):
                value = data.get(key)
                if isinstance(value, dict):
                    ctx["settings_locations"][key] = OrderedDict((k, bool(v)) for k, v in value.items())
                elif isinstance(value, list):
                    ctx["settings_locations"][key] = OrderedDict((str(k), True) for k in value)
    ctx["mcp_json"] = os.path.isfile(os.path.join(root, ".vscode", "mcp.json"))
    ctx["agents_md"] = os.path.isfile(os.path.join(root, "AGENTS.md"))
    ctx["claude_md"] = os.path.isfile(os.path.join(root, "CLAUDE.md"))
    plugin_path = os.path.join(root, "plugin.json")
    ctx["plugin_json"] = None
    if os.path.isfile(plugin_path):
        data, err = load_json_lenient(plugin_path)
        entry = OrderedDict((("error", err), ("version", ""), ("members", OrderedDict())))
        if isinstance(data, dict):
            entry["version"] = str(data.get("version", ""))
            for key in ("agents", "prompts", "commands", "instructions", "rules", "skills"):
                value = data.get(key)
                if isinstance(value, list):
                    entry["members"][key] = [str(v) for v in value if isinstance(v, str)]
        ctx["plugin_json"] = entry
    return ctx


def tracking_activity(path):
    out = OrderedDict()
    if os.path.islink(path):
        return out
    for sub in ("research", "plans", "changes", "reviews", "hve-builder", "security-plans", "rai-plans", "adr-plans", "dt"):
        p = os.path.join(path, sub)
        if not os.path.isdir(p) or os.path.islink(p):
            continue
        files, latest = 0, ""
        for dp, dns, fns in os.walk(p):
            dns[:] = [d for d in dns if not os.path.islink(os.path.join(dp, d))]
            files += len([f for f in fns if f.lower().endswith(".md")])
            for d in dns:
                if re.match(r"^\d{4}-\d{2}-\d{2}$", d) and d > latest:
                    latest = d
        out[sub] = OrderedDict((("files", files), ("latest", latest)))
    return out


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------

RULES = OrderedDict([
    ("FM1", ("Frontmatter missing or unparseable", "high")),
    ("FM2", ("Description missing", "high")),
    ("FM3", ("Description length outside the documented range", "low")),
    ("FM4", ("Field that belongs to another artifact type", "medium")),
    ("FM5", ("Field not in the HVE Core schema reference", "info")),
    ("FM6", ("Deprecated infer field", "low")),
    ("AG1", ("Agent without a name", "medium")),
    ("AG2", ("Agent model given as a list", "medium")),
    ("AG3", ("Subagent allowlist without the agent tool", "medium")),
    ("AG4", ("Subagent visible in the picker", "medium")),
    ("AG5", ("Handoff entry without label or agent", "medium")),
    ("AG6", ("Handoff or subagent target not found", "low")),
    ("AG7", ("Agent name duplicates an HVE Core agent", "low")),
    ("AG8", ("Read-only agent with unrestricted tools", "low")),
    ("PR1", ("Prompt delegates to an unknown agent", "low")),
    ("PR2", ("Prompt without a target agent", "info")),
    ("IN1", ("Instruction without applyTo", "medium")),
    ("IN2", ("applyTo pattern matches the repository root only", "low")),
    ("IN3", ("applyTo pattern applies globally", "low")),
    ("IN4", ("Instruction files sharing one applyTo pattern", "info")),
    ("IN5", ("applyTo pattern also used by an HVE Core instruction", "info")),
    ("SK1", ("Skill name does not match its folder", "high")),
    ("SK2", ("Skill name is not lowercase kebab-case", "medium")),
    ("SK3", ("Unrecognised folder inside a skill", "low")),
    ("SK4", ("Scripts with external surface and no SECURITY.md", "medium")),
    ("SK5", ("Scripts folder without a PowerShell script", "info")),
    ("SK6", ("Skill body navigates by workspace-root .github path", "low")),
    ("LY1", ("Artifacts at the root of a .github type folder", "info")),
    ("LY2", ("Package folder not in kebab-case", "low")),
    ("LY3", ("plugin.json membership drift", "medium")),
    ("LY4", ("Deprecated artifact without a replacement note", "low")),
    ("LY5", ("Artifact file outside the naming convention", "medium")),
    ("WS1", (".copilot-tracking not ignored by git", "medium")),
    ("WS2", ("More than one HVE Core source in one workspace", "medium")),
    ("WS3", (".hve-tracking.json out of date", "medium")),
    ("WS4", ("Chat location setting points to a missing folder", "low")),
    ("WS5", ("MCP-dependent agents without .vscode/mcp.json", "info")),
    ("WS6", ("No copilot-instructions.md", "info")),
    ("WS7", ("copilot-instructions.md over the soft length threshold", "low")),
    ("WS8", ("HVE Core source detected", "info")),
    ("CT1", ("No H1 heading", "low")),
    ("CT2", ("XML-style block tags unbalanced or duplicated", "low")),
    ("CT3", ("Fenced code block without a language", "low")),
    ("CT4", ("Relative link target missing", "medium")),
    ("CT5", ("Trailing whitespace or missing final newline", "info")),
])

WORKSPACE_RULES = ("IN4", "IN5", "LY1", "LY2", "LY3", "LY4", "LY5", "WS1", "WS2", "WS3", "WS4", "WS5", "WS6", "WS7", "WS8")


class Audit:
    def __init__(self, args):
        self.args = args
        self.findings = []
        self.warnings = []
        self.not_evaluated = OrderedDict()
        self.artifacts = []
        self.misnamed = []
        self.deprecated = []
        self.symlinks = []
        self.ctx = OrderedDict()
        self.single = bool(args.file)
        self.as_of = args.as_of or date.today().isoformat()

    # -- helpers ---------------------------------------------------------

    def add(self, rule, artifact, detail, severity=None, fix=None):
        sev = severity or RULES[rule][1]
        fid = "F%d" % (len(self.findings) + 1)
        rec = OrderedDict((("id", fid), ("rule", rule), ("title", RULES[rule][0]), ("severity", sev),
                           ("artifact", artifact.rel if isinstance(artifact, Artifact) else (artifact or "(workspace)")),
                           ("detail", detail)))
        if fix:
            rec["fix"] = fix
        self.findings.append(rec)
        if isinstance(artifact, Artifact):
            artifact.findings.append(fid)
        return fid

    def skip(self, rule, reason):
        self.not_evaluated[rule] = reason

    def known_agent_names(self):
        """Names and file stems of workspace agents; both forms resolve a handoff or agent: target."""
        names = set()
        for art in self.artifacts:
            if art.kind == "agent":
                if art.name:
                    names.add(art.name.lower())
                stem = agent_stem(art.rel)
                if stem:
                    names.add(stem)
        return names

    # -- run -------------------------------------------------------------

    def run(self):
        if self.single:
            art = load_single(self.args.file)
            self.artifacts = [art]
            for rule in WORKSPACE_RULES:
                if rule == "WS7" and art.kind == "global":
                    continue
                self.skip(rule, "single-file mode (--file); needs the whole workspace")
            self.check_artifact(art, workspace_names=None)
            if art.kind == "global":
                lines = len(art.text.splitlines())
                if lines > self.args.global_lines:
                    self.add("WS7", art, "%d lines, above the soft threshold of %d (--global-lines); the file loads for every interaction, so sprawl costs context on each turn" % (lines, self.args.global_lines),
                             fix="Keep cross-cutting rules here and move path-specific ones into applyTo-scoped instruction files.")
            return
        root = self.args.root
        if not os.path.isdir(root):
            raise SystemExit("ROOT is not a folder: %s" % root)
        self.ctx = detect_workspace(root)
        clone_dirs = [c["path"] for c in self.ctx["clones"] if c["method"] != "peer-clone"]
        self.artifacts, self.misnamed, self.deprecated, self.symlinks = discover(root, clone_dirs)
        names = self.known_agent_names()
        for art in self.artifacts:
            if art.hve_copy and not self.args.include_hve_copies:
                continue
            self.check_artifact(art, workspace_names=names)
        self.check_layout()
        self.check_workspace()

    # -- per-artifact rules ---------------------------------------------

    def check_artifact(self, art, workspace_names):
        if art.kind == "global":
            self.check_content(art)
            return
        if art.fm is None:
            self.add("FM1", art, art.fm_error or "frontmatter missing",
                     fix="Start the file with a '---' line, YAML key: value pairs, and a closing '---' line.")
            self.check_content(art)
            return
        fm = art.fm
        fields = set(k for k in fm.keys())
        desc = art.description
        if not desc:
            self.add("FM2", art, "no description in the frontmatter; Copilot and HVE Core route on it",
                     fix="Add a one-sentence description that says what the artifact does and when it applies.")
        else:
            if art.kind == "skill":
                if len(desc) > 1024:
                    self.add("FM3", art, "description is %d characters; the Agent Skills convention caps it at 1,024" % len(desc))
            elif not (10 <= len(desc) <= 200):
                self.add("FM3", art, "description is %d characters; HVE Core's contribution standard is one sentence of 10 to 200" % len(desc))
        allowed = {"agent": AGENT_FIELDS, "prompt": PROMPT_FIELDS, "instruction": INSTRUCTION_FIELDS, "skill": SKILL_FIELDS}[art.kind]
        cross = []
        if art.kind == "skill":
            cross = [f for f in AGENT_ONLY_FIELDS if f in fields]
        elif art.kind != "instruction" and "applyTo" in fields:
            cross = ["applyTo"]
        elif art.kind == "instruction":
            cross = [f for f in ("tools", "model", "agent", "handoffs", "agents", "mcp-servers") if f in fields]
        if cross:
            self.add("FM4", art, "fields that belong to another artifact type: %s" % ", ".join(cross),
                     fix="Remove them; HVE Core's frontmatter lint rejects cross-type fields and skills must stay portable.")
        unknown = sorted(f for f in fields if f not in allowed and f not in cross)
        if unknown:
            self.add("FM5", art, "fields not in HVE Core's schema reference for a %s: %s (the host may still accept them)" % (art.kind, ", ".join(unknown)))
        if art.kind == "agent":
            self.check_agent(art, workspace_names)
        elif art.kind == "prompt":
            self.check_prompt(art, workspace_names)
        elif art.kind == "instruction":
            self.check_instruction(art)
        elif art.kind == "skill":
            self.check_skill(art)
        self.check_content(art)

    def check_agent(self, art, workspace_names):
        fm = art.fm
        if "infer" in fm:
            self.add("FM6", art, "'infer' is deprecated; use user-invocable and disable-model-invocation")
        if not art.name:
            self.add("AG1", art, "no name; handoffs and agents: lists resolve agents by name, and the schema reference lists it as required",
                     fix="Add name: with the display name shown in the agent picker.")
        model = fm.get("model")
        if isinstance(model, list):
            self.add("AG2", art, "model is a list (%s); VS Code tries the entries in order, but the Copilot CLI rejects array-form model values and drops the agent, and HVE Core's frontmatter lint rejects it" % capped([str(m) for m in model]),
                     fix="Use one scalar model string, or omit model to inherit the session selection. Treat as high if anyone on the team uses the Copilot CLI.")
        agents = fm.get("agents")
        tools = fm.get("tools")
        tool_list = [str(t).strip().strip("'\"") for t in tools] if isinstance(tools, list) else ([str(tools)] if isinstance(tools, str) and tools.strip() else None)
        agents_declared = (isinstance(agents, list) and bool(agents)) or (isinstance(agents, str) and agents.strip() == "*")
        if agents_declared and tool_list is not None:
            if not any(t == "agent" or t == "*" or t.startswith("agent/") for t in tool_list):
                shown = capped([str(a) for a in agents]) if isinstance(agents, list) else "'*' (any agent)"
                self.add("AG3", art, "agents: names %s but tools: does not include the agent tool, so the subagents cannot be dispatched" % shown,
                         fix="Add 'agent' to tools, or remove the agents: list.")
        ui = fm.get("user-invocable")
        if art.is_subagent and ui is not False:
            self.add("AG4", art, "file sits under subagents/ but user-invocable is not false, so it appears in the agent picker",
                     fix="Add user-invocable: false.")
        handoffs = fm.get("handoffs")
        targets = []
        if handoffs is not None:
            if not isinstance(handoffs, list):
                self.add("AG5", art, "handoffs is not a list of entries")
            else:
                for idx, entry in enumerate(handoffs):
                    if not isinstance(entry, dict) or not entry.get("label") or not entry.get("agent"):
                        self.add("AG5", art, "handoff entry %d lacks label or agent" % (idx + 1),
                                 fix="Each handoff needs label and agent; prompt and send are optional.")
                    if isinstance(entry, dict) and isinstance(entry.get("agent"), str) and entry["agent"].strip():
                        targets.append(entry["agent"].strip())
        if isinstance(agents, list):
            targets.extend(str(a).strip() for a in agents if isinstance(a, str) and a.strip() not in ("*", ""))
        unknown = []
        own = {(art.name or "").lower(), agent_stem(art.rel)}
        for t in targets:
            low = t.lower()
            if low in own:
                continue
            if workspace_names is not None and low in workspace_names:
                continue
            if low in HVE_AGENT_BY_NAME or low in HVE_AGENT_STEMS:
                continue
            unknown.append(t)
        if unknown:
            note = " (workspace agents unknown in single-file mode)" if workspace_names is None else ""
            self.add("AG6", art, "targets matching neither a name: value nor a file stem of any workspace or HVE Core agent: %s%s" % (capped(sorted(set(unknown))), note),
                     fix="Match the target agent's name: value (HVE Core's practice) or its file name without .agent.md (the contributing guide's wording), or add the missing agent.")
        if art.name and art.name.lower() in HVE_AGENT_BY_NAME and not art.hve_copy:
            self.add("AG7", art, "name '%s' is also the name of HVE Core's %s; two entries appear in the picker when the extension, plugin, or a clone is also present" % (art.name, HVE_AGENT_BY_NAME[art.name.lower()]),
                     fix="Rename the local agent, or keep only one source for it.")
        text = (art.description + " " + first_heading(art.body)).lower()
        if tool_list is None and re.search(r"\bread[- ]only\b|\breview(er)?\b|\baudit", text):
            self.add("AG8", art, "no tools: list, which grants full tool access, although the agent describes itself as read-only or review-only",
                     fix="List read-oriented tools only (read, search, web) when the agent must not edit or run commands.")
        mcp = fm.get("mcp-servers")
        hints = set()
        if mcp:
            hints.add("mcp-servers field")
        for t in tool_list or []:
            base = t.split("/")[0].lower()
            if "/" in t and base in MCP_SERVER_HINTS:
                hints.add(base)
        art.mcp_hints = sorted(hints)

    def check_prompt(self, art, workspace_names):
        fm = art.fm
        agent = fm.get("agent")
        if isinstance(agent, str) and agent.strip():
            low = agent.strip().lower()
            if low not in BUILTIN_PROMPT_AGENTS and not ((workspace_names and low in workspace_names) or low in HVE_AGENT_BY_NAME or low in HVE_AGENT_STEMS):
                note = " (workspace agents unknown in single-file mode)" if workspace_names is None else ""
                self.add("PR1", art, "agent: '%s' is not a built-in agent (ask, agent, plan) and matches no workspace agent name and no HVE Core agent%s" % (agent.strip(), note))
        elif "mode" in fm:
            self.add("PR2", art, "declares mode: %s but no agent:; VS Code now routes prompts with agent: (ask, agent, plan, or a custom agent name) and the older mode field is no longer documented" % short_value(fm.get("mode")))
        else:
            self.add("PR2", art, "no agent:; the prompt runs in whichever agent is current (VS Code) and HVE Core's prompt checklist expects an explicit target")

    def check_instruction(self, art):
        fm = art.fm
        patterns = split_patterns(fm.get("applyTo"))
        art.patterns = patterns
        if not patterns:
            if art.description:
                self.add("IN1", art, "no applyTo, so the file never attaches by file pattern; VS Code can still load it on demand from its description, and an agent or skill can load it by #file: reference, as HVE Core does for its commit-message and git-merge files", severity="low",
                         fix="Add applyTo with one or more globs such as '**/*.py' if the rules belong to specific files.")
            else:
                self.add("IN1", art, "neither applyTo nor description, so nothing loads the file unless a user attaches it or an artifact references it with #file:",
                         fix="Add applyTo with one or more globs such as '**/*.py', and a description.")
            return
        root_only = [p for p in patterns if "/" not in p and "**" not in p]
        if root_only:
            self.add("IN2", art, "pattern(s) without a '**/' prefix match files in the repository root only: %s" % capped(root_only),
                     fix="Prefix with '**/' for recursive matching, unless a root-only match such as package.json is intended.")
        glob_all = [p for p in patterns if p in ("**", "**/*", "*", "**/**")]
        if glob_all:
            self.add("IN3", art, "pattern %s attaches the file to every edit; repository-wide rules belong in copilot-instructions.md" % capped(glob_all),
                     fix="Narrow the pattern or move the rules to .github/copilot-instructions.md.")

    def check_skill(self, art):
        fm = art.fm
        folder = os.path.basename(art.skill_dir) if art.skill_dir else ""
        name = art.name
        raw_name = fm.get("name")
        if not name:
            what = "missing" if raw_name is None else ("blank" if isinstance(raw_name, str) else "not a string (%s)" % type(raw_name).__name__)
            self.add("SK1", art, "name is %s; it is required and must equal the folder '%s', which is how Copilot and HVE Core's skill validation find the skill" % (what, folder or "<skill folder>"),
                     fix="Add name: %s." % (folder or "<folder-name>"))
            return
        if folder and name != folder:
            self.add("SK1", art, "name '%s' differs from the folder '%s'; Copilot and HVE Core's skill validation key the skill by that match" % (name, folder),
                     fix="Set name: to the folder name, or rename the folder.")
        if name and (not KEBAB.match(name) or len(name) > 64):
            self.add("SK2", art, "name '%s' is not lowercase kebab-case of at most 64 characters; VS Code fails such skills silently" % name,
                     fix="Use lowercase letters, digits, and single hyphens, 64 characters or fewer.")
        if art.skill_dir and os.path.isdir(art.skill_dir):
            extra = sorted(d for d in os.listdir(art.skill_dir)
                           if os.path.isdir(os.path.join(art.skill_dir, d)) and d not in ALLOWED_SKILL_DIRS and d not in SKIP_DIRS and not d.startswith("."))
            if extra:
                self.add("SK3", art, "folder(s) outside the recognized set (%s): %s" % (", ".join(ALLOWED_SKILL_DIRS), capped(extra)),
                         fix="Move content into scripts/, references/, assets/, templates/, examples/, or tests/.")
            scripts_dir = os.path.join(art.skill_dir, "scripts")
            if os.path.islink(scripts_dir):
                self.symlinks.append(posix(os.path.relpath(scripts_dir, self.ctx.get("root", os.getcwd()))))
            elif os.path.isdir(scripts_dir):
                exts = Counter()
                surfaces = OrderedDict()
                for dp, dns, fns in os.walk(scripts_dir):
                    dns[:] = [d for d in dns if d not in SKIP_DIRS and not os.path.islink(os.path.join(dp, d))]
                    for fn in fns:
                        if os.path.islink(os.path.join(dp, fn)):
                            continue
                        ext = os.path.splitext(fn)[1].lower()
                        exts[ext] += 1
                        if ext in (".py", ".sh", ".ps1", ".psm1", ".js", ".mjs", ".cjs", ".ts"):
                            body = read_text(os.path.join(dp, fn)) or ""
                            # Skip comment lines and lines that define search patterns, so a scanner
                            # for these words does not report itself.
                            code = "\n".join(l for l in body.splitlines()
                                             if not re.match(r"^\s*(#|//|<#|\*)", l) and "re.compile(" not in l and "regex" not in l.lower())
                            for label, pat in EGRESS_PATTERNS:
                                if pat.search(code):
                                    surfaces.setdefault(label, []).append(fn)
                has_security = os.path.isfile(os.path.join(art.skill_dir, "SECURITY.md"))
                if surfaces and not has_security:
                    desc = "; ".join("%s in %s" % (label, capped(sorted(set(files)), 3)) for label, files in surfaces.items())
                    self.add("SK4", art, "scripts show %s, and the skill has no SECURITY.md" % desc,
                             fix="Add a SECURITY.md describing trust boundaries and STRIDE categories, or remove the external surface. This is a keyword heuristic; confirm by reading the scripts.")
                if exts and exts.get(".ps1", 0) == 0:
                    self.add("SK5", art, "scripts/ has no .ps1 file; HVE Core's own contribution rule requires one (Python skills packaging modules are exempt). Irrelevant for a repository-local skill.")
        body_refs = github_root_refs(art.body)
        if body_refs:
            self.add("SK6", art, "body refers to workspace-root .github/ paths for loading or execution: %s" % capped(body_refs),
                     fix="Use paths relative to the skill root, and refer to other artifacts by name.")

    def check_content(self, art):
        body = art.body if art.kind != "global" else art.text
        if art.kind != "global" and not re.search(r"^# \S", body, re.M):
            self.add("CT1", art, "no H1 heading in the body")
        opens, closes = OrderedDict(), Counter()
        dup = set()
        for m in re.finditer(r"^\s*<!--\s*<(/?)([a-z0-9-]+)>\s*-->\s*$", body, re.M):
            closing, tag = m.group(1) == "/", m.group(2)
            if closing:
                closes[tag] += 1
            else:
                if tag in opens:
                    dup.add(tag)
                opens[tag] = opens.get(tag, 0) + 1
        problems = []
        for tag, count in opens.items():
            if closes[tag] != count:
                problems.append("<%s> opened %d, closed %d" % (tag, count, closes[tag]))
        for tag in closes:
            if tag not in opens:
                problems.append("</%s> without an opening tag" % tag)
        if dup:
            problems.append("duplicate tag name(s): %s" % capped(sorted(dup)))
        if problems:
            self.add("CT2", art, "; ".join(problems),
                     fix="Each XML-style block needs matching opening and closing tags on their own lines, and tag names must be unique in the file.")
        bare = 0
        in_fence = None
        for line in body.splitlines():
            m = re.match(r"^\s*(`{3,}|~{3,})\s*(\S*)", line)
            if not m:
                continue
            fence = m.group(1)
            if in_fence is None:
                in_fence = fence
                if not m.group(2):
                    bare += 1
            elif line.strip().startswith(in_fence[0] * len(in_fence)):
                in_fence = None
        if bare:
            self.add("CT3", art, "%s without a language identifier" % plural(bare, "fenced code block"))
        missing = []
        base_dir = os.path.dirname(art.abs_path)
        prose = strip_fences(body)
        for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", prose):
            target = m.group(1)
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#") or target.startswith("<"):
                continue
            if PLACEHOLDER_LINK.search(target):
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            if clean.startswith("/"):
                continue
            if not os.path.exists(os.path.join(base_dir, clean)):
                missing.append(target)
        if missing:
            self.add("CT4", art, "relative link target(s) not found next to the file: %s" % capped(sorted(set(missing))),
                     fix="Fix the path or add the file; HVE Core's link lint fails on missing local targets.")
        text = art.text
        trailing = sum(1 for l in text.splitlines() if l.rstrip() != l and not l.endswith("  "))
        no_final = bool(text) and not text.endswith("\n")
        if trailing or no_final:
            parts = []
            if trailing:
                parts.append("%s with trailing whitespace" % plural(trailing, "line"))
            if no_final:
                parts.append("no final newline")
            self.add("CT5", art, "; ".join(parts))

    # -- workspace rules ------------------------------------------------

    def check_layout(self):
        root = self.ctx["root"]
        checked = [a for a in self.artifacts if a.kind in ("agent", "prompt", "instruction", "skill") and (self.args.include_hve_copies or not a.hve_copy)]
        # IN4 / IN5
        by_pattern = defaultdict(list)
        for art in checked:
            if art.kind == "instruction":
                for pat in getattr(art, "patterns", []):
                    by_pattern[pat].append(art)
        for pat, arts in by_pattern.items():
            if len(arts) > 1:
                self.add("IN4", None, "pattern '%s' is declared by %s; all attach together, and identical patterns give conflicts no winner" % (pat, capped([a.rel for a in arts])),
                         fix="Keep overlapping files consistent, or merge them.")
            local_arts = [a for a in arts if not a.hve_copy]
            if pat in HVE_PATTERNS and local_arts:
                hve_present = bool(self.ctx["sources"]) or any(a.hve_copy for a in self.artifacts)
                self.add("IN5", None, "pattern '%s' in %s is also used by HVE Core's %s%s" % (pat, capped([a.rel for a in local_arts]), capped(HVE_PATTERNS[pat]), "; both attach when HVE Core is installed and the more specific pattern wins conflicts" if hve_present else " (no HVE Core source detected in this workspace, so only the local file attaches today)"),
                         fix="Keep organization rules that add to HVE Core's; do not restate them.")
        # LY1 aggregated per .github folder and kind
        root_level = Counter()
        for art in checked:
            if not art.package and art.location == ".github":
                root_level[(art.gh_prefix, art.kind)] += 1
        for (prefix, kind), count in sorted(root_level.items()):
            self.add("LY1", None, "%s directly under %s.github/%ss/ with no package folder; HVE Core treats these as repository-specific and excludes them from plugin packaging" % (plural(count, kind), prefix, kind),
                     fix="Fine for repository-only artifacts. Move distributable ones under .github/<type>/<package-id>/.")
        # LY2
        bad_pkgs = sorted(set(a.package for a in checked if a.package and not KEBAB.match(a.package)))
        for pkg in bad_pkgs:
            self.add("LY2", None, "package folder '%s' is not lowercase kebab-case" % pkg, fix="Rename the folder; package ids organise membership and must be unique, lowercase, and kebab-cased.")
        # LY3
        plugin = self.ctx.get("plugin_json")
        if plugin is None:
            self.skip("LY3", "no plugin.json at the root (only HVE Core forks and plugin repositories carry one)")
        elif plugin["error"]:
            self.add("LY3", "plugin.json", "plugin.json could not be parsed: %s" % plugin["error"])
        else:
            listed = []
            for key, items in plugin["members"].items():
                listed.extend(items)
            missing = [p for p in listed if not os.path.exists(os.path.join(root, re.sub(r"^(\./)+", "", p).lstrip("/")))]
            if missing:
                self.add("LY3", "plugin.json", "%s listed but missing on disk: %s" % (plural(len(missing), "member"), capped(missing)),
                         fix="Run npm run plugin:sync in the HVE Core fork, then npm run plugin:validate.")
            listed_set = set(re.sub(r"^(\./)+", "", p).lstrip("/").rstrip("/") for p in listed)
            unlisted = []
            for art in self.artifacts:
                if art.kind in ("agent", "prompt", "instruction", "skill") and art.package:
                    lic = str(art.fm.get("license", "")) if isinstance(art.fm, dict) else ""
                    if art.kind == "skill" and re.search(r"\bNC\b|noncommercial|non-commercial", lic, re.I):
                        continue  # HVE Core excludes noncommercial-licensed skills from membership on purpose
                    rel = art.rel
                    skill_dir = os.path.dirname(rel) if art.kind == "skill" else None
                    if rel not in listed_set and (skill_dir is None or skill_dir not in listed_set):
                        unlisted.append(rel)
            if unlisted:
                self.add("LY3", "plugin.json", "%s under package folders not listed in plugin.json: %s" % (plural(len(unlisted), "package-scoped artifact"), capped(unlisted)), severity="low",
                         fix="Run npm run plugin:sync, or move repository-only artifacts to the root of their type folder.")
        # LY4
        for path in self.deprecated:
            text = read_text(path) or ""
            head = "\n".join(text.splitlines()[:40]).lower()
            if not re.search(r"deprecat|replace|supersed|moved to|use .* instead", head):
                self.add("LY4", posix(os.path.relpath(path, root)), "no note naming the replacement in the frontmatter or the first lines",
                         fix="Add a frontmatter note or heading that names what replaces it.")
        # LY5
        for rel, kind, reason in self.misnamed:
            self.add("LY5", rel, reason, severity="low" if kind == "agent" else None,
                     fix="Rename to <name>.agent.md, <name>.prompt.md, <name>.instructions.md, or <folder>/SKILL.md.")

    def check_workspace(self):
        ctx = self.ctx
        root = ctx["root"]
        # WS1
        if ctx["tracking_present"] and not ctx["tracking_ignored"]:
            self.add("WS1", ".gitignore", ".copilot-tracking/ exists and no .gitignore rule covers it; research, plans, and change logs would be committed",
                     fix="Add the line .copilot-tracking/ to .gitignore (HVE Core's post-install step for every method).")
        elif not ctx["tracking_present"] and not ctx["tracking_ignored"]:
            self.add("WS1", ".gitignore", "no .gitignore rule for .copilot-tracking/ yet; the folder does not exist, so nothing is committed today", severity="info",
                     fix="Add .copilot-tracking/ to .gitignore before the first RPI run.")
        # WS2 and WS8
        sources = ctx["sources"]
        copies = [a for a in self.artifacts if a.hve_copy]
        kinds = set(s[0] for s in sources)
        if copies:
            sources = sources + [("copied-artifacts", "%s matching HVE Core paths under .github/ (%s)" % (plural(len(copies), "artifact"), capped([a.github_rel for a in copies], 3)), "")]
            kinds.add("copied-artifacts")
        for kind, desc, _ in sources:
            self.add("WS8", None, desc)
        if not sources:
            self.add("WS8", None, "no HVE Core source detected in the workspace (extension recommendation, clone, submodule, git-ignored folder, workspace file, .hve-tracking.json, or copied artifacts). A user-level extension install or a Copilot CLI plugin is invisible to this audit.")
        managed = "extension" in kinds
        local = kinds - {"extension"}
        if "selective-clone" in local and "copied-artifacts" in local:
            local = local - {"copied-artifacts"}  # the installer's record and the files it copied are one source
        if managed and local:
            self.add("WS2", None, "the extension is recommended and the workspace also carries %s; agents and skills present in both load twice and appear as duplicates" % ", ".join(sorted(local)),
                     fix="Keep one source per workspace: the extension for managed content, or the clone or copied selection for version-controlled files.")
        elif len(local) > 1:
            self.add("WS2", None, "more than one local HVE Core source: %s" % ", ".join(sorted(local)), severity="low",
                     fix="Confirm which one Copilot discovers and remove the other.")
        # WS3
        track = ctx.get("hve_tracking")
        if track is None:
            self.skip("WS3", "no .hve-tracking.json (written only by the hve-core-installer selective clone)")
        else:
            if track["error"]:
                self.add("WS3", ".hve-tracking.json", "file could not be parsed: %s" % track["error"])
            else:
                if str(track["schemaVersion"]) != "2":
                    self.add("WS3", ".hve-tracking.json", "schema version is %s; the current installer writes schema version 2" % (track["schemaVersion"] if track["schemaVersion"] is not None else "absent"), severity="low",
                             fix="Re-run the hve-core-installer skill to upgrade the selection record.")
                if track["missing"]:
                    self.add("WS3", ".hve-tracking.json", "%s recorded as installed but missing on disk: %s" % (plural(len(track["missing"]), "path"), capped(track["missing"])),
                             fix="Re-run the installer, or remove the stale entries.")
        # WS4
        if not ctx["settings_json"]:
            self.skip("WS4", "no .vscode/settings.json in the workspace")
        elif ctx["settings_error"]:
            self.add("WS4", ".vscode/settings.json", "file could not be parsed: %s" % ctx["settings_error"], severity="low")
        else:
            missing = []
            for key, entries in ctx["settings_locations"].items():
                for path, enabled in entries.items():
                    if enabled and not os.path.exists(os.path.join(root, path)):
                        missing.append("%s: %s" % (key.replace("chat.", ""), path))
            if missing:
                self.add("WS4", ".vscode/settings.json", "enabled location(s) that do not exist: %s. These chat.*Locations settings are deprecated in current VS Code and read only by Local harness sessions" % capped(missing),
                         fix="Point the setting at the folder that holds the artifacts, or remove the entry; for monorepos prefer chat.useCustomizationsInParentRepositories.")
        # WS5
        needs = [(a.rel, getattr(a, "mcp_hints", [])) for a in self.artifacts if getattr(a, "mcp_hints", [])]
        if needs and not ctx["mcp_json"]:
            self.add("WS5", None, "%s reference MCP servers (%s) and the workspace has no .vscode/mcp.json; those tools report as unavailable until a server is configured" % (plural(len(needs), "agent"), capped(sorted(set(h for _, hs in needs for h in hs)))),
                     fix="Create .vscode/mcp.json from HVE Core's MCP configuration guide, keeping only the servers you use.")
        # WS6 / WS7
        globals_ = [a for a in self.artifacts if a.kind == "global"]
        if not globals_:
            if ctx.get("agents_md"):
                self.add("WS6", None, "no .github/copilot-instructions.md; AGENTS.md is present and VS Code reads it when chat.useAgentsMdFile is on, but HVE Core's adoption guide and its conflict policy center on copilot-instructions.md")
            else:
                self.add("WS6", None, "no .github/copilot-instructions.md and no AGENTS.md; repository-wide rules have no home and HVE Core's adoption guide starts there")
        for art in globals_:
            lines = len(art.text.splitlines())
            if lines > self.args.global_lines:
                self.add("WS7", art, "%d lines, above the soft threshold of %d (--global-lines); the file loads for every interaction, so sprawl costs context on each turn" % (lines, self.args.global_lines),
                         fix="Keep cross-cutting rules here and move path-specific ones into applyTo-scoped instruction files.")

    # -- summaries --------------------------------------------------------

    def sev_counts(self):
        c = Counter(f["severity"] for f in self.findings)
        return OrderedDict((s, c.get(s, 0)) for s in SEVERITY_ORDER)

    def artifacts_by_kind(self):
        return Counter(a.kind for a in self.artifacts)

    def summary(self):
        arts = self.artifacts
        checked = [a for a in arts if self.args.include_hve_copies or not a.hve_copy]
        agents = [a for a in checked if a.kind == "agent"]
        s = OrderedDict()
        s["Artifacts scanned"] = len(arts)
        s["Agents (of which subagents)"] = "%d (%d)" % (len([a for a in arts if a.kind == "agent"]), len([a for a in arts if a.kind == "agent" and a.is_subagent]))
        s["Prompts"] = len([a for a in arts if a.kind == "prompt"])
        s["Instructions (with applyTo)"] = "%d (%d)" % (len([a for a in arts if a.kind == "instruction"]), len([a for a in arts if a.kind == "instruction" and isinstance(a.fm, dict) and split_patterns(a.fm.get("applyTo"))]))
        s["Skills (slash-visible)"] = "%d (%d)" % (len([a for a in arts if a.kind == "skill"]), len([a for a in arts if a.kind == "skill" and isinstance(a.fm, dict) and a.fm.get("user-invocable") is not False]))
        s["Copies of HVE Core artifacts"] = len([a for a in arts if a.hve_copy])
        s["Artifacts with blocking frontmatter errors"] = len(set(f["artifact"] for f in self.findings if f["rule"] in ("FM1", "FM2")))
        s["Agents the Copilot CLI would drop"] = len(set(f["artifact"] for f in self.findings if f["rule"] == "AG2"))
        s["Instructions without applyTo"] = len(set(f["artifact"] for f in self.findings if f["rule"] == "IN1"))
        s["Skills not discoverable by name"] = len(set(f["artifact"] for f in self.findings if f["rule"] in ("SK1",))) + len([m for m in self.misnamed if m[1] == "skill"])
        s["Files Copilot will not discover"] = len(self.misnamed)
        if not self.single:
            s[".copilot-tracking ignored"] = "yes" if self.ctx["tracking_ignored"] else ("no (folder present)" if self.ctx["tracking_present"] else "no (folder absent)")
            s["HVE Core sources detected"] = ", ".join(sorted(set(src[0] for src in self.ctx["sources"])) + (["copied-artifacts"] if any(a.hve_copy for a in arts) else [])) or "none"
        return s

    def attention(self):
        rows = []
        for art in self.artifacts:
            fids = art.findings
            if not fids:
                continue
            recs = [f for f in self.findings if f["id"] in fids]
            high = sum(1 for f in recs if f["severity"] == "high")
            med = sum(1 for f in recs if f["severity"] == "medium")
            if not (high or med):
                continue
            hm = [f["id"] for f in recs if f["severity"] in ("high", "medium")]
            li = [f["id"] for f in recs if f["severity"] in ("low", "info")]
            rows.append((art, high, med, hm, li))
        rows.sort(key=lambda r: (-r[1], -r[2], r[0].rel))
        return rows

    def remediation(self):
        groups = OrderedDict()
        for f in self.findings:
            control = CONTROL_FOR.get(f["rule"], "Other")
            groups.setdefault(control, OrderedDict()).setdefault(f["rule"], []).append(f)
        ordered = OrderedDict()
        for control in CONTROL_ORDER:
            if control in groups:
                ordered[control] = groups[control]
        for control, rules in groups.items():
            if control not in ordered:
                ordered[control] = rules
        return ordered


WORKSPACE_TARGETS = ("(workspace)", ".gitignore", ".vscode/settings.json", ".hve-tracking.json", "plugin.json")
CONTROL_ORDER = ["Artifact discovery (file names and locations)", "Frontmatter of the artifact", "Install source choice", ".gitignore",
                 ".vscode settings and MCP", "plugin.json membership", "Skill folder", "Body content", "Facts to carry forward"]
CONTROL_FOR = {
    "FM1": "Frontmatter of the artifact", "FM2": "Frontmatter of the artifact", "FM3": "Frontmatter of the artifact", "FM4": "Frontmatter of the artifact",
    "FM5": "Facts to carry forward", "FM6": "Frontmatter of the artifact",
    "AG1": "Frontmatter of the artifact", "AG2": "Frontmatter of the artifact", "AG3": "Frontmatter of the artifact", "AG4": "Frontmatter of the artifact",
    "AG5": "Frontmatter of the artifact", "AG6": "Frontmatter of the artifact", "AG7": "Install source choice", "AG8": "Frontmatter of the artifact",
    "PR1": "Frontmatter of the artifact", "PR2": "Facts to carry forward",
    "IN1": "Frontmatter of the artifact", "IN2": "Frontmatter of the artifact", "IN3": "Frontmatter of the artifact", "IN4": "Facts to carry forward", "IN5": "Facts to carry forward",
    "SK1": "Artifact discovery (file names and locations)", "SK2": "Frontmatter of the artifact", "SK3": "Skill folder", "SK4": "Skill folder", "SK5": "Facts to carry forward", "SK6": "Body content",
    "LY1": "Facts to carry forward", "LY2": "Artifact discovery (file names and locations)", "LY3": "plugin.json membership", "LY4": "Body content", "LY5": "Artifact discovery (file names and locations)",
    "WS1": ".gitignore", "WS2": "Install source choice", "WS3": "Install source choice", "WS4": ".vscode settings and MCP", "WS5": ".vscode settings and MCP",
    "WS6": "Facts to carry forward", "WS7": "Body content", "WS8": "Facts to carry forward",
    "CT1": "Body content", "CT2": "Body content", "CT3": "Body content", "CT4": "Body content", "CT5": "Facts to carry forward",
}
FIX_FOR_RULE = {
    "FM1": "Add or repair the frontmatter block.", "FM2": "Write a one-sentence description.", "FM3": "Trim or extend the description.",
    "FM4": "Remove the cross-type field.", "FM6": "Replace infer with user-invocable and disable-model-invocation.",
    "AG1": "Add name:.", "AG2": "Make model a single string or omit it.", "AG3": "Add the agent tool or drop agents:.", "AG4": "Add user-invocable: false.",
    "AG5": "Give each handoff a label and an agent.", "AG6": "Match the target agent's name exactly.", "AG7": "Keep one source per agent name.",
    "AG8": "List read-oriented tools only.", "PR1": "Point agent: at an existing agent name.", "PR2": "Add agent: with ask, agent, plan, or a custom agent name.", "IN1": "Add applyTo.", "IN2": "Prefix patterns with **/.",
    "IN3": "Narrow the pattern or move rules to copilot-instructions.md.", "SK1": "Make name and folder match.", "SK2": "Use kebab-case.",
    "SK3": "Use the recognized subfolders.", "SK4": "Add SECURITY.md or remove the external surface.", "SK6": "Use skill-relative paths.",
    "LY2": "Rename the package folder.", "LY3": "Run npm run plugin:sync and plugin:validate.", "LY4": "Name the replacement.", "LY5": "Rename the file.",
    "WS1": "Add .copilot-tracking/ to .gitignore.", "WS2": "Keep one HVE Core source.", "WS3": "Re-run the installer.", "WS4": "Fix the location setting.",
    "WS5": "Create .vscode/mcp.json.", "WS7": "Split path-specific rules into instruction files.",
    "CT1": "Add an H1 title.", "CT2": "Balance the XML-style tags.", "CT3": "Add language identifiers.", "CT4": "Fix the link targets.",
}


def first_heading(body):
    m = re.search(r"^#\s+(.*)$", body or "", re.M)
    return m.group(1) if m else ""


def strip_fences(body):
    """Return the body with fenced code blocks removed (their lines replaced by blanks)."""
    out = []
    in_fence = None
    for line in (body or "").splitlines():
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if m:
            fence = m.group(1)
            if in_fence is None:
                in_fence = fence
            elif fence[0] == in_fence[0] and len(fence) >= len(in_fence):
                in_fence = None
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def github_root_refs(body):
    """Workspace-root .github paths used as concrete file references in prose; globs, placeholders, and folder mentions are skipped."""
    refs = []
    for line in strip_fences(body).splitlines():
        for m in re.finditer(r"(?:^|[\s(\[`'\"])(\.github/(?:agents|prompts|instructions|skills)/[^\s)\]`'\"]+)", line):
            ref = m.group(1)
            if "*" in ref or "{" in ref or "<" in ref or ref.endswith("/"):
                continue
            refs.append(ref)
    return sorted(set(refs))


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def table(headers, rows, max_rows, more_label="rows"):
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    shown = rows[:max_rows]
    for row in shown:
        out.append("| " + " | ".join(md_escape(c) for c in row) + " |")
    if len(rows) > max_rows:
        rest = rows[max_rows:]
        ids = [r[0] for r in rest if isinstance(r[0], str) and re.match(r"^F\d+$", r[0])]
        tail = " (%s)" % capped(ids, 5) if ids else ""
        out.append("")
        out.append("... and %s%s. Use --max-rows to show more or --json for the full list." % (plural(len(rest), "more " + more_label.rstrip("s"), "more " + more_label), tail))
    return "\n".join(out)


def render_header(audit, brief=False):
    a = audit
    rows = []
    if a.single:
        rows.append(("Target", "%s (single file, --file)" % posix(a.args.file)))
    else:
        rows.append(("Workspace", posix(a.ctx["root"])))
    kinds = a.artifacts_by_kind()
    rows.append(("Artifacts scanned", "%d (%s)" % (len(a.artifacts), ", ".join("%d %s" % (kinds[k], k) for k in ("global", "agent", "prompt", "instruction", "skill") if kinds.get(k)) or "none")))
    rows.append(("Reference date (--as-of)", a.as_of))
    rows.append(("HVE Core catalog", "%s (%s); verify against the live repository when it matters" % (HVE_CORE_CATALOG_VERSION, HVE_CORE_CATALOG_DATE)))
    if not brief:
        copies = [x for x in a.artifacts if x.hve_copy]
        if copies:
            rows.append(("HVE Core copies", "%d, %s" % (len(copies), "audited (--include-hve-copies)" if a.args.include_hve_copies else "exempt from convention rules (pass --include-hve-copies to audit them)")))
        if a.not_evaluated:
            rows.append(("Rules not evaluated", "; ".join("%s: %s" % (k, v) for k, v in a.not_evaluated.items())))
        if a.symlinks:
            rows.append(("Symbolic links skipped", "%s, not followed because they can point outside the workspace: %s" % (plural(len(a.symlinks), "link"), capped(sorted(set(a.symlinks)), 8))))
        rows.append(("Not visible to this audit", "whether the extension or CLI plugin is installed on a machine, which files git tracks, symbolic links (never followed; listed above when present), user-level (~/.copilot, ~/.claude) and organization-level customizations, what Copilot actually discovers through settings outside the repository, the behavior of the rules in use, and the results of HVE Core's own lint commands"))
    rows.append(("Tool", "hve_core_workspace_audit.py %s" % TOOL_VERSION))
    out = ["# HVE Core workspace audit", "", "| Item | Value |", "| --- | --- |"]
    for k, v in rows:
        out.append("| %s | %s |" % (k, md_escape(v)))
    return "\n".join(out)


def render_findings(audit, max_rows, brief=False):
    out = []
    counts = audit.sev_counts()
    if brief:
        rows = [(f["id"], f["artifact"], "%s %s" % (f["rule"], f["detail"])) for f in audit.findings if f["severity"] in ("high", "medium")]
        rows.sort(key=lambda r: (SEVERITY_ORDER[next(f["severity"] for f in audit.findings if f["id"] == r[0])], int(r[0][1:])))
        out.append("## High and medium findings (%d high, %d medium)" % (counts["high"], counts["medium"]))
        out.append("")
        out.append(table(("#", "Artifact", "Finding"), rows, max_rows, "findings") if rows else "None.")
        out.append("")
        out.append("## Low and info, one line per rule")
        out.append("")
        per_rule = OrderedDict()
        for f in audit.findings:
            if f["severity"] in ("low", "info"):
                per_rule.setdefault(f["rule"], []).append(f)
        if not per_rule:
            out.append("None.")
        for rule, fs in per_rule.items():
            out.append("- **%s %s** (%s, %s): %s" % (rule, RULES[rule][0], SEV_LABEL[fs[0]["severity"]], plural(len(fs), "finding"), capped([f["id"] for f in fs])))
        return "\n".join(out)
    out.append("## Findings")
    out.append("")
    for sev in SEVERITY_ORDER:
        fs = [f for f in audit.findings if f["severity"] == sev]
        out.append("### %s (%d)" % (SEV_LABEL[sev], len(fs)))
        out.append("")
        if not fs:
            out.append("None.")
            out.append("")
            continue
        rows = [(f["id"], f["rule"], f["artifact"], f["detail"] + (" Fix: " + f["fix"] if f.get("fix") else "")) for f in fs]
        out.append(table(("#", "Rule", "Artifact", "Finding"), rows, max_rows, "findings"))
        out.append("")
    return "\n".join(out)


def render_remediation(audit, brief=False):
    out = ["## Remediation plan", ""]
    groups = audit.remediation()
    if not groups:
        out.append("No findings.")
        return "\n".join(out)
    if brief:
        for control, rules in groups.items():
            for rule, fs in rules.items():
                sev = max(fs, key=lambda f: -SEVERITY_ORDER[f["severity"]])["severity"]
                out.append("- **%s %s**, %s, %s. %s Refs: %s." % (rule, RULES[rule][0], SEV_LABEL[sev], plural(len(fs), "finding"), FIX_FOR_RULE.get(rule, "See the convention catalog."), capped([f["id"] for f in fs])))
        return "\n".join(out)
    for control, rules in groups.items():
        out.append("### %s" % control)
        out.append("")
        for rule, fs in rules.items():
            sev = max(fs, key=lambda f: -SEVERITY_ORDER[f["severity"]])["severity"]
            arts = sorted(set(f["artifact"] for f in fs if f["artifact"] not in WORKSPACE_TARGETS))
            scope = plural(len(arts), "artifact") if arts else "the workspace"
            out.append("- **%s %s**, %s, %s on %s. %s Refs: %s." % (rule, RULES[rule][0], SEV_LABEL[sev], plural(len(fs), "finding"), scope, FIX_FOR_RULE.get(rule, "See the convention catalog."), capped([f["id"] for f in fs])))
        out.append("")
    return "\n".join(out)


def render_inventory(audit, max_rows):
    a = audit
    out = ["## Inventory", ""]
    if a.single:
        art = a.artifacts[0]
        out.append("Single artifact: %s (%s%s%s)." % (art.rel, art.kind, ", package %s" % art.package if art.package else "", ", copy of an HVE Core file" if art.hve_copy else ""))
        if isinstance(art.fm, dict) and art.fm:
            out.append("")
            out.append("| Field | Value |")
            out.append("| --- | --- |")
            for k, v in art.fm.items():
                out.append("| %s | %s |" % (md_escape(k), md_escape(short_value(v))))
        return "\n".join(out)
    pk = OrderedDict()
    for art in a.artifacts:
        if art.kind == "global":
            continue
        key = art.package or ("(root of type folder)" if art.location == ".github" else "(%s/skills)" % art.location)
        row = pk.setdefault(key, Counter())
        row[art.kind] += 1
        if art.is_subagent:
            row["subagent"] += 1
        if art.hve_copy:
            row["copy"] += 1
    rows = [(k, str(c["agent"]), str(c["subagent"]), str(c["prompt"]), str(c["instruction"]), str(c["skill"]), str(c["copy"])) for k, c in sorted(pk.items())]
    out.append("### Packages")
    out.append("")
    out.append(table(("Package", "Agents", "of which subagents", "Prompts", "Instructions", "Skills", "HVE Core copies"), rows, max_rows, "packages") if rows else "No package folders.")
    out.append("")
    agents = [x for x in a.artifacts if x.kind == "agent"]
    if agents:
        rows = []
        for x in sorted(agents, key=lambda z: z.rel):
            fm = x.fm if isinstance(x.fm, dict) else {}
            tools = fm.get("tools")
            tools_desc = "unrestricted" if tools is None else ("%d listed" % len(tools) if isinstance(tools, list) else "1 listed")
            hand = fm.get("handoffs")
            targets = []
            if isinstance(hand, list):
                targets = [str(h.get("agent")) for h in hand if isinstance(h, dict) and h.get("agent")]
            sub = fm.get("agents")
            sub_desc = "" if sub is None else ("none allowed" if sub == [] else ("any" if sub == "*" or sub == ["*"] else capped([str(s) for s in sub], 3) if isinstance(sub, list) else str(sub)))
            rows.append((x.name or "(no name)", x.rel, "copy" if x.hve_copy else ("subagent" if x.is_subagent else "agent"), "no" if fm.get("user-invocable") is False else "yes", short_value(fm.get("model")) or "inherits", tools_desc, capped(sorted(set(targets)), 3) or "", sub_desc))
        out.append("### Agents")
        out.append("")
        out.append(table(("Name", "File", "Role", "In picker", "Model", "Tools", "Handoffs to", "Subagents"), rows, max_rows, "agents"))
        out.append("")
    instr = [x for x in a.artifacts if x.kind == "instruction"]
    if instr:
        rows = [(x.rel, ", ".join(split_patterns(x.fm.get("applyTo"))) if isinstance(x.fm, dict) and split_patterns(x.fm.get("applyTo")) else "(none)", "copy" if x.hve_copy else "local") for x in sorted(instr, key=lambda z: z.rel)]
        out.append("### Instructions")
        out.append("")
        out.append(table(("File", "applyTo", "Source"), rows, max_rows, "instructions"))
        out.append("")
    prompts = [x for x in a.artifacts if x.kind == "prompt"]
    if prompts:
        rows = [(x.rel, short_value(x.fm.get("agent")) if isinstance(x.fm, dict) else "", short_value(x.fm.get("mode")) if isinstance(x.fm, dict) else "") for x in sorted(prompts, key=lambda z: z.rel)]
        out.append("### Prompts")
        out.append("")
        out.append(table(("File", "Target agent", "Legacy mode"), rows, max_rows, "prompts"))
        out.append("")
    skills = [x for x in a.artifacts if x.kind == "skill"]
    if skills:
        rows = []
        for x in sorted(skills, key=lambda z: z.rel):
            fm = x.fm if isinstance(x.fm, dict) else {}
            subdirs = sorted(d for d in os.listdir(x.skill_dir) if os.path.isdir(os.path.join(x.skill_dir, d)) and not d.startswith(".")) if x.skill_dir and os.path.isdir(x.skill_dir) else []
            rows.append((x.name or "(no name)", x.package or ("(root)" if x.location == ".github" else x.location), "copy" if x.hve_copy else "local", "no" if fm.get("user-invocable") is False else "yes", short_value(fm.get("argument-hint")), short_value(fm.get("license")) or "", ", ".join(subdirs), "yes" if x.skill_dir and os.path.isfile(os.path.join(x.skill_dir, "SECURITY.md")) else "no"))
        out.append("### Skills")
        out.append("")
        out.append(table(("Name", "Package", "Source", "Slash-visible", "Argument hint", "License", "Folders", "SECURITY.md"), rows, max_rows, "skills"))
        out.append("")
    if a.deprecated:
        out.append("### Deprecated artifacts")
        out.append("")
        for p in a.deprecated[:max_rows]:
            out.append("- %s" % posix(os.path.relpath(p, a.ctx["root"])))
        if len(a.deprecated) > max_rows:
            out.append("- ... and %d more" % (len(a.deprecated) - max_rows))
        out.append("")
    out.append("### HVE Core sources")
    out.append("")
    srcs = a.ctx["sources"]
    copies = [x for x in a.artifacts if x.hve_copy]
    if not srcs and not copies:
        out.append("None detected in the workspace. A user-level extension install or a Copilot CLI plugin cannot be seen here.")
    for kind, desc, _ in srcs:
        out.append("- %s: %s" % (kind, desc))
    if copies:
        out.append("- copied artifacts: %s matching HVE Core paths (%s)" % (plural(len(copies), "artifact"), capped([c.github_rel for c in copies], 5)))
    out.append("")
    out.append("### Workspace files")
    out.append("")
    ctx = a.ctx
    out.append("| Item | Value |")
    out.append("| --- | --- |")
    globals_ = [x for x in a.artifacts if x.kind == "global"]
    out.append("| copilot-instructions.md | %s |" % ("; ".join("%s (%d lines)" % (x.rel, len(x.text.splitlines())) for x in globals_) if globals_ else "absent"))
    out.append("| AGENTS.md / CLAUDE.md at the root | %s / %s |" % ("present" if ctx.get("agents_md") else "absent", "present" if ctx.get("claude_md") else "absent"))
    out.append("| .gitignore covers .copilot-tracking/ | %s |" % ("yes" if ctx["tracking_ignored"] else "no"))
    out.append("| .copilot-tracking/ | %s |" % ("present" if ctx["tracking_present"] else "absent"))
    out.append("| .vscode/settings.json chat locations | %s |" % (", ".join("%s (%d)" % (k.replace("chat.", ""), len(v)) for k, v in ctx["settings_locations"].items()) if ctx["settings_locations"] else ("none" if ctx["settings_json"] else "no settings.json")))
    out.append("| .vscode/mcp.json | %s |" % ("present" if ctx["mcp_json"] else "absent"))
    out.append("| .vscode/extensions.json recommends the HVE Core extension | %s |" % ("yes" if ctx["extension_recommended"] else ("no" if ctx["extensions_json"] else "no extensions.json")))
    out.append("| .hve-tracking.json | %s |" % ("present, schema version %s, %d paths recorded" % (ctx["hve_tracking"].get("schemaLabel", "unknown"), len(ctx["hve_tracking"]["paths"])) if ctx["hve_tracking"] else "absent"))
    out.append("| plugin.json | %s |" % ("present, version %s, %d members" % (ctx["plugin_json"]["version"], sum(len(v) for v in ctx["plugin_json"]["members"].values())) if ctx["plugin_json"] else "absent"))
    out.append("")
    if ctx["tracking_activity"]:
        out.append("### RPI tracking activity")
        out.append("")
        out.append("Files under .copilot-tracking/ by area, with the latest dated folder. These are working artifacts, not deliverables.")
        out.append("")
        out.append("| Area | Markdown files | Latest dated folder |")
        out.append("| --- | --- | --- |")
        for area, info in ctx["tracking_activity"].items():
            out.append("| %s | %d | %s |" % (area, info["files"], info["latest"] or "none"))
        out.append("")
    return "\n".join(out)


def short_value(value, cap=60):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        text = ", ".join(short_value(v, cap) for v in value)
    elif isinstance(value, dict):
        text = ", ".join("%s: %s" % (k, short_value(v, cap)) for k, v in value.items())
    else:
        text = str(value).replace("\n", " ")
    return text if len(text) <= cap else text[:cap - 1] + "..."


def render_method(audit, brief=False):
    text = ("Method and limits. The script reads the workspace and applies the rules in references/convention-catalog.md, "
            "which approximate HVE Core %s's documented authoring, layout, and install conventions; they are not HVE Core's own "
            "lint commands (npm run lint:frontmatter, validate:skills, plugin:validate), which only run inside an HVE Core clone. "
            "Severity orders the work and is this tool's heuristic, not a Microsoft rating. Copies of HVE Core artifacts are "
            "identified by path and exempt by default. The frontmatter parser handles the YAML subset HVE Core artifacts use; "
            "a file it cannot parse is reported under FM1 rather than guessed. Symbolic links are never followed, including a linked .github, type folder, skill folder, scripts folder, or artifact file, and the header lists the ones skipped. Nothing is installed, moved, or changed." % HVE_CORE_CATALOG_VERSION)
    if brief:
        return text
    return "## Method and limits\n\n" + text


def render_markdown(audit, brief=False):
    max_rows = audit.args.max_rows
    parts = [render_header(audit, brief)]
    counts = audit.sev_counts()
    summary = audit.summary()
    if brief:
        parts.append("")
        parts.append("%s scanned; %d high, %d medium, %d low, %d info findings." % (plural(len(audit.artifacts), "artifact"), counts["high"], counts["medium"], counts["low"], counts["info"]))
    else:
        parts.append("")
        parts.append("## Posture summary")
        parts.append("")
        parts.append("| Measure | Value |")
        parts.append("| --- | --- |")
        for k, v in summary.items():
            parts.append("| %s | %s |" % (k, md_escape(v)))
    rows = audit.attention()
    parts.append("")
    parts.append("## Artifacts needing attention")
    parts.append("")
    if rows:
        parts.append(table(("Artifact", "Kind", "High", "Medium", "Findings"),
                           [(r[0].rel, r[0].kind + (" (subagent)" if r[0].is_subagent else ""), str(r[1]), str(r[2]), " ".join(r[3]) + (" · " + " ".join(r[4]) if r[4] else "")) for r in rows], max_rows, "artifacts"))
    else:
        parts.append("No artifact carries a high or medium finding.")
    ws = [f for f in audit.findings if f["artifact"] in WORKSPACE_TARGETS and f["severity"] in ("high", "medium")]
    if ws:
        parts.append("")
        parts.append("Workspace-level high and medium findings: %s." % ", ".join("%s (%s)" % (f["id"], f["rule"]) for f in ws))
    parts.append("")
    parts.append(render_findings(audit, max_rows, brief))
    parts.append("")
    parts.append(render_remediation(audit, brief))
    if not brief:
        parts.append("")
        parts.append(render_inventory(audit, max_rows))
    parts.append("")
    parts.append(render_method(audit, brief))
    parts.append("")
    return "\n".join(parts)


def to_json(audit):
    data = OrderedDict()
    data["tool"] = OrderedDict((("name", "hve_core_workspace_audit.py"), ("version", TOOL_VERSION), ("hveCoreCatalog", HVE_CORE_CATALOG_VERSION), ("catalogDate", HVE_CORE_CATALOG_DATE)))
    data["referenceDate"] = audit.as_of
    data["target"] = posix(audit.args.file) if audit.single else posix(audit.ctx["root"])
    data["summary"] = audit.summary()
    data["severityCounts"] = audit.sev_counts()
    data["rulesNotEvaluated"] = audit.not_evaluated
    data["findings"] = audit.findings
    arts = []
    for art in audit.artifacts:
        rec = OrderedDict()
        rec["path"] = art.rel
        rec["kind"] = art.kind
        rec["package"] = art.package
        rec["subagent"] = art.is_subagent
        rec["hveCoreCopy"] = art.hve_copy
        rec["name"] = art.name
        rec["frontmatter"] = art.fm if isinstance(art.fm, dict) else None
        rec["frontmatterError"] = art.fm_error
        rec["findings"] = art.findings
        arts.append(rec)
    data["artifacts"] = arts
    data["misnamed"] = [OrderedDict((("path", p), ("type", k), ("reason", r))) for p, k, r in audit.misnamed]
    data["symlinksSkipped"] = sorted(set(audit.symlinks))
    if not audit.single:
        ctx = OrderedDict()
        for k, v in audit.ctx.items():
            ctx[k] = v
        data["workspace"] = ctx
        data["deprecated"] = [posix(os.path.relpath(p, audit.ctx["root"])) for p in audit.deprecated]
    return data


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit a repository's Copilot customization layout against HVE Core conventions. Read-only.")
    parser.add_argument("root", nargs="?", default=".", help="repository or workspace folder (default: current folder)")
    parser.add_argument("--file", help="audit one artifact file alone instead of a workspace")
    parser.add_argument("--md", help="write the Markdown report to this path (default: print to stdout)")
    parser.add_argument("--json", dest="json_path", help="write the JSON report to this path")
    parser.add_argument("--brief", action="store_true", help="chat-sized report")
    parser.add_argument("--include-hve-copies", action="store_true", help="apply convention rules to copied HVE Core artifacts too")
    parser.add_argument("--global-lines", type=int, default=200, help="soft line threshold for copilot-instructions.md (default 200)")
    parser.add_argument("--as-of", help="reference date to print, YYYY-MM-DD (default: today)")
    parser.add_argument("--max-rows", type=int, default=25, help="rows per table before truncation (default 25)")
    args = parser.parse_args(argv)
    if args.as_of:
        try:
            datetime.strptime(args.as_of, "%Y-%m-%d")
        except ValueError:
            parser.error("--as-of must be YYYY-MM-DD")
    if args.file and not os.path.isfile(args.file):
        parser.error("--file does not exist: %s" % args.file)
    build_catalog_indexes()
    audit = Audit(args)
    audit.run()
    report = render_markdown(audit, brief=args.brief)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write(report)
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as fh:
            json.dump(to_json(audit), fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    if not args.md:
        sys.stdout.write(report)
    elif args.json_path:
        sys.stderr.write("Wrote %s and %s\n" % (args.md, args.json_path))
    else:
        sys.stderr.write("Wrote %s\n" % args.md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
