---
name: Stakeholder & Decision Map
description: "Map a deal's buying group, engagement, and decision process, highlighting missing stakeholders and evidence."
agentDescription: "Mines customer interactions to identify stakeholders, infer their likely roles and engagement, map the decision process, and highlight who or what may be missing. Use when asked to \"map a deal's buying group\", identify influential or missing stakeholders, \"assess who has gone quiet\", or \"explain how the customer will decide\". Do not use for phased engagement plans, contact sequences, choosing or drafting outreach to the single next contact, seller or team performance reviews, or contacting, scheduling, or changing records."
platforms: [Cowork]
category: sales
builtByMicrosoft: true
tags: [sales, stakeholders, decision-making]
author: Copilot Cowork team
authorUrl: "https://www.microsoft.com/en-us/copilot/features/cowork"
createdAt: 2026-10-31
---
# Stakeholder & Decision Map

**Seller job:** Help me understand the people and decision process for this customer.

## Purpose

Help a seller understand who is involved in a customer decision, what role each person may play, and who may be missing. The skill reads the interactions a seller already has — conversations, meetings, documents — and turns them into a picture of the buying group and the path a decision has to travel.

## When to use

- Who is involved in the deal?
- Who seems influential or likely to make the decision?
- Who is supportive, neutral, or blocking progress?
- Who has gone quiet?
- Who may still need to be engaged?
- How does the customer appear to be making the decision?

## Data it can use

The skill uses the best trusted context available. CRM is not required; where it is connected it adds to the picture rather than gating it.

| Source | What it contributes |
| --- | --- |
| Outlook email | Customer conversations, stakeholder participation, concerns and follow-ups |
| Meetings and transcripts | Who attends, what they say, decisions, objections and next steps |
| Teams | Internal context, deal discussion, specialist input and follow-up |
| Documents and proposals | Customer requirements, stakeholders, approvals and decision criteria |
| Uploaded files | Org charts, notes, account plans, spreadsheets and other deal context |
| CRM, when connected | Known contacts, roles, opportunity data and activity history |

## What the skill does

### Find the people

Identify customer stakeholders mentioned or participating across the available context, reconciling name variants and addresses so one person is counted once.

### Understand their role

Look for evidence that suggests roles such as decision maker, champion, evaluator, procurement, technical stakeholder, or executive sponsor, and record the evidence behind each read. Describe evidenced objections or dependencies separately from roles.

### Assess engagement

Show who is actively engaged, occasionally involved, newly involved, or no longer participating, using recency and substance rather than message count alone.

### Map the decision process

Summarize who needs to approve, what decisions remain, what criteria matter, key dates, and any procurement or legal steps the deal has to pass through.

### Find gaps

Highlight missing or unclear roles. For example: a technical evaluator and a business sponsor are active, but no evidence shows that procurement or an economic buyer has been engaged.

### Suggest next steps

Recommend where the seller may need to learn more or engage someone, tied to the gap it closes.

## Output

Deliver both a concise chat summary and one saved primary editable artifact, following the
sections below. The artifact must include the stakeholder map, decision process, gaps and next moves.

### Chat summary

Summarize the buying group, known decision process, largest role or engagement gap, and next
move. Qualify inferred roles and link the saved map. Suggest `customer-engagement-and-deal-risk-insights`
for the first deal or account.

### Artifact content

The skill produces a simple stakeholder map per deal or account that the user includes in the prompt. The example below shows the shape of the result, with illustrative names.

| Deal or Account name | Stakeholder | Likely role | Engagement | What we know | Gap / next step |
| --- | --- | --- | --- | --- | --- |
| Contoso account | Priya Shah | Likely champion | High | Leading evaluation and attending weekly meetings | Keep engaged |
| Contoso account | David Lee | Possible executive sponsor | Low | Joined first meeting; no recent activity | Re-engage |
| | Procurement | Unknown | None found | Mentioned as required before signature | Identify owner |

Beneath the map the skill adds three bullets at not more than three lines each: the decision process, separating what is known from what is still unclear; the key gaps, covering missing stakeholders/roles, unclear roles and engagement risks; and two to four suggested next moves the seller can act on.

### Artifact selection

Choose one format for the complete stakeholder map, decision-process summary, gaps and next moves, respecting the user's requested format:

- **Word:** Default for a readable map plus the decision, gap and next-move narrative.
- **Excel:** For a working stakeholder matrix the seller filters, sorts or keeps updating across deals.
- **PowerPoint:** For a deal review or account team readout.
- **Markdown:** When requested or the preferred format is unavailable or fails.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

Verify the save before reporting success and provide the actual link or location. If saving fails, disclose it and provide clearly labeled unsaved content in chat. Keep the map tabular and supporting narrative concise.

## Guardrails

- Use only information the seller is authorized to access.
- Do not guess roles as facts. Use qualified language such as “likely champion” or “appears to be the decision maker” when the evidence is indirect.
- Describe observed objections and dependencies neutrally; do not infer motives or label someone a blocker from silence alone.
- Show the evidence used for important conclusions, so the seller can judge the read rather than take it on trust.
- If there is not enough information, say what is missing.
- Do not fail just because CRM data is unavailable.

## Example prompts

- Map the stakeholders for Contoso.
- Who seems to be driving the decision at Fabrikam?
- Who am I missing in this deal?
- How does the customer appear to be making this decision?
- Which stakeholders have gone quiet?

## When NOT to Use

- It does not build a phased engagement plan or a contact sequence; use a separate engagement-planning procedure outside this catalog.
- It does not choose the single next person to contact or draft the message; use a separate outreach procedure with its own permission checks outside this catalog.
- It does not assess or compare the performance of the seller or the account team.
- It does not contact anyone, schedule anything, or write to any record. Every suggested move is a recommendation the seller decides on.

## Fit in the portfolio

Stakeholder & Decision Map is the Navigate step in the seller flow, between catching up on a deal and watching its momentum. Because it reads the interactions a seller already has rather than a CRM contact table, it serves the CRM-light and file-first sellers the portfolio targets.
