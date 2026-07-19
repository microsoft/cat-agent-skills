---
name: Copilot & Agents News Scout
description: "A Monday-morning Scout automation that scans authoritative Microsoft sources for the past week's Copilot, Copilot Studio, and agent news and posts a concise, linked digest to Teams."
platforms: [Scout]
type: automation
tags: [news, copilot, agent, digest, automation, weekly, teams]
author: Elliot Margot
authorUrl: "https://e-margot.ch"
authorGithub: OwnOptic
version: 1.0.0
createdAt: 2026-07-18
updatedAt: 2026-07-18
bundle: bundles/copilot-agents-news-scout.json
---
A Monday-morning Scout automation that scans authoritative Microsoft sources for the past week's Copilot, Copilot Studio, and agent news and posts a concise, linked digest to Teams.

> **Scout automation.** This is a Microsoft **Scout** automation (a `.json` of a schedule plus ordered prompt steps). It runs on Scout only.

## Trigger

Runs on a **schedule** — every Monday at 8:00 AM.

## Steps

### 1. Gather the week's updates

```text
Search authoritative Microsoft sources published or updated in the last 7 days for news about Microsoft 365 Copilot, Copilot Studio, Copilot agents, and Microsoft Scout. Prioritize: the Microsoft 365 and Copilot blogs (microsoft.com/blog), Microsoft Learn 'what's new' and release pages, the Message Center and Microsoft 365 roadmap, and the Power Platform / Copilot Studio release plans. For each item, capture the title, the canonical URL, the publish or update date, and a one-sentence summary in your own words. Collect everything relevant now; do not filter yet.
```

### 2. Filter to what matters

```text
From the items gathered, keep only material changes a Copilot Studio maker or M365 admin would act on: general availability, public preview, deprecations and breaking changes, pricing or Copilot Credits changes, new connectors or capabilities, and roadmap dates. Drop marketing recaps, opinion pieces, and anything older than 7 days. Deduplicate items that cover the same announcement, keeping the most authoritative source. If nothing material shipped this week, note that plainly rather than padding the list.
```

### 3. Write and post the Teams digest

```text
Write a concise digest titled 'Copilot & Agents - week of <date>'. Group items under headings: Microsoft 365 Copilot, Copilot Studio, Agents & Scout, and Governance & Admin (omit any empty group). For each item give the title as a link, the date, and a one-line 'why it matters'. Keep the whole digest scannable in under two minutes. Post it to Teams. Do not invent items, dates, or links; include only what the previous step verified. Do not use the em dash character.
```

## Import into Scout

1. Download the automation (the `.json` on this page).
2. In **Scout › Automations**, choose **Import** and select the file (or paste its contents). Review the schedule and steps, then enable it.

You can also point Scout's **Import from GitHub** at a repository directory of automation `.json` files (a `skills/` subfolder is installed automatically). This automation's file is `submissions/copilot-agents-news-scout/` in this repo.

> Review the steps before enabling — automations act on your behalf on a schedule.
