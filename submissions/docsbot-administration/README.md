# DocsBot Administration

Manage DocsBot teams, bots, sources, members, integrations, and reporting using the hosted DocsBot Admin MCP server at `https://mcp.docsbot.ai`.

## Requirements and setup

Use a skill-capable Cowork client with a configured remote Streamable HTTP MCP connector and browser OAuth. Add the DocsBot connector, complete OAuth in the browser, and import this unpacked skill. The skill itself does not install or authenticate the connector. A DocsBot account and an accessible team are required; available operations depend on live role and plan checks.

The bundled skill uses predefined named tools and includes bot-building and answer-quality workflows. It resolves team and bot IDs before scoped actions, respects client approvals, verifies uncertain writes before retrying, and prepares voice instructions while enabling voice only when authorized. Evals workflows run only when their tools are advertised. Subscription and commerce changes are outside this skill.

Source: [DocsBot agent skills](https://github.com/uglyrobot/docsbot-agent-skills). Setup guide: [DocsBot MCP server](https://docsbot.ai/documentation/developer/mcp-server).

## Additional client setup

The following onboarding notes are for people configuring the maintained upstream package in other clients. They are not bundled into the running agent skill.

### Direct connector setup

If the MCP server is not already configured, add it to the client as a Streamable HTTP MCP server:

```json
{
  "mcpServers": {
    "docsbot": {
      "url": "https://mcp.docsbot.ai"
    }
  }
}
```

For Codex, the direct MCP setup is:

```bash
codex mcp add docsbot --url https://mcp.docsbot.ai
codex mcp login docsbot
```

For Codex plugin installation, use the marketplace package in this repository instead:

```bash
codex plugin marketplace add uglyrobot/docsbot-agent-skills
codex plugin add docsbot-administration@docsbot
```

### Client-specific installation

## Generic Streamable HTTP MCP

```json
{
  "mcpServers": {
    "docsbot": {
      "url": "https://mcp.docsbot.ai"
    }
  }
}
```

## Codex Direct MCP

```bash
codex mcp add docsbot --url https://mcp.docsbot.ai
codex mcp login docsbot
```

## Codex Plugin Marketplace

```bash
codex plugin marketplace add uglyrobot/docsbot-agent-skills
codex plugin add docsbot-administration@docsbot
```

Then start a new Codex thread and ask Codex to use DocsBot.

## Claude Chat, Cowork, And Claude Code

The package uses `.claude-plugin/plugin.json`, root `skills/`, and `.mcp.json`. Claude chat and Cowork install through **Customize → Plugins → Add**, then connect DocsBot from the plugin’s **Connectors** tab. Direct remote connectors use **Settings → Connectors**, rather than `claude_desktop_config.json`. Claude Code installs through its plugin marketplace and authenticates with `/mcp`.

See [Claude’s package reference](https://claude.com/docs/plugins/build) and [remote connector setup](https://support.claude.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers).

## Cursor

Cursor accepts Agent Plugins v1 and `.cursor-plugin/plugin.json`. Official listing review is pending; direct MCP is available through the generic configuration above. Project `.agents/skills/` installation does not automatically reach Cloud Agents. [Official plugin reference](https://prod.cursor.com/docs/reference/plugins).

## Grok Build, Consumer Grok, And xAI API

Grok Build reads the Claude-compatible plugin package without a separate Grok manifest. Review the package before explicitly trusting it:

```bash
grok plugin marketplace add uglyrobot/docsbot-agent-skills
grok plugin install docsbot-administration --trust
```

For direct MCP, use `grok mcp add --transport http docsbot https://mcp.docsbot.ai` and complete its OAuth flow. [Plugin compatibility](https://docs.x.ai/build/features/skills-plugins-marketplaces), [CLI guide](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/09-plugins.md), [MCP setup](https://docs.x.ai/build/features/mcp-servers).

Consumer Grok adds a custom MCP connector at [Grok Connectors](https://grok.com/connectors), with organization provisioning for Business and Enterprise. This is separate from installing skills or plugin ZIPs. [Connector documentation](https://docs.x.ai/grok/connectors).

The xAI API receives a remote MCP tool in each request with application-managed `authorization`; do not assume a browser OAuth or registration flow in the API. [API documentation](https://docs.x.ai/developers/tools/remote-mcp).

## Admin Tool Compatibility

This package requires fixed named Admin tools. If MCP `tools/list` still shows the old Admin `search`/`execute` dispatcher, complete the server and plugin migration before using the updated workflow. Old dispatcher calls fail once the new server is deployed. Update the package, refresh advertised tools, and start a new session if needed. Per-bot Documentation Search and Question History retain `search`/`fetch`. Marketplace availability depends on the relevant listing approval.

## Other Agent Skills Clients

Copy or install the folder:

```text
skills/docsbot-administration/
```

into the client's skills directory. Then configure the MCP server using that client's remote MCP setup flow.

### OAuth discovery and access management

DocsBot authentication:

- MCP endpoint: `https://mcp.docsbot.ai`
- Protected resource metadata: `https://mcp.docsbot.ai/.well-known/oauth-protected-resource`
- Authorization server metadata: `https://mcp.docsbot.ai/.well-known/oauth-authorization-server`
- Dynamic client registration: `https://mcp.docsbot.ai/oauth/register`

DocsBot uses browser-based OAuth. Authorized clients can be reviewed and revoked from **API & Integrations** in the DocsBot dashboard.
