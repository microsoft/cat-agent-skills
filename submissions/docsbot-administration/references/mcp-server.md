# DocsBot MCP Servers

DocsBot provides multiple MCP servers:

| Server | Endpoint | Tools | Best for |
| --- | --- | --- | --- |
| DocsBot | `https://mcp.docsbot.ai` | fixed named tools; `list_tool_categories`, `search_tools`, `get_tool_schema` for metadata | Administering DocsBot teams, bots, sources, members, account usage, integrations, Skills, and reporting through existing dashboard permissions. |
| Documentation MCP | `https://api.docsbot.ai/teams/{teamId}/bots/{botId}/mcp/` | `search`, `fetch` | Searching and retrieving one bot's indexed documentation/training sources. |
| Question History MCP | `https://api.docsbot.ai/teams/{teamId}/bots/{botId}/questions/mcp/` | `search`, `fetch` | Searching and retrieving prior support questions, answers, and conversation history for one bot. |

This package is for **DocsBot**.

DocsBot authentication:

- MCP endpoint: `https://mcp.docsbot.ai`
- Protected resource metadata: `https://mcp.docsbot.ai/.well-known/oauth-protected-resource`
- Authorization server metadata: `https://mcp.docsbot.ai/.well-known/oauth-authorization-server`
- Dynamic client registration: `https://mcp.docsbot.ai/oauth/register`

DocsBot uses browser-based OAuth. Authorized clients can be reviewed and revoked from **API & Integrations** in the DocsBot dashboard.
