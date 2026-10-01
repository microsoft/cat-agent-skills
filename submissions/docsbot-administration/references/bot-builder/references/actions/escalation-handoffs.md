# Escalation Handoffs

Read this only when configuring human escalation, support links, helpdesk/widget handoffs, or `conversation.escalated` automation.

DocsBot docs:

- Widget integrations: `https://docsbot.ai/documentation/developer/widget-integrations`
- Embeddable widget support callback: `https://docsbot.ai/documentation/developer/embeddable-chat-widget#support-callback`
- Answer rating and escalation API: `https://docsbot.ai/documentation/developer/answer-rating#conversation-support-escalations`
- Webhooks API: `https://docsbot.ai/documentation/developer/webhooks-api`

## Purpose

Escalation gives the user a clear path to a human when the bot cannot resolve the issue, the user asks for a person, or the workflow requires a support, sales, onboarding, or compliance handoff.

For public bots, configure a real support/contact route unless the user explicitly wants no handoff. For internal/helpdesk bots, route escalation to staff workflow rather than end-customer support copy.

## Operation Workflow

1. Read the bot with `get_bot`.
2. Research the website for a support URL and existing helpdesk/live-chat widget.
3. If a supported helpdesk widget is confirmed on the site, link the relevant DocsBot widget integration page and tell the user to use the embed code handoff pattern.
4. If no widget is confirmed, set or recommend a normal `supportLink` to the support/contact page.
5. Preserve or enable `tools.human_escalation.enabled` through `update_bot`.
6. If downstream automation is needed, load [webhooks.md](webhooks.md) and configure `conversation.escalated`.
7. Read the bot again and verify `supportLink`, `tools.human_escalation`, and any webhook state.

## Helpdesk Widget Detection

Only claim a provider-specific handoff when site research or page HTML confirms it. Useful signatures:

| Provider | Signals | Docs link |
| --- | --- | --- |
| Help Scout Beacon | `Beacon(`, `beacon-v2.helpscout.net` | `https://docsbot.ai/documentation/developer/widget-integrations/helpscout` |
| Zendesk | `zE(`, `ze-snippet`, `static.zdassets.com/ekr/snippet.js` | `https://docsbot.ai/documentation/developer/widget-integrations/zendesk` |
| Intercom | `Intercom(`, `widget.intercom.io` | `https://docsbot.ai/documentation/developer/widget-integrations/intercom` |
| Freshdesk/Freshchat | `freshchat`, `freshworks`, `wchat.freshchat.com` | `https://docsbot.ai/documentation/developer/widget-integrations/freshdesk` |
| HubSpot | `js.hs-scripts.com`, `HubSpotConversations`, `hubspot` | `https://docsbot.ai/documentation/developer/widget-integrations/hubspot` |
| LiveChat | `LiveChatWidget`, `cdn.livechatinc.com` | `https://docsbot.ai/documentation/developer/widget-integrations/livechat` |
| Gorgias | `gorgias-chat-widget`, `gorgias.chat` | `https://docsbot.ai/documentation/developer/widget-integrations/gorgias` |
| Zoho Chat | `SalesIQ`, `salesiq.zoho`, `ZohoHCAsap` | `https://docsbot.ai/documentation/developer/widget-integrations/zoho-chat` |

If detection is uncertain, say that a generic support link is configured and provide the widget integrations index as a next step instead of naming a provider.

## Prompt Guidance

Keep escalation rules concise:

- Offer escalation when the user asks for a human, asks for account-specific help the bot cannot access, reports a failed or urgent issue, or needs sales/support follow-up.
- Do not promise SLA, ticket creation, refunds, or account changes unless an action or integration actually performs them.
- If a helpdesk handoff is configured, tell the user what will happen next in plain language.

## Verification

- Saved bot read shows `supportLink` when a simple link is used.
- Saved bot read shows `tools.human_escalation.enabled` when agent escalation should be available.
- If using webhooks, `list_webhooks` shows an active `conversation.escalated` subscription and test delivery has succeeded.
- Handoff includes the exact support URL or provider docs link and states whether provider detection was confirmed.
