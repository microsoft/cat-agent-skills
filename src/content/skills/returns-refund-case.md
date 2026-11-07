---
name: Returns & Refund Case
description: "Consistent, policy-cited return decisions with a complete case packet on first touch: classify the return reason, validate eligibility deterministically with the policy clause cited, surface fraud signals without adjudicating them, and draft the recommendation and case packet."
platforms: [Cowork]
type: plugin
category: retail-cpg
builtByMicrosoft: true
tags: [retailer, returns, refund, reverse-commerce, eligibility, fraud-signals]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.4
createdAt: 2026-09-05
updatedAt: 2026-11-06
bundle: bundles/returns-refund-case.zip
---
Returns Refund Case builds a return case from desk notes, customer emails and order exports. It attaches the policy clauses, codes the return reason, determines eligibility with the clause cited, lists fraud signals as facts and drafts the case packet and customer response. It never authorises a refund, releases funds or adjudicates fraud.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **return-intake** — Structures a customer return request - item, order/receipt, reason as stated, condition, serials, customer history - into the rtl.returns-refund-case.v1 contract as case.json. Use when the user says "customer wants to return", "process this return", "start a return case", "log this return", "new return at the desk", or a return case begins. Do NOT use for eligibility or refund decisions - use eligibility-check instead; not for policy text - use policy-retrieve; not for the write-up or customer response - use case-packet.
- **policy-retrieve** — Retrieves the applicable return policy clauses and the configured windows/limits for a return case and attaches them verbatim as policy_context. Use after return-intake, or on "what does the return policy say for <category>", "what's the return window for", "pull the policy clauses", "what does policy say about no receipt", "attach the policy to the case". Do NOT use to decide eligibility or red flags - use eligibility-check instead; not to start a case - use return-intake; not for the packet - use case-packet.
- **reason-classify** — Classifies the stated return reason against the reason-code taxonomy with the deterministic reason_classify engine, recording confidence and candidate codes. Use after return-intake in every case, or on "what reason code is this", "classify the return reason", "which reason code", "code this return", "why are they returning it". Do NOT use for sentiment or complaint triage; not for eligibility or red flags - use eligibility-check instead; not for policy text - use policy-retrieve.
- **eligibility-check** — Determines return eligibility against the configured policy and surfaces fraud signals deterministically with the eligibility_check engine - the explicit Govern step of this plugin. Use after reason-classify, or on "is this returnable", "do they qualify for a refund", "check eligibility", "any fraud signals", "can we accept this return". Do NOT use to retrieve policy text - use policy-retrieve instead; not to start a case - use return-intake; not to draft the packet or customer response - use case-packet.
- **case-packet** — Drafts the return case packet - determination, recommendation, evidence list, fraud signals, customer response draft, manager exception request - from the governed contract payload using the packet template. Use to close every return case: "build the case packet", "write up the return", "draft the customer response", "draft the manager exception request", "close the return case". Do NOT use to start a case - use return-intake instead; not for eligibility or red flags - use eligibility-check; not for incident or safety write-ups.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
