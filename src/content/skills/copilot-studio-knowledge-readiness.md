---
name: Copilot Studio Knowledge Readiness
description: "Assess whether an uploaded or exported document set is ready to power a Copilot Studio agent. Produces a corpus-based readiness score, prioritized cleanup backlog, chunking and metadata guidance, and a test-prompt suite, while calling out any evidence gaps that require live system review."
agentDescription: "Use when a Copilot Studio maker provides uploaded files, exported text, or a document set and wants to assess whether that corpus is ready for knowledge grounding. Use this before scoring chunkability, freshness signals, conflicts, or whether content belongs in knowledge versus an action or workflow. Do not use for live SharePoint or Dataverse inspection, general agent design, publishing checklists, analytics troubleshooting, or unrelated Power Platform work."
platforms: [Copilot Studio]
tags: [copilot-studio, knowledge, rag, sharepoint, dataverse, governance, readiness, assessment]
author: Jay Padimiti
version: 1.0.0
createdAt: 2026-06-22
updatedAt: 2026-06-22
bundle: bundles/copilot-studio-knowledge-readiness.zip
---
# Copilot Studio Knowledge Readiness

Assess whether an uploaded or exported knowledge corpus is ready to power a Copilot Studio agent, and produce a maker-actionable remediation plan.

## When this skill applies

Activate only when the user is assessing, preparing, cleaning, or governing knowledge sources for a Copilot Studio agent. This skill is optimized for uploaded files and exported text rather than live system inspection. If they are designing workflows, configuring channels, debugging publishing, asking general agent questions, or expecting live SharePoint/Dataverse analysis, stop and hand back.

## Bundled files and when to load them

Load on demand — do not read these up front.

| File | Load when |
|---|---|
| `scripts/references/knowledge-vs-action-decision-tree.md` | Classifying any item as knowledge, instruction, workflow, action, or skill (step 3). |
| `scripts/references/readiness-rubric.md` | Scoring the source (step 4). Required for every assessment. |
| `scripts/references/chunking-guidance.md` | Producing chunking recommendations or diagnosing retrieval-quality issues. |
| `scripts/references/metadata-schema.md` | Producing metadata recommendations or when the user asks what fields to tag. |
| `scripts/assets/readiness-report-template.md` | Producing the final assessment artifact. Fill this in rather than composing from memory. |
| `scripts/assets/cleanup-backlog-template.csv` | Producing the cleanup backlog as a tracked artifact (Excel/Planner-friendly). Use instead of an inline markdown table when the user wants to import or share it. |
| `scripts/assets/test-prompts-template.md` | Producing the test-prompt suite at the end of an assessment. |

## Workflow

Track progress against this checklist:

- [ ] 1. Frame the assessment (scenario, audience, boundary, assumptions)
- [ ] 2. Inventory sources
- [ ] 3. Classify content role (load `scripts/references/knowledge-vs-action-decision-tree.md`)
- [ ] 4. Score readiness (load `scripts/references/readiness-rubric.md`)
- [ ] 5. Detect risks (use the Gotchas list below)
- [ ] 6. Recommend remediation (load `scripts/assets/cleanup-backlog-template.csv` if exporting)
- [ ] 7. Produce the report (load `scripts/assets/readiness-report-template.md`)
- [ ] 8. Produce test prompts (load `scripts/assets/test-prompts-template.md`)

### 1. Frame

Identify agent scenario, user audience, and knowledge boundary (what is in scope vs. out of scope for the agent to answer). State assumptions when inputs are missing — do not silently invent. Explicitly note whether you are working from uploaded files only, exported metadata, or additional maker-provided system facts.

### 2. Inventory

For each source capture: type, location, and any evidence visible in the provided materials. Only record owner, last-modified or reviewed date, audience, access boundary, region, lifecycle state, or Dataverse security details when the user explicitly provides them or they appear in an export. If those facts are missing, mark them as `not assessed from supplied files` rather than guessing.

### 3. Classify content role

Decide whether each item should be modeled as:

- **Knowledge** — factual material the agent retrieves to answer questions.
- **Agent instructions** — behavior that is always true in every conversation.
- **Skill** — situational procedure that loads only for a specific task.
- **Workflow** — deterministic guided flow.
- **Action** — operation that reads live data, writes records, starts approvals, creates tickets, sends notifications, or checks status.

Load `scripts/references/knowledge-vs-action-decision-tree.md` and walk each item through it.

### 4. Score readiness

Load `scripts/references/readiness-rubric.md`. Always emit category scores and a total, but mark categories that require external evidence as `not assessed` unless the user supplied that evidence.

### 5. Detect risks

Prioritize risks you can substantiate from the supplied corpus: conflicting answers across pages, duplicate or stale policy content, long mixed-topic documents that chunk poorly, static content that actually needs live data, and tables/images/attachments that hold answer context but may not retrieve cleanly. Only call out permissions, owners, review dates, effective dates, audience labels, region labels, or lifecycle metadata when they are visible in the provided files or separately supplied by the maker.

### 6. Recommend remediation

Prioritized backlog with severity, owner role, effort, and recommended fix. Maker-actionable, not abstract. If the user wants a trackable artifact, fill `scripts/assets/cleanup-backlog-template.csv` instead of an inline table.

### 7 & 8. Produce artifacts

Fill `scripts/assets/readiness-report-template.md` for the report and `scripts/assets/test-prompts-template.md` for the validation prompts. Do not reconstruct these from memory — open the template files and substitute.

## Readiness recommendation bands

See `scripts/references/readiness-rubric.md` for the canonical bands and scoring formula.

Override: if the supplied evidence shows any high-severity **permission or sensitivity** issue, do not recommend production even if the numeric score is high. This overrides the band. If permissions were not assessable from the evidence, say so explicitly instead of implying they were reviewed.

## Gotchas

These are Copilot Studio–specific facts that an agent will get wrong without being told.

- **"Connected" is not "indexed."** A SharePoint site connected as a knowledge source can take hours to index and longer to reindex after changes. Recommend a verification step (test prompts after publish) before declaring readiness, not just after connection.
- **SharePoint file-type and size limits apply.** Files outside the supported types, files larger than the documented size limit, and content behind required check-out are silently skipped. Treat "connection succeeded" as necessary but not sufficient evidence of coverage.
- **Public-website knowledge respects robots.txt and login walls.** Authenticated or JS-gated content will not crawl. If the user lists an internal portal URL as a "public website" source, flag it as misclassified, not as a low-quality source.
- **Dataverse knowledge requires semantic indexing to be enabled on each table** and respects row-level security at runtime. Permission risks are real but different from SharePoint — answers can vary per user.
- **Conflicting answers are worse than missing answers.** Two documents that disagree will score lower than one document that is silent, because the model will pick one nondeterministically. Treat duplicates and contradictions as high severity.
- **Long mixed-topic PDFs chunk badly.** A 200-page handbook covering ten policies will retrieve worse than ten focused documents. Recommend splitting before recommending re-uploading.
- **Tables, images, and embedded attachments don't always retrieve.** If the answer lives only in a screenshot, a wide table, or an attached file inside a Word/PDF, call it out — the maker may need to transcribe critical content into prose.
- **"Static content with live values" is an action, not knowledge.** A page that says "current pricing: $X" must be modeled as an action that calls a live source, otherwise answers go stale silently. Use the decision tree before classifying.
- **Uploaded files do not prove effective permissions or platform metadata.** SharePoint ACLs, Dataverse row-level security, owner fields, region tags, and lifecycle state often live outside the document body. Unless the user provides an export that contains them, mark these as not assessed.
- **Don't claim a script touched a live system it can't reach.** The bundled scripts work on URL lists and exported files. They do not analyze a live SharePoint site, a Dataverse environment, or authenticated content. State this explicitly in the report.

When a maker correction reveals a new gotcha, add it here.

## Scripts

Bundled optional helpers under `scripts/`. The default v1 workflow is document-first and offline-safe; do not rely on outbound network access.

| Script | Run when |
|---|---|
| `scripts/analyze-exported-docs.py` | The user provides exported text-oriented files (e.g., `.txt`, `.md`, `.html`, `.csv`) and wants heading, length, and stale-date signals. Requires Python 3.9+. |
| `scripts/detect-conflicts.py` | The user provides exported text files and you suspect duplicates or contradictions. Requires Python 3.9+. Flags candidate duplicates/contradictions for human review — output is not a confirmed conflict list. |

If a script's prerequisite isn't available, state what could be done manually instead of refusing.

## Quality bar

- Be specific about evidence and assumptions; cite the source item by name or URL.
- Prefer short, actionable findings over generic best practices.
- Separate source problems from Copilot Studio design recommendations.
- Never recommend connecting sensitive or over-permissive content without an explicit permission review step.
- When uncertain, recommend a pilot gate and test prompts rather than declaring readiness.
