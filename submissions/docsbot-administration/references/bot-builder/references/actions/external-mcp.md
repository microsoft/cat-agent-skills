# External MCP Actions

Read this only from the actions index when external MCP servers are in scope.

## Scope Decision

Prefer external MCP servers for non-user-scoped lookups/actions, such as public docs, status, inventory, catalog, billing lookup with safe identifiers, or internal operations for private team bots.

Be cautious with OAuth MCP servers that inherit the bot owner's scopes. Those are usually appropriate only for internal team bots, because public customers chatting with the bot are not the OAuth user and actions cannot automatically be limited to the end customer's account.

## Operation Flow

1. Use `search_tools` only if the relevant advertised MCP tool name is unfamiliar.
2. Confirm the target server URL, label, purpose, audience, and whether it requires OAuth, custom headers, bearer tokens, or no auth.
3. Discover tools with `discover_external_mcp_tools` when the server is reachable without unresolved user auth, or when discovery is supported for that auth mode.
4. If discovery or the catalog indicates `requiresOAuth`, missing auth, or another user-owned credential state, register only the safe metadata the Admin MCP can save, then give the dashboard MCP connections deep link for connection/authorization: `https://docsbot.ai/app/bots/{botId}/configure/mcp-connections`. Do not promise the server is available until the user completes auth and a read/discovery confirms it.
5. Choose only the tool subset needed for the use case.
6. Draft metadata with `draft_mcp_server` when available.
7. Save the reviewed server entry in `mcpServers` through `update_bot`. Admin MCP can register the external MCP server on the bot, but it usually cannot complete third-party OAuth or private credential entry for the user.
8. Add prompt instructions that say when to use the MCP server and when not to.
9. Read the saved bot settings and verify the server appears with the expected tools/metadata. If auth remains incomplete, list it as a dashboard-only next step rather than a finished action.

## Safety Rules

- Do not run write-capable external MCP tools during setup unless the user explicitly authorizes that live action.
- Do not expose custom headers, OAuth tokens, or connector secrets.
- Do not ask the user to paste OAuth tokens or long-lived secrets into chat. Use the MCP connections dashboard page for authorization or credential entry whenever possible.
- Public bots should not use owner-scoped OAuth MCP tools for customer account actions unless the user explicitly accepts the scope model and risk.
- If a tool needs customer identity, add prompt rules to ask for it and refuse unsafe assumptions.
- Prefer non-user-scoped reads for public bots; reserve owner-scoped actions for internal/private bots.

## Prompt Lines

```text
Use the status MCP server only for current service status or incident questions. For product usage and setup questions, use search_documentation first.
```

```text
Use the internal billing MCP only for staff-facing account lookup after the user provides a verified account identifier. Do not use it in public anonymous chats.
```

## Verification

- Read saved `mcpServers` from bot settings.
- Confirm the prompt mentions the server's use boundary.
- Confirm OAuth/dashboard-only steps are listed in handoff if incomplete, with the deep link `https://docsbot.ai/app/bots/{botId}/configure/mcp-connections`.
- If the discovery result includes write-capable tools, document that they were not executed during verification unless explicitly authorized.
