# Copilot Studio Apps: Idea Finder

**Built for Copilot Studio apps.** Microsoft Copilot Studio can now generate a working app from a natural-language description. The hard part is often deciding *which* app to build first. This skill finds, scores and picks it for you.

## Before you start

- Access to [Copilot Studio](https://copilotstudio.microsoft.com/) with the **New experience** toggle on.
- The **App (Preview)** tile visible on the Home page, or **Apps (Preview)** in the side pane. App creation is on by default, but your administrator can turn it off.
- Apps are created in your **personal environment**. This is a preview feature, not meant for production use, so treat the ideas as pilots.

## How to use it

Add the skill to your Copilot Studio agent and ask, for example:

> *"What AI apps could our finance team build in Copilot Studio?"*

The skill:

1. **Asks up to 4 questions**: department, top manual tasks, where the data lives, and how many people would use the app.
2. **Generates 6 ideas**, each with a concrete AI behavior: extract, classify, summarize, flag or draft.
3. **Scores each idea out of 25** on pain, reach, data readiness, build fit and risk.
4. **Picks the winner** and writes a ready-to-paste build prompt for it.

Paste the prompt into **Apps (Preview) → New app** and select **Submit**.

## Good to know

- **List-shaped data wins.** Ideas whose data already sits in SharePoint, Dataverse or Excel score higher on data readiness and connect fastest.
- **Sensitive data is flagged.** Ideas touching regulated data are marked "pilot with admin approval".
- **Pair it with Prompt Architect.** If you want to refine the winning prompt further, use the *Copilot Studio Apps: Prompt Architect* skill.

Based on the Microsoft Learn documentation for [apps in Copilot Studio (preview)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/apps-experience/apps-overview).

Created by [Renato Romão](https://www.linkedin.com/in/renatoromao/), Microsoft MVP (Copilot Studio & Microsoft Foundry).
