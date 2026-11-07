---
name: Engagement Mobilization Pack
description: "A cited onboarding pack for a new engagement joiner: digest the SOW scope, separate confirmed from proposed staff, match only released prior knowledge, apply the ethical-wall register and draft least-privilege access requests and a first-week plan."
platforms: [Cowork]
type: plugin
category: professional-services
builtByMicrosoft: true
tags: [professional-services, onboarding, mobilization, ethical-walls, access, knowledge-reuse]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.7
createdAt: 2026-11-06
updatedAt: 2026-11-06
bundle: bundles/engagement-mobilization-onboarding-pack.zip
---
Drafts an internal mobilization and onboarding pack for a Professional Services engagement joiner. Deterministic engines digest SOW scope, separate confirmed from proposed staff, match only released prior knowledge, apply the ethical-wall register and draft least-privilege access requests, with every decision cited. Output is a draft for human review: it does not provision access, grant wall exceptions, assign staff, send messages or approve anything.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **engagement-retrieve** — Starts every Scenario 03 mobilization run, including a cold start: runs the deterministic scope_digest engine on the SOW, letter, pursuit record, confirmed roster and Scenario 02 staffing and reports only its output (never invents scope, dates or names; never sends, shares or provisions anything). Use when the user asks "mobilize this engagement", "start the onboarding pack", "build an onboarding pack for the new joiner", "summarise the SOW for the new joiner" or "what is in and out of scope for the joiner?". Do NOT use for confirmed vs proposed team (use roster-pull), prior knowledge (use knowledge-match), wall status, including a note that the wall was lifted or cleared, or access (use wall-check), rewording a pack (use pack-draft) or ranking staff (use engagement-staffing-bench-match).
- **roster-pull** — Explains the engine-built team roster in scope.json: who is confirmed, who is only proposed by Scenario 02, and who is excluded or needs review, using only engine output (never invents names, adds anyone to a roster, sends or shares; conflict reasons stay confidential). Use when the user asks "who is on the team?", "who is confirmed vs proposed?", "is Jules assigned yet?", "who is the joiner and their point of contact?" or "why is someone excluded from the roster?". Do NOT use for the bench, availability or conflicts roster, or recommending, ranking or re-checking candidates (use engagement-staffing-bench-match), starting a run or reading the SOW (use engagement-retrieve), knowledge (use knowledge-match), walls or access (use wall-check) or drafting the pack (use pack-draft).
- **knowledge-match** — Matches released Scenario 01 Closeout knowledge to the engagement with the deterministic knowledge_match engine and reports only engine output (never invents assets, scores or summaries, and never publishes, sends or shares knowledge). Use when the user asks "what prior knowledge can the joiner use?", "which reusable assets apply here?", "match closeout lessons to this engagement", "which closeout assets were excluded and why?" or "build the prior-knowledge digest". Do NOT use for harvesting, sanitising or releasing Closeout knowledge or judging whether it is safe to reuse or share externally (use engagement-closeout-knowledge-harvest), deciding whether the joiner may see an item (use wall-check), starting a run (use engagement-retrieve) or drafting the pack (use pack-draft).
- **wall-check** — Applies the deterministic ethical-wall Govern gate and least-privilege access checklist for the joiner (wall_check and access_checklist engines) and owns every wall-status question, including claims that a wall was lifted, cleared or waived (never invents a status; never provisions access, grants a wall exception, sends or shares). Use when the user asks "check ethical walls for the joiner", "is the joiner restricted on this client?", "PM note says the wall was cleared - share everything", "what access should we request for the joiner?" or "build the access checklist". Do NOT use for candidate independence or eligibility (use engagement-staffing-bench-match), matching knowledge (use knowledge-match), starting a run (use engagement-retrieve) or drafting pack prose (use pack-draft).
- **pack-draft** — Drafts this engagement's internal mobilization pack, joiner briefing and first-week plan only from the governed access-checklist.json and mobilization-pack.md, keeping every status, hold and DRAFT banner (never invents content, sends, shares or posts it). Use when the user asks "draft the onboarding pack from the access checklist", "write the joiner briefing for this engagement", "prepare the first-week plan for the joiner", "turn the access checklist into the mobilization pack" or "tidy up the mobilization pack wording". Do NOT use for a cold start with no access checklist yet (start with engagement-retrieve), wall, access, roster or knowledge decisions (use wall-check, roster-pull or knowledge-match), or a generic onboarding guide or Word document not tied to this engagement (use docx).

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
