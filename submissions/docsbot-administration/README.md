# DocsBot Administration

Manage DocsBot teams, bots, sources, members, integrations, and reporting using the hosted DocsBot Admin MCP server at `https://mcp.docsbot.ai`.

## Requirements and setup

Use a skill-capable Cowork client with a configured remote Streamable HTTP MCP connector and browser OAuth. Add the DocsBot connector, complete OAuth in the browser, and import this unpacked skill. The skill itself does not install or authenticate the connector. A DocsBot account and an accessible team are required; available operations depend on live role and plan checks.

The bundled skill uses predefined named tools and includes bot-building and answer-quality workflows. It resolves team and bot IDs before scoped actions, respects client approvals, verifies uncertain writes before retrying, and prepares voice instructions while enabling voice only when authorized. Evals workflows run only when their tools are advertised. Subscription and commerce changes are outside this skill.

Source: [DocsBot agent skills](https://github.com/uglyrobot/docsbot-agent-skills). Setup guide: [DocsBot MCP server](https://docsbot.ai/documentation/developer/mcp-server).
