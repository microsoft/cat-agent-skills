# Web Search Action

Read this only when deciding whether to enable live web search or tuning instructions for it.

DocsBot guide: `https://docsbot.ai/documentation/doc/web-search-action`

Developer behavior: `https://docsbot.ai/documentation/developer/chat-agent#tool_call`

## Purpose

Use web search for public, current information that is not practical to keep in the bot's sources: third-party API changes, recent announcements, live status, current pricing pages, or external docs that change often.

Do not use web search as a substitute for training on stable canonical sources. If a docs site, sitemap, help center, or source connection should be part of the bot knowledge base, add it as a source instead.

## Fit Checks

Enable web search when:

- The use case depends on fresh public information.
- The selected model and plan support the action.
- The prompt can state when search is allowed.

Keep it off when:

- The bot should answer only from owned docs or internal content.
- The bot is public and live search would invite unsupported claims.
- The content can be ingested and auto-refreshed as a source.

Public bots force `tools.web_search.live` to `false` on update. Do not fight that guardrail.

## Operation Workflow

1. Read the bot with `get_bot`.
2. Confirm the use case and model/plan fit.
3. Save web search config with `update_bot`, preserving other `tools`.
4. Add prompt guidance for when the agent should search and when it should rely on trained sources.
5. Read the bot again and verify `tools.web_search`.

Compact save shape:

```json
{
  "tools": {
    "web_search": {
      "enabled": true,
      "live": false,
      "allowed_domains": ["example.com"]
    }
  }
}
```

`allowed_domains` is optional, capped at 20 domains, and Business-plan gated. Public bots force `live: false` on save.

## Prompt Guidance

Use narrow instructions:

- Search the web only for current public facts, recent release notes, live third-party documentation, or pages that may have changed since ingestion.
- Prefer the bot's trained sources for product policy, setup instructions, troubleshooting, and company-owned documentation.
- Cite or summarize the current source context without presenting live results as internal policy unless the source is official.

## Verification

- Saved bot read shows the intended `tools.web_search` state.
- If `allowed_domains` is set, verify normalized domains after readback.
- Widget/API deployment enables web search where applicable, such as `useWebSearch` or Chat Agent API `web_search`.
- Handoff includes why web search is enabled and any cost/safety caveat from the live docs or product policy.
