---
name: Risk and Compliance
description: "Cited working papers for compliance, risk, and audit teams: regulatory change triage, policy gap tables, exam request trackers, enforcement read-across, vendor SOC 2 reviews, and KYC research records."
platforms: [Cowork]
type: plugin
category: financial-services
builtByMicrosoft: true
tags: [financial-services, compliance, regulatory-change, kyc, vendor-risk]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.29
createdAt: 2026-10-28
bundle: bundles/fsi-risk-and-compliance.zip
---
FSI Risk and Compliance drafts cited working papers for compliance, risk and audit teams: regulatory change triage, policy-to-rule gap tables, exam request trackers, enforcement read-across, vendor SOC 2 reviews and KYC research records. It never concludes compliance, rates risk, approves a vendor or screens sanctions. Nothing is sent or filed.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **reg-change-triage** — Triages a new or changed regulatory instrument into a decision-ready brief covering what changed, date ladder, affected parties, obligations cited to primary source, candidate policies, gaps, and actions. Applicability is proposed with reasoning, never decided. Use when the user says "what does this new rule mean for us", "triage this SR letter", "summarize the impact of this regulatory change", "when do we have to comply", or "which policies does this hit". Do NOT use for enforcement actions, settlements, or consent orders (use enforcement-action-review), one policy against one rule (use policy-gap-analysis), request trackers (use exam-request-response), a vendor SOC 2 (use vendor-risk-review), workbook formatting (use built-in xlsx), or sending email (use built-in outlook-email).
- **policy-gap-analysis** — Compares a firm policy to a regulation clause by clause, giving a coverage table with verbatim excerpts, suggested edits and a memo. Reports coverage states; never concludes compliance. Use when the user says "does our policy cover this regulation", "where are the gaps against this rule", "map our procedure to the requirements", "compare our AML policy to the rule", or "what needs to change in this policy". Do NOT use for customer or counterparty research or EDD packs (use kyc-research-pack), firm-wide triage of a new rule (use reg-change-triage), enforcement read-across (use enforcement-action-review), exam requests (use exam-request-response), vendor SOC 2 reviews (use vendor-risk-review), workbook formatting (use built-in xlsx), or sending email (use built-in outlook-email).
- **exam-request-response** — Turns a regulator or auditor request list, PDL, IRL, or first-day letter into a tracked response register with original numbering, owners, candidate evidence, status, gaps, and a draft memo. Never asserts that evidence satisfies a request and never sends anything. Use when the user says "build a tracker for this PDL", "who owns each exam item", "find evidence for this request list", "draft responses to the first-day letter", or "what are we missing for the exam". Do NOT use for vendor SOC 2 or DDQ reviews (use vendor-risk-review), enforcement read-across (use enforcement-action-review), one policy against one rule (use policy-gap-analysis), new regulatory instruments (use reg-change-triage), document formatting (use built-in docx), or sending email (use built-in outlook-email).
- **enforcement-action-review** — Reads a public enforcement action, complaint, settlement, or consent order and produces a read-across against the firm's controls covering alleged conduct, cited rules, and corrective actions. Exposure is framed as hypotheses for human review, never admissions. Use when the user says "could this happen here", "what does this consent order mean for us", "lessons learned from this enforcement action", "read this across to our controls", or "which controls does this implicate". Do NOT use for customer or counterparty research (use kyc-research-pack), new rules, bulletins, SR letters, or proposed or final regulations (use reg-change-triage), request trackers (use exam-request-response), document formatting (use built-in docx), or sending email (use built-in outlook-email).
- **vendor-risk-review** — Reviews a vendor's SOC 2 report, DDQ, contract, or public vendor research against the interagency third-party risk lifecycle, covering report type, scope, opinion, exceptions, CUECs, residual risks, public findings, and open questions. Produces no risk rating and no approval decision. Use when the user says "review this SOC 2", "assess this third party", "what are the exceptions in this report", "write up a vendor risk review", or "what should we ask this vendor". Do NOT use for customer or beneficial-owner research (use kyc-research-pack), request trackers (use exam-request-response), regulatory-change triage (use reg-change-triage), enforcement read-across (use enforcement-action-review), workbook formatting (use built-in xlsx), or sending email (use built-in outlook-email).
- **kyc-research-pack** — Assembles a cited public-source research record on a customer, counterparty, or beneficial owner for a human-owned KYC/CDD/EDD file, covering adverse media, litigation, registry data, and identity resolution. NOT a sanctions or PEP screen; route list screening to the firm's screening tool. Use when the user says "run a negative news check on this customer", "background on this beneficial owner", "what is public on this counterparty", "build an EDD pack", or "any adverse media on this entity". Do NOT use for policy-versus-rule gap analysis (use policy-gap-analysis), vendor due diligence (use vendor-risk-review), enforcement read-across (use enforcement-action-review), rule triage (use reg-change-triage), exam trackers (use exam-request-response), or document formatting (use built-in docx).

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
