# Slack Deployment

Read this only when the bot should be available in Slack or when the user asks to connect, route, verify, or disconnect Slack.

## Purpose

Slack deployment is best for internal team assistants, staff support copilots, and team knowledge bots. It is usually not the right primary deployment for public customer support unless the customer support channel already lives in Slack.

DocsBot public docs: `https://docsbot.ai/documentation/doc/slack-integration`

Slack OAuth background: `https://docs.slack.dev/authentication/installing-with-oauth`

## User Handoff

The user must complete Slack OAuth in a browser. Give one of these links:

- Team API/Integrations Slack section: `https://docsbot.ai/app/api#slack-settings`
- If MCP returns an authorize URL, send that exact URL and explain that it installs/connects the workspace.

Tell the user they must be a DocsBot team admin and have permission to install apps in the Slack workspace. Do not ask for Slack tokens or print stored tokens.

## Operation Workflow

1. Read bot settings with `get_bot` and confirm the bot is appropriate for internal Slack use.
2. Start connection with `get_slack_authorization_url`.
   - Optional query: `defaultBotId` to preselect this bot after connection.
   - Optional query: `afterConnect` to return the user to a dashboard route after OAuth.
3. Have the user open the returned `url` or the dashboard deep link and complete Slack OAuth.
4. After the user confirms completion, read Slack configuration with `get_slack_integration`.
5. If workspace routing needs changes, call `update_slack_routing` with `workspaces`.
   - Set `defaultBotId` for the workspace default.
   - Set `channelBotMap` for channel-specific routing.
   - Set `adminsOnly` when only Slack admins should use the integration.
6. Verify linked bots with `list_slack_bots`.

Disconnect only after explicit confirmation:

- `disconnect_slack_workspace` with `slackTeamId`.
- Verify removal with `get_slack_integration`.

## Prompt Guidance

For internal Slack bots, add a short instruction that answers are for employees or workspace members and that the bot should avoid customer-facing claims unless the source material supports them.

If Slack is only one of multiple surfaces, keep the prompt safe for the broadest audience or explicitly state which topics are internal-only.

## Handoff Checklist

- Slack connection status and workspace name from `get_slack_integration`.
- Default bot and any channel mappings from `list_slack_bots`.
- Dashboard link: `https://docsbot.ai/app/api#slack-settings`.
- Any unresolved user-only steps, such as app approval by a Slack workspace owner.
