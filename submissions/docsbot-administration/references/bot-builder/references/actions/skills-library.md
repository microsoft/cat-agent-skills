# Skills Library Actions

Read this only from the actions index when imported DocsBot Skills are in scope.

## When To Use Skills

Use library Skills when a vendor, workflow, or deterministic action is clearly useful for the bot's job, for example:

- Billing/account questions through a billing vendor Skill such as Freemius or Stripe.
- Code or issue lookup through GitHub for open-source or developer-support bots.
- Calculators, eligibility checks, enrichment, CRM lookup, or other repeatable tools.

Do not import Skills just because they exist. Each enabled Skill should map to a user question cluster or action the bot should handle.

## Operation Flow

1. Search the library with `list_library_skills` using vendor and task keywords.
2. Read existing bot Skills with `list_skill_drafts` to avoid duplicates.
3. Import the best match with `import_library_skill`.
4. Read the imported skill and settings.
5. Configure published settings with `configure_published_skill`.
6. Add prompt instructions for when the bot should use the Skill.
7. Verify with settings readback and worker logs when relevant.

## Binding Rules

- `enabledWidget` controls whether the Skill is available to widget chat. Enable it only when the Skill is safe for the deployment audience.
- Configure declared `envBindings` and `secretBindings`; do not invent undeclared bindings.
- Secret values are never returned. Verify presence/status without printing values.
- Metadata bindings such as customer email or ID may only work when that metadata is available in the chat/deployment surface.
- For public bots, be careful with account-specific Skills. Do not expose owner-scoped data to anonymous customers.

## Prompt Lines

Add concise use instructions:

```text
Use the Freemius billing skill for questions about the customer's subscription, license, renewals, invoices, or billing status when the required customer identity is available. If identity is missing, ask for the required account email before using the skill.
```

```text
Use the GitHub code-reading skill for technical questions that require current repository code, issue, or release details. Use search_documentation first for published documentation questions, then GitHub only when the answer depends on live code or issues.
```

## Verification

- Read the bot Skill list and published settings.
- Confirm missing bindings are resolved or documented as dashboard-only follow-up.
- Confirm `enabledWidget` matches public/internal deployment risk.
- Read worker logs after a test trigger when available.
- Confirm the prompt explains when to use the Skill and when to fall back to documentation search or escalation.
