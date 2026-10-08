# Deployment Surfaces

Read this when deciding how the bot will be deployed or when handoff depends on widget, embed, dashboard chat, Help Scout, Slack, API, share links, or private/internal access.

## Surface Selection

| Surface | Best fit | Setup notes |
| --- | --- | --- |
| Website widget | Public support, presales, docs help, onboarding | Configure branding, `labels.firstMessage`, support URL, safety settings, lead/escalation/action choices, and public-facing prompt tone. |
| Embed/share chat | Public demo, docs portal, lightweight assistant | Verify the share/embed URL from saved dashboard/bot data before promising it. |
| Dashboard chat | Internal testing, private support, validation | Use for initial testing and dashboard-only bots. Provide dashboard chat deep link. |
| Help Scout | Support email auto-drafts/replies and staff workflow | Load [helpscout-auto-drafting.md](helpscout-auto-drafting.md) before configuring Help Scout app credentials, webhooks, routing, or Help Scout prompt behavior. |
| Slack | Internal team assistant or Slack app surface | Load [slack.md](slack.md). User must complete OAuth outside MCP, usually from the API/Integrations dashboard. Verify Slack bot mapping after install. |
| Advanced voice / phone / SIP | Spoken support, reception, inbound sales | Read [voice.md](voice.md). Prepare instructions for new/full setup; enable only with user authorization or clear voice context. Phone/SIP assignments are separate. |
| API | Custom app integration or server-side use | Confirm API docs and auth handoff; do not invent endpoint/share details. |
| External MCP/search | Documentation retrieval by other tools/agents | Verify source tags and retrieval schema when tag-filtered search is expected. |

## Decision Rules

- Infer likely deployment from website, docs, helpdesk widget, Slack/community hints, and user context before asking.
- For public deployments, verify support/contact route, lead decision, link safety, PII redaction choice, and only the actions that serve the use case.
- For internal deployments, decide access boundary, PII/log/token handling, and whether owner-scoped actions are acceptable.
- For Help Scout, load [helpscout-auto-drafting.md](helpscout-auto-drafting.md). For Slack, load [slack.md](slack.md) and treat OAuth/install and workspace selection as user-completed even when MCP can generate the authorize URL.
- If the bot will support multiple surfaces, make the prompt and actions safe for the broadest audience or explicitly restrict the risky surface.

## Handoff Links

Use these deep links when `botId` is known:

- Voice settings: `https://docsbot.ai/app/bots/{botId}/voice`
- Voice phone/SIP: `https://docsbot.ai/app/bots/{botId}/voice/phone`
- Dashboard chat: `https://docsbot.ai/app/bots/{botId}/chat`
- Sources: `https://docsbot.ai/app/bots/{botId}/configure/sources`
- Widget actions: `https://docsbot.ai/app/bots/{botId}/widget/actions`
- Widget design: `https://docsbot.ai/app/bots/{botId}/widget/design`
- Skills: `https://docsbot.ai/app/bots/{botId}/configure/skills`
- Webhooks: `https://docsbot.ai/app/bots/{botId}/configure/webhooks`
- MCP connections: `https://docsbot.ai/app/bots/{botId}/configure/mcp-connections`
- Help Scout integration: `https://docsbot.ai/app/api#helpscout-integration`
- Slack integration: `https://docsbot.ai/app/api#slack-settings`

Only provide public share/embed links after confirming the current route or saved bot/dashboard data.

## Verification

- Read saved bot settings after deployment-related updates.
- Verify integration reads or dashboard-only handoff for Help Scout/Slack.
- Verify the prompt matches the chosen deployment surface.
- Include the selected surface, unresolved dashboard-only steps, and exact deep links in handoff.
