---
name: copilot-studio-apps-prompt-architect
description: Use this skill when the user wants to build an app with the Copilot Studio apps experience (Apps (Preview) / App tile) and needs a strong first prompt — turning a vague business idea into a complete, build-ready app description with users, data, roles, statuses, views, AI features, and notifications.
---

# Copilot Studio App Prompt Architect

Turn a business idea into a single, build-ready prompt for the **Apps (Preview)** experience in Microsoft Copilot Studio, where the agent generates a data model, logic, and UI from natural language.

## Why this matters

The first prompt decides how close the first draft is to what the user needs. The agent may ask clarifying questions and propose an approach before generating the preview. A complete prompt means fewer questions, fewer rebuilds, and fewer Copilot Credits spent (building, previewing and testing apps can consume credits).

## Workflow

### 1. Intake (ask only what is missing, max 5 questions in one batch)

Collect these eight elements. If the user already gave some, do not ask again.

| # | Element | Example |
|---|---------|---------|
| 1 | **Problem** — what is painful today | "Expense receipts are typed by hand and approvals live in email" |
| 2 | **Users and roles** | Employee, Manager, Finance |
| 3 | **Records** — the main things the app tracks, with fields | Expense: vendor, date, amount, currency, category, receipt |
| 4 | **Lifecycle** — statuses and who moves them | Draft → Submitted → Approved / Rejected → Paid |
| 5 | **Views** — who sees what | My expenses, Pending approvals, All expenses |
| 6 | **AI assistance** — what the app should infer, extract, summarize, or flag | Extract fields from a receipt photo; flag policy violations |
| 7 | **Actions and notifications** | Email/Teams message when submitted or decided |
| 8 | **Data home** — sample data for now, or an existing SharePoint list / Dataverse table / Excel table | "Start with sample data" |

If the user has a spreadsheet, form, or screenshot of the current process, tell them to attach it with **+** in the chat — it gives the agent context (it does not create a live connection).

### 2. Draft the prompt

Write one paragraph (or a short structured block) in this order:

1. One sentence: "Create an app to …" + the problem.
2. Records and fields.
3. Roles and assignment.
4. Statuses.
5. Views and a dashboard (if useful).
6. AI features, stated as concrete behavior ("AI extracts X from Y", "AI flags Z and explains why").
7. Notifications and connector actions.
8. Data instruction ("Use sample data for now" or "Connect to the existing SharePoint list named …").

Rules:
- Be specific about fields, statuses, and roles. Avoid vague words like "manage", "handle", "smart" without saying what they do.
- Keep to one app per prompt. Split big ideas into a v1 and a backlog.
- Do not promise capabilities the user's tenant may not allow (connectors and data sources depend on admin policies).
- Write the prompt in the language the user will type into Copilot Studio (default English).

### 3. Deliver

Return, in this order:
1. **The prompt** in a code block, ready to paste.
2. **Likely follow-up questions** the agent may ask, with suggested answers.
3. **v2 backlog** — 3–5 features left out on purpose, each as a one-line follow-up prompt for later iteration.
4. **Before you start** — a 3-line checklist: New experience toggle on, **App (Preview)** tile visible (admins can turn app creation off), app will be created in your personal environment.

## Example

Input: "We need something for equipment loans."

Output prompt:
```
Create an app to manage equipment loans. Track equipment (name, type, serial number, condition, photo, location) and loans (borrower, equipment, start date, due date, return date, notes). Roles: Employee requests a loan, Equipment Manager approves and records returns. Statuses: Requested, Approved, On loan, Overdue, Returned. Add views for My loans, Pending requests, Overdue items, and an inventory dashboard by type and availability. Use AI to summarize the condition notes at return and flag items with repeated damage. Notify the borrower when a request is approved and two days before the due date. Use sample data for now.
```
