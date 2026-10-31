---
name: Education for Cowork
description: "Helps education teams with teaching, governance, and institution workflows."
platforms: [Cowork]
type: plugin
category: education
builtByMicrosoft: true
tags: [education, teaching, governance]
author: Copilot Cowork team
authorUrl: "https://www.microsoft.com/en-us/copilot/features/cowork"
version: 1.0.0
createdAt: 2026-10-31
bundle: bundles/education-for-cowork.zip
---
Helps education teams run the work that repeats each term.

This plugin offers the following functionality:

- Accessibility audits
- Discussion patterns
- Course retrospectives
- Substitute packs
- Governance reviews
- Accreditation evidence
- Policy rollouts
- Staff AI adoption
- Weekly and research briefs.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **accessible-learning-materials** — Maintains instructionally equivalent, accessible variants of a set of learning materials — lessons, readings, slides, and handouts — with parity checks against the original learning goals and recorded approvals. Use when the user asks to "make these materials accessible", "audit this lesson set for accessibility", "create an accessible version of this reading", "check reading level and alt text", or "keep my accessible variants in sync". Do NOT use for individual student accommodation or support-plan decisions (IEP, EHCP, or local equivalent), and do NOT use for generic document formatting (use docx).
- **ai-rollout-education** — Coordinates a phased AI rollout across schools, colleges, universities, trusts, districts, or an education ministry: staff cohorts, prerequisites, role-based learning paths mapped to professional development windows, communications, support readiness, and wave gates checked against the academic calendar, with state carried between waves. Use when the user asks to "plan our AI rollout", "set up the training cohorts", "are we ready for the next wave", "what training does this role need", or "how is the rollout tracking". Do NOT use for any learner- or student-facing enablement wave, which is always referred out; for approving the tools themselves (use governance-review-for-education); for rolling out an approved policy document (use policy-change-pack-for-education); or for a single announcement (use stakeholder-comms).
- **discussion-insights-for-education** — Maintains group-level patterns from classroom discussions, exit checks, and learner questions — themes, misconceptions, and shifts across cycles — using notes, transcripts, and summaries, never individual student judgments. Use when the user asks to "what patterns are showing in class discussions", "analyze this exit ticket set", "what misconceptions are coming up", "compare this week's discussion to last", or "did my teaching response work". Do NOT use for grading, individual student assessment, or ranking learners.
- **evidence-package-for-education** — Maintains requirements, evidence, gaps, owners, and review packages for accreditation, program review, grant reporting, and research compliance in education. Searches approved repositories and preserves requirement-to-evidence traceability. Use when the user asks to "build the evidence package", "what evidence do we have for this standard", "find the gaps in our accreditation evidence", "update the evidence ledger", or "prepare the review submission". Do NOT use for authoring the narrative report alone, or for reviewing AI tools and connectors (use governance-review-for-education).
- **governance-review-for-education** — Runs the pre-deployment review and approval pipeline for agents, plugins, skills, connectors, and AI capabilities in education IT and governance teams: technical, policy, data, accessibility, ownership, and support evidence, with risks, exceptions, remediation, and revalidation dates. Prepares and records the approval; never issues it. Use when the user asks to "review this agent for deployment", "run a governance review", "is this tool approved for our tenant", "what's the risk review status", or "when is this due for revalidation". Do NOT use to make, sign, or grant the approval decision itself, for policy rollout after approval (use policy-change-pack-for-education), or for accreditation evidence (use evidence-package-for-education).
- **instructional-continuity** — Keeps a K-12 handover pack ready so a substitute or covering colleague can run the day during a planned or unexpected absence: current plans, schedules, routines, materials, and operational guidance, checked for privacy and freshness and reported as a standing readiness state rather than only when a date is known. Use when the user asks to "prepare my sub plans", "get my handover pack ready", "what does a substitute need for tomorrow", "check my continuity pack is current", or "I'll be out next week". Do NOT use for the absence request or leave approval itself, and do NOT include student records or individual support-plan details (IEP, EHCP, or local equivalent).
- **instructional-retrospective** — Maintains a private, evidence-backed teaching retrospective across course cycles for higher-education faculty: what was planned, what changed, what the evidence suggests, and which next-cycle actions were accepted, including counterevidence. Use when the user asks to "run my course retrospective", "did my course changes work", "review last term's teaching", "what should I change next cycle", or "compare this cycle to last". Do NOT use for evaluating other instructors, for any personnel or performance process, or for grading students.
- **policy-change-pack-for-education** — Carries an approved education policy through local procedures, audience communications, owners, and deadlines, comparing policy versions to establish what changed and which audiences, procedures, and forms are affected, traced across Microsoft 365. Use when the user asks to "build a policy change pack", "roll out this policy update", "what changes with the new policy", "draft the policy communications", or "who needs to know about this policy change". Do NOT use for drafting the policy itself, for a generic announcement with no source policy (use stakeholder-comms), for reviewing AI tools and connectors (use governance-review-for-education), or for AI rollout training and cohort communications (use ai-rollout-education).
- **research-project-brief** — Maintains a living research project brief for higher-education faculty and research staff: literature, methods, collaborator input, decisions, milestones, disagreements, and open questions, with source freshness tracked across runs. Use when the user asks to "update my research project brief", "what's the state of this project", "summarize where the literature and methods stand", "what did collaborators decide", or "what's blocking the next milestone". Do NOT use for public web literature reviews with citations (use deep-research) or for grant evidence packages (use evidence-package-for-education).
- **weekly-brief-for-education** — Maintains a running weekly brief for education faculty, staff, and leaders: priorities, commitments, decisions, risks, open questions, and upcoming work, reconciled from calendar, meetings, messages, and files. Carries accepted decisions and owners across weeks. Use when the user asks to "build my weekly brief", "what happened this week", "prep my week ahead", "update my weekly brief", "what commitments am I carrying", or "what changed since last week". Do NOT use for a single meeting recap (use meeting-intel), a one-off daily catch-up (use daily-briefing), or an audience-facing status message (use stakeholder-comms).

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
