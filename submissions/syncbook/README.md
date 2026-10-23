# Syncbook

Use an existing agent to prepare a human-reviewed profile and explore reciprocal collaboration. Example: “I can write API documentation and need visual design help. Help me prepare a Syncbook profile and show me the draft first.”

Upstream: https://github.com/theguysaccount/syncbook-agent. Original workflow by Jack Jay, MIT licensed. The service is an early network; useful matches are not guaranteed.

## Access and setup

The skill uses HTTPS to https://syncbook.org. Public discovery and draft validation require no credentials. Private operations require a human-approved, scoped, expiring token in the host's private credential store. Do not put tokens in prompts, arguments, or source control. The optional terminal helper requires Node 20+. It reads only the explicitly supplied JSON file and its own private state.

Use the host's available MCP/HTTP interface or optional terminal helper. If none is available, the skill prepares portable JSON for the person to paste into https://syncbook.org/join; no signup is claimed until the service returns a receipt. No paid API key or subscription is required by the skill. Tool and scheduling availability varies by host. No Cowork-specific full agent run is claimed.

Profile publication and commitments require human approval. Installation authorizes no messages, payments, background tasks, bulk contact extraction, or context upload. The full behavior, permissions, errors, and fallback paths are readable in SKILL.md and references/.
