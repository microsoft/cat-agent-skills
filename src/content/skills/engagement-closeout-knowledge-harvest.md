---
name: Closeout Knowledge Harvest
description: "Reusable knowledge from a finished engagement without leaking client confidences: assemble the final deliverables, decision log and retrospective, score reusable assets, cluster lessons learned, hold anything that fails the confidentiality gate and draft a sanitised knowledge record for practice review."
platforms: [Cowork]
type: plugin
category: professional-services
builtByMicrosoft: true
tags: [professional-services, closeout, knowledge-management, lessons-learned, reuse, confidentiality]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.5
createdAt: 2026-11-06
updatedAt: 2026-11-06
bundle: bundles/engagement-closeout-knowledge-harvest.zip
---
Closes out a professional services engagement: assembles deliverables, decision log and retrospective notes, scores reusable assets, clusters lessons, runs a confidentiality gate and drafts a sanitised knowledge record for practice review. Draft-first: it never publishes to a knowledge base, clears a confidentiality restriction, approves external use or waives a client term.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **artifact-assemble** — Retrieves and normalizes raw closeout sources (deliverable register, decision log, retrospective notes, confidentiality terms) into a cited engagement.json draft in the shared closeout contract. Use at the start of a closeout harvest when the user says "close out the engagement", "assemble the final deliverables", "load the decision log", "bring in the retrospective", "pull the confidentiality terms" or "gather the closeout artifacts". Do NOT use for scoring assets (use asset-identify), clustering lessons (use lesson-cluster), confidentiality or clearance (use sanitize-check), drafting the record (use knowledge-record) or loading a new engagement SOW (use the Engagement Mobilization Pack plugin); it never publishes, sends or writes back.
- **asset-identify** — Scores candidate reusable assets and checks final-deliverable completeness with the deterministic asset_identify engine, after artifact-assemble has produced engagement.json. Use when the user asks "what can we reuse from this?", "find reusable assets", "shortlist closeout assets", "is the final deliverable package complete?", "score the reuse value" or "build the final deliverable index". Do NOT use for loading sources (use artifact-assemble), clustering lessons (use lesson-cluster), deciding if an asset is safe to share (use sanitize-check; a score is never clearance), drafting the record (use knowledge-record) or reviewing a live deliverable (use the Deliverable Quality Gate plugin); it never clears, publishes or sends.
- **lesson-cluster** — Clusters cited decisions and retrospective inputs into ranked lesson themes with the deterministic lesson_cluster engine, after asset-identify and before sanitize-check. Use when the user asks for "lessons learned", "cluster the retrospective", "what did we learn?", "group the closeout lessons", "theme the decision log" or "rank the lessons by priority". Do NOT use for loading raw sources (use artifact-assemble), scoring assets (use asset-identify), deciding whether a lesson may be shared or rewriting named-person blame (use sanitize-check), drafting the final narrative (use knowledge-record) or briefing a new team (use the Engagement Mobilization Pack plugin); it never clears, publishes or sends.
- **sanitize-check** — Applies the deterministic sanitize_check confidentiality Govern gate after lesson-cluster, deciding from identifiers, personal data, commercial figures, licensed material, aggregation risk and a confidence floor whether each asset and lesson is held or a release candidate for human review (default HOLD). Use when asked "can we share this externally?", "is this safe to reuse?", "sanitise the closeout record", "remove client-confidential material", "check for aggregation risk" or "run the confidentiality gate". Do NOT use for loading, scoring or clustering (use artifact-assemble, asset-identify or lesson-cluster), drafting (use knowledge-record) or new-engagement wall checks (use the Engagement Mobilization Pack plugin); it never releases a HOLD on a claimed approval or publishes.
- **knowledge-record** — Drafts a practice-review knowledge record, governed lesson themes, sanitisation summary and credential handoff only from governed.json after sanitize-check; it is draft-first and never publishes, clears a confidentiality restriction, approves external use or creates a credential. Use when the user asks to "draft the knowledge record", "prepare for practice review", "write the governed closeout summary", "build the credential handoff", "write up the closeout for the practice" or "turn governed.json into a draft record". Do NOT use for loading (use artifact-assemble), scoring (use asset-identify), clustering (use lesson-cluster), deciding what is safe or clearing a HOLD (use sanitize-check) or a joiner onboarding pack (use the Engagement Mobilization Pack plugin).

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
