# Copilot Studio Apps: Prompt Architect

**Built for Copilot Studio apps.** Microsoft Copilot Studio can now generate a working app (data model, logic and UI) from a natural-language description. This skill makes sure that description is good enough to get a strong first draft.

A vague prompt like *"create an expense app"* gives you a generic app and a long round of fixes. This skill interviews you briefly, then writes one complete, paste-ready prompt covering everything the app builder needs.

## Before you start

- Access to [Copilot Studio](https://copilotstudio.microsoft.com/) with the **New experience** toggle on.
- The **App (Preview)** tile visible on the Home page, or **Apps (Preview)** in the side pane. App creation is on by default, but your administrator can turn it off.
- Apps are created in your **personal environment**. This is a preview feature, not meant for production use yet.
- Building, previewing and testing apps can consume **Copilot Credits**. A complete first prompt means fewer rebuilds.

## How to use it

Add the skill to your Copilot Studio agent and ask for help with an app idea, for example:

> *"Help me write a prompt for a Copilot Studio app to manage equipment loans."*

The skill:

1. **Asks only what's missing** (max 5 questions in one batch) across 8 elements: problem, users and roles, records and fields, statuses, views, AI assistance, notifications, and where the data lives.
2. **Writes the prompt** in a fixed order the app builder understands well.
3. **Predicts follow-up questions** Copilot Studio may ask, with suggested answers.
4. **Gives you a v2 backlog**: features left out on purpose, each as a one-line follow-up prompt.

### Example output

```
Create an app to manage equipment loans. Track equipment (name, type, serial number, condition, photo, location) and loans (borrower, equipment, start date, due date, return date, notes). Roles: Employee requests a loan, Equipment Manager approves and records returns. Statuses: Requested, Approved, On loan, Overdue, Returned. Add views for My loans, Pending requests, Overdue items, and an inventory dashboard by type and availability. Use AI to summarize the condition notes at return and flag items with repeated damage. Notify the borrower when a request is approved and two days before the due date. Use sample data for now.
```

Paste it into **Apps (Preview) → New app** and select **Submit**.

## Good to know

- **One app per prompt.** Big ideas are split into a v1 prompt and a backlog.
- **Attach what you have.** A spreadsheet, form or screenshot of today's process, attached with **+** in the app chat, gives the builder context. It doesn't create a live data connection.
- **Start with sample data**, then connect SharePoint, Dataverse or Excel once the design is right.
- **Connectors depend on your tenant.** The skill won't promise actions your admin policies may block.

Based on the Microsoft Learn documentation for [apps in Copilot Studio (preview)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/apps-experience/apps-overview).

Created by [Renato Romão](https://www.linkedin.com/in/renatoromao/), Microsoft MVP (Copilot Studio & Microsoft Foundry).
