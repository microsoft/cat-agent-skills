---
name: Reg Submission Authoring
description: "A cited first draft of a clinical study report or 510(k) section set: plan the sections from the locked protocol, SAP and TLFs, draft each one from source facts, check every number and population against the sources and assemble the draft with its open items."
platforms: [Cowork]
type: plugin
category: healthcare
builtByMicrosoft: true
tags: [healthcare, life-sciences, regulatory, clinical-study-report, 510k, medical-writing]
author: Microsoft
authorUrl: "https://github.com/microsoft"
authorGithub: microsoft
version: 1.0.3
createdAt: 2026-10-28
updatedAt: 2026-10-28
bundle: bundles/reg-submission-authoring.zip
---
Reg Submission Authoring turns a locked protocol, statistical analysis plan and tables, listings and figures into a cited first draft of a clinical study report or 510(k) section set. It plans the sections, drafts each one from source facts, checks every number and population against the sources and assembles the draft with its open items. It never files or submits anything.

Sign up: https://www.microsoft.com/en-us/copilot/pricing/enterprise
Get started: https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork
Help: https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/use-cowork
Contact us: https://support.microsoft.com/home/contact

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **source-ingest** — Pull every number, date and population definition out of a study's protocol, SAP, TLF tables, investigator brochure and prior approved text into one cited fact map, keyed per config/field-dictionary.json, before any CSR or 510(k) section is written. Use when the user asks "here's the locked TLF set and SAP, set up the CSR", "load the protocol and tables before we start drafting", "what figures do we have from the database lock?", "pull the disposition counts out of Table 14.1.1" or "ingest the IB for the 510(k)". Do NOT use for drafting or assembling submission sections - use section-draft or submission-assemble instead. Do NOT use for reconciling a patient's medications - use the discharge-care-transition plugin instead. Guardrail: reads and cites sources only; never estimates, rounds or invents a fact.
- **section-plan** — Work out which sections a CSR or 510(k) requires, from the templates in config, check each one against the cited fact map, and name what is missing before a word is drafted. Use when the user asks "what do we still need before we can draft the CSR?", "which sections are ready to start?", "what's blocking the performance data section?", "do we have everything for the synopsis?" or "map our tables to the E3 structure". Do NOT use for writing section language - use section-draft instead. Do NOT use for cross-checking a finished draft - use consistency-check instead. Do NOT use for outlining general Word documents or business reports - use the built-in docx skill instead. Only structures with a template in config are supported. Guardrail: plans only; never marks a section ready on a missing fact and never invents a structure.
- **section-draft** — Write or revise the language for one planned CSR or 510(k) section - synopsis, efficacy, safety, discussion, device description - using only figures already in the cited fact map, each with its TLF or SAP citation. Use when the user asks "draft the Synopsis from our locked tables", "write up safety from Table 14.3.1", "give me a first pass at the discussion", "draft the device description for the 510(k)" or "tighten the wording of the Discussion section". Do NOT use for supplying a number not already in source_facts - use source-ingest instead. Do NOT use for verifying a draft's figures - use consistency-check instead. Do NOT use for appeal letters, clinical notes or discharge summaries - use the matching HLS plugin instead. Guardrail: drafts for human approval only (L1); never asserts an unsourced number or harmonises two figures.
- **consistency-check** — Catch the stale N, the wrong date or the swapped population count before a CSR or 510(k) draft goes out: runs the deterministic consistency_check engine over every figure asserted across sections, compares it with the locked TLF/SAP fact map and reports each disagreement as an open item. Use when the user asks "do the numbers in this draft match the tables?", "does the discussion still say 252 completers?", "cross-check every figure in the CSR draft", "check the synopsis against the discussion before we send it" or "is this draft ready to assemble?". Do NOT use for proofreading, tone or readability - use section-draft instead. Do NOT use for reconciling medication lists or payer criteria - use the discharge-care-transition or prior-auth-assist plugin instead. Guardrail: reports only; never edits a draft, never waives a finding and never calls a number close enough.
- **submission-assemble** — Put the checked CSR or 510(k) sections together in template order with a reviewer-facing open-items register, as a draft package for human sign-off. Use when the user asks "assemble the CSR draft", "put the module together for review", "build the review package with the open items on top", "compile the 510(k) sections in order" or "package this up for the submission lead". Do NOT use for assembling an unchecked draft - use consistency-check instead. Do NOT use for loading protocol, SAP or TLF sources - use source-ingest instead. Do NOT use for compiling general documents or slide decks - use the built-in docx or pptx skill instead. Do NOT use for filing or submitting to a regulator - use the sponsor's validated gateway, operated by a human, instead. Guardrail: draft for human approval only (L1); status is draft_clean or draft_open_items, never submitted.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.
