# MCP Client Configuration

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
