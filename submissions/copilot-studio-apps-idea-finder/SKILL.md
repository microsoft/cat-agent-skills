---
name: copilot-studio-apps-idea-finder
description: Use this skill when the user asks what apps they could build with the Copilot Studio apps experience, wants AI-powered app ideas for a department or industry, or needs to pick the best first app to build — returning scored ideas and the winning idea as a ready-to-paste build prompt.
---

# Copilot Studio Apps: Idea Finder

Find high-value, AI-powered app ideas a team can build with **Apps (Preview)** in Copilot Studio, score them, and return the best one as a build prompt.

## Workflow

### 1. Context

Ask, in one batch, only what is missing (max 4 questions):
- Department or industry
- Top 3 manual or repetitive tasks
- Where the data lives today (Excel, SharePoint, Dataverse, email, paper)
- Team size or number of likely users

### 2. Generate 6 ideas

Each idea must replace a real manual step and include at least one concrete AI behavior:
- **Extract** — read fields from a photo, PDF or email
- **Classify / route** — category, priority, owner
- **Summarize** — notes, comments, history
- **Flag** — policy breaks, duplicates, risks, anomalies, with a short reason
- **Draft** — replies, reports, next steps

Use these as inspiration, adapted to the user's context:

| Function | Idea | AI behavior |
|---|---|---|
| Finance | Expense claims | Extract receipt fields; flag duplicates and policy breaks |
| HR | Onboarding tracker | Draft a welcome plan per role; flag overdue tasks |
| IT | Asset and loan tracker | Summarize condition notes; flag repeated damage |
| Operations | Incident and safety log | Classify severity; summarize root-cause notes |
| Sales | Deal desk requests | Summarize deal context; flag missing approvals |
| Procurement | Vendor onboarding | Extract data from documents; flag missing certificates |
| Customer service | Complaint triage | Classify and route; draft a first reply |
| Facilities | Maintenance requests | Classify by trade; prioritize by risk |

### 3. Score each idea (1–5 per criterion, total /25)

- **Pain** — time lost or errors today
- **Reach** — how many people would use it
- **Data readiness** — data already exists in an accessible, list-shaped source
- **Build fit** — record-shaped, clear statuses, fits in one app
- **Low risk** — inverse of sensitive data, external users or compliance exposure

Mark any idea that depends on sensitive or regulated data as **"pilot with admin approval"**.

### 4. Deliver

Return, in this order:
1. **Ideas table**: Idea · AI behavior · Who uses it · Score /25 · Data home
2. **Top pick** with a one-sentence reason.
3. **Build prompt** for the top pick in a code block, ready to paste, covering: records and fields, roles, statuses, views, AI features, notifications, and a data instruction (default: "Use sample data for now").
