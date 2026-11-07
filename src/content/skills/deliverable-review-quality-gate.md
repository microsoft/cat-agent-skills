---
name: Deliverable Quality Gate
description: "A cited partner review packet before a deliverable goes to the client: map each assertion to the support pack, run the firm's quality-gate criteria and required-language checks, rank the findings by severity and list every release blocker."
platforms: [Cowork]
type: plugin
category: professional-services
builtByMicrosoft: true
tags: [professional-services, quality-review, deliverable, qrm, evidence, release-gate]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.9
createdAt: 2026-11-06
updatedAt: 2026-11-06
bundle: bundles/deliverable-review-quality-gate.zip
---
Checks a client deliverable against your firm's quality-gate criteria. It maps each assertion to supporting evidence, runs the release gates, ranks issues by severity and drafts a partner review packet that cites every finding. Outputs are drafts for a human reviewer: it never signs off, approves client issue, authorizes reliance or sends anything.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **deliverable-ingest** — Retrieves and structures a draft deliverable, recipients, evidence index, registers and prior review notes for the gate. Use to start a deliverable review or when the user asks "review this deliverable", "check this support pack", "find unsupported claims", "start a deliverable gate review" or "ingest the draft and evidence". For a release yes/no on already-ingested material, use gate-check. Do NOT use for choosing criteria (use criteria-retrieve), support mapping (use assertion-map), gate findings (use gate-check), the partner packet (use review-packet), time or expense narratives (use time-expense-narrative-compliance), closeout harvest (use engagement-closeout-knowledge-harvest), client status/QBR (use client-status-qbr) or general document editing (use built-in document tools).
- **criteria-retrieve** — Retrieves the applicable QRM quality framework, gate criteria, required language, brand rules and prior-review findings for a deliverable review. Use after intake or when the user asks "which checklist applies?", "retrieve the gate criteria", "what disclaimer is required?", "what did QRM ask us to fix?" or "load the review rules". Do NOT use for ingesting documents (use deliverable-ingest), mapping evidence (use assertion-map), determining findings (use gate-check), drafting the review packet (use review-packet), time or expense narratives (use time-expense-narrative-compliance), closeout harvest (use engagement-closeout-knowledge-harvest), client status/QBR (use client-status-qbr) or generic policy search outside this plugin (use built-in search).
- **assertion-map** — Maps each deliverable assertion to the support pack with the deterministic assertion_map engine and reports its support status. Use after intake and criteria, or when the user asks "what is not substantiated?", "check the claims", "trace this saving", "which assertions lack evidence?" or "map assertions to evidence". Do NOT use for ingesting documents (use deliverable-ingest), choosing criteria (use criteria-retrieve), gate findings or review status (use gate-check), drafting the partner packet (use review-packet), time or expense narratives (use time-expense-narrative-compliance), closeout harvest (use engagement-closeout-knowledge-harvest), client status/QBR (use client-status-qbr) or generic citation search outside this plugin (use built-in search).
- **gate-check** — Runs the explicit Govern step: deterministic gate_check and severity_rank set gate results, release blockers and review status. Use after assertion-map or when the user asks "run the quality gate", "what blocks client issue?", "can this go to the client?", "rank the review findings", "check required reliance language" or "list the release blockers". Do NOT use for ingesting documents (use deliverable-ingest), retrieving criteria (use criteria-retrieve), mapping assertion support (use assertion-map), the packet narrative (use review-packet), time or expense narratives (use time-expense-narrative-compliance), closeout harvest (use engagement-closeout-knowledge-harvest), client status/QBR (use client-status-qbr), or to approve, sign off, send or authorize reliance (never; a human decides).
- **review-packet** — Drafts the partner/QRM review packet from verified gate_check and severity_rank output, marked DRAFT - HUMAN REVIEW REQUIRED. Use after the gate check or when the user asks "draft the review packet", "summarize partner review items", "make the issue list", "what needs fixing before client issue?" or "prepare the QRM packet". Do NOT use for ingesting documents (use deliverable-ingest), retrieving criteria (use criteria-retrieve), mapping support (use assertion-map), computing findings, severity or status (use gate-check), time or expense narratives (use time-expense-narrative-compliance), closeout harvest (use engagement-closeout-knowledge-harvest), client status/QBR (use client-status-qbr), or to send, approve, sign off, publish or authorize reliance (never; a human decides).

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
