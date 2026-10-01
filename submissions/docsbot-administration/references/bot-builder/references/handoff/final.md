# Final Handoff

Read this before writing the final user-facing response after creating, configuring, tuning, testing, or judging a DocsBot bot.

The final response must help the user immediately try the bot and continue setup. Do not end with only an audit, source list, or generic "next steps."

## Required Shape

Keep the response concise, but include these sections in this order:

1. **Try It**
   - Lead with the best available link to test the bot.
   - Prefer dashboard chat: `https://docsbot.ai/app/bots/{botId}/chat`.
   - Include a public share/embed URL only if confirmed from bot/dashboard data.
   - If the bot is not ready, still provide the dashboard chat link and label the setup status honestly.

2. **What I Set Up**
   - One short paragraph or bullets covering bot purpose, deployment surface, branding, source scope, prompt behavior, and enabled actions/integrations.
   - Mention the exact team and bot ID.

3. **Custom Next Steps**
   - Give next steps specific to the user's use case and unresolved work.
   - Examples: connect Google Drive and pick folders, install Slack OAuth, finish Help Scout webhook, add private PDFs, review lead fields, test escalation, paste widget embed, or approve auto-send.
   - Do not give generic dashboard chores when no action is needed.

4. **Useful Deep Links**
   - Include only links relevant to this bot's setup. Use [../operations.md](../operations.md) for canonical paths.
   - At minimum include chat and sources.
   - Add widget actions/design for website widgets, skills/MCP links for integrations, webhooks for automations, and Help Scout/Slack API anchors when those surfaces are involved.

5. **Test Prompts**
   - Provide 4-8 prompts tailored to the bot's sources, tags, actions, and deployment.
   - Include at least one normal answer test, one missing-info/clarifying test, one escalation or lead test when configured, and one source-tag conflict test when tags exist.

6. **Readiness Notes**
   - State final-product ready, demo-scale, or not final-product ready.
   - Include the final source status check. If any sources are still `pending` or `indexing`, say that indexing is still running and answers for those areas may be incomplete until it finishes.
   - List blockers separately from optional polish.
   - Include source coverage only at summary level unless the user asked for full audit details.

## Voice Status

For new bots/full setup or voice work, distinguish saved voice instructions, Advanced voice enabled/disabled, and connected phone/SIP routing. Report “voice prompt prepared; Advanced voice disabled” when only preparation was authorized. For authorized voice, include the saved activation state, verified route or unresolved connection step, and useful spoken tests; do not claim a live phone agent from an instruction save. Include voice dashboard links when relevant, without turning disabled preparation into a required activation step.

## Deep Link Selection

Use current dashboard paths:

- Voice settings: `https://docsbot.ai/app/bots/{botId}/voice`
- Voice phone/SIP: `https://docsbot.ai/app/bots/{botId}/voice/phone`
- Chat: `https://docsbot.ai/app/bots/{botId}/chat`
- Sources: `https://docsbot.ai/app/bots/{botId}/configure/sources`
- System settings: `https://docsbot.ai/app/bots/{botId}/configure/system`
- Instructions: `https://docsbot.ai/app/bots/{botId}/configure/instructions`
- Widget actions: `https://docsbot.ai/app/bots/{botId}/widget/actions`
- Widget design: `https://docsbot.ai/app/bots/{botId}/widget/design`
- Widget deploy/embed: `https://docsbot.ai/app/bots/{botId}/widget/deploy`
- Skills: `https://docsbot.ai/app/bots/{botId}/configure/skills`
- Webhooks: `https://docsbot.ai/app/bots/{botId}/configure/webhooks`
- MCP connections: `https://docsbot.ai/app/bots/{botId}/configure/mcp-connections`
- Help Scout integration: `https://docsbot.ai/app/api#helpscout-integration`
- Slack integration: `https://docsbot.ai/app/api#slack-settings`

## Example Skeleton

```markdown
**Try It**
Test the bot here: [Dashboard chat](https://docsbot.ai/app/bots/{botId}/chat).

**What I Set Up**
Created `{botName}` in `{teamName}` (`{botId}`) for `{purpose}`. It is tuned for `{deployment}` with `{sourceSummary}`, `{promptSummary}`, and `{actionsSummary}`.

**Custom Next Steps**
- `{specific next step 1}`
- `{specific next step 2}`
- `{specific next step 3}`

**Useful Links**
- [Chat](https://docsbot.ai/app/bots/{botId}/chat)
- [Sources](https://docsbot.ai/app/bots/{botId}/configure/sources)
- [Widget deploy](https://docsbot.ai/app/bots/{botId}/widget/deploy)

**Test Prompts**
- `{happy path question}`
- `{clarifying question}`
- `{tag conflict/version question}`
- `{escalation or lead capture question}`

**Readiness**
`{Final-product ready | Demo-scale | Not final-product ready}`. `{one-sentence reason}`.
```

## Guardrails

- Do not expose secrets, signed URLs, raw tokens, or private connector IDs.
- Do not promise share/embed URLs unless confirmed.
- Do not say a dashboard-only integration is configured until integration reads verify it.
- Do not bury required user action in a long audit; put it in Custom Next Steps.
