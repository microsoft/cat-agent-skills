# Help Scout Auto-Drafting Deployment

Read this from the deployment surfaces reference when configuring the advanced Help Scout integration for support email auto-drafts, notes, or auto-sent first replies.

This is different from the Help Scout Beacon widget handoff. Beacon integration opens Help Scout chat/ticket UI from the DocsBot widget. Help Scout auto-drafting connects DocsBot to Help Scout mailboxes/tags so DocsBot can draft or publish replies inside Help Scout using a bot's sources, Help Scout prompt, and optional customer metadata.

## Background

DocsBot's Help Scout integration needs three layers:

1. Help Scout API app credentials: App ID and App Secret from a Help Scout OAuth2 app.
2. DocsBot team integration: stored through Admin MCP, then refreshed until mailboxes/tags and webhook secret are available.
3. Help Scout webhook app: configured in Help Scout with DocsBot's callback URL and webhook secret so Help Scout sends conversation events to DocsBot.

The dashboard callback URL shape is:

```text
https://api.docsbot.ai/teams/{teamId}/helpscout
```

For auto-drafts, the safer default is draft reply behavior: `noteResponse: false` and `publishReply: false`. `publishReply: true` sends the bot's first reply automatically instead of saving a draft. Enable that only when the user explicitly wants auto-send and has reviewed the prompt and source coverage.

## Help Scout Setup For The User

Have the user complete these Help Scout-side steps when credentials or webhooks are not already configured:

1. In Help Scout, create an OAuth2 app:
   - Go to Help Scout profile/settings, then `My Apps`, then create a new app.
   - Copy the App ID and App Secret.
   - DocsBot uses client credentials for API access. If Help Scout asks for a redirect URL while creating the app, use a valid HTTPS placeholder/admin URL; the Admin MCP connection flow uses App ID and App Secret, not an end-user OAuth redirect.
2. Give the App ID and App Secret to DocsBot out of band. Do not paste secrets into final handoff text.
3. After the DocsBot integration is ready, create or open the Help Scout Webhooks app:
   - Help Scout UI path is typically `Manage > Apps > Webhooks`, or use `https://secure.helpscout.net/apps/webhooks/`.
   - Set the webhook Active.
   - Callback URL: `https://api.docsbot.ai/teams/{teamId}/helpscout`.
   - Secret: use the DocsBot Help Scout webhook secret from the integration settings. Do not print it in normal user-facing output.
   - Events: select `Conversation Created`; select `Conversation Customer Reply` for follow-up customer replies; select `Conversation Tags Updated` only when using tag listeners. If Help Scout shows event slugs, choose the equivalent conversation-created, customer-reply-created, and tag-updated events.
4. Save the Help Scout webhook.

Official Help Scout references:

- OAuth2 app credentials: `https://developer.helpscout.com/mailbox-api/overview/authentication`
- Webhooks app setup: `https://developer.helpscout.com/webhooks/`
- Webhook secret/signature concept: `https://developer.helpscout.com/mailbox-api/endpoints/webhooks/update/`

## Admin MCP Operation Workflow

Inspect the advertised schema before the first write, then call the named tool.

1. Choose team and bot:
   - `list_teams`
   - `get_team`
   - `list_bots`
   - `get_bot`
2. Check existing integration:
   - `list_team_integrations` with query `{ "type": "helpscout" }`
   - If the user needs the webhook secret and has permission, query `{ "type": "helpscout", "revealWebhookSecret": "true" }`, but do not print the secret in final output.
3. Connect or reconnect credentials:

```json
{
  "type": "helpscout",
  "appID": "HELP_SCOUT_APP_ID",
  "appSecret": "HELP_SCOUT_APP_SECRET"
}
```

Use the DocsBot dashboard to connect Help Scout; the hosted named-tool catalog does not advertise this credential write. The dashboard stores the integration as pending and queues backend connection work. For new Help Scout integrations, DocsBot seeds the Help Scout prompt on bots that do not already have one.

4. Poll/refresh metadata:
   - Poll `list_team_integrations` until `status` is no longer `pending` or `working`.
   - If metadata is stale or credentials were updated, run `refresh_helpscout_metadata`, then poll again.
   - Wait for `status: "ready"` and available `mailboxes` and/or `tags` before routing.
5. Configure routing and behavior with `configure_helpscout_integration`.

Mailbox listener example:

```json
{
  "assignedMailboxes": {
    "mailbox_id": "bot_id"
  },
  "noteResponse": false,
  "publishReply": false,
  "sourceResponse": true,
  "saveMeta": true
}
```

Tag listener example:

```json
{
  "assignedBots": {
    "tag_id": "bot_id"
  },
  "noteResponse": false,
  "publishReply": false,
  "sourceResponse": true,
  "saveMeta": true
}
```

Use `"none"` as the mapped bot ID to clear an assignment.

6. Configure Help Scout prompt:
   - Read [../prompt-instructions.md](../prompt-instructions.md).
   - Use the Help Scout prompt asset as the base template: [helpscout.md](../../assets/prompts/helpscout.md).
   - Save with `update_bot` using `helpscoutPrompt`.
   - Verify it includes `search_documentation` and does not tell customers to escalate to support; the AI is acting as the support team draft/reply agent.

## Routing Decisions

- Use mailbox mapping when every new conversation in a mailbox should receive the selected bot's draft or note.
- Use tag mapping when staff or automation applies a tag to choose which bot should respond.
- Avoid using both mailbox and tag listeners for the same workflow unless the user understands the routing interaction; the dashboard warns that setting both may not work as expected.
- For multi-product support, prefer separate bots or strong source tags plus mailbox/tag routing that matches product ownership.
- If the Help Scout bot will answer from private/internal procedures, do not also expose that same bot publicly without reviewing sources, prompt, and privacy settings.

## Response Flags

- `noteResponse`: when true, DocsBot adds responses as Help Scout notes with response and sources instead of a draft reply.
- `publishReply`: when true, the bot's first reply to a new conversation is sent immediately instead of saved as a draft. Treat this as high-impact.
- `sourceResponse`: when true, if the bot cannot fully answer, a note is made showing relevant sources.
- `saveMeta`: when true, customer name/email and custom Help Scout customer properties are stored with interactions and can be used as model context for replies.

Recommended starting point:

```json
{
  "noteResponse": false,
  "publishReply": false,
  "sourceResponse": true,
  "saveMeta": true
}
```

## Plan And Permission Notes

- Help Scout integration is plan-gated by the Help Scout/integrations plan permission. Current UI describes this as Standard plan or higher; verify the live Admin MCP response if a 402 is returned.
- Connecting and configuring Help Scout requires team/integration management permission.
- Revealing the webhook secret requires team owner/admin-level permission or super admin.
- Secret values are redacted in normal integration reads. Report `appSecretSet`, `appSecretLast4`, `webhookSecretSet`, or `webhookSecretLast4`, not the secret.

## Verification

Before calling the setup final-product ready:

- `list_team_integrations` shows Help Scout `status: "ready"`.
- Integration read shows expected `mailboxes`, `tags`, routing maps, and behavior flags.
- `appSecretSet` and `webhookSecretSet` are true or otherwise clearly present in redacted readback.
- Help Scout webhook is active in Help Scout with the callback URL and selected events.
- The bot has a Help Scout prompt in `helpscoutPrompt` with `search_documentation`.
- Critical sources for the support workflow are ready, nonzero, and broad enough.
- If source tags are used, the Help Scout prompt routes to those tag keys.
- `publishReply` is false unless the user explicitly approved auto-send.
- A test Help Scout conversation or tag event has been created when possible; otherwise the handoff states that Help Scout-side webhook testing remains.

Handoff should include:

- Team, bot, selected mailbox/tag mappings, and response flags.
- Dashboard links: `https://docsbot.ai/app/api#helpscout-integration` and `https://docsbot.ai/app/bots/{botId}/chat`.
- Help Scout action still needed, if any: create OAuth app, paste App ID/App Secret, install Webhooks app, add callback URL/secret, choose events, or create a test conversation.
