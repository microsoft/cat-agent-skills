---
name: Service
description: "Investigate, respond, and resolve customer needs faster."
platforms: [Cowork]
type: plugin
category: service
builtByMicrosoft: true
tags: [customer-service, case-management, knowledge]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.1
createdAt: 2026-10-31
updatedAt: 2026-11-24
bundle: bundles/service-for-cowork.zip
licenseName: MIT
licenseFile: LICENSE
---
The Service for Cowork helps service professionals get work done faster by bringing together the people, knowledge, communications, and business context needed to resolve customer needs and drive outcomes.

With Copilot Cowork, users can delegate complex service-related work using natural language and receive actionable results grounded in information from across their connected systems. Whether you're preparing for customer engagements, investigating issues, coordinating follow-ups, or uncovering insights, the Service for Cowork helps reduce manual effort, streamline workflows, and keep teams focused on delivering exceptional customer experiences.

Designed for service teams across industries, the Service for Cowork extends Copilot Cowork with service-focused intelligence that helps turn requests into results.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **answer-research** — Use when a support, policy, eligibility, informational, or troubleshooting question needs a bounded, source-backed investigation that reconciles authority, applicability, currency, contradictions, and source coverage. Triggers include "research this answer," "what does the guidance support," "reconcile these sources," and "does this customer appear eligible." Do not use merely to compose a reply after the answer is established.
- **case-preparation-brief** — Use before the next interaction or action on one case, incident, ticket, customer issue, request, or complaint — reconciling what's happened, what's still open, and what to do next, even from a single description or one substantive interaction with no full record yet.
- **case-triage** — Use when two or more tickets, incidents, issues, requests, or complaints need an explainable relative work order based on impact, deadlines, commitments, staleness, unanswered contact, documented urgency, and any available priority or response-time evidence. Also supports a bounded urgency assessment for one issue without inventing a queue rank. Do not use for a deep brief on one selected issue or to claim work automatically.
- **draft-customer-reply** — Use when a ticket, incident, issue, request, or complaint needs a reviewable customer-facing reply grounded in the known facts, applicable policy, customer need, and communication context. Triggers include "draft a reply," "respond to the customer," "write a status update," and requests to adjust tone, length, or language. Do not use to research an unresolved answer or to send automatically.
- **knowledge-harvest** — Helps customer service representatives harvest reusable knowledge from a recently closed case or verified workaround, with a brief chat summary and one saved editable review artifact in CRM when supported, otherwise in Word or Markdown. Separates symptoms, cause, workaround, fix, and tested scope, removes identifying details, checks guidance overlap, and proposes knowledge updates and recurrence-prevention actions without publishing.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
