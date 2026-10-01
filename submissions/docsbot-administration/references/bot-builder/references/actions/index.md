# Actions And Integrations

Read this when configuring bot actions, integrations, Skills, external MCP servers, deployment actions, or widget safety settings.

Use actions only when they serve the bot's purpose. Prefer a small number of well-configured actions over a broad set of unverified capabilities.

For the bot fields that store each action, see the Compact Field Map in [../operations.md](../operations.md), then load the specific subref below before writing payloads.

## Action Index

| Area | Use when | Notes |
| --- | --- | --- |
| Escalation | Support, onboarding, complex billing, failed answer recovery | Load [escalation-handoffs.md](escalation-handoffs.md) before configuring support links, helpdesk widget handoffs, or escalation webhooks. |
| Lead collection | Presales, demos, sales qualification, support follow-up | Load [lead-collection.md](lead-collection.md) before configuring forms or fields. |
| Custom buttons | Specific link-based handoffs that other actions cannot satisfy | Load [custom-buttons.md](custom-buttons.md) only when a use case needs a deterministic button and no better built-in action, Skill, MCP connector, source, or normal support link covers it. |
| Scheduling | Demos, onboarding, office hours, sales consults | Load [scheduling.md](scheduling.md) when the bot should book time through Calendly, Cal.com, or TidyCal. |
| Web search | Live public facts only | Load [web-search.md](web-search.md) before enabling live search or adding prompt guidance for it. |
| Help Scout | Support email workflows and Help Scout deployment | Load [../deployment/helpscout-auto-drafting.md](../deployment/helpscout-auto-drafting.md) from the deployment refs before assigning mailboxes/tags or changing response flags. |
| Slack | Internal team assistants or Slack app deployment | Load [../deployment/slack.md](../deployment/slack.md). User must complete OAuth outside MCP. Verify bot mapping after install. |
| Webhooks | Lead, escalation, rating, research, or downstream event delivery | Load [webhooks.md](webhooks.md). Treat endpoints and signing keys as secrets; do not print them. |
| Billing/vendor account actions | Authenticated customer billing support, subscriptions, invoices, license lookup | Load [billing.md](billing.md) before enabling Stripe tools, importing billing Skills, or recommending external billing MCP. |
| Skills library | Vendor/task tools like billing, GitHub, search, calculators, enrichment | Load [skills-library.md](skills-library.md). |
| External MCP servers | Non-user-scoped lookup/action tools or internal owner-scoped tools | Load [external-mcp.md](external-mcp.md). |

## Public Widget Safety

For public widgets, explicitly evaluate:

- Keep `showCopyButton` and `linkSafetyEnabled` omitted, false, or unchanged. They are not generic public-widget defaults. See [Response Sharing And Link Privacy](../workflow.md#response-sharing-and-link-privacy) for the only allowed enablement case.
- `piiRedaction`: keep it `false` unless the user requests PII redaction or the deployment has a specific compliance requirement.
- `recordIP`, image uploads, and audio uploads. Do not set them during initial bot creation; leave their default/null state alone unless the user explicitly requests them or the deployment has a concrete requirement.
- Whether every lead field is necessary and has concise labels/options; load [lead-collection.md](lead-collection.md) before adding or changing fields.
- Whether escalation/contact URLs are support-oriented, sales-oriented, or intentionally both.
- Whether scheduling is needed for demos, onboarding, or sales qualification.

## Optional Progressive Disclosure

Load subrefs only when the action is selected or clearly recommended by research:

- [escalation-handoffs.md](escalation-handoffs.md): support links, widget/helpdesk JavaScript handoffs, `support_escalation`, and `conversation.escalated` webhooks.
- [custom-buttons.md](custom-buttons.md): narrow button use cases, fallback patterns, draft operation, save payload, and verification.
- [scheduling.md](scheduling.md): Calendly, Cal.com, and TidyCal URL validation and bot tool shape.
- [web-search.md](web-search.md): live-search fit, public bot limits, cost/safety notes, and prompt guidance.
- [webhooks.md](webhooks.md): outgoing event subscriptions, test delivery operations, payload preview, and signing-key handling.
- [../deployment/slack.md](../deployment/slack.md): Slack OAuth handoff, dashboard deep links, and workspace bot routing.
- [billing.md](billing.md): Stripe customer billing tools, vendor billing Skills, external MCP boundaries, and private metadata requirements.

## Expected Public Basics

For public presales/support widgets, configure these unless the user says otherwise:

- Human escalation or a clear support/contact route.
- Lead collection for demo, sales, or support follow-up flows, or an explicit no-lead rationale in the handoff.
- A company-specific `labels.firstMessage` and starter questions.
- A verified support/contact URL if human escalation is enabled.

## Internal Or Helpdesk Bots

For internal support or helpdesk copilot bots, explicitly decide and record:

- Public vs private deployment, and any allowed-domain constraints.
- Whether Help Scout auto-drafting, Slack, webhook, MCP connector, dashboard-only chat, or a website widget handoff is the intended surface.
- Live evidence for that deployment choice, such as integration lists, webhook reads, Slack mapping reads, or an explicit dashboard-only decision.
- Treat `widgetType` as detected website support-widget metadata for handoff guidance, not proof that a DocsBot integration is connected.
- For Help Scout auto-drafting or Slack deployment, verify the actual integration with the relevant integration read operations. For Help Scout Beacon, Zendesk, Freshdesk, Intercom, or HubSpot widget handoffs, confirm the site's widget script and use [escalation-handoffs.md](escalation-handoffs.md); no DocsBot team integration connection is implied.
- Whether the user explicitly confirmed that team members will reuse or share answer output. Only then may `showCopyButton` be enabled; `linkSafetyEnabled` additionally requires an explicit link-privacy request. Otherwise preserve both values and do not write either field.
- How escalation should route for staff, not end customers.
- PII/log/token handling. Internal support bots may need `piiRedaction`, but do not assume it must be enabled; record the user's preference or a concrete compliance reason before enabling it.

## Verification

- Read bot settings after every action update.
- Verify configured lead fields, support links, web search, Skills, MCP servers, integrations, and any custom buttons from reads, not intended payloads.
- Verify `showCopyButton` and `linkSafetyEnabled` after any intentional change, and record the confirmed private/internal output-sharing use case in the handoff.
- Add matching prompt instructions for every action the user should know how to trigger.
- In handoff, list enabled actions/integrations and any dashboard-only connection steps.
