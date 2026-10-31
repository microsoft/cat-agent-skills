---
name: Customer Engagement and Deal Risk Insights
description: "Explain customer engagement and deal momentum with evidence-backed risks, blockers, and next actions."
agentDescription: "Explains customer engagement and deal momentum, identifying evidence-backed risks, blockers, their owners, and meaningful seller actions. Use this skill when a seller asks \"which deals need attention\", \"what changed with a customer\", \"what is blocking progress\", whether a deal has lost momentum, who owns the blocker, or what they can do next. Support both portfolio questions and questions about one deal. Do not use to predict win or close probability, infer deal risk from low activity alone, claim authoritative pipeline risk without live CRM, or take unapproved external action."
platforms: [Cowork]
category: sales
builtByMicrosoft: true
tags: [sales, customer-engagement, deal-risk]
author: Copilot Cowork team
authorUrl: "https://www.microsoft.com/en-us/copilot/features/cowork"
createdAt: 2026-10-31
---
# Customer Engagement and Deal Risk Insights

## Objective

Help a seller identify active deals that need attention, understand when and why momentum changed, and choose a meaningful next action. Combine authorized Microsoft 365 work signals with CRM context when available. If CRM is unavailable, provide customer engagement insights without claiming authoritative pipeline risk.

## When to use this skill

Use this skill when a seller asks which deals need attention, whether a deal has lost momentum, what changed with a customer, what is blocking progress, who owns the blocker, or what they can do next. Support both portfolio questions and questions about one deal.

Example requests: “Which active deals should I focus on this quarter?” “What changed with Contoso?” “Where did momentum change?” “Which risks can I actually act on?” “Which quiet deals are still on track?”

## Inputs and access

- Use only information the seller is authorized to access. Relevant work signals may include Outlook email, Teams chats and channel messages, calendar activity, meetings and transcripts, documents, and shared files.
- When available, use live CRM accounts, opportunities, stages, forecast categories, value, close dates, owners, next steps, stakeholders, activities, notes, milestones, products, and competitors.
- A seller-uploaded CRM view is a point-in-time snapshot. Retain its date, distinguish its fields from later observations, and never describe it as live.
- Associate a work signal with a specific opportunity only when the mapping is supported. Do not merge activities from different opportunities at the same account.

## Workflow

### 1 Find and prioritize relevant deals

Start with the seller’s active deals when CRM is available. Rank by quarter timing (use the organization’s fiscal quarter when available; otherwise clarify which quarter the seller means if it affects the answer), time left to act, value or exposure, meaningful momentum change, missed commitments, blockers, stakeholder changes, and available seller action. Do not rank on value alone. If CRM is missing, identify customers and engagements from authorized work signals where possible; do not imply the set is a complete pipeline.

### 2 Reconstruct what happened

Select the few dated events that explain progress or delay: customer commitments, milestone completion, postponed decision meetings, unanswered critical questions, stakeholder participation, seller deliverables, technical or commercial review, and approvals. Avoid an activity dump. Track what was agreed, who owns it, its due date, and whether it happened.

### 3 Identify the momentum change

Assess momentum against the deal’s expected next steps and its recent pattern of progress. Identify what was expected, what actually happened, and the specific date or event where that changed. Give the most weight to agreed commitments, milestones, and material stakeholder changes; use activity trends only as supporting evidence.

Classify momentum as Improving, Stable, Softening, or Stalled only when evidence supports a classification. Improving requires progress such as a completed milestone or resolved blocker. Stable means progress is consistent with expectations. Softening requires credible slowing, such as a delayed milestone or overdue critical response. Stalled requires strong evidence that expected progress stopped, such as repeated missed commitments or a critical step with no path forward.

Lower activity alone is not deal risk. Fewer emails or meetings matter only when linked to missed commitments, postponed milestones, unresolved blockers, stakeholder disengagement, timing impact, or failure to complete an agreed step. If no reliable inflection point exists, say “No clear momentum change identified.” If the evidence cannot support any momentum classification, show “Insufficient evidence” in the Momentum column; do not force one of the four labels or treat it as Stable. A quiet deal can be healthy.

### 4 Explain the blocker and ownership

Identify what prevents progress and tie it to evidence. Possible blockers include procurement, legal, budget, security, technical validation, executive approval, customer alignment, missing stakeholder, pricing, contracting, competing priority, seller deliverable, or unclear next step. Classify ownership separately as Our side, Customer, Shared, or Unclear. If evidence does not identify a blocker, say “Blocker unclear.”

### 5 Decide whether the seller can act

Classify actionability as Yes, Partly, or No. Use Yes when the seller can take a meaningful action now; Partly when another party owns the dependency but the seller can influence it; No when the seller can only monitor an agreed dependency. For Yes or Partly, name a specific action, person or role, and purpose. For No, name the next agreed event or date to monitor. Do not recommend generic follow-up when a precise request is possible.

### 6 Check evidence and confidence

Separate observations from interpretations. Show dated evidence behind each material finding. Flag limited, stale, conflicting, or incomplete evidence. Show positive and negative signals together. Do not force a single conclusion when they conflict. Where evidence is sparse, say “Insufficient evidence to establish a reliable momentum trend.”

## Output

Deliver both a concise chat summary and one saved primary editable artifact, following the
sections below. The artifact must explain momentum, blockers, ownership and what the seller can do.

### Chat summary

Summarize the leading deal or customer, momentum, blocker, next action and evidence gaps;
link the saved brief.

### Artifact content

For a portfolio question, lead with a short table of the deals most relevant to the seller. Show what happened, when momentum changed, what is blocking progress, who owns the blocker, and whether the seller can act. Keep the table easy to scan.

| Deal | What happened | Momentum changed | Blocker | Owner | Can I act? |
| --- | --- | --- | --- | --- | --- |
| Contoso | Decision meeting postponed twice | 🔴 Apr 15 — Stalled | Procurement | Customer | 🟡 Partly |
| Fabrikam | Executive sponsor re-engaged | 🟢 May 2 — Improving | None | — | 🟢 Yes |
| Northwind | Budget approval slipped | 🟠 Apr 22 — Softening | Budget | Shared | 🟢 Yes |

Momentum: 🟢 Improving · 🟡 Stable · 🟠 Softening · 🔴 Stalled

Can I act? 🟢 Yes · 🟡 Partly · ⚪ No

Use colored circles only for momentum and actionability. Keep blocker and owner visually neutral. Include text labels so the table is understandable without color. If momentum cannot be assessed, show Insufficient evidence without a colored circle or a forced momentum label, and briefly explain what is missing.

For a question about one deal, respond in short bullets:

- **What happened:** Summarize the few dated events that matter.
- **Momentum:** State the current assessment, identify when the pattern changed, and cite the evidence. If no change point is supported, say so.
- **Blocker and owner:** Explain what is preventing progress and whether Our side, the Customer, or both own the dependency. Use Unclear when the evidence does not establish a blocker or owner.
- **Can I act?** Answer Yes, Partly, or No. For Yes or Partly, give a concrete action. For No, name the agreed dependency or checkpoint to monitor.
- **Evidence confidence:** State whether the evidence is strong, limited, stale, conflicting, or incomplete, and why.

When a timeline helps explain the assessment, include a short one and mark the momentum change. For example:

#### Contoso activity timeline

| Date | What happened |
| --- | --- |
| Apr 3 | Customer meeting held. |
| Apr 5 | Seller sent the agreed follow-up. |
| Apr 8 | Customer replied. |
| Apr 15 | 🔴 Momentum changed: Customer postponed the decision meeting. |
| Apr 22 | Seller’s follow-up remained unanswered. |
| Apr 29 | Customer postponed the decision meeting again. |
| May 5 | Customer procurement had not started vendor onboarding. |

Assessment: Stalled. The April 15 postponement marks the change; the second postponement supports the current assessment. Blocker: Procurement, owned by the customer. Can I act? 🟡 Partly — ask the customer sponsor to confirm when vendor onboarding will begin and whether the decision meeting can be rescheduled. These are illustrative events; the skill must use the seller’s authorized evidence in a real response.

At the end, suggest `stakeholder-and-decision-map` for the deal at highest risk.

### Artifact selection

Choose one format for the complete deal-risk and momentum brief, respecting the user's requested format:

- **Word:** Default for a narrative brief covering what happened, momentum, blockers, ownership, and next actions.
- **PowerPoint:** For a pipeline review, manager update, or deal review discussion.
- **Excel:** For a working portfolio matrix that the seller sorts, filters, or tracks across deals.
- **Markdown:** When requested or the preferred format is unavailable or fails.

Keep required columns, momentum and actionability labels, and dated evidence.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

Verify the save before reporting success and provide the actual link or location. If saving fails, disclose it and provide clearly labeled unsaved insight in chat.

## Missing data behavior

- No live CRM: continue with authorized Microsoft 365 signals. Describe the result as customer engagement and momentum insight; omit unsupported deal value, stage, forecast category, official close date, owner, and formal stakeholder roles. Communicate sources for the output.
- Uploaded CRM view only: state its snapshot date and distinguish older CRM facts from newer work signals. Prefer newer evidence when they conflict.
- Missing email or Teams: use available meetings, transcripts, documents, and CRM activities; explain material gaps.
- Sparse or conflicting history: show “Insufficient evidence” when a momentum classification is unsupported, identify what is missing, and present both sides of conflicting evidence. Do not default to Stable.
- No identified blocker or meaningful action: return “Blocker unclear” or “Can I act? No” as appropriate and identify the next dependency to monitor.
- If there is insufficient data to build a view, give clear feedback to the user.

## When NOT to Use

- For a standalone ranked work-next list, use `pipeline-prioritizer`; for a sales progress or forecast-position report, use `sales-progress-update`.
- For stakeholder roles and decision-process mapping, use `stakeholder-and-decision-map`.

## Guardrails

- Never invent a blocker, momentum change, stakeholder role, deal field, win probability, or close probability.
- Do not equate reduced activity or every delayed response with risk. Do not automatically propose a close-date change because activity declined.
- Do not overstate confidence, hide contrary evidence, or attribute communications to a deal when the mapping is uncertain.
- Do not expose unauthorized content or update CRM or take external action without explicit user intent and an authorized action path.

## Success check

A seller should be able to see which deals need attention within seconds, then understand what happened, where momentum changed, what blocks progress, who owns it, and whether they can act. Each recommendation should be grounded in evidence and specific enough to use.
