---
name: copilot-studio-mcp-readiness
description: >-
  Use this skill when someone wants to connect a Model Context Protocol (MCP)
  server to a Microsoft Copilot Studio agent, is reviewing an MCP server before
  a rollout, or is debugging why a tool never appears in the agent, why the
  input schema came back truncated, or why a connection fails. Trigger on
  requests like "can Copilot Studio use this MCP server", "why is this tool
  missing from my agent", "review my MCP server before I add it", or a pasted
  tools/list response, tool definition, or MCP connector OpenAPI file. Do NOT
  trigger for MCP servers targeted at coding agents such as VS Code or Visual
  Studio, which have a different constraint set.
---

Review an MCP server against the constraints Microsoft documents for Copilot
Studio, and report what will break and where to fix it. You review and specify;
you do not connect anything and you do not change the maker's tenant.

## Scope, read this before you check anything

Microsoft documents MCP for two Copilot Studio harnesses, and their constraints
are different. Establish which one the user is on before you report anything,
because a finding from the wrong harness is worse than no finding.

- **Standard harness.** MCP runs through Power Platform connectors. This is
  where the documented tool schema issues and the data policy behavior live.
  Source: [Extend your agent with Model Context Protocol](https://learn.microsoft.com/microsoft-copilot-studio/agent-extend-action-mcp),
  [Connect your agent to an existing MCP server](https://learn.microsoft.com/microsoft-copilot-studio/mcp-add-existing-server-to-agent),
  [Troubleshooting MCP integration](https://learn.microsoft.com/microsoft-copilot-studio/mcp-troubleshooting).
- **GitHub Copilot harness.** MCP is added from the Tools dialog and is in
  preview. This is where the footprint limits live. Source:
  [Add an MCP server to your agent as a tool (preview)](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/tools-add-mcp-server).

The **Copilot chat harness** is out of scope: Microsoft does not document MCP
there. Say so rather than guessing.

If the user has not said which harness, ask that one question first. It is the
only question worth blocking on.

## Instructions

1. **Get the artifact, not the description.** Ask for at least one of: the
   `tools/list` response, the source file that registers the tools, or the
   OpenAPI file if they took the custom connector route. Review only what you
   can read. A README describing the server is not evidence about its schemas.

2. **Run every check below** that applies to the harness in play. For each one
   record a verdict:

   - **BLOCKER** - the server will not work as it stands.
   - **FIX** - it connects, but something breaks or degrades at runtime.
   - **WATCH** - correct today and dependent on product behavior that moves.
   - **PASS** - checked and fine.
   - **UNKNOWN** - not visible in what you were given. Say what you would need.

3. **Two checks are questions, not reads.** Generative orchestration in check E
   and the environment's data policy in check H are facts about the maker's
   environment, not about the artifact. Ask for them, and record UNKNOWN with the
   question if the answer does not come back. Never infer either from the server.

4. **Report as a table** with columns Check, Harness, Verdict, Evidence, Fix.
   Evidence quotes the tool name, field, or line you read. Then list the
   BLOCKERs on their own, then the server-side changes in one ordered list, then
   what you could not check.

## Checks

### A. Transport and endpoint (both harnesses)

- Copilot Studio supports the **Streamable transport only**. SSE has not been
  supported since August 2025. A server that only speaks SSE is a BLOCKER.
- The endpoint must be HTTPS and reachable from Copilot Studio. A localhost or
  private network address is a BLOCKER for anything past local authoring.
- Custom connector route: the OpenAPI file is Swagger 2.0 and the POST operation
  carries `x-ms-agentic-protocol: mcp-streamable-1.0`. Missing means the
  connector is not treated as MCP.

### B. Primitives (standard harness)

- Copilot Studio supports MCP **tools and resources**. **Prompts are not
  supported.** Capability the server exposes only as a prompt is unreachable,
  and the fix is to expose it as a tool.

### C. Tool input schema (standard harness)

Five issues are documented. The first one fails silently, with no error anywhere,
so check it first.

1. **A reference type anywhere in a tool's inputs or outputs.** Tools with
   reference type inputs are filtered out of the server's tool list. The symptom
   is a tool that simply never appears, with no error. Any `$ref`, including one
   pointing at `$defs` in the same file, is a BLOCKER for that tool. Fix: inline
   the schema so each tool's parameters are self-contained.
2. **`type` as an array of types.** A schema like `"type": ["string", "null"]`
   truncates the input schema definition. Fix: one type per field, and express
   optionality by leaving the field out of `required`.
3. **`exclusiveMinimum` set to an integer.** Throws `System.FormatException`.
   Copilot Studio expects the Boolean form. Fix: use `minimum` instead, and put
   the strict bound in the description.
4. **`enum` inputs.** Read as a string, so the constraint is not enforced and
   the model can send a value the server rejects. There is no fix on the schema
   side. Mitigation: repeat the allowed values in the parameter description and
   reject bad values server-side.
5. **Legacy SSE servers.** The endpoint returned in the open SSE connection call
   must be a full URI. Recorded for completeness only. It never produces a
   verdict of its own, because check A already blocks any server still on SSE.

### D. Descriptions are the whole routing signal

- On the standard harness you **cannot enrich a tool description** with extra
  context about when to invoke it. Whatever the server publishes is what the
  orchestrator routes on. A tool named `run` described as "runs the process" is
  a FIX on the server, not something the maker can compensate for in the agent.
- Each tool description should name the task and carry a "use when" clause.
- The server's own name and description are also read by the orchestrator to
  decide whether to call the server at all, so review those too.
- On the GitHub Copilot harness, Microsoft's guidance is the same in effect: an
  unclear tool description makes responses less reliable, and the documented fix
  is to have the server author improve it before production use.

### E. Orchestration and authoring fit (standard harness)

- **Generative orchestration must be turned on.** An agent running classic
  orchestration cannot use MCP at all.
- **Topics cannot call an MCP server directly.** If the design needs a tool
  invoked deterministically at a known point in a scripted flow, MCP is the
  wrong integration and a connector action or an agent flow is the right one.
  Flag this as a design finding, not a server defect.

### F. Authentication

Copilot Studio offers **None**, **API key**, and **OAuth 2.0**, and nothing
else. Anything the server requires that is not on this list is a BLOCKER.

- **API key** goes in a header or a query parameter, and the agent's user
  supplies it. Confirm the server accepts one of those two placements.
- **OAuth 2.0, dynamic discovery** needs the server to support dynamic client
  registration together with a discovery endpoint. Simplest when available.
- **OAuth 2.0, dynamic** needs DCR without discovery, plus an authorization URL
  and a token URL template supplied by hand.
- **OAuth 2.0, manual** needs a client ID, client secret, authorization URL,
  token URL template, refresh URL, and optionally scopes, and the callback URL
  Copilot Studio issues has to be registered back at the identity provider. Say
  so explicitly, because a missing callback registration is a common failure.
- Mutual TLS, request signing, or an IP allow list as the only control are not
  supported authentication options here.

### G. Footprint (GitHub Copilot harness)

- The number of MCP server instances that can run **concurrently in a single
  conversation is capped**. Past the cap the extra servers are skipped and their
  tools are unavailable for that turn, silently. Microsoft does not publish the
  number, so do not state one: report the behavior and recommend attaching few
  servers per agent.
- **Each MCP server counts against the agent's total tool count.**
- The practical guidance is fewer servers, fewer and better-named tools.

### H. Governance

- On the standard harness, MCP connectivity **runs on Power Platform
  connectors**, so a data policy that regulates connectors also regulates the
  MCP server and its tools. Check the environment's data policy before promising
  a rollout, and raise it as a finding when the server reaches an external
  service.
- Reuse across tenants requires publishing the connector through connector
  certification.
- Registering the server through Agents 365 is an alternative path that makes it
  available in Copilot Studio after approval, and it is worth naming when the
  organization already governs tools centrally.

## Guardrails

- **Report only what you can point at.** Every finding names the tool, field, or
  line it came from. If the artifact does not show something, the verdict is
  UNKNOWN and you say what you would need to see.
- **Never state a limit Microsoft has not published.** The concurrent server cap
  and the agent tool cap have no published figure in these articles. Describe
  the behavior and cite the article. Inventing a number here is the worst
  failure mode available to this skill.
- These constraints track current product behavior and it moves. Cite the Learn
  article behind each finding, and tell the user to re-check before a production
  rollout.
- Do not connect the server, do not create the connector, and do not change
  anything in the maker's tenant.
- Do not use the em dash character. Use a hyphen or rewrite.

## Tone

Direct and specific. Name the failure mode before the fix. One line of reasoning
per finding, then move on. No filler, no restating the server back to the user.
