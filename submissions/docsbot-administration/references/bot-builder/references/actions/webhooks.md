# Webhooks

Read this only when configuring outgoing event delivery for leads, escalations, ratings, or deep research jobs.

DocsBot Webhooks API: `https://docsbot.ai/documentation/developer/webhooks-api`

## Purpose

Use webhooks when another system must react to DocsBot events: CRM lead creation, support escalation, answer rating feedback, deep research completion, or Zapier/Make/viaSocket style automations.

Webhook endpoint URLs and signing keys are secrets or semi-secrets. Do not print signing keys. Prefer redacted verification.

## Events

- `lead.created`
- `conversation.escalated`
- `conversation.rated`
- `deep_research.done`

## Operation Workflow

1. List current hooks with `list_webhooks`.
2. Preview payloads when needed with `list_webhook_samples`.
3. Create a hook with `create_webhook`.
   - Body usually includes `targetUrl`, `events`, and optional `label`, `source`, `expirationDate`.
4. Read it with `get_webhook`.
5. Test delivery with the matching operation:
   - `send_test_lead_webhook`
   - `send_test_escalation_webhook`
   - `send_test_rated_webhook`
   - `send_test_research_webhook`
6. If changing configuration, use `update_webhook`.
7. Pause with `status: "paused"` when temporary disablement is safer than deletion.
8. Delete only after explicit confirmation with `delete_webhook`.

## Escalation Notes

For `conversation.escalated`, escalation must be confirmed and logged through the Conversation Support Escalation API before the webhook fires. A `support_escalation` event from Chat Agent indicates intent and confirmation UI, not a completed handoff by itself.

## Verification

- Webhook read shows expected `targetUrl`, `events`, `status`, `label`, and expiration.
- Test delivery returns success for the configured event.
- Handoff tells the user which downstream system receives each event and which signing-key verification step remains outside MCP.
